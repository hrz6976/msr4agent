import re
import json
import os
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple, Optional
import requests
from bs4 import BeautifulSoup
from github import Github, GithubException
from itertools import cycle
import time

DEFAULT_INPUT_FILE = ""
DEFAULT_OUTPUT_FILE = ""
TOKEN_FILE_PATH = ""
MAX_WORKERS = 10

CORE_CONTEXT_PATTERNS = [r'https?://github\.com/([^/]+)/([^/]+)/(issues|pull)/(\d+)']
TEMPLATE_PATTERNS = [
    r'\.(png|jpe?g|gif|svg)$',
    r'github\.com/.*/(blob|tree)/(main|master)/(CONTRIBUTING|CODE_OF_CONDUCT|SECURITY)',
    r'stackoverflow\.com/(questions|users|tags)/'
    r'www\.sphinx-doc\.org/en/master/internals/contributing\.html',
    r'docs\.astropy\.org/en/latest/development/workflow',
    r'docs\.astropy\.org/en/latest/development/((doc|test|code)guide|when_to_rebase)\.html',
    r'matplotlib\.org/(devdocs/devel/contribute|devel/gitwash/development_workflow|devel/documenting_mpl)\.html',
    r'scikit-learn\.org/dev/faq\.html',
    r'flake8\.pycqa\.org',
    r'reproducible-builds\.org',
    r'docutils\.sourceforge\.io',
    r'code\.google\.com/p/sympy/issues/',
    r'tinyurl\.com',
    r'groups\.google\.com/forum/',
]

_tokens: list = []
_token_cycler: Optional[cycle] = None
_token_lock = threading.Lock()

