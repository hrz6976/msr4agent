import os
import json
import re
from collections import Counter, defaultdict
from packaging import version
from datetime import datetime, timezone
import fnmatch

cnt_before = 0
cnt_after = 0

def load_target_versions(filepath: str) -> dict:
    target_versions = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                repo = data.get("repo")
                ver_str = data.get("version")
                date_str = data.get("commit_date")
                if not all([repo, ver_str, date_str]):
                    continue
                try:
                    parsed_ver = version.parse(ver_str)
                    parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    target_versions[repo] = {
                        "version": parsed_ver,
                        "commit_date": parsed_date
                    }
                except (version.InvalidVersion, ValueError, TypeError) as e:
                    print(f"Warning: Could not parse entry for {repo}: {e}")
                    continue
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return {}
    print(f"Successfully loaded target versions for {len(target_versions)} repositories.")
    return target_versions

TARGET_VERSIONS_DATA = load_target_versions("swebench_versions.jsonl")

def compare_pr_to_target_version(pr_item: dict) -> str:
    repo_name = '/'.join(pr_item.get("id", "").split('/')[:2])
    merged_at_str = pr_item.get("merged_at")

    pr_merged_at_date = datetime.fromisoformat(merged_at_str.replace('Z', '+00:00'))
    target_data = TARGET_VERSIONS_DATA[repo_name]
    target_commit_date = target_data["commit_date"]
    is_date_later = pr_merged_at_date > target_commit_date
    if is_date_later:
        return "after"
    is_date_same = pr_merged_at_date == target_commit_date
    if is_date_same:
        return "same"
    else:
        return "before"

def is_bot_user(user_login: str | None) -> bool:
    if not user_login:
        return False
    user_lower = user_login.lower()

    known_bots = {
        'dependabot[bot]', 'renovate[bot]', 'pre-commit-ci[bot]',
        'github-actions[bot]', 'snyk-bot', 'pyup-bot', 'codecov[bot]',
        'styleci[bot]', 'greenkeeper[bot]', 'release-please[bot]',
        'weblate',
    }
    if user_lower in known_bots:
        return True

    bot_patterns = [
        re.compile(r'\[bot\]$'),
        re.compile(r'[-_]bot$'),
        re.compile(r'^bot[-_]'),
    ]
    if any(pattern.search(user_lower) for pattern in bot_patterns):
        return True
    return False

def is_functional_file_pr(pr_item: dict) -> bool:
    global cnt_before, cnt_after

    OTHER_FUNCTIONAL_EXTENSIONS = {
        '.c', '.cpp', '.h', '.hpp', '.m', '.mm', '.cs', '.go', '.rs', '.swift',
        '.java', '.kt', '.kts', '.scala', '.groovy',
        '.js', '.jsx', '.ts', '.tsx', '.vue',
        '.php', '.rb', '.pl', '.lua', '.sh',
    }

    NON_CORE_PATTERNS = [
        '*test*',
        '*build*',
        '*dist*',
        '*bench*',
        'node_modules',
        'doc*',
        'example*',
    ]

    CORE_DIRS = {
        'astropy', 'django', 'src', 'lib', 'seaborn', 'requests', 'xarray', 'xray', 'flask', 'pylint', 'sklearn', 'sphinx', 'sympy'
    }

    def extract_core_functional_files(pr_item: dict) -> list[dict]:
        repo_name = '/'.join(pr_item.get("id").split('/')[:2])
        changed_files = pr_item.get("files", [])
        if not changed_files:
            return []

        potential_core_py_files = []
        for file_info in changed_files:
            filename = file_info.get("filename", "")
            if not filename:
                continue
            path_parts = os.path.normpath(filename).split(os.sep)

            if repo_name == 'pytest-dev/pytest':
                is_non_core = any(
                    fnmatch.fnmatch(part, pattern)
                    for part in path_parts if part not in ['_pytest', 'pytest']
                    for pattern in NON_CORE_PATTERNS
                )
            else:
                is_non_core = any(
                    fnmatch.fnmatch(part, pattern)
                    for part in path_parts
                    for pattern in NON_CORE_PATTERNS
                )
            if is_non_core:
                continue

            if path_parts[0] not in CORE_DIRS:
                continue

            if any(filename.endswith(ext) for ext in OTHER_FUNCTIONAL_EXTENSIONS):
                return []

            if filename.endswith(".py"):
                potential_core_py_files.append(filename)

        return potential_core_py_files

    def check_file_type_and_path_condition(core_files: list[dict]) -> bool:
        return bool(core_files)

    def check_change_persistence_condition(pr_item: dict, core_files: list[dict]) -> bool:
        if not core_files:
            return False
        all_files_stats = pr_item.get("files_stats", [])
        if not all_files_stats:
            return False

        stats_map = {stat.get("filename"): stat for stat in all_files_stats}

        for filename in core_files:
            file_stat = stats_map.get(filename)
            if not file_stat:
                continue
            if file_stat.get("status") != "persistent":
                return False
            if file_stat.get("change_lines_count", 0) > 0:
                return False
        return True

    core_files = extract_core_functional_files(pr_item)
    if not check_file_type_and_path_condition(core_files):
        return False

    result = compare_pr_to_target_version(pr_item)

    benchmark_dir = ""
    write_file_path = os.path.join(benchmark_dir, 'benchmark.jsonl')

    if result == "after":
        cnt_after += 1
        with open(write_file_path, 'a', encoding='utf-8') as file:
            pr_item_new = {
                "id": pr_item["id"],
                "number": pr_item["number"],
                "milestone": pr_item["milestone"],
                "history": "after",
                "core_files": core_files,
                "title": pr_item["title"],
                "body": pr_item["body"],
                "labels": pr_item["labels"],
                "files": pr_item["files"]
            }
            json_string = json.dumps(pr_item_new, ensure_ascii=False)
            file.write(json_string + '\n')
        return True

    if result == "before" or result == "same":
        if check_change_persistence_condition(pr_item, core_files):
            cnt_before += 1
            with open(write_file_path, 'a', encoding='utf-8') as file:
                pr_item_new = {
                    "id": pr_item["id"],
                    "number": pr_item["number"],
                    "milestone": pr_item["milestone"],
                    "history": "before-same",
                    "core_files": core_files,
                    "title": pr_item["title"],
                    "body": pr_item["body"],
                    "labels": pr_item["labels"],
                    "files": pr_item["files"]
                }
                json_string = json.dumps(pr_item_new, ensure_ascii=False)
                file.write(json_string + '\n')
            return True

    return False

