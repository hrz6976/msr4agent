#!/usr/bin/env python3
"""Bootstrap compact agent memory from GitHub GraphQL data.

This script is intentionally lightweight:
- one main GraphQL query for high-signal repo context
- deterministic local aggregation (no LLM dependency)
- markdown + json outputs under .agent_memory/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://api.github.com/graphql"

GRAPHQL_QUERY = """
query RepoContext($owner: String!, $name: String!, $prLimit: Int!, $issueLimit: Int!, $fileLimit: Int!) {
  rateLimit {
    cost
    remaining
    resetAt
  }
  repository(owner: $owner, name: $name) {
    nameWithOwner
    description
    url
    stargazerCount
    forkCount
    defaultBranchRef {
      name
    }
    primaryLanguage {
      name
    }
    languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
      nodes {
        name
      }
    }
    labels(first: 30) {
      nodes {
        name
      }
    }
    pullRequests(first: $prLimit, states: MERGED, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        url
        mergedAt
        additions
        deletions
        changedFiles
        author {
          login
        }
        labels(first: 10) {
          nodes {
            name
          }
        }
        files(first: $fileLimit) {
          nodes {
            path
            additions
            deletions
          }
        }
      }
    }
    issues(first: $issueLimit, states: CLOSED, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        url
        closedAt
        labels(first: 10) {
          nodes {
            name
          }
        }
      }
    }
    agents: object(expression: "HEAD:AGENTS.md") {
      ... on Blob {
        text
      }
    }
    contributing: object(expression: "HEAD:CONTRIBUTING.md") {
      ... on Blob {
        text
      }
    }
    codeowners: object(expression: "HEAD:.github/CODEOWNERS") {
      ... on Blob {
        text
      }
    }
  }
}
"""

POLICY_HINTS = (
    "must",
    "should",
    "required",
    "require",
    "do not",
    "don't",
    "never",
    "always",
    "before",
    "after",
    "test",
    "lint",
    "format",
    "review",
)

BUG_HINTS = (
    "bug",
    "fix",
    "regression",
    "crash",
    "race",
    "deadlock",
    "panic",
    "leak",
    "security",
    "vulnerability",
)

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "when",
    "after",
    "before",
    "about",
    "during",
    "merge",
    "merged",
    "request",
    "pull",
    "issue",
    "update",
    "improve",
    "support",
    "tests",
    "test",
    "fix",
    "bug",
    "add",
    "remove",
    "use",
    "allow",
    "prevent",
    "handle",
    "refactor",
    "docs",
    "documentation",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap .agent_memory from GitHub GraphQL")
    parser.add_argument("--repo", required=True, help="GitHub repo in owner/name format")
    parser.add_argument("--out-dir", default=".agent_memory", help="Output directory")
    parser.add_argument("--token", default=None, help="GitHub token (default: GITHUB_TOKEN env)")
    parser.add_argument("--pr-limit", type=int, default=25, help="Number of recent merged PRs")
    parser.add_argument("--issue-limit", type=int, default=25, help="Number of recent closed issues")
    parser.add_argument("--file-limit", type=int, default=30, help="Max files fetched per PR")
    parser.add_argument("--top-k", type=int, default=20, help="Top hotspots for coverage metric")
    parser.add_argument("--min-pair-support", type=int, default=2, help="Minimum support for couplings")
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=365,
        help="Ignore PR/Issue items older than this many days by merged/closed date (0 disables filter)",
    )
    return parser.parse_args()


def split_repo(repo: str) -> tuple[str, str]:
    parts = repo.strip().split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError("--repo must be in owner/name format")
    return parts[0], parts[1]


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def short_date(value: str | None) -> str:
    if not value:
        return "n/a"
    return value[:10]


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        # GitHub timestamps are typically ISO 8601 with trailing Z.
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|")


def blob_text(blob_node: Any) -> str:
    if isinstance(blob_node, dict):
        text = blob_node.get("text")
        if isinstance(text, str):
            return text
    return ""


def graphql_query(token: str, owner: str, name: str, pr_limit: int, issue_limit: int, file_limit: int) -> dict[str, Any]:
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "owner": owner,
            "name": name,
            "prLimit": pr_limit,
            "issueLimit": issue_limit,
            "fileLimit": file_limit,
        },
    }
    req = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "github-context-bootstrap/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub GraphQL HTTPError {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error calling GitHub GraphQL: {exc}") from exc

    data = json.loads(raw)
    if data.get("errors"):
        raise RuntimeError(f"GitHub GraphQL returned errors: {json.dumps(data['errors'], ensure_ascii=False)}")
    if not data.get("data") or not data["data"].get("repository"):
        raise RuntimeError("Repository not found or inaccessible")
    return data["data"]


def extract_policy_lines(source_name: str, text: str, limit: int = 16) -> list[dict[str, str]]:
    if not text:
        return []
    hits: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^[\-*\d\.)\s]+", "", line).strip()
        if len(line) < 18 or len(line) > 220:
            continue
        lowered = line.lower()
        if any(hint in lowered for hint in POLICY_HINTS):
            key = lowered
            if key in seen:
                continue
            seen.add(key)
            hits.append({"source": source_name, "line": line})
            if len(hits) >= limit:
                break
    return hits


def parse_codeowners_patterns(text: str, limit: int = 12) -> list[str]:
    patterns: list[str] = []
    if not text:
        return patterns
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
        if len(patterns) >= limit:
            break
    return patterns


def is_bug_like(title: str, labels: list[str]) -> bool:
    lowered_title = title.lower()
    if any(hint in lowered_title for hint in BUG_HINTS):
        return True
    for label in labels:
        lowered = label.lower()
        if any(hint in lowered for hint in BUG_HINTS):
            return True
    return False


def top_terms(texts: list[str], limit: int = 12) -> list[tuple[str, int]]:
    tokens: list[str] = []
    for text in texts:
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}", text.lower()):
            if token in STOPWORDS:
                continue
            if token.isdigit():
                continue
            tokens.append(token)
    counts = Counter(tokens)
    return counts.most_common(limit)


def build_memory(repo_data: dict[str, Any], args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    repository = repo_data["repository"]
    rate_limit = repo_data.get("rateLimit", {})

    prs = repository.get("pullRequests", {}).get("nodes", []) or []
    issues = repository.get("issues", {}).get("nodes", []) or []
    age_cutoff = None
    if args.max_age_days > 0:
        age_cutoff = datetime.now(timezone.utc) - timedelta(days=args.max_age_days)

    file_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "touches": 0,
        "additions": 0,
        "deletions": 0,
        "prs": [],
    })
    author_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "prs": 0,
        "file_touches": Counter(),
    })
    pair_counter: Counter[tuple[str, str]] = Counter()
    bug_examples: list[dict[str, str]] = []

    merged_dates: list[str] = []
    analyzed_pr_count = 0

    for pr in prs:
        pr_number = pr.get("number")
        pr_title = pr.get("title") or ""
        pr_url = pr.get("url") or ""
        merged_at = pr.get("mergedAt") or ""
        merged_dt = parse_iso_datetime(merged_at)
        if age_cutoff and merged_dt and merged_dt < age_cutoff:
            continue
        if merged_at:
            merged_dates.append(merged_at)
        analyzed_pr_count += 1

        label_nodes = pr.get("labels", {}).get("nodes", []) or []
        labels = [node.get("name", "") for node in label_nodes if node.get("name")]

        file_nodes = pr.get("files", {}).get("nodes", []) or []
        file_paths = sorted({node.get("path") for node in file_nodes if node.get("path")})

        author = (pr.get("author") or {}).get("login") or "unknown"
        author_stats[author]["prs"] += 1

        for path in file_paths:
            author_stats[author]["file_touches"][path] += 1

        for node in file_nodes:
            path = node.get("path")
            if not path:
                continue
            file_stats[path]["additions"] += int(node.get("additions") or 0)
            file_stats[path]["deletions"] += int(node.get("deletions") or 0)

        for path in file_paths:
            file_stats[path]["touches"] += 1
            file_stats[path]["prs"].append(pr_number)

        bounded_files = file_paths[:40]
        for left, right in combinations(bounded_files, 2):
            pair_counter[(left, right)] += 1

        if is_bug_like(pr_title, labels):
            bug_examples.append({
                "kind": "PR",
                "title": pr_title,
                "url": pr_url,
                "date": short_date(merged_at),
                "labels": ", ".join(labels) if labels else "n/a",
            })

    issue_dates: list[str] = []
    analyzed_issue_count = 0
    for issue in issues:
        issue_title = issue.get("title") or ""
        issue_url = issue.get("url") or ""
        closed_at = issue.get("closedAt") or ""
        closed_dt = parse_iso_datetime(closed_at)
        if age_cutoff and closed_dt and closed_dt < age_cutoff:
            continue
        if closed_at:
            issue_dates.append(closed_at)
        analyzed_issue_count += 1

        label_nodes = issue.get("labels", {}).get("nodes", []) or []
        labels = [node.get("name", "") for node in label_nodes if node.get("name")]

        if is_bug_like(issue_title, labels):
            bug_examples.append({
                "kind": "Issue",
                "title": issue_title,
                "url": issue_url,
                "date": short_date(closed_at),
                "labels": ", ".join(labels) if labels else "n/a",
            })

    hotspots = sorted(
        file_stats.items(),
        key=lambda item: (
            item[1]["touches"],
            item[1]["additions"] + item[1]["deletions"],
        ),
        reverse=True,
    )

    total_touches = sum(item[1]["touches"] for item in hotspots)
    top_k_touches = sum(item[1]["touches"] for item in hotspots[: args.top_k])
    hotspot_coverage = (top_k_touches / total_touches) if total_touches else 0.0

    strong_pairs: list[dict[str, Any]] = []
    for (left, right), support in pair_counter.most_common(120):
        if support < args.min_pair_support:
            continue
        left_touches = file_stats[left]["touches"] or 1
        right_touches = file_stats[right]["touches"] or 1
        strong_pairs.append(
            {
                "left": left,
                "right": right,
                "support": support,
                "confidence_left": support / left_touches,
                "confidence_right": support / right_touches,
            }
        )

    top_authors = sorted(
        author_stats.items(),
        key=lambda item: (item[1]["prs"], len(item[1]["file_touches"])),
        reverse=True,
    )[:15]

    policy_lines: list[dict[str, str]] = []
    policy_lines.extend(extract_policy_lines("AGENTS.md", blob_text(repository.get("agents"))))
    policy_lines.extend(extract_policy_lines("CONTRIBUTING.md", blob_text(repository.get("contributing"))))

    codeowners_patterns = parse_codeowners_patterns(blob_text(repository.get("codeowners")))

    bug_texts = [item["title"] for item in bug_examples]
    bug_keywords = top_terms(bug_texts, limit=12)

    name_with_owner = repository.get("nameWithOwner", "unknown/unknown")
    repo_url = repository.get("url", "")
    description = repository.get("description") or "n/a"
    stars = repository.get("stargazerCount", 0)
    forks = repository.get("forkCount", 0)
    default_branch = (repository.get("defaultBranchRef") or {}).get("name") or "n/a"
    primary_language = (repository.get("primaryLanguage") or {}).get("name") or "n/a"
    languages = [node.get("name") for node in (repository.get("languages", {}).get("nodes", []) or []) if node.get("name")]
    repo_labels = [node.get("name") for node in (repository.get("labels", {}).get("nodes", []) or []) if node.get("name")]

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "1_conventions").mkdir(parents=True, exist_ok=True)
    (out_dir / "2_architecture").mkdir(parents=True, exist_ok=True)
    (out_dir / "3_lessons").mkdir(parents=True, exist_ok=True)
    (out_dir / "4_team").mkdir(parents=True, exist_ok=True)

    merged_start = short_date(min(merged_dates) if merged_dates else None)
    merged_end = short_date(max(merged_dates) if merged_dates else None)
    issue_start = short_date(min(issue_dates) if issue_dates else None)
    issue_end = short_date(max(issue_dates) if issue_dates else None)

    index_content = [
        "# Agent Memory Bootstrap",
        "",
        f"- Repository: [{name_with_owner}]({repo_url})",
        f"- Description: {description}",
        f"- Generated at (UTC): {iso_now()}",
        f"- GraphQL cost: {rate_limit.get('cost', 'n/a')} | remaining: {rate_limit.get('remaining', 'n/a')} | reset: {rate_limit.get('resetAt', 'n/a')}",
        "",
        "## Read Order",
        "",
        "1. `1_conventions/working_agreements.md`",
        "2. `2_architecture/recent_change_hotspots.md`",
        "3. `3_lessons/implicit_couplings.md`",
        "4. `3_lessons/recent_bug_signals.md`",
        "5. `4_team/expertise_map.md`",
        "",
        "## Snapshot",
        "",
        f"- Merged PRs analyzed: {analyzed_pr_count} ({merged_start} -> {merged_end})",
        f"- Closed issues analyzed: {analyzed_issue_count} ({issue_start} -> {issue_end})",
        f"- Distinct changed files in PR sample: {len(file_stats)}",
        f"- Top-{args.top_k} hotspot coverage: {hotspot_coverage:.2%}",
        f"- Coupling rules (support >= {args.min_pair_support}): {len(strong_pairs)}",
        f"- Bug-like signals: {len(bug_examples)}",
        "",
        "## Trigger Hints",
        "",
        "- Before editing a hotspot file, scan `implicit_couplings.md` for likely co-change files.",
        "- For bug-prone modules, read `recent_bug_signals.md` before refactor.",
        "- If ownership is unclear, pick reviewers from `expertise_map.md`.",
    ]
    (out_dir / "index.md").write_text("\n".join(index_content) + "\n", encoding="utf-8")

    conventions_lines = [
        "# Working Agreements",
        "",
        "Extracted from repository-level rule files.",
        "",
    ]
    if policy_lines:
        for item in policy_lines:
            conventions_lines.append(f"- [{item['source']}] {item['line']}")
    else:
        conventions_lines.append("- No explicit policy lines found in AGENTS.md or CONTRIBUTING.md.")

    conventions_lines.append("")
    conventions_lines.append("## CODEOWNERS Hints")
    conventions_lines.append("")
    if codeowners_patterns:
        for pattern in codeowners_patterns:
            conventions_lines.append(f"- `{pattern}`")
    else:
        conventions_lines.append("- `.github/CODEOWNERS` not found or empty.")
    (out_dir / "1_conventions" / "working_agreements.md").write_text(
        "\n".join(conventions_lines) + "\n", encoding="utf-8"
    )

    hotspot_lines = [
        "# Recent Change Hotspots",
        "",
        f"Sample window: recent {analyzed_pr_count} merged PRs.",
        "",
        "| Rank | File | PR touches | Churn(add+del) | Sample PRs |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for idx, (path, stat) in enumerate(hotspots[:30], start=1):
        sample_prs = ", ".join(f"#{num}" for num in stat["prs"][:3] if num is not None) or "n/a"
        churn = stat["additions"] + stat["deletions"]
        hotspot_lines.append(
            f"| {idx} | `{markdown_escape(path)}` | {stat['touches']} | {churn} | {sample_prs} |"
        )

    if len(hotspots) == 0:
        hotspot_lines.append("| - | n/a | 0 | 0 | n/a |")

    hotspot_lines.extend(
        [
            "",
            f"Top-{args.top_k} hotspot coverage: {hotspot_coverage:.2%} of file touches.",
        ]
    )
    (out_dir / "2_architecture" / "recent_change_hotspots.md").write_text(
        "\n".join(hotspot_lines) + "\n", encoding="utf-8"
    )

    coupling_lines = [
        "# Implicit Couplings",
        "",
        "Co-change rules mined from files touched in the same merged PR.",
        "",
        "| Rank | File A | File B | Support | Conf(A->B) | Conf(B->A) |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for idx, pair in enumerate(strong_pairs[:40], start=1):
        coupling_lines.append(
            "| {rank} | `{left}` | `{right}` | {support} | {cl:.2f} | {cr:.2f} |".format(
                rank=idx,
                left=markdown_escape(pair["left"]),
                right=markdown_escape(pair["right"]),
                support=pair["support"],
                cl=pair["confidence_left"],
                cr=pair["confidence_right"],
            )
        )

    if len(strong_pairs) == 0:
        coupling_lines.append("| - | n/a | n/a | 0 | 0.00 | 0.00 |")

    coupling_lines.append("")
    coupling_lines.append("## Actionable Triggers")
    coupling_lines.append("")
    if strong_pairs:
        for pair in strong_pairs[:10]:
            coupling_lines.append(
                "- Editing `{left}` should also inspect `{right}` (support={support}, conf={conf:.2f}).".format(
                    left=pair["left"],
                    right=pair["right"],
                    support=pair["support"],
                    conf=max(pair["confidence_left"], pair["confidence_right"]),
                )
            )
    else:
        coupling_lines.append("- No stable coupling rules in the sampled window.")

    (out_dir / "3_lessons" / "implicit_couplings.md").write_text(
        "\n".join(coupling_lines) + "\n", encoding="utf-8"
    )

    bug_lines = [
        "# Recent Bug Signals",
        "",
        "Bug-like items are selected by title/label keywords.",
        "",
        "## Topic Keywords",
        "",
    ]
    if bug_keywords:
        for token, count in bug_keywords:
            bug_lines.append(f"- `{token}`: {count}")
    else:
        bug_lines.append("- No concentrated bug keywords found.")

    bug_lines.append("")
    bug_lines.append("## Recent Examples")
    bug_lines.append("")
    if bug_examples:
        for item in bug_examples[:30]:
            bug_lines.append(
                "- [{kind}] [{title}]({url}) ({date}) | labels: {labels}".format(
                    kind=item["kind"],
                    title=item["title"],
                    url=item["url"],
                    date=item["date"],
                    labels=item["labels"],
                )
            )
    else:
        bug_lines.append("- No bug-like issues/PRs found in the sampled window.")

    (out_dir / "3_lessons" / "recent_bug_signals.md").write_text(
        "\n".join(bug_lines) + "\n", encoding="utf-8"
    )

    team_lines = [
        "# Expertise Map",
        "",
        "Ranked by merged PR count in the sampled window.",
        "",
        "| Rank | Contributor | Merged PRs | Unique files | Top touched files |",
        "| --- | --- | ---: | ---: | --- |",
    ]

    for idx, (author, stat) in enumerate(top_authors, start=1):
        top_files = ", ".join(
            f"`{markdown_escape(path)}`({count})" for path, count in stat["file_touches"].most_common(3)
        )
        team_lines.append(
            f"| {idx} | `{author}` | {stat['prs']} | {len(stat['file_touches'])} | {top_files or 'n/a'} |"
        )

    if len(top_authors) == 0:
        team_lines.append("| - | n/a | 0 | 0 | n/a |")

    (out_dir / "4_team" / "expertise_map.md").write_text(
        "\n".join(team_lines) + "\n", encoding="utf-8"
    )

    report = {
        "generated_at": iso_now(),
        "repository": {
            "name_with_owner": name_with_owner,
            "url": repo_url,
            "description": description,
            "stars": stars,
            "forks": forks,
            "default_branch": default_branch,
            "primary_language": primary_language,
            "languages": languages,
            "labels_sample": repo_labels,
        },
        "source_window": {
            "pr_count": analyzed_pr_count,
            "issue_count": analyzed_issue_count,
            "merged_pr_date_start": merged_start,
            "merged_pr_date_end": merged_end,
            "closed_issue_date_start": issue_start,
            "closed_issue_date_end": issue_end,
            "file_limit_per_pr": args.file_limit,
            "max_age_days": args.max_age_days,
        },
        "metrics": {
            "distinct_files": len(file_stats),
            "hotspot_top_k": args.top_k,
            "hotspot_coverage": round(hotspot_coverage, 4),
            "coupling_rule_count": len(strong_pairs),
            "bug_signal_count": len(bug_examples),
            "policy_line_count": len(policy_lines),
            "top_contributor_count": len(top_authors),
        },
        "rate_limit": rate_limit,
    }
    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    args = parse_args()
    token = args.token or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Missing GitHub token. Set GITHUB_TOKEN or use --token.", file=sys.stderr)
        return 2

    try:
        owner, name = split_repo(args.repo)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        data = graphql_query(token, owner, name, args.pr_limit, args.issue_limit, args.file_limit)
        report = build_memory(data, args, Path(args.out_dir))
    except Exception as exc:  # broad by design for CLI UX
        print(f"bootstrap failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "status": "ok",
        "repository": report["repository"]["name_with_owner"],
        "out_dir": str(Path(args.out_dir).resolve()),
        "metrics": report["metrics"],
        "rate_limit": report["rate_limit"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
