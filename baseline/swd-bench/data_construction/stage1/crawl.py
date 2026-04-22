import os
import json
import threading
import time
import random
import base64
from queue import Queue
from github import Github, GithubException

PR_STATE_TO_CRAWL = "all" 
def load_tokens(token_file):
    with open(token_file, 'r') as f:
        tokens = [line.strip() for line in f if line.strip()]
    return tokens

class TokenPool:
    def __init__(self, tokens, switch_interval=60):
        self.tokens = tokens
        self.idx = 0
        self.lock = threading.Lock()
        self.switch_interval = switch_interval
        self.last_switch = time.time()

    def get_token(self):
        with self.lock:
            now = time.time()
            if now - self.last_switch > self.switch_interval:
                self.idx = (self.idx + 1) % len(self.tokens)
                self.last_switch = now
            return self.tokens[self.idx]
    
    def force_switch_token(self):
        with self.lock:
            self.idx = (self.idx + 1) % len(self.tokens)
            self.last_switch = time.time()
            print(f"Rate limit hit. Switched to token index {self.idx}")
            return self.tokens[self.idx]

def safe_filename(name):
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

def get_existing_pr_numbers(output_dir):
    file_path = os.path.join(output_dir, "prs.jsonl")
    numbers = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    info = json.loads(line)
                    numbers.add(info['number'])
                except (json.JSONDecodeError, KeyError):
                    continue
    return numbers

def fetch_pr_info(repo, pr, repo_name):
    pr_info = {
        "id": f"{repo_name}/pr/{pr.number}",
        "number": pr.number,
        "title": pr.title,
        "body": pr.body,
        "state": pr.state,
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
        "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
        "user": pr.user.login if pr.user else None,
        "author_association": pr.author_association,
        "merged": pr.merged,
        "merged_by": pr.merged_by.login if pr.merged_by else None,
        "merge_commit_sha": pr.merge_commit_sha,
        "milestone": pr.milestone.number,
        "assignees": [a.login for a in pr.assignees],
        "requested_reviewers": [r.login for r in pr.requested_reviewers],
        "requested_teams": [t.name for t in pr.requested_teams],
        "labels": [l.name for l in pr.labels],
        "base_branch": pr.base.ref,
        "base_sha": pr.base.sha,
        "head_branch": pr.head.ref,
        "head_sha": pr.head.sha,
        "html_url": pr.html_url,
        "diff_url": pr.diff_url,
        "patch_url": pr.patch_url,
        "issue_url": pr.issue_url,
        "is_cross_repository": pr.head.repo.full_name != pr.base.repo.full_name if pr.head.repo and pr.base.repo else None,
        "auto_merge": pr.auto_merge,
        "comments_count": pr.comments,
        "review_comments_count": pr.review_comments,
        "commits_count": pr.commits,
        "additions": pr.additions,
        "deletions": pr.deletions,
        "changed_files": pr.changed_files,
    }
    
    files = []
    try:
        for f in pr.get_files():
            base_content = None
            head_content = None
            try:
                base_file = repo.get_contents(f.filename, ref=pr.base.sha)
                base_content = base64.b64decode(base_file.content).decode('utf-8', errors='ignore')
            except Exception:
                base_content = None
            try:
                head_file = repo.get_contents(f.filename, ref=pr.head.sha)
                head_content = base64.b64decode(head_file.content).decode('utf-8', errors='ignore')
            except Exception:
                head_content = None

            files.append({
                "filename": f.filename,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions,
                "changes": f.changes,
                "patch": f.patch,
                "blob_url": f.blob_url,
                "raw_url": f.raw_url,
                "base_content": base_content,
                "head_content": head_content
            })
    except Exception as e:
        print(f"Warning: Could not fetch files for PR #{pr.number}. Error: {e}")
        pass 
    
    pr_info["files"] = files
    return pr_info

def worker(repo_name, token_pool, queue, output_dir, lock):
    file_path = os.path.join(output_dir, "prs.jsonl")
    
    while True:
        pr_number = queue.get()
        if pr_number is None:
            break

        for _ in range(len(token_pool.tokens) + 1):
            token = token_pool.get_token()
            g = Github(token, per_page=100)
            try:
                repo = g.get_repo(repo_name)
                pr = repo.get_pull(pr_number)
                pr_info = fetch_pr_info(repo, pr, repo_name)
                
                with lock:
                    with open(file_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(pr_info, ensure_ascii=False) + '\n')
                    print(f'Successfully fetched PR: {repo_name}#{pr_number}')
                
                break 

            except GithubException as e:
                if e.status == 403 and 'rate limit' in str(e.data).lower():
                    print(f"Rate limit exceeded for current token. Retrying with another token for PR #{pr_number}...")
                    token_pool.force_switch_token()
                    time.sleep(random.uniform(5, 10)) 
                    continue
                else:
                    print(f"An unhandled GitHub error occurred for PR {repo_name}#{pr_number}: {e}")
                    break 
            except Exception as e:
                print(f"A general error occurred for PR {repo_name}#{pr_number}: {e}")
                break 
        
        queue.task_done()

def crawl_all_prs(repo_name, token_file, output_dir, num_threads=4):
    tokens = load_tokens(token_file)
    if not tokens:
        print(f"Error: Token file '{token_file}' is empty or not found.")
        return
        
    token_pool = TokenPool(tokens, switch_interval=60)
    
    print(f"Initializing crawler for repository: {repo_name}")
    g = Github(token_pool.get_token(), per_page=100)
    repo = g.get_repo(repo_name)

    existing_prs = get_existing_pr_numbers(output_dir)
    print(f"Found {len(existing_prs)} existing PRs in '{os.path.join(output_dir, 'prs.jsonl')}'.")
    print(f"Fetching list of all PRs with state '{PR_STATE_TO_CRAWL}'...")
    all_repo_prs = repo.get_pulls(state=PR_STATE_TO_CRAWL, sort="created", direction="asc")
    prs_to_crawl = [pr.number for pr in all_repo_prs if pr.number not in existing_prs]
    
    if not prs_to_crawl:
        print("No new PRs to crawl. All data is up to date.")
        return

    print(f"Total PRs to crawl: {len(prs_to_crawl)}")

    queue = Queue()
    for pr_number in prs_to_crawl:
        queue.put(pr_number)

    lock = threading.Lock()
    threads = []
    print(f"Starting {num_threads} worker threads...")
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(repo_name, token_pool, queue, output_dir, lock))
        t.start()
        threads.append(t)

    queue.join()

    for _ in range(num_threads):
        queue.put(None)
    for t in threads:
        t.join()
        
    print(f"Finished crawling for repository: {repo_name}")

if __name__ == "__main__":

    repo_names = [
        "astropy/astropy",
        "django/django",
        "matplotlib/matplotlib",
        "mwaskom/seaborn",
        "pallets/flask",
        "psf/requests",
        "pydata/xarray",
        "pylint-dev/pylint",
        "pytest-dev/pytest",
        "scikit-learn/scikit-learn",
        "sphinx-doc/sphinx",
        "sympy/sympy"
    ]

    TOKEN_FILENAME = "tokens.txt"
    NUM_THREADS = 10

    for repo_name in repo_names:
        output_dir = os.path.join(os.getcwd(), safe_filename(repo_name))
        os.makedirs(output_dir, exist_ok=True)
        
        crawl_all_prs(
            repo_name=repo_name,
            token_file=TOKEN_FILENAME,
            output_dir=output_dir,
            num_threads=NUM_THREADS,
        )