def find_urls_in_text(text: str) -> List[str]:
    if not isinstance(text, str) or not text:
        return []
    url_pattern = re.compile(r'https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+!?*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    found_urls = url_pattern.findall(text)
    trailing_punctuation = '.,:;!?)]}>'
    cleaned_urls = [url.rstrip(trailing_punctuation) for url in found_urls]
    return cleaned_urls

def parse_keywords_to_urls(text: str, repo_owner: str, repo_name: str) -> List[str]:
    keyword_pattern = re.compile(r'\b(?:closes|closed|close|fixes|fixed|fix|resolves|resolved|resolve)\s+#(\d+)\b', re.IGNORECASE)
    issue_numbers = keyword_pattern.findall(text)
    if repo_name == 'django':
        return [f"https://code.djangoproject.com/ticket/{number}" for number in issue_numbers if str(number) != '0000']
    else:
        return [f"https://github.com/{repo_owner}/{repo_name}/issues/{number}" for number in issue_numbers if str(number) != '0000']

def classify_url(url: str) -> Tuple[str, Any]:
    for pattern in CORE_CONTEXT_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return "core", match
    for pattern in TEMPLATE_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return "template", None
    return "supplemental", None

def _load_tokens():
    global _tokens, _token_cycler
    if _tokens:
        return
    try:
        token_path = TOKEN_FILE_PATH or 'tokens.txt'
        with open(token_path, 'r') as f:
            _tokens = [line.strip() for line in f if line.strip()]
        if not _tokens:
            print(f"[Warning] Token file '{token_path}' is empty. Will proceed with unauthenticated requests.")
            _tokens.append(None)
        else:
            print(f"Tokens loaded. Available tokens: {len([t for t in _tokens if t])}.")
        _token_cycler = cycle(_tokens)
    except FileNotFoundError:
        token_path = TOKEN_FILE_PATH or 'tokens.txt'
        print(f"[Warning] Token file '{token_path}' not found. Will proceed with unauthenticated requests.")
        _tokens.append(None)
        _token_cycler = cycle(_tokens)

def _get_next_token() -> Optional[str]:
    with _token_lock:
        if not _token_cycler:
            _load_tokens()
        return next(_token_cycler)

def fetch_github_content(url: str) -> Optional[str]:
    match = re.search(r'github\.com/([^/]+)/([^/]+)/(issues|pull)/(\d+)', url)
    if not match:
        return None
    owner, repo_name, url_type, number = match.groups()
    number = int(number)
    
    for _ in range(len(_tokens) + 1):
        try:
            token = _get_next_token()
            g = Github(token)
            repo = g.get_repo(f"{owner}/{repo_name}")
            item = repo.get_pull(number) if url_type == 'pull' else repo.get_issue(number)
            title = item.title
            body = item.body or ""
            return title + "<SPLITSPLITSPLIT>" + body
        except GithubException as e:
            if e.status == 403 and 'rate limit' in str(e.data).lower():
                print(f"Rate limit hit for a token. Retrying with next token for {url}...")
                time.sleep(1)
                continue
            else:
                print(f"Failed to fetch content from {url}: {e}")
                return None
        except Exception as e:
            print(f"An unexpected error occurred for {url}: {e}")
            return None
    print(f"All tokens failed for {url}. Giving up.")
    return None

def fetch_supplemental_content(url: str) -> Optional[str]:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content_selectors = [
            'main', 'article', '#content', '#main-content', 
            '.post-content', '.entry-content', '#main', '.main'
        ]
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        if not main_content:
            main_content = soup.find('body')
        if not main_content:
            return None

        noise_selectors = [
            'nav', 'footer', 'header', 'aside', '#sidebar', '.sidebar',
            '.comments', '#comments', '.ads', '.advertisement', 'script', 'style',
            'img', 'svg', 'button', 'input'
        ]
        for selector in noise_selectors:
            for element in main_content.select(selector):
                element.decompose()

        text = main_content.get_text(separator='\n', strip=True)
        cleaned_text = "\n".join(line for line in text.splitlines() if line.strip())
        return cleaned_text if cleaned_text else None
    except requests.RequestException as e:
        print(f"Failed to fetch content from {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing HTML from {url}: {e}")
        return None

def process_single_url(url: str) -> Optional[Dict[str, Any]]:
    url_type, _ = classify_url(url)
    entry = {"url": url, "type": url_type, "content": None}

    if url_type == "core":
        entry["content"] = fetch_github_content(url)
    elif url_type == "supplemental":
        entry["content"] = fetch_supplemental_content(url)

    time.sleep(2)

    if entry["content"]:
        return entry
    else:
        return None

def enrich_pr_data(pr_data: Dict[str, Any], executor: ThreadPoolExecutor) -> Dict[str, Any]:
    pr_body = pr_data.get('body') or ""
    pr_title = pr_data.get('title') or ""
    repo_owner, repo_name = pr_data['id'].split('/')[:2]

    raw_urls = find_urls_in_text(pr_title) + find_urls_in_text(pr_body)
    keyword_urls = parse_keywords_to_urls(pr_title, repo_owner, repo_name) + parse_keywords_to_urls(pr_body, repo_owner, repo_name)
    all_urls_to_process = sorted(list(set(raw_urls + keyword_urls)))

    enriched_urls = []
    results = executor.map(process_single_url, all_urls_to_process)

    for result in results:
        if result:
            enriched_urls.append(result)

    return {
        "id": pr_data.get("id"),
        "urls": enriched_urls
    }

def main():
    parser = argparse.ArgumentParser(
        description="Extract URLs from PR data, fetch content concurrently, and generate an enriched JSONL file."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT_FILE,
        help=f"Input JSONL file path. "
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output enriched JSONL file path. "
    )
    args = parser.parse_args()

    input_file = args.input 
    output_file = args.output

    _load_tokens()

    lines_dict = {}
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()
            for line in lines:
                pr_data = json.loads(line)
                pr_id = pr_data.get('id')
                if pr_id:
                    lines_dict[pr_id] = pr_data
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_file}'")
        return

    completed_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f_out_check:
            for line in f_out_check:
                try:
                    completed_data = json.loads(line)
                    pr_id = completed_data.get('id')
                    if not pr_id or pr_id not in lines_dict:
                        continue
                    
                    completed_urls_content = completed_data.get('urls', [])
                    completed_urls = {content['url'] for content in completed_urls_content if content}
                    
                    pr_data = lines_dict[pr_id]
                    pr_body = pr_data.get('body', "")
                    pr_title = pr_data.get('title', "")
                    repo_owner, repo_name = pr_data['id'].split('/')[:2]
                    
                    raw_urls = find_urls_in_text(pr_title) + find_urls_in_text(pr_body)
                    keyword_urls = parse_keywords_to_urls(pr_title, repo_owner, repo_name) + parse_keywords_to_urls(pr_body, repo_owner, repo_name)
                    all_urls = set(raw_urls + keyword_urls)
                    
                    is_complete = True
                    for url in all_urls:
                        url_type, _ = classify_url(url)
                        if url_type in ("supplemental", "core"):
                            if url not in completed_urls:
                                is_complete = False
                                break
                    if is_complete:
                        completed_ids.add(pr_id)
                except (json.JSONDecodeError, KeyError):
                    continue
        if completed_ids:
            print(f"Detected existing output file, loaded {len(completed_ids)} completed item IDs.")

    tasks_to_run = [data for pr_id, data in lines_dict.items() if pr_id not in completed_ids]
    total_tasks_to_run = len(tasks_to_run)
    print(f"Total items to process: {total_tasks_to_run}")

    with open(output_file, 'a', encoding='utf-8') as outfile, \
         ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        for i, pr_data in enumerate(tasks_to_run, 1):
            pr_id = pr_data.get('id')
            try:
                print(f"Processing PR {pr_id} ({i}/{total_tasks_to_run})...")
                enriched_data = enrich_pr_data(pr_data, executor)
                if enriched_data:
                    outfile.write(json.dumps(enriched_data) + '\n')
                    outfile.flush()
            except Exception as e:
                print(f"An error occurred while processing PR {pr_id}: {e}")

    print(f"\nProcessing complete! Results saved to: {output_file}")

if __name__ == "__main__":
    main()