def is_function_label_pr(pr_item: dict) -> bool:
    functional_labels = [
        "feature", "enhancement", "performance", "refactor", "api", "proposal",
    ]

    non_functional_labels = [
        "bug", "crash", "regression", "doc", "test", "build", "dependen", "install", "packag"
    ]

    pr_labels_lower = {label.lower() for label in pr_item.get("labels", [])}

    for label in pr_labels_lower:
        if any(keyword in label for keyword in functional_labels):
            return True

    for label in pr_labels_lower:
        if any(keyword in label for keyword in non_functional_labels):
            return False

    return True

def filter_data(pr_list):
    remaining_items = list(pr_list)
    remaining_items = [pr for pr in remaining_items if pr.get("merged")]
    remaining_items = [pr for pr in remaining_items if pr.get("milestone")]
    remaining_items = [pr for pr in remaining_items if not is_bot_user(pr.get("user"))]
    remaining_items = [pr for pr in remaining_items if len((pr.get("body") or "").strip()) + len((pr.get("title") or "").strip()) >= 50]
    main_branches = ['main', 'master', 'develop', 'dev']
    remaining_items = [pr for pr in remaining_items if pr.get("base_branch") in main_branches]
    remaining_items = [pr for pr in remaining_items if (pr.get("comments_count", 0) + pr.get("review_comments_count", 0)) >= 1]
    remaining_items = [pr for pr in remaining_items if is_function_label_pr(pr)]
    remaining_items = [pr for pr in remaining_items if is_functional_file_pr(pr)]

    print(f"\nFinal filtering result: {len(remaining_items)} items")
    return remaining_items

def process_jsonl_files_for_repo(repo_dir, repo_name):
    print(f"\n--- Processing repository: {repo_name} ---")
    datas = []
    source_file_path = os.path.join(repo_dir, repo_name + '.jsonl')
    
    if not os.path.exists(source_file_path):
        print(f"Warning: Source file '{source_file_path}' not found, skipping.")
        return 0

    with open(source_file_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            try:
                data = json.loads(line)
                datas.append(data)
            except json.JSONDecodeError:
                continue

    datas_filter = filter_data(datas)
    return len(datas_filter)

if __name__ == "__main__":
    repo_names = [
        "astropy/astropy", "django/django", "matplotlib/matplotlib",
        "mwaskom/seaborn", "pallets/flask", "psf/requests",
        "pydata/xarray", "pylint-dev/pylint", "pytest-dev/pytest",
        "scikit-learn/scikit-learn", "sphinx-doc/sphinx", "sympy/sympy"
    ]

    total_processed_items = 0
    current_script_dir = os.getcwd()
    
    for repo_name_raw in repo_names:
        repo_folder_name = repo_name_raw.replace('/', '__')
        repo_directory = os.path.join(current_script_dir, 'process_file_change')
        
        if not os.path.isdir(repo_directory):
            print(f"\nWarning: Repository directory '{repo_directory}' does not exist, skipping.")
            continue
            
        count = process_jsonl_files_for_repo(repo_directory, repo_folder_name)
        total_processed_items += count
        
        print(f"{repo_name_raw} produced {count} items. 'before' items: {cnt_before}, 'after' items: {cnt_after}")
        cnt_before = 0
        cnt_after = 0

    print(f"\nTotal items processed and output: {total_processed_items}.")
