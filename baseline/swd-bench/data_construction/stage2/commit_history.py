import os
import json
from github import Github, GithubException
from typing import List, Dict, Any

TOKEN_FILE = "tokens.txt"

class TokenManager:
    def __init__(self, token_file: str):
        self.tokens = self._load_tokens(token_file)
        if not self.tokens:
            raise ValueError("Token file is empty or not found. Cannot proceed.")
        self.token_idx = 0

    def _load_tokens(self, token_file: str) -> List[str]:
        if not os.path.exists(token_file):
            print(f"Warning: Token file '{token_file}' not found.")
            return []
        with open(token_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def get_github_instance(self) -> Github:
        token = self.tokens[self.token_idx]
        self.token_idx = (self.token_idx + 1) % len(self.tokens)
        return Github(token, retry=3, timeout=20)

def track_pr_commit_history(repo_name: str, pr_number: int, token_manager: TokenManager) -> Dict[str, Any]:
    try:
        g = token_manager.get_github_instance()
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        print(f"Successfully fetched PR #{pr_number} from {repo_name}.")
    except GithubException as e:
        print(f"Error fetching PR {repo_name}#{pr_number}: {e}")
        return None

    print("Collecting review comments...")
    review_comments_by_commit = {}
    try:
        review_comments = pr.get_review_comments()
        for comment in review_comments:
            commit_id = comment.commit_id
            if commit_id not in review_comments_by_commit:
                review_comments_by_commit[commit_id] = []
            
            review_comments_by_commit[commit_id].append({
                "id": comment.id,
                "user": comment.user.login,
                "body": comment.body,
                "path": comment.path,
                "position": comment.position,
                "created_at": comment.created_at.isoformat(),
                "html_url": comment.html_url
            })
    except Exception as e:
        print(f"Warning: Could not fetch review comments for PR #{pr_number}. Error: {e}")

    print(f"Tracking {pr.commits} commits in the PR...")
    commits_history = []
    pr_commits = pr.get_commits()

    for commit in pr_commits:
        commit_sha = commit.sha
        print(f"  - Processing commit: {commit_sha[:7]}")

        commit_message = commit.commit.message

        changed_files_details = []
        try:
            if commit.parents:
                base_commit = commit.parents[0].sha
                comparison = repo.compare(base=base_commit, head=commit_sha)
                for file in comparison.files:
                    changed_files_details.append({
                        "filename": file.filename,
                        "status": file.status,
                        "additions": file.additions,
                        "deletions": file.deletions,
                        "changes": file.changes,
                        "patch": file.patch,
                    })
        except Exception as e:
            print(f"    Warning: Could not get code changes for commit {commit_sha[:7]}. Error: {e}")

        associated_comments = review_comments_by_commit.get(commit_sha, [])

        commits_history.append({
            "sha": commit_sha,
            "author": commit.author.login if commit.author else "N/A",
            "committer": commit.committer.login if commit.committer else "N/A",
            "date": commit.commit.author.date.isoformat(),
            "message": commit_message,
            "changed_files": changed_files_details,
            "review_comments": associated_comments,
            "html_url": commit.html_url,
        })

    result = {
        "pr_id": f"{repo_name}/pr/{pr_number}",
        "pr_title": pr.title,
        "pr_url": pr.html_url,
        "total_commits": pr.commits,
        "commit_history": commits_history
    }

    return result

