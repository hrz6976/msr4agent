#!/usr/bin/env python3
"""Mine high-signal context from a local Git repository for agent cold-start.

This script is Git-first and API-free:
- parse git history (`git log --numstat`) in a bounded window
- compute deterministic signals (hotspots, couplings, bugfix patterns, risk, expertise)
- write compact `.agent_memory/` markdown + JSON report
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

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
    "ci",
)

BUG_HINTS = (
    "fix",
    "bug",
    "regression",
    "crash",
    "panic",
    "leak",
    "error",
    "race",
    "deadlock",
    "hotfix",
    "vulnerability",
    "security",
)

CONVENTIONAL_RE = re.compile(
    r"^(feat|fix|docs|chore|refactor|test|perf|style|build|ci|revert)(\([^\)]+\))?(!)?:",
    re.IGNORECASE,
)
ISSUE_RE = re.compile(r"(#\d+|[A-Z]{2,}-\d+)")
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}")

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
    "file",
    "files",
    "code",
    "ci",
}

INTENT_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("security", ("security", "vuln", "cve", "xss", "csrf", "injection", "overflow")),
    ("fix", ("fix", "bug", "regression", "hotfix", "repair", "resolve")),
    ("refactor", ("refactor", "cleanup", "clean up", "simplify", "restructure")),
    ("perf", ("perf", "performance", "optimize", "faster", "speed", "latency")),
    ("feature", ("feat", "feature", "add", "support", "implement", "introduce")),
    ("test", ("test", "assert", "fixture", "coverage")),
    ("docs", ("docs", "documentation", "readme", "guide", "comment")),
    ("chore", ("chore", "bump", "release", "deps", "dependency", "upgrade")),
]

CONCEPT_HINTS = {
    "schema",
    "validator",
    "serialization",
    "deserialization",
    "json",
    "typing",
    "type",
    "async",
    "concurrency",
    "cache",
    "auth",
    "security",
    "network",
    "url",
    "error",
    "exception",
    "config",
    "plugin",
    "migration",
    "compat",
    "performance",
    "dataclass",
    "model",
    "field",
    "test",
}


@dataclass
class FileChange:
    path: str
    additions: int
    deletions: int


@dataclass
class CommitRecord:
    sha: str
    author_name: str
    author_email: str
    authored_at: str
    subject: str
    files: list[FileChange]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mine local Git context into .agent_memory")
    parser.add_argument("--repo-path", default=".", help="Path to local git repository")
    parser.add_argument("--out-dir", default=".agent_memory", help="Output directory")
    parser.add_argument("--since-days", type=int, default=240, help="Analyze commits in recent N days (0 disables)")
    parser.add_argument("--max-commits", type=int, default=1800, help="Max commits to parse")
    parser.add_argument("--include-merges", action="store_true", help="Include merge commits in main sample")
    parser.add_argument("--max-files-per-commit", type=int, default=40, help="Cap files used for pair mining")
    parser.add_argument("--min-pair-support", type=int, default=3, help="Minimum support for coupling rule")
    parser.add_argument("--top-k-hotspots", type=int, default=30, help="Top-K hotspot files for coverage")
    parser.add_argument("--router-limit", type=int, default=120, help="Max router entries in 0_router/insight_router.jsonl")
    parser.add_argument(
        "--router-load-k",
        type=int,
        default=5,
        help="Expected number of router lines loaded at runtime for context budget estimate",
    )
    parser.add_argument("--top-insights", type=int, default=20, help="Number of top insights in 0_router/top_insights.md")
    parser.add_argument(
        "--preload-insights",
        type=int,
        default=2,
        help="Number of top action packs assumed in default context budget estimate",
    )
    return parser.parse_args()


def run_git(repo: Path, args: list[str]) -> str:
    cmd = ["git", "-C", str(repo), *args]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
    return proc.stdout


def ensure_git_repo(repo: Path) -> Path:
    if not repo.exists():
        raise RuntimeError(f"repo path does not exist: {repo}")
    top = run_git(repo, ["rev-parse", "--show-toplevel"]).strip()
    return Path(top)


def parse_int(value: str) -> int:
    if value == "-":
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def short_date(value: str | None) -> str:
    if not value:
        return "n/a"
    return value[:10]


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|")


def infer_module(path: str) -> str:
    if "/" not in path:
        return "(root)"
    return path.split("/", 1)[0]


def classify_path(path: str) -> str:
    p = path.lower()
    if p.startswith("tests/") or "/tests/" in p or p.endswith("_test.py") or p.endswith(".spec.ts") or p.endswith(".test.ts"):
        return "test"
    if p.startswith("docs/") or p.endswith(".md") or p.endswith(".rst"):
        return "doc"
    if p.startswith(".github/workflows/") or "ci" in p and p.endswith((".yml", ".yaml")):
        return "ci"
    if p in {"pyproject.toml", "package.json", "cargo.toml", "go.mod", "requirements.txt", "uv.lock", "poetry.lock"}:
        return "config"
    if p.endswith((".toml", ".yaml", ".yml", ".json", ".ini")) and p.count("/") <= 1:
        return "config"
    return "code"


def extract_policy_lines(path: Path, limit: int = 16) -> list[str]:
    if not path.exists() or not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    lines: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^[\-*\d\.)\s]+", "", line).strip()
        if len(line) < 18 or len(line) > 220:
            continue
        lowered = line.lower()
        if any(h in lowered for h in POLICY_HINTS):
            if lowered in seen:
                continue
            seen.add(lowered)
            lines.append(line)
            if len(lines) >= limit:
                break
    return lines


def read_log_commits(repo: Path, since_days: int, max_commits: int, include_merges: bool) -> list[CommitRecord]:
    pretty = "%x1e%H%x1f%an%x1f%ae%x1f%ad%x1f%s"
    args = ["log", "--date=iso-strict", "--numstat", "--no-renames", f"--pretty=format:{pretty}"]
    if since_days > 0:
        args.append(f"--since={since_days}.days")
    if max_commits > 0:
        args.append(f"--max-count={max_commits}")
    if not include_merges:
        args.append("--no-merges")
    out = run_git(repo, args)

    commits: list[CommitRecord] = []
    for raw_rec in out.split("\x1e"):
        rec = raw_rec.strip("\n")
        if not rec:
            continue
        lines = rec.splitlines()
        if not lines:
            continue

        fields = lines[0].split("\x1f")
        if len(fields) < 5:
            continue
        sha, author_name, author_email, authored_at, subject = fields[:5]

        files: list[FileChange] = []
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            add_s, del_s, path = parts
            files.append(FileChange(path=path, additions=parse_int(add_s), deletions=parse_int(del_s)))

        commits.append(
            CommitRecord(
                sha=sha,
                author_name=author_name,
                author_email=author_email,
                authored_at=authored_at,
                subject=subject,
                files=files,
            )
        )
    return commits


def top_terms(texts: list[str], limit: int = 12) -> list[tuple[str, int]]:
    c = Counter()
    for text in texts:
        for token in TOKEN_RE.findall(text.lower()):
            if token in STOPWORDS or token.isdigit():
                continue
            c[token] += 1
    return c.most_common(limit)


def month_key(date_str: str) -> str:
    dt = parse_iso(date_str)
    if not dt:
        return "unknown"
    return dt.strftime("%Y-%m")


def weekday_key(date_str: str) -> str:
    dt = parse_iso(date_str)
    if not dt:
        return "unknown"
    return dt.strftime("%a")


def entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    e = 0.0
    for v in counter.values():
        p = v / total
        e += -p * math.log2(p)
    return e


def estimate_tokens(text: str) -> int:
    # Rough approximation for GPT-style token accounting.
    return max(1, len(text) // 4)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip())
    cleaned = cleaned.strip("-").lower()
    return cleaned or "item"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def age_days_from_date(date_str: str | None) -> int:
    if not date_str:
        return 9999
    dt = parse_iso(date_str)
    if not dt:
        return 9999
    delta = datetime.now(timezone.utc) - dt
    return max(0, int(delta.total_seconds() // 86400))


def split_words(text: str) -> list[str]:
    # Split snake_case, kebab-case, and camelCase into normalized tokens.
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    normalized = re.sub(r"[_\-/\.]+", " ", normalized)
    tokens = [t.lower() for t in re.findall(r"[a-zA-Z][a-zA-Z0-9]{1,}", normalized)]
    return tokens


def concepts_from_text(text: str, limit: int = 8) -> list[str]:
    counts: Counter[str] = Counter()
    for token in split_words(text):
        if token in STOPWORDS:
            continue
        if token in CONCEPT_HINTS:
            counts[token] += 3
        elif len(token) >= 5:
            counts[token] += 1
    return [k for k, _ in counts.most_common(limit)]


def concepts_from_path(path: str, limit: int = 6) -> list[str]:
    return concepts_from_text(path, limit=limit)


def safe_read_text(path: Path, max_bytes: int = 512_000) -> str:
    try:
        if path.stat().st_size > max_bytes:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def extract_python_semantic_atoms(rel_path: str, text: str, max_atoms: int = 80) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return atoms

    path_kind = classify_path(rel_path)

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.stack: list[str] = []

        def _emit(self, node: ast.AST, kind: str, name: str) -> None:
            if len(atoms) >= max_atoms:
                return
            qual = ".".join(self.stack + [name]) if self.stack else name
            doc = ast.get_docstring(node, clean=False) if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) else ""
            doc = doc or ""

            has_raise = False
            has_assert = False
            has_try = False
            for n in ast.walk(node):
                if isinstance(n, ast.Raise):
                    has_raise = True
                elif isinstance(n, ast.Assert):
                    has_assert = True
                elif isinstance(n, ast.Try):
                    has_try = True

            constraints: list[str] = []
            if has_raise:
                constraints.append("raises-on-invalid-state")
            if has_assert:
                constraints.append("contains-assertions")
            if has_try:
                constraints.append("has-exception-branch")
            lowered_doc = doc.lower()
            if "must" in lowered_doc or "should" in lowered_doc or "never" in lowered_doc:
                constraints.append("docstring-contract")

            role = "behavior"
            if path_kind == "test" or name.startswith("test_"):
                role = "test-spec"
            elif kind == "class":
                role = "domain-model"

            concepts = concepts_from_text(f"{qual} {doc}")
            if not concepts:
                concepts = concepts_from_path(rel_path, limit=4)

            atoms.append(
                {
                    "path": rel_path,
                    "symbol": qual,
                    "kind": kind,
                    "role": role,
                    "line_start": int(getattr(node, "lineno", 0) or 0),
                    "line_end": int(getattr(node, "end_lineno", 0) or 0),
                    "concepts": concepts,
                    "constraints": constraints,
                }
            )

        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            self._emit(node, "class", node.name)
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
            kind = "method" if self.stack else "function"
            self._emit(node, kind, node.name)
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
            kind = "async_method" if self.stack else "async_function"
            self._emit(node, kind, node.name)
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

    Visitor().visit(tree)
    return atoms


def extract_lightweight_semantic_atoms(rel_path: str, text: str, max_atoms: int = 40) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    patterns = [
        ("rust_fn", re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)),
        ("js_fn", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)),
        ("ts_method", re.compile(r"^\s*(?:public|private|protected)?\s*(?:async\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)),
    ]
    seen: set[str] = set()
    for kind, pat in patterns:
        for m in pat.finditer(text):
            if len(atoms) >= max_atoms:
                break
            symbol = m.group(1)
            key = f"{kind}:{symbol}"
            if key in seen:
                continue
            seen.add(key)
            start_line = text.count("\n", 0, m.start()) + 1
            role = "test-spec" if classify_path(rel_path) == "test" else "behavior"
            atoms.append(
                {
                    "path": rel_path,
                    "symbol": symbol,
                    "kind": kind,
                    "role": role,
                    "line_start": start_line,
                    "line_end": 0,
                    "concepts": concepts_from_text(symbol + " " + rel_path, limit=6),
                    "constraints": [],
                }
            )
        if len(atoms) >= max_atoms:
            break
    return atoms


def build_code_semantic_atoms(repo: Path, candidate_paths: list[str], max_files: int = 140) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    scanned = 0
    seen_paths: set[str] = set()
    for rel_path in candidate_paths:
        if rel_path in seen_paths:
            continue
        seen_paths.add(rel_path)
        if scanned >= max_files:
            break
        full = repo / rel_path
        if not full.exists() or not full.is_file():
            continue
        text = safe_read_text(full)
        if not text:
            continue
        scanned += 1

        if rel_path.endswith(".py"):
            file_atoms = extract_python_semantic_atoms(rel_path, text)
        else:
            file_atoms = extract_lightweight_semantic_atoms(rel_path, text)
        if not file_atoms:
            # Fallback file-level semantic atom.
            file_atoms = [
                {
                    "path": rel_path,
                    "symbol": rel_path.split("/")[-1],
                    "kind": "file",
                    "role": "test-spec" if classify_path(rel_path) == "test" else "behavior",
                    "line_start": 1,
                    "line_end": 0,
                    "concepts": concepts_from_path(rel_path),
                    "constraints": [],
                }
            ]
        atoms.extend(file_atoms)

    for idx, atom in enumerate(atoms, start=1):
        atom["id"] = f"CSA-{idx:05d}"
    return atoms


def classify_commit_intent(commit: CommitRecord) -> dict[str, Any]:
    subject = commit.subject.strip()
    lowered = subject.lower()
    primary = "chore"
    secondary: list[str] = []
    for intent, words in INTENT_PATTERNS:
        if any(w in lowered for w in words):
            if primary == "chore":
                primary = intent
            else:
                secondary.append(intent)

    changed_paths = sorted({f.path for f in commit.files if f.path})
    file_kinds = sorted({classify_path(p) for p in changed_paths})
    code_touched = "code" in file_kinds or "ci" in file_kinds
    tests_touched = "test" in file_kinds
    docs_touched = "doc" in file_kinds

    risk_flags: list[str] = []
    if "breaking" in lowered or "drop support" in lowered or "backward incompatible" in lowered:
        risk_flags.append("breaking-change")
    if "deprecated" in lowered or "deprecate" in lowered:
        risk_flags.append("deprecation")
    if lowered.startswith("revert") or " revert " in f" {lowered} ":
        risk_flags.append("rollback")
    if code_touched and not tests_touched and primary in {"fix", "feature", "refactor"}:
        risk_flags.append("code-without-tests")

    issue_refs = sorted(set(ISSUE_RE.findall(subject)))
    pr_refs = sorted(set(re.findall(r"\(#(\d+)\)", subject)))
    concepts = concepts_from_text(subject + " " + " ".join(changed_paths), limit=10)

    return {
        "sha": commit.sha,
        "date": commit.authored_at,
        "subject": subject,
        "intent_primary": primary,
        "intent_secondary": sorted(set(secondary)),
        "file_kinds": file_kinds,
        "code_touched": code_touched,
        "tests_touched": tests_touched,
        "docs_touched": docs_touched,
        "risk_flags": risk_flags,
        "issue_refs": issue_refs,
        "pr_refs": [f"#{n}" for n in pr_refs],
        "concepts": concepts,
        "paths_sample": changed_paths[:8],
    }


def mine_git_context(args: argparse.Namespace) -> dict[str, Any]:
    repo = ensure_git_repo(Path(args.repo_path).resolve())
    commits = read_log_commits(repo, args.since_days, args.max_commits, args.include_merges)

    if not commits:
        raise RuntimeError("no commits found in selected window; increase --since-days or --max-commits")

    head_sha = run_git(repo, ["rev-parse", "HEAD"]).strip()
    current_branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"]).strip()

    branch_names = [
        line.strip()
        for line in run_git(repo, ["for-each-ref", "refs/heads", "--format=%(refname:short)"]).splitlines()
        if line.strip()
    ]
    tag_rows = [
        line.strip()
        for line in run_git(
            repo,
            ["for-each-ref", "refs/tags", "--sort=-creatordate", "--format=%(refname:short)|%(creatordate:short)"],
        ).splitlines()
        if line.strip()
    ]

    merge_subjects = [
        line.strip()
        for line in run_git(repo, ["log", "--merges", "--max-count=200", "--pretty=format:%s"]).splitlines()
        if line.strip()
    ]

    # Aggregate structures
    file_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "touches": 0,
            "additions": 0,
            "deletions": 0,
            "contributors": set(),
            "bugfix_touches": 0,
            "revert_touches": 0,
            "last_seen": "",
        }
    )
    file_author_touches: dict[str, Counter[str]] = defaultdict(Counter)
    file_commit_samples: dict[str, list[dict[str, str]]] = defaultdict(list)
    file_bugfix_samples: dict[str, list[dict[str, str]]] = defaultdict(list)
    module_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {"touches": 0, "churn": 0, "files": set()})
    module_author_counter: dict[str, Counter[str]] = defaultdict(Counter)
    author_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "commits": 0,
            "churn": 0,
            "files": Counter(),
            "modules": Counter(),
            "bugfix_commits": 0,
        }
    )

    pair_counts: Counter[tuple[str, str]] = Counter()
    pair_samples: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    commit_type_counter: Counter[str] = Counter()
    branch_prefix_counter: Counter[str] = Counter()
    merge_style_counter: Counter[str] = Counter()
    weekday_counter: Counter[str] = Counter()
    month_counter: Counter[str] = Counter()

    bugfix_commits: list[CommitRecord] = []
    revert_commits: list[CommitRecord] = []
    commit_intent_frames: list[dict[str, Any]] = []

    issue_linked_commit_count = 0
    code_test_cocommit = 0
    code_doc_cocommit = 0
    file_type_touch_counter: Counter[str] = Counter()

    first_dt: datetime | None = None
    last_dt: datetime | None = None

    for br in branch_names:
        if "/" in br:
            prefix = br.split("/", 1)[0]
        else:
            prefix = "(plain)"
        branch_prefix_counter[prefix] += 1

    for s in merge_subjects:
        sl = s.lower()
        if sl.startswith("merge pull request"):
            merge_style_counter["merge_pr"] += 1
        elif sl.startswith("merge branch"):
            merge_style_counter["merge_branch"] += 1
        elif sl.startswith("merge remote-tracking branch"):
            merge_style_counter["merge_remote"] += 1
        else:
            merge_style_counter["other_merge"] += 1

    for c in commits:
        dt = parse_iso(c.authored_at)
        if dt:
            first_dt = dt if first_dt is None or dt < first_dt else first_dt
            last_dt = dt if last_dt is None or dt > last_dt else last_dt
        weekday_counter[weekday_key(c.authored_at)] += 1
        month_counter[month_key(c.authored_at)] += 1

        subject_l = c.subject.lower()
        is_bugfix = any(h in subject_l for h in BUG_HINTS)
        is_revert = subject_l.startswith("revert") or " revert " in f" {subject_l} "

        if is_bugfix:
            bugfix_commits.append(c)
        if is_revert:
            revert_commits.append(c)

        conv_match = CONVENTIONAL_RE.match(c.subject.strip())
        if conv_match:
            commit_type_counter[conv_match.group(1).lower()] += 1
        else:
            commit_type_counter["other"] += 1

        if ISSUE_RE.search(c.subject):
            issue_linked_commit_count += 1

        author_key = f"{c.author_name} <{c.author_email}>"
        author_stats[author_key]["commits"] += 1

        changed_paths = sorted({f.path for f in c.files if f.path})
        file_kinds = {classify_path(p) for p in changed_paths}
        if "code" in file_kinds and "test" in file_kinds:
            code_test_cocommit += 1
        if "code" in file_kinds and "doc" in file_kinds:
            code_doc_cocommit += 1

        for fc in c.files:
            if not fc.path:
                continue
            churn = fc.additions + fc.deletions
            category = classify_path(fc.path)
            file_type_touch_counter[category] += 1

            st = file_stats[fc.path]
            st["touches"] += 1
            st["additions"] += fc.additions
            st["deletions"] += fc.deletions
            st["contributors"].add(author_key)
            if not st["last_seen"]:
                st["last_seen"] = c.authored_at
            if is_bugfix:
                st["bugfix_touches"] += 1
            if is_revert:
                st["revert_touches"] += 1

            file_author_touches[fc.path][author_key] += 1
            if len(file_commit_samples[fc.path]) < 8:
                file_commit_samples[fc.path].append(
                    {"sha": c.sha, "date": c.authored_at, "subject": c.subject}
                )
            if is_bugfix and len(file_bugfix_samples[fc.path]) < 8:
                file_bugfix_samples[fc.path].append(
                    {"sha": c.sha, "date": c.authored_at, "subject": c.subject}
                )

            module = infer_module(fc.path)
            module_stats[module]["touches"] += 1
            module_stats[module]["churn"] += churn
            module_stats[module]["files"].add(fc.path)
            module_author_counter[module][author_key] += 1

            author_stats[author_key]["churn"] += churn
            author_stats[author_key]["files"][fc.path] += 1
            author_stats[author_key]["modules"][module] += 1

        if is_bugfix:
            author_stats[author_key]["bugfix_commits"] += 1

        bounded = changed_paths[: args.max_files_per_commit]
        for left, right in combinations(bounded, 2):
            pair_counts[(left, right)] += 1
            if len(pair_samples[(left, right)]) < 8:
                pair_samples[(left, right)].append(
                    {"sha": c.sha, "date": c.authored_at, "subject": c.subject}
                )

        commit_intent_frames.append(classify_commit_intent(c))

    # Ranking outputs
    hotspots = sorted(
        file_stats.items(),
        key=lambda kv: (
            kv[1]["touches"],
            kv[1]["additions"] + kv[1]["deletions"],
        ),
        reverse=True,
    )

    total_touches = sum(v["touches"] for _, v in hotspots)
    top_touches = sum(v["touches"] for _, v in hotspots[: args.top_k_hotspots])
    hotspot_coverage = (top_touches / total_touches) if total_touches else 0.0

    coupling_rules: list[dict[str, Any]] = []
    for (left, right), support in pair_counts.most_common(300):
        if support < args.min_pair_support:
            continue
        left_t = file_stats[left]["touches"] or 1
        right_t = file_stats[right]["touches"] or 1
        coupling_rules.append(
            {
                "left": left,
                "right": right,
                "support": support,
                "confidence_left": support / left_t,
                "confidence_right": support / right_t,
            }
        )

    risky_rows: list[dict[str, Any]] = []
    for path, st in hotspots:
        churn = st["additions"] + st["deletions"]
        contributors = len(st["contributors"])
        bugfix_touches = st["bugfix_touches"]
        revert_touches = st["revert_touches"]
        author_counter = file_author_touches[path]
        top_author = author_counter.most_common(1)[0][1] if author_counter else 0
        top_author_share = (top_author / st["touches"]) if st["touches"] else 0.0
        # Higher score = more risky to change blindly.
        risk_score = (
            st["touches"] * 2
            + bugfix_touches * 4
            + revert_touches * 6
            + contributors
            + (2 if top_author_share > 0.7 and st["touches"] >= 4 else 0)
            + (1 if churn > 400 else 0)
        )
        risky_rows.append(
            {
                "path": path,
                "risk_score": risk_score,
                "touches": st["touches"],
                "churn": churn,
                "bugfix_touches": bugfix_touches,
                "revert_touches": revert_touches,
                "contributors": contributors,
                "top_author_share": top_author_share,
            }
        )
    risky_rows.sort(key=lambda x: (x["risk_score"], x["touches"], x["churn"]), reverse=True)

    module_rows = sorted(
        (
            {
                "module": m,
                "touches": st["touches"],
                "churn": st["churn"],
                "files": len(st["files"]),
            }
            for m, st in module_stats.items()
        ),
        key=lambda x: (x["touches"], x["churn"]),
        reverse=True,
    )

    expert_rows = sorted(
        (
            {
                "author": a,
                "commits": st["commits"],
                "churn": st["churn"],
                "bugfix_commits": st["bugfix_commits"],
                "files": len(st["files"]),
                "top_modules": st["modules"].most_common(3),
                "top_files": st["files"].most_common(3),
                "module_entropy": entropy(st["modules"]),
            }
            for a, st in author_stats.items()
        ),
        key=lambda x: (x["commits"], x["churn"]),
        reverse=True,
    )

    bugfix_texts = [c.subject for c in bugfix_commits]
    bugfix_keywords = top_terms(bugfix_texts, limit=15)

    semantic_candidate_paths: list[str] = []
    semantic_candidate_paths.extend([path for path, _st in hotspots[:220]])
    for r in coupling_rules[:140]:
        semantic_candidate_paths.append(r["left"])
        semantic_candidate_paths.append(r["right"])
    code_semantic_atoms = build_code_semantic_atoms(repo, semantic_candidate_paths, max_files=160)
    path_semantic_concepts: dict[str, Counter[str]] = defaultdict(Counter)
    for atom in code_semantic_atoms:
        for concept in atom.get("concepts", []):
            path_semantic_concepts[atom["path"]][concept] += 1

    # Phase A discussion frames: infer minimal discourse context from commit-linked issue/PR references.
    discussion_frames: list[dict[str, Any]] = []
    seen_refs: set[str] = set()
    for frame in commit_intent_frames:
        refs = list(frame.get("issue_refs", [])) + list(frame.get("pr_refs", []))
        if not refs:
            continue
        for ref in refs[:2]:
            key = f"{ref}:{frame['intent_primary']}"
            if key in seen_refs:
                continue
            seen_refs.add(key)
            discussion_frames.append(
                {
                    "id": f"DSC-{len(discussion_frames)+1:04d}",
                    "source": "commit-message-proxy",
                    "reference": ref,
                    "problem_hint": frame["subject"],
                    "decision_hint": frame["intent_primary"],
                    "redlines": (
                        ["ensure regression coverage"]
                        if frame["intent_primary"] in {"fix", "security"} else []
                    ),
                    "provenance": {"commit": frame["sha"]},
                    "confidence": 0.35,
                }
            )

    # Conventions from repository docs
    policy_sources = [
        ("AGENTS.md", repo / "AGENTS.md"),
        ("CONTRIBUTING.md", repo / "CONTRIBUTING.md"),
        (".cursorrules", repo / ".cursorrules"),
    ]
    policy_lines: list[tuple[str, str]] = []
    for label, p in policy_sources:
        for line in extract_policy_lines(p, limit=12):
            policy_lines.append((label, line))

    codeowners_path = repo / ".github" / "CODEOWNERS"
    codeowners_lines: list[str] = []
    if codeowners_path.exists():
        for raw in codeowners_path.read_text(encoding="utf-8", errors="replace").splitlines():
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            codeowners_lines.append(s)
            if len(codeowners_lines) >= 15:
                break

    # Prepare output directories
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "0_router").mkdir(parents=True, exist_ok=True)
    (out_dir / "1_actions" / "packs").mkdir(parents=True, exist_ok=True)
    (out_dir / "1_action_bundles").mkdir(parents=True, exist_ok=True)
    (out_dir / "2_evidence").mkdir(parents=True, exist_ok=True)
    (out_dir / "3_semantic_frames").mkdir(parents=True, exist_ok=True)
    (out_dir / "1_conventions").mkdir(parents=True, exist_ok=True)
    (out_dir / "2_architecture").mkdir(parents=True, exist_ok=True)
    (out_dir / "3_lessons").mkdir(parents=True, exist_ok=True)
    (out_dir / "4_team").mkdir(parents=True, exist_ok=True)

    period_start = first_dt.strftime("%Y-%m-%d") if first_dt else "n/a"
    period_end = last_dt.strftime("%Y-%m-%d") if last_dt else "n/a"

    # Semantic frame dumps (Phase A).
    (out_dir / "3_semantic_frames" / "code_semantic_atoms.jsonl").write_text(
        "".join(json.dumps(a, ensure_ascii=False, separators=(",", ":")) + "\n" for a in code_semantic_atoms),
        encoding="utf-8",
    )
    (out_dir / "3_semantic_frames" / "change_intent_frames.jsonl").write_text(
        "".join(json.dumps(f, ensure_ascii=False, separators=(",", ":")) + "\n" for f in commit_intent_frames),
        encoding="utf-8",
    )
    (out_dir / "3_semantic_frames" / "discussion_frames.jsonl").write_text(
        "".join(json.dumps(f, ensure_ascii=False, separators=(",", ":")) + "\n" for f in discussion_frames),
        encoding="utf-8",
    )

    # index.md
    index_lines = [
        "# Agent Memory (Git-Mined)",
        "",
        f"- Repository root: `{repo}`",
        f"- HEAD: `{head_sha[:12]}` on branch `{current_branch}`",
        f"- Generated at (UTC): {iso_now()}",
        f"- Commit window: {len(commits)} commits ({period_start} -> {period_end})",
        "",
        "## Read Order",
        "",
        "1. `0_router/preload_router.jsonl` (default tiny load)",
        "2. `0_router/intent_path_router.jsonl` (full semantic router)",
        "3. `0_router/top_action_bundles.md`",
        "4. `1_action_bundles/<id>.md` (load only matched IDs)",
        "5. `3_semantic_frames/*.jsonl` (load on semantic ambiguity)",
        "6. `1_conventions/git_workflow_conventions.md`",
        "7. `2_architecture/change_topology.md`",
        "8. `3_lessons/implicit_couplings.md`",
        "9. `3_lessons/historical_bugfix_patterns.md`",
        "10. `3_lessons/risky_hotspots.md`",
        "11. `4_team/expertise_map.md`",
        "",
        "## Snapshot",
        "",
        f"- Distinct files touched: {len(file_stats)}",
        f"- Top-{args.top_k_hotspots} hotspot coverage: {hotspot_coverage:.2%}",
        f"- Coupling rules (support >= {args.min_pair_support}): {len(coupling_rules)}",
        f"- Bug-fix-like commits: {len(bugfix_commits)}",
        f"- Revert-like commits: {len(revert_commits)}",
        f"- Code+Test co-change ratio: {(code_test_cocommit / len(commits)):.2%}",
        f"- Code+Docs co-change ratio: {(code_doc_cocommit / len(commits)):.2%}",
    ]
    (out_dir / "index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    # 1_conventions
    conventional_total = sum(commit_type_counter.values())
    conventional_ratio = (
        (conventional_total - commit_type_counter.get("other", 0)) / conventional_total if conventional_total else 0.0
    )
    issue_linked_ratio = issue_linked_commit_count / len(commits) if commits else 0.0

    conv_lines = [
        "# Git Workflow Conventions",
        "",
        "## Extracted Rule Lines",
        "",
    ]
    if policy_lines:
        for src, line in policy_lines[:30]:
            conv_lines.append(f"- [{src}] {line}")
    else:
        conv_lines.append("- No explicit rule lines found in AGENTS/CONTRIBUTING/.cursorrules.")

    conv_lines.extend(
        [
            "",
            "## Commit Message Discipline",
            "",
            f"- Conventional commit ratio: {conventional_ratio:.2%}",
            f"- Issue-linked commit ratio: {issue_linked_ratio:.2%}",
            f"- Top commit types: {', '.join(f'{k}:{v}' for k, v in commit_type_counter.most_common(6)) or 'n/a'}",
            "",
            "## Branch & Merge Signals",
            "",
            f"- Local branch prefixes: {', '.join(f'{k}:{v}' for k, v in branch_prefix_counter.most_common(8)) or 'n/a'}",
            f"- Merge styles: {', '.join(f'{k}:{v}' for k, v in merge_style_counter.most_common(8)) or 'n/a'}",
            "",
            "## CODEOWNERS Glimpse",
            "",
        ]
    )
    if codeowners_lines:
        for row in codeowners_lines:
            conv_lines.append(f"- `{row}`")
    else:
        conv_lines.append("- `.github/CODEOWNERS` not found or empty.")

    (out_dir / "1_conventions" / "git_workflow_conventions.md").write_text(
        "\n".join(conv_lines) + "\n", encoding="utf-8"
    )

    # 2_architecture
    arch_lines = [
        "# Change Topology",
        "",
        "## Module Hotspots",
        "",
        "| Rank | Module | Touches | Churn | Files |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for i, row in enumerate(module_rows[:25], start=1):
        arch_lines.append(
            f"| {i} | `{markdown_escape(row['module'])}` | {row['touches']} | {row['churn']} | {row['files']} |"
        )
    if not module_rows:
        arch_lines.append("| - | n/a | 0 | 0 | 0 |")

    arch_lines.extend(["", "## File Hotspots", "", "| Rank | File | Touches | Churn | Contributors |", "| --- | --- | ---: | ---: | ---: |"])
    for i, (path, st) in enumerate(hotspots[:35], start=1):
        churn = st["additions"] + st["deletions"]
        arch_lines.append(
            f"| {i} | `{markdown_escape(path)}` | {st['touches']} | {churn} | {len(st['contributors'])} |"
        )
    if not hotspots:
        arch_lines.append("| - | n/a | 0 | 0 | 0 |")

    arch_lines.extend(
        [
            "",
            f"Top-{args.top_k_hotspots} hotspot coverage: {hotspot_coverage:.2%}.",
            "",
            "## Temporal Rhythm",
            "",
            f"- Peak weekdays: {', '.join(f'{k}:{v}' for k, v in weekday_counter.most_common(3)) or 'n/a'}",
            f"- Active months: {', '.join(f'{k}:{v}' for k, v in month_counter.most_common(6)) or 'n/a'}",
        ]
    )

    (out_dir / "2_architecture" / "change_topology.md").write_text(
        "\n".join(arch_lines) + "\n", encoding="utf-8"
    )

    # 3_lessons/implicit_couplings
    coupling_lines = [
        "# Implicit Couplings",
        "",
        "Co-change rules mined from commits touching files together.",
        "",
        "| Rank | File A | File B | Support | Conf(A->B) | Conf(B->A) |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for i, r in enumerate(coupling_rules[:50], start=1):
        coupling_lines.append(
            "| {rank} | `{a}` | `{b}` | {s} | {ca:.2f} | {cb:.2f} |".format(
                rank=i,
                a=markdown_escape(r["left"]),
                b=markdown_escape(r["right"]),
                s=r["support"],
                ca=r["confidence_left"],
                cb=r["confidence_right"],
            )
        )
    if not coupling_rules:
        coupling_lines.append("| - | n/a | n/a | 0 | 0.00 | 0.00 |")

    coupling_lines.extend(["", "## Actionable Triggers", ""])
    if coupling_rules:
        for r in coupling_rules[:12]:
            coupling_lines.append(
                "- Editing `{a}` should also inspect `{b}` (support={s}, max_conf={c:.2f}).".format(
                    a=r["left"], b=r["right"], s=r["support"], c=max(r["confidence_left"], r["confidence_right"])
                )
            )
    else:
        coupling_lines.append("- No stable coupling rules under current sample window.")

    (out_dir / "3_lessons" / "implicit_couplings.md").write_text(
        "\n".join(coupling_lines) + "\n", encoding="utf-8"
    )

    # 3_lessons/historical_bugfix_patterns
    bug_lines = [
        "# Historical Bugfix Patterns",
        "",
        f"- Bug-fix-like commits: {len(bugfix_commits)} / {len(commits)}",
        f"- Revert-like commits: {len(revert_commits)} / {len(commits)}",
        "",
        "## Bug Topic Keywords",
        "",
    ]
    if bugfix_keywords:
        for token, count in bugfix_keywords:
            bug_lines.append(f"- `{token}`: {count}")
    else:
        bug_lines.append("- No concentrated bug topic keywords in window.")

    bug_lines.extend(["", "## Recent Bugfix Examples", ""])
    if bugfix_commits:
        for c in bugfix_commits[:25]:
            bug_lines.append(f"- `{c.sha[:12]}` {c.subject} ({short_date(c.authored_at)})")
    else:
        bug_lines.append("- No bug-fix-like commits found.")

    bug_lines.extend(["", "## Heuristics", ""])
    bug_lines.append(
        f"- Commits touching code+tests together: {code_test_cocommit} ({(code_test_cocommit / len(commits)):.2%})"
    )
    bug_lines.append(
        f"- Commits touching code+docs together: {code_doc_cocommit} ({(code_doc_cocommit / len(commits)):.2%})"
    )

    (out_dir / "3_lessons" / "historical_bugfix_patterns.md").write_text(
        "\n".join(bug_lines) + "\n", encoding="utf-8"
    )

    # 3_lessons/risky_hotspots
    risk_lines = [
        "# Risky Hotspots",
        "",
        "Risk score combines change frequency, bugfix/revert history, and ownership concentration.",
        "",
        "| Rank | File | Risk | Touches | Bugfix | Revert | Contributors | Top-author share |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for i, row in enumerate(risky_rows[:30], start=1):
        risk_lines.append(
            "| {rank} | `{path}` | {risk} | {touches} | {bug} | {rev} | {contrib} | {share:.2%} |".format(
                rank=i,
                path=markdown_escape(row["path"]),
                risk=row["risk_score"],
                touches=row["touches"],
                bug=row["bugfix_touches"],
                rev=row["revert_touches"],
                contrib=row["contributors"],
                share=row["top_author_share"],
            )
        )
    if not risky_rows:
        risk_lines.append("| - | n/a | 0 | 0 | 0 | 0 | 0 | 0.00% |")

    risk_lines.extend(["", "## Guardrails", ""])
    risk_lines.append("- For top-10 risky files, review coupling rules before edits.")
    risk_lines.append("- Prefer adding/refreshing tests when `bugfix` or `revert` history is non-trivial.")
    risk_lines.append("- If top-author share is high, request review from module experts before merge.")

    (out_dir / "3_lessons" / "risky_hotspots.md").write_text("\n".join(risk_lines) + "\n", encoding="utf-8")

    # 4_team/expertise_map
    team_lines = [
        "# Expertise Map",
        "",
        "| Rank | Contributor | Commits | Bugfix commits | Churn | File breadth | Module focus |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for i, row in enumerate(expert_rows[:20], start=1):
        modules = ", ".join(f"`{m}`({v})" for m, v in row["top_modules"]) or "n/a"
        team_lines.append(
            f"| {i} | `{row['author']}` | {row['commits']} | {row['bugfix_commits']} | {row['churn']} | {row['files']} | {modules} |"
        )

    if not expert_rows:
        team_lines.append("| - | n/a | 0 | 0 | 0 | 0 | n/a |")

    team_lines.extend(["", "## Reviewer Routing Hints", ""])
    for row in expert_rows[:10]:
        if not row["top_modules"]:
            continue
        module, _count = row["top_modules"][0]
        team_lines.append(f"- `{module}` changes can start review routing with `{row['author']}`.")

    (out_dir / "4_team" / "expertise_map.md").write_text("\n".join(team_lines) + "\n", encoding="utf-8")

    # Agent-operable insight layers: router -> action packs -> evidence
    insights: list[dict[str, Any]] = []
    insight_seq: dict[str, int] = {"CPL": 0, "BUG": 0, "RSK": 0, "REV": 0}

    def next_id(prefix: str) -> str:
        insight_seq[prefix] += 1
        return f"{prefix}-{insight_seq[prefix]:03d}"

    def infer_insight_concepts(paths: list[str], seed_text: str = "", limit: int = 6) -> list[str]:
        c: Counter[str] = Counter()
        for p in paths:
            for concept, cnt in path_semantic_concepts.get(p, Counter()).items():
                c[concept] += cnt
            for concept in concepts_from_path(p, limit=4):
                c[concept] += 1
        for concept in concepts_from_text(seed_text, limit=8):
            c[concept] += 1
        return [k for k, _ in c.most_common(limit)]

    def add_insight(
        *,
        prefix: str,
        insight_type: str,
        glob: str,
        intents: list[str],
        concepts: list[str],
        actions: list[str],
        verify: list[str],
        watchout: str,
        escalate: str,
        why: str,
        proof_refs: list[str],
        evidence: dict[str, Any],
        confidence: float,
        impact: float,
        last_seen: str,
    ) -> None:
        conf = clamp(confidence, 0.05, 0.99)
        imp = clamp(impact, 0.05, 1.0)
        stale = age_days_from_date(last_seen)
        freshness = clamp(1.0 - (stale / 365.0), 0.15, 1.0)
        actionability = 1.0 if actions and verify else 0.7
        context_cost = estimate_tokens(" ".join(actions + verify + [watchout, why, escalate] + proof_refs))
        utility = clamp((imp * conf * freshness * actionability) / (1.0 + context_cost / 200.0), 0.05, 0.99)
        risk = "H" if utility >= 0.75 else ("M" if utility >= 0.45 else "L")
        insight_id = next_id(prefix)
        insights.append(
            {
                "id": insight_id,
                "type": insight_type,
                "glob": glob,
                "intents": intents,
                "concepts": concepts,
                "actions": actions,
                "verify": verify,
                "watchout": watchout,
                "escalate": escalate,
                "why": why,
                "proof_refs": proof_refs,
                "evidence": evidence,
                "confidence": round(conf, 4),
                "impact": round(imp, 4),
                "utility": round(utility, 4),
                "risk": risk,
                "last_seen": last_seen,
                "stale_days": stale,
                "context_cost_tokens": context_cost,
            }
        )

    # Coupling guardrails
    for r in coupling_rules[:80]:
        left = r["left"]
        right = r["right"]
        support = r["support"]
        max_conf = max(r["confidence_left"], r["confidence_right"])
        samples = pair_samples.get((left, right), [])
        last_seen = samples[0]["date"] if samples else file_stats[left].get("last_seen", "")
        verify_cmds = []
        if classify_path(right) == "test" and right.endswith(".py"):
            verify_cmds.append(f"pytest {right} -q")
        verify_cmds.append(f"git diff --name-only  # ensure `{right}` was evaluated for co-change")
        sample_issue_refs = sorted(
            {
                ref
                for s in samples
                for ref in ISSUE_RE.findall(s.get("subject", ""))
            }
        )
        proof_refs = [f"commit:{s['sha'][:12]}" for s in samples[:3]]
        proof_refs.extend(f"issue:{ref}" for ref in sample_issue_refs[:2])
        add_insight(
            prefix="CPL",
            insight_type="coupling_guardrail",
            glob=left,
            intents=["fix", "refactor", "feature"],
            concepts=infer_insight_concepts([left, right], seed_text=f"{left} {right}"),
            actions=[
                f"Inspect `{right}` before finalizing changes in `{left}`.",
                "If behavior changes, update tests/docs for both files.",
            ],
            verify=verify_cmds,
            watchout=f"Do not merge if `{left}` changes without explicit impact check on `{right}`.",
            escalate=f"if conf<{0.55:.2f}, inspect recent history: git log --oneline -- {left} {right} | head -n 20",
            why=f"co-change support={support}, max_conf={max_conf:.2f}",
            proof_refs=proof_refs,
            evidence={
                "left": left,
                "right": right,
                "support": support,
                "confidence_left": round(r["confidence_left"], 4),
                "confidence_right": round(r["confidence_right"], 4),
                "sample_commits": samples,
            },
            confidence=max_conf,
            impact=clamp((support / 10.0) * 0.7 + max_conf * 0.3, 0.2, 1.0),
            last_seen=last_seen,
        )

    # Bugfix playbooks
    bugfix_candidates = sorted(
        (
            (path, st)
            for path, st in file_stats.items()
            if st["bugfix_touches"] >= 2
        ),
        key=lambda x: (x[1]["bugfix_touches"], x[1]["revert_touches"], x[1]["touches"]),
        reverse=True,
    )
    for path, st in bugfix_candidates[:60]:
        related_test = None
        for r in coupling_rules:
            if r["left"] == path and classify_path(r["right"]) == "test":
                related_test = r["right"]
                break
        verify_cmds = []
        if related_test and related_test.endswith(".py"):
            verify_cmds.append(f"pytest {related_test} -q")
        verify_cmds.append(f"git log --oneline -- {path} | head -n 15")
        bugfix_samples = file_bugfix_samples.get(path, [])
        proof_refs = [f"commit:{s['sha'][:12]}" for s in bugfix_samples[:3]]
        issue_refs = sorted(
            {
                ref
                for s in bugfix_samples
                for ref in ISSUE_RE.findall(s.get("subject", ""))
            }
        )
        proof_refs.extend(f"issue:{ref}" for ref in issue_refs[:2])
        add_insight(
            prefix="BUG",
            insight_type="bugfix_playbook",
            glob=path,
            intents=["fix", "refactor", "feature"],
            concepts=infer_insight_concepts([path, related_test] if related_test else [path], seed_text="bugfix regression"),
            actions=[
                f"Review recent bugfix commits touching `{path}` before edits.",
                "Preserve existing edge-case guards unless tests prove otherwise.",
                "Add one focused regression test for the changed behavior.",
            ],
            verify=verify_cmds,
            watchout="Do not simplify branches that previously fixed regressions without equivalent tests.",
            escalate=f"if uncertainty remains, inspect full patch context: git log -p -- {path} | head -n 240",
            why=f"bugfix_touches={st['bugfix_touches']}, revert_touches={st['revert_touches']}, touches={st['touches']}",
            proof_refs=proof_refs,
            evidence={
                "path": path,
                "bugfix_touches": st["bugfix_touches"],
                "revert_touches": st["revert_touches"],
                "touches": st["touches"],
                "sample_bugfix_commits": bugfix_samples,
            },
            confidence=clamp(
                (st["bugfix_touches"] + 1.5 * st["revert_touches"]) / max(2, st["touches"]),
                0.3,
                0.95,
            ),
            impact=clamp((st["bugfix_touches"] / 6.0) * 0.8 + (st["revert_touches"] / 3.0) * 0.2, 0.2, 1.0),
            last_seen=st.get("last_seen", ""),
        )

    # Risk hotspot guards
    max_risk = max((r["risk_score"] for r in risky_rows), default=1)
    for row in risky_rows[:40]:
        path = row["path"]
        owners = file_author_touches[path].most_common(1)
        owner = owners[0][0] if owners else "unknown"
        verify_cmds = [f"git diff --stat -- {path}"]
        for r in coupling_rules:
            if r["left"] == path and classify_path(r["right"]) == "test" and r["right"].endswith(".py"):
                verify_cmds.append(f"pytest {r['right']} -q")
                break
        risk_samples = file_commit_samples.get(path, [])
        proof_refs = [f"commit:{s['sha'][:12]}" for s in risk_samples[:3]]
        proof_refs.append(f"owner:{owner}")
        add_insight(
            prefix="RSK",
            insight_type="risk_hotspot_guard",
            glob=path,
            intents=["fix", "refactor", "feature"],
            concepts=infer_insight_concepts([path], seed_text="risk hotspot regression"),
            actions=[
                f"Keep edits in `{path}` small and review co-change guards first.",
                "Add or refresh tests before broad refactors.",
                f"Request review from `{owner}` or module experts before merge.",
            ],
            verify=verify_cmds,
            watchout="Avoid broad refactor + behavior change in one commit on this hotspot.",
            escalate=f"if diff grows large, split commits for `{path}` and re-run focused tests",
            why=(
                f"risk_score={row['risk_score']}, bugfix={row['bugfix_touches']}, "
                f"revert={row['revert_touches']}, owner_share={row['top_author_share']:.2%}"
            ),
            proof_refs=proof_refs,
            evidence={
                "path": path,
                "risk_row": row,
                "sample_commits": risk_samples,
            },
            confidence=clamp(
                (min(20, row["touches"]) / 20.0) * 0.5
                + min(1.0, row["bugfix_touches"] / 4.0) * 0.3
                + min(1.0, row["revert_touches"] / 2.0) * 0.2,
                0.3,
                0.95,
            ),
            impact=clamp(row["risk_score"] / max_risk, 0.2, 1.0),
            last_seen=file_stats[path].get("last_seen", ""),
        )

    # Reviewer routing
    module_touch_max = max((m["touches"] for m in module_rows), default=1)
    for m in module_rows[:20]:
        module = m["module"]
        if m["touches"] < 10:
            continue
        owners = module_author_counter[module].most_common(2)
        if not owners:
            continue
        primary = owners[0][0]
        backup = owners[1][0] if len(owners) > 1 else None
        glob = "*" if module == "(root)" else f"{module}/**"
        module_dates = [
            file_stats[path].get("last_seen", "")
            for path in module_stats[module]["files"]
            if path in file_stats
        ]
        module_last_seen = next((d for d in module_dates if d), "")
        add_insight(
            prefix="REV",
            insight_type="reviewer_routing",
            glob=glob,
            intents=["fix", "refactor", "feature", "docs", "chore"],
            concepts=infer_insight_concepts([f"{module}/"], seed_text=f"owner reviewer {module}"),
            actions=[
                f"Route review for `{module}` changes to `{primary}`.",
                (f"Use `{backup}` as backup reviewer." if backup else "Choose one backup reviewer if primary unavailable."),
                "Ask reviewer to validate module-specific historical constraints.",
            ],
            verify=["ensure reviewer is requested before merge"],
            watchout="Do not merge sensitive module changes without explicit reviewer acknowledgement.",
            escalate="if no reviewer responds, expand to top module contributors from expertise_map",
            why=f"module_touches={m['touches']}, owner_share={owners[0][1] / max(1, m['touches']):.2%}",
            proof_refs=[f"owner:{a}" for a, _ in owners],
            evidence={
                "module": module,
                "touches": m["touches"],
                "owners": [{"author": a, "touches": t} for a, t in owners],
            },
            confidence=clamp(owners[0][1] / max(1, m["touches"]), 0.35, 0.95),
            impact=clamp(m["touches"] / module_touch_max, 0.2, 0.85),
            last_seen=module_last_seen,
        )

    insights.sort(key=lambda x: (x["utility"], x["confidence"], x["impact"]), reverse=True)
    selected_insights = insights[: args.router_limit]
    type_counts = Counter(i["type"] for i in selected_insights)

    router_lines: list[str] = []
    top_lines = [
        "# Top Insights",
        "",
        "| Rank | ID | Type | Trigger | Concepts | First Action | Verify | Utility |",
        "| --- | --- | --- | --- | --- | --- | --- | ---: |",
    ]
    pack_texts: dict[str, str] = {}
    router_records: list[dict[str, Any]] = []

    def router_record(ins: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": ins["id"],
            "p": int(round(ins["utility"] * 100)),
            "glob": ins["glob"],
            "intent": "|".join(ins["intents"]),
            "cx": "|".join(ins.get("concepts", [])[:3]),
            "bundle": f"AB:{ins['id']}",
            "do": f"PACK:{ins['id']}",  # backward compatibility
            "risk": ins["risk"],
            "conf": round(ins["confidence"], 2),
            "stale": ins["stale_days"],
        }

    for idx, ins in enumerate(selected_insights, start=1):
        rec = router_record(ins)
        router_records.append(rec)
        router_lines.append(json.dumps(rec, ensure_ascii=False, separators=(",", ":")))

        concepts_str = "|".join(ins.get("concepts", [])) or "n/a"
        pack_lines = [f"WHEN: modify `{ins['glob']}` with intent `{ '|'.join(ins['intents']) }` and concepts `{concepts_str}`"]
        pack_lines.extend(f"DO: {line}" for line in ins["actions"])
        pack_lines.extend(f"VERIFY: {line}" for line in ins["verify"])
        pack_lines.append(f"WATCHOUT: {ins.get('watchout', 'n/a')}")
        pack_lines.append(f"ESCALATE: {ins['escalate']}")
        pack_lines.append(f"WHY: {ins['why']}")
        pack_lines.append(f"PROOF: {', '.join(ins.get('proof_refs', [])[:6]) or 'n/a'}")
        pack_text = "\n".join(pack_lines) + "\n"
        pack_texts[ins["id"]] = pack_text
        (out_dir / "1_actions" / "packs" / f"{ins['id']}.md").write_text(pack_text, encoding="utf-8")
        (out_dir / "1_action_bundles" / f"{ins['id']}.md").write_text(pack_text, encoding="utf-8")

        evidence_payload = {
            "id": ins["id"],
            "type": ins["type"],
            "glob": ins["glob"],
            "intents": ins["intents"],
            "concepts": ins.get("concepts", []),
            "risk": ins["risk"],
            "confidence": ins["confidence"],
            "utility": ins["utility"],
            "last_seen": ins["last_seen"],
            "stale_days": ins["stale_days"],
            "watchout": ins.get("watchout", ""),
            "why": ins["why"],
            "proof_refs": ins.get("proof_refs", []),
            "evidence": ins["evidence"],
        }
        (out_dir / "2_evidence" / f"{ins['id']}.json").write_text(
            json.dumps(evidence_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        if idx <= args.top_insights:
            first_action = ins["actions"][0] if ins["actions"] else "n/a"
            first_verify = ins["verify"][0] if ins["verify"] else "n/a"
            top_lines.append(
                "| {rank} | `{id}` | `{typ}` | `{glob}` | `{concepts}` | {action} | {verify} | {u:.2f} |".format(
                    rank=idx,
                    id=ins["id"],
                    typ=ins["type"],
                    glob=markdown_escape(ins["glob"]),
                    concepts=markdown_escape("|".join(ins.get("concepts", [])[:3]) or "n/a"),
                    action=markdown_escape(first_action),
                    verify=markdown_escape(first_verify),
                    u=ins["utility"],
                )
            )

    if not selected_insights:
        top_lines.append("| - | n/a | n/a | n/a | n/a | n/a | n/a | 0.00 |")

    router_text = "\n".join(router_lines) + ("\n" if router_lines else "")
    router_preload_k = min(args.router_load_k, len(router_lines))
    preload_order = [
        "risk_hotspot_guard",
        "bugfix_playbook",
        "coupling_guardrail",
        "reviewer_routing",
    ]
    preload_selected: list[dict[str, Any]] = []
    preload_seen: set[str] = set()
    for insight_type in preload_order:
        for ins in selected_insights:
            if ins["id"] in preload_seen:
                continue
            if ins["type"] == insight_type:
                preload_selected.append(ins)
                preload_seen.add(ins["id"])
                break
    for ins in selected_insights:
        if len(preload_selected) >= router_preload_k:
            break
        if ins["id"] in preload_seen:
            continue
        preload_selected.append(ins)
        preload_seen.add(ins["id"])
    router_preload_text = (
        "\n".join(
            json.dumps(router_record(ins), ensure_ascii=False, separators=(",", ":"))
            for ins in preload_selected[:router_preload_k]
        )
        + ("\n" if router_preload_k > 0 else "")
    )
    (out_dir / "0_router" / "insight_router.jsonl").write_text(router_text, encoding="utf-8")
    (out_dir / "0_router" / "intent_path_router.jsonl").write_text(router_text, encoding="utf-8")
    (out_dir / "0_router" / "preload_router.jsonl").write_text(router_preload_text, encoding="utf-8")
    top_text = "\n".join(top_lines) + "\n"
    (out_dir / "0_router" / "top_insights.md").write_text(top_text, encoding="utf-8")
    (out_dir / "0_router" / "top_action_bundles.md").write_text(top_text, encoding="utf-8")

    # Append runtime hints to index now that insight counts are available.
    index_runtime = [
        "",
        "## Insight Runtime",
        "",
        f"- Router entries: {len(selected_insights)}",
        f"- Preload router entries (runtime budget): {router_preload_k}",
        f"- Insight types: {', '.join(f'{k}:{v}' for k, v in type_counts.most_common()) or 'n/a'}",
        f"- Recommended preload action packs: top-{min(args.preload_insights, len(selected_insights))}",
        f"- Code semantic atoms: {len(code_semantic_atoms)}",
        f"- Change intent frames: {len(commit_intent_frames)}",
        f"- Discussion frames: {len(discussion_frames)}",
    ]
    (out_dir / "index.md").write_text(
        (out_dir / "index.md").read_text(encoding="utf-8") + "\n".join(index_runtime) + "\n",
        encoding="utf-8",
    )

    preload_n = min(args.preload_insights, len(preload_selected))
    preload_tokens = sum(estimate_tokens(pack_texts[i["id"]]) for i in preload_selected[:preload_n])
    router_tokens_full = estimate_tokens(router_text)
    router_tokens_runtime = estimate_tokens(router_preload_text)
    context_overhead_tokens = router_tokens_runtime + preload_tokens

    # report.json
    report = {
        "generated_at": iso_now(),
        "repository": {
            "path": str(repo),
            "head": head_sha,
            "branch": current_branch,
            "branch_count": len(branch_names),
            "tag_count": len(tag_rows),
        },
        "window": {
            "since_days": args.since_days,
            "max_commits": args.max_commits,
            "include_merges": args.include_merges,
            "commit_count": len(commits),
            "period_start": period_start,
            "period_end": period_end,
        },
        "metrics": {
            "distinct_files": len(file_stats),
            "module_count": len(module_stats),
            "hotspot_top_k": args.top_k_hotspots,
            "hotspot_coverage": round(hotspot_coverage, 4),
            "coupling_rule_count": len(coupling_rules),
            "bugfix_commit_count": len(bugfix_commits),
            "revert_commit_count": len(revert_commits),
            "code_test_cocommit_ratio": round((code_test_cocommit / len(commits)), 4),
            "code_doc_cocommit_ratio": round((code_doc_cocommit / len(commits)), 4),
            "conventional_commit_ratio": round(conventional_ratio, 4),
            "issue_linked_commit_ratio": round(issue_linked_ratio, 4),
            "policy_line_count": len(policy_lines),
            "insight_count": len(selected_insights),
            "insight_router_tokens_runtime_est": router_tokens_runtime,
            "insight_router_tokens_full_est": router_tokens_full,
            "insight_preload_pack_count": preload_n,
            "insight_preload_pack_tokens_est": preload_tokens,
            "context_overhead_tokens_est": context_overhead_tokens,
            "code_semantic_atom_count": len(code_semantic_atoms),
            "change_intent_frame_count": len(commit_intent_frames),
            "discussion_frame_count": len(discussion_frames),
            "semantic_paths_covered": len(path_semantic_concepts),
        },
        "insights": {
            "router_limit": args.router_limit,
            "router_load_k": args.router_load_k,
            "top_insights": args.top_insights,
            "counts_by_type": dict(type_counts),
            "top_ids": [ins["id"] for ins in selected_insights[: args.top_insights]],
            "preload_ids": [ins["id"] for ins in preload_selected[:router_preload_k]],
        },
        "semantic_frames": {
            "code_semantic_atoms_file": "3_semantic_frames/code_semantic_atoms.jsonl",
            "change_intent_frames_file": "3_semantic_frames/change_intent_frames.jsonl",
            "discussion_frames_file": "3_semantic_frames/discussion_frames.jsonl",
        },
        "counters": {
            "commit_types": dict(commit_type_counter),
            "branch_prefixes": dict(branch_prefix_counter),
            "merge_styles": dict(merge_style_counter),
            "file_type_touches": dict(file_type_touch_counter),
            "top_months": month_counter.most_common(12),
            "top_weekdays": weekday_counter.most_common(7),
        },
    }

    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "ok",
        "repo": str(repo),
        "out_dir": str(out_dir.resolve()),
        "metrics": report["metrics"],
    }


def main() -> int:
    args = parse_args()
    try:
        result = mine_git_context(args)
    except Exception as exc:  # broad for CLI UX
        print(f"mine_git_context failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
