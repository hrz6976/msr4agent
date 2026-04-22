import requests
from bs4 import BeautifulSoup
import json
import time
from tqdm import tqdm
import re
import os
import threading
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from github import Github, RateLimitExceededException, UnknownObjectException
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64

REPO_NAME = "django/django"
BASE_URL = "https://code.djangoproject.com"
TOKEN_FILE = ""
MAX_WORKERS = 4

VERSIONS_TO_SCRAPE = [
    "5.2", "5.1", "5.0", "4.2", "4.1", "4.0",
    "3.2", "3.1", "3.0", "2.2", "2.1", "2.0"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_rendered_html_for_django_issue(url):
    linked_pr_ids = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000)
            pr_header_locator = page.locator('th:has-text("Pull Requests:")')
            pr_header_locator.wait_for(timeout=5000)
            pr_data_td_locator = pr_header_locator.locator('xpath=./following-sibling::td')
            links = pr_data_td_locator.locator('a').all()
            for link_locator in links:
                href = link_locator.get_attribute('href')
                if href:
                    match = re.search(r'/pull/(\d+)', href)
                    if match:
                        linked_pr_ids.append(int(match.group(1)))
        except PlaywrightTimeoutError:
            pass
        except Exception as e:
            print(f"An unexpected error occurred while processing {url}: {e}")
        finally:
            browser.close()
    return linked_pr_ids

