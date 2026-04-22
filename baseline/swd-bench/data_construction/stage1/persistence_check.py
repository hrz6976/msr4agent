import os
import json
import subprocess

TARGET_REPO_VERSIONS = {
    "astropy/astropy": "5.2",
    "django/django": "5.0",
    "matplotlib/matplotlib": "3.7",
    "mwaskom/seaborn": "0.12",
    "pallets/flask": "2.3",
    "psf/requests": "2.27",
    "pydata/xarray": "2022.09",
    "pylint-dev/pylint": "3.0",
    "pytest-dev/pytest": "7.2",
    "scikit-learn/scikit-learn": "1.3",
    "sphinx-doc/sphinx": "7.2",
    "sympy/sympy": "1.12"
}

REPOSITORIES_CHECKOUT_DIR = ""
SWE_BENCH_VERSIONS_FILE = "swebench_versions.jsonl"

def load_version_checkout_paths(swe_bench_file):
    version_map = {}
    if not os.path.exists(swe_bench_file):
        raise FileNotFoundError(f"Error: SWE Bench version file '{swe_bench_file}' not found.")

    with open(swe_bench_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            repo = data['repo']
            version = data['version']
            base_commit = data['base_commit']
            repo_folder_name = f"{repo.replace('/', '-')}_{base_commit}"
            checkout_path = os.path.join(REPOSITORIES_CHECKOUT_DIR, repo_folder_name)
            version_map[(repo, version)] = checkout_path
    return version_map

def get_added_lines_from_patch(patch_text):
    if not patch_text:
        return []
    added_lines = []
    for line in patch_text.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            code_line = line[1:]
            if not is_comment_or_empty(code_line):
                added_lines.append(code_line.strip())
    return added_lines

def is_comment_or_empty(line):
    stripped_line = line.strip()
    if not stripped_line or stripped_line.startswith('#'):
        return True
    return False

def find_file_rename_history(repo_path, start_commit, old_filepath):
    if os.path.exists(os.path.join(repo_path, old_filepath)):
        return old_filepath

    command = [
        'git', 'log', '--follow', '--name-status', '--pretty=format:%H',
        start_commit, '--', old_filepath
    ]

    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            errors='ignore'
        )

        lines = result.stdout.strip().split('\n')

        for i in range(len(lines) - 1):
            if lines[i+1].startswith('R'):
                parts = lines[i+1].split('\t')
                if len(parts) == 3:
                    new_path_in_history = parts[2]
                    if os.path.exists(os.path.join(repo_path, new_path_in_history)):
                        print(f"  [Trace] File '{old_filepath}' was renamed to '{new_path_in_history}' in the target version.")
                        return new_path_in_history
        return None

    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def check_changes_in_version(pr_file_changes, version_checkout_path):
    original_filename = pr_file_changes['filename']

    current_filename_in_version = find_file_rename_history(
        repo_path=version_checkout_path,
        start_commit='HEAD',
        old_filepath=original_filename
    )

    stats = {
        "change_lines_count": len(pr_file_changes['added_lines']),
        "target_file_lines_count": 0,
        "unmatched_lines_count": 0,
        "unmatched_lines": [],
        "status": "persistent"
    }

    if not current_filename_in_version:
        stats["status"] = "file_not_found"
        stats["unmatched_lines_count"] = stats["change_lines_count"]
        stats["unmatched_lines"] = pr_file_changes['added_lines']
        return stats

    target_file_path = os.path.join(version_checkout_path, current_filename_in_version)

    added_lines_to_check = pr_file_changes['added_lines']
    if not added_lines_to_check:
        stats["status"] = "only_comments_or_deletions"
        return stats

    try:
        with open(target_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            target_content_lines = f.readlines()
    except Exception as e:
        print(f"  - Failed to read file '{target_file_path}': {e}")
        stats["status"] = "read_error"
        stats["unmatched_lines_count"] = stats["change_lines_count"]
        stats["unmatched_lines"] = added_lines_to_check
        return stats

    target_code_lines = [line for line in target_content_lines if not is_comment_or_empty(line)]
    stats["target_file_lines_count"] = len(target_code_lines)
    target_lines_stripped = {line.strip() for line in target_code_lines}

    unmatched = [line for line in added_lines_to_check if line not in target_lines_stripped]
    stats["unmatched_lines_count"] = len(unmatched)
    stats["unmatched_lines"] = unmatched

    if stats["unmatched_lines_count"] > 0:
        stats["status"] = "partially_or_fully_changed"

    return stats

def process_repo(repo_name, repo_crawl_dir, version_map, output_dir):
    print(f"\n--- Starting to process repository: {repo_name} ---")

    output_file_path = os.path.join(output_dir, f"{repo_name.replace('/', '__')}.jsonl")

    processed_pr_ids = set()
    if os.path.exists(output_file_path):
        with open(output_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    processed_pr_ids.add(json.loads(line)['id'])
                except (json.JSONDecodeError, KeyError):
                    continue
        print(f"  - Found {len(processed_pr_ids)} processed records, they will be skipped.")

    all_prs_data = []
    for filename in os.listdir(repo_crawl_dir):
        if filename.endswith('.jsonl') and 'prs' in filename:
            source_file_path = os.path.join(repo_crawl_dir, filename)
            with open(source_file_path, 'r', encoding='utf-8') as infile:
                for line in infile:
                    pr_data = json.loads(line)
                    if pr_data.get('id') not in processed_pr_ids:
                        all_prs_data.append(pr_data)

    if not all_prs_data:
        print("  - No new PR data to process, skipping.")
        return 0

    print(f"  - Loaded {len(all_prs_data)} new PR data entries. Starting analysis...")

    target_version = TARGET_REPO_VERSIONS[repo_name]
    version_key = (repo_name, target_version)
    if version_key not in version_map:
        return 0
    checkout_path = version_map[version_key]
    if not os.path.isdir(checkout_path):
        return 0

    processed_count = 0
    with open(output_file_path, 'a', encoding='utf-8') as outfile:
        for pr_data in all_prs_data:
            pr_data["files_stats"] = []
            if pr_data.get('files'):
                for pr_file in pr_data['files']:
                    if pr_file["filename"].endswith('.py'):
                        added_lines = get_added_lines_from_patch(pr_file.get('patch'))
                        if pr_file['status'] in ('added', 'modified') and added_lines:
                            pr_file_changes = {
                                "filename": pr_file['filename'],
                                "added_lines": added_lines
                            }
                            file_stats = check_changes_in_version(pr_file_changes, checkout_path)
                            file_stats['filename'] = pr_file['filename']
                            pr_data["files_stats"].append(file_stats)

            outfile.write(json.dumps(pr_data, ensure_ascii=False) + '\n')
            processed_count += 1

    return processed_count

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    output_dir = os.path.join(script_dir, "process_file_change")
    swe_bench_file_path = os.path.join(script_dir, SWE_BENCH_VERSIONS_FILE)
    crawl_base_dir = os.path.join(script_dir, "crawl")

    os.makedirs(output_dir, exist_ok=True)

    try:
        version_checkout_map = load_version_checkout_paths(swe_bench_file_path)
        print(f"Successfully loaded repository path information for {len(version_checkout_map)} versions.")
    except FileNotFoundError as e:
        print(e)
        exit(1)

    repo_names = list(TARGET_REPO_VERSIONS.keys())
    total_processed_items = 0

    for repo_name in repo_names:
        repo_folder_name = repo_name.replace('/', '__')
        repo_crawl_directory = os.path.join(crawl_base_dir, repo_folder_name)

        if not os.path.isdir(repo_crawl_directory):
            print(f"\nWarning: Crawl directory '{repo_crawl_directory}' for repository does not exist, skipping.")
            continue

        count = process_repo(repo_name, repo_crawl_directory, version_checkout_map, output_dir)
        total_processed_items += count

    print("\n\n--- All repositories processed ---")
    print(f"Total items processed: {total_processed_items}.")