def get_issue_links_for_version(version):
    print(f"\nFetching issue list for Django version {version}...")
    query_params = {
        "status": "closed", "version": version, "order": "id",
        "desc": "1", "max": 10000
    }
    list_url = f"{BASE_URL}/query"

    try:
        response = requests.get(list_url, params=query_params, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to get issue list for version {version}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", class_="listing tickets")
    if not table:
        print(f"Could not find issue table on page for version {version}.")
        return []

    issue_links = [BASE_URL + row.find("td", class_="id").a["href"] for row in table.find_all("tr")[1:] if row.find("td", class_="id") and row.find("td", class_="id").a]
    print(f"Found {len(issue_links)} issues.")
    return issue_links

def scrape_issue_details(issue_url, milestone_title):
    try:
        response = requests.get(issue_url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to access issue page {issue_url}: {e}")
        return None
    soup = BeautifulSoup(response.text, "html.parser")

    script_tag_content = soup.find("script", string=re.compile(r"var old_values\s*="))
    if not script_tag_content:
        print(f"Error: Could not find 'old_values' script tag on {issue_url}.")
        return None

    match = re.search(r"var old_values\s*=\s*({.*?});", script_tag_content.string, re.DOTALL)
    if not match:
        print(f"Error: Could not match 'old_values' object on {issue_url}.")
        return None

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse old_values JSON on {issue_url}: {e}")
        return None

    linked_pr_ids = get_rendered_html_for_django_issue(issue_url)
    issue_number = data.get('id')
    state = data.get('status')
    keywords = data.get('keywords', "")
    owner = data.get('owner')

    return {
        "id": f"{REPO_NAME}/issue/{issue_number}" if issue_number else None,
        "number": issue_number,
        "title": data.get('summary'),
        "body": data.get('description'),
        "state": state,
        "created_at": data.get('time'),
        "updated_at": data.get('changetime'),
        "closed_at": data.get('changetime') if state == 'closed' else None,
        "user": data.get('reporter'),
        "labels": [kw.strip() for kw in keywords.split(',') if kw.strip()],
        "assignees": [owner] if owner and owner != "nobody" else [],
        "milestone": milestone_title,
        "comments_count": None,
        "html_url": issue_url,
        "linked_pull_requests": linked_pr_ids,
        "link": issue_url
    }

def load_tokens(token_file):
    token_path = token_file or "tokens.txt"
    if not os.path.exists(token_path):
        print(f"Error: Token file '{token_path}' not found.")
        return []
    with open(token_path, 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]
    if not tokens:
        print(f"Warning: Token file '{token_path}' is empty or contains no valid tokens.")
    return tokens

class TokenManager:
    def __init__(self, tokens):
        if not tokens:
            raise ValueError("Token list cannot be empty.")
        self.tokens = tokens
        self.idx = 0
        self.lock = threading.Lock()

    def get_github_instance(self):
        with self.lock:
            token = self.tokens[self.idx]
            self.idx = (self.idx + 1) % len(self.tokens)
            return Github(token, retry=5, timeout=30)

def fetch_pr_info(github_instance, pr_number, repo_name, milestone_title):
    repo = github_instance.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    pr_info = {
        "id": f"{repo_name}/pr/{pr.number}", "number": pr.number, "title": pr.title,
        "body": pr.body, "state": pr.state,
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
        "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
        "user": pr.user.login if pr.user else None,
        "author_association": pr.author_association, "merged": pr.merged,
        "merged_by": pr.merged_by.login if pr.merged_by else None,
        "merge_commit_sha": pr.merge_commit_sha, "milestone": milestone_title,
        "assignees": [a.login for a in pr.assignees],
        "requested_reviewers": [r.login for r in pr.requested_reviewers],
        "requested_teams": [t.name for t in pr.requested_teams],
        "labels": [l.name for l in pr.labels],
        "base_branch": pr.base.ref, "base_sha": pr.base.sha,
        "head_branch": pr.head.ref, "head_sha": pr.head.sha,
        "html_url": pr.html_url, "diff_url": pr.diff_url, "patch_url": pr.patch_url,
        "issue_url": pr.issue_url,
        "is_cross_repository": pr.head.repo.full_name != pr.base.repo.full_name if pr.head.repo and pr.base.repo else None,
        "auto_merge": pr.auto_merge, "comments_count": pr.comments,
        "review_comments_count": pr.review_comments, "commits_count": pr.commits,
        "additions": pr.additions, "deletions": pr.deletions, "changed_files": pr.changed_files,
    }

    files = []
    try:
        for f in pr.get_files():
            file_data = {
                "filename": f.filename, "status": f.status, "additions": f.additions,
                "deletions": f.deletions, "changes": f.changes, "patch": f.patch,
                "blob_url": f.blob_url, "raw_url": f.raw_url,
                "base_content": None, "head_content": None
            }
            try:
                base_file = repo.get_contents(f.filename, ref=pr.base.sha)
                file_data["base_content"] = base64.b64decode(base_file.content).decode('utf-8', 'ignore')
            except Exception:
                pass
            try:
                head_file = repo.get_contents(f.filename, ref=pr.head.sha)
                file_data["head_content"] = base64.b64decode(head_file.content).decode('utf-8', 'ignore')
            except Exception:
                pass
            files.append(file_data)
    except Exception as e:
        print(f"Warning: Failed to get file list for PR #{pr_number}: {e}")

    pr_info["files"] = files
    return pr_info

def pr_worker(token_manager, pr_number, repo_name, milestone_title):
    while True:
        try:
            github_instance = token_manager.get_github_instance()
            return fetch_pr_info(github_instance, pr_number, repo_name, milestone_title)
        except RateLimitExceededException:
            print(f"Warning: Rate limit exceeded for PR #{pr_number}. Waiting 60s before retrying with a new token...")
            time.sleep(random.uniform(50, 60))
        except UnknownObjectException:
            print(f"Error: PR #{pr_number} not found (404), it may have been deleted. Skipping.")
            return None
        except Exception as e:
            print(f"Error: An unknown error occurred while processing PR #{pr_number}: {e}. Aborting.")
            return None

def main():
    tokens = load_tokens(TOKEN_FILE)
    if not tokens:
        print("Execution stopped due to lack of GitHub tokens.")
        return
    token_manager = TokenManager(tokens)
    output_base_dir = 'django__django'
    os.makedirs(output_base_dir, exist_ok=True)

    for version in VERSIONS_TO_SCRAPE:
        print(f"\n--- Starting process for version: {version} ---")
        
        issues_output_filepath = os.path.join(output_base_dir, f"milestone_{version}_issues.jsonl")
        issue_links = get_issue_links_for_version(version)
        if not issue_links:
            continue

        scraped_urls = set()
        if os.path.exists(issues_output_filepath):
            try:
                with open(issues_output_filepath, "r", encoding="utf-8") as f:
                    scraped_urls.update(json.loads(line)['html_url'] for line in f if line.strip())
            except (IOError, json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Error reading or parsing {issues_output_filepath}: {e}. Re-scraping all content.")
                scraped_urls.clear()

        links_to_scrape = [link for link in issue_links if link not in scraped_urls]
        if not links_to_scrape:
            print(f"All issues for version {version} are already scraped. Skipping issue scraping.")
        else:
            print(f"Version {version}: Total {len(issue_links)} issues, {len(scraped_urls)} scraped, {len(links_to_scrape)} to scrape now.")
            with open(issues_output_filepath, "a", encoding="utf-8") as f:
                for link in tqdm(links_to_scrape, desc=f"Scraping Issues for v{version}"):
                    details = scrape_issue_details(link, milestone_title=version)
                    if details:
                        f.write(json.dumps(details, ensure_ascii=False) + '\n')
                        f.flush()
                    time.sleep(0.2)
            print(f"Issue data for version {version} saved to {issues_output_filepath}")

        if not os.path.exists(issues_output_filepath):
            print(f"Warning: Issue file {issues_output_filepath} not found. Cannot scrape PRs for version {version}.")
            continue

        all_pr_numbers = set()
        with open(issues_output_filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    all_pr_numbers.update(data.get('linked_pull_requests', []))

        if not all_pr_numbers:
            print(f"No linked PRs found for version {version}. Skipping PR scraping.")
            continue

        prs_output_filepath = os.path.join(output_base_dir, f"milestone_{version}_prs.jsonl")
        scraped_pr_numbers = set()
        if os.path.exists(prs_output_filepath):
            with open(prs_output_filepath, "r", encoding="utf-8") as f:
                scraped_pr_numbers.update(json.loads(line)['number'] for line in f if line.strip())

        prs_to_scrape = sorted(list(all_pr_numbers - scraped_pr_numbers))
        print(f"Total {len(all_pr_numbers)} PRs, {len(scraped_pr_numbers)} scraped, {len(prs_to_scrape)} to scrape now.")
        if not prs_to_scrape:
            continue

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor, \
             open(prs_output_filepath, "a", encoding="utf-8") as f:
            futures = {executor.submit(pr_worker, token_manager, pr_num, REPO_NAME, version): pr_num for pr_num in prs_to_scrape}
            progress_bar = tqdm(as_completed(futures), total=len(prs_to_scrape), desc=f"Scraping PRs for v{version}")
            for future in progress_bar:
                pr_info = future.result()
                if pr_info:
                    f.write(json.dumps(pr_info, ensure_ascii=False) + '\n')
                    f.flush()

    print("\nAll versions processed successfully!")

if __name__ == "__main__":
    main()
