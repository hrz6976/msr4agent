#!/usr/bin/env python3
"""Prepare clean workspace snapshots for benchmarking.

Creates flat workspace directories:
    workspace/{reponame}_{shortsha}_{variant}_{WORKSPACE_VERSION}/

Five experiment conditions (variants):
    nodocs       – remove all documentation and agent directives
    vanilla      – remove agent directive files only
    human        – inject human-written agent directives
    llm-{model}  – inject LLM-generated AGENTS.md (codex/claude/qwen/gemini)
    ours         – inject our custom directives (placeholder)

Each workspace contains git history truncated at the target commit.
Commit SHAs are never rewritten.

Usage:
    uv run src/prepare-snapshot.py --variant vanilla
    uv run src/prepare-snapshot.py --variant llm-codex --repo pallets/flask
    uv run src/prepare-snapshot.py --variant nodocs --manifest agentbench
    uv run src/prepare-snapshot.py --variant vanilla --variant human  # multiple
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_DIR = ROOT / "repo"
DEFAULT_WORKSPACE = ROOT / "workspace"
GENERATED_MD_DIR = ROOT / "data" / "generated_agents_md"
HUMAN_DIRECTIVES_PATH = ROOT / "data" / "human_agent_directives.json"


# ── .env loading ──────────────────────────────────────────────────────────


def _load_dotenv() -> dict[str, str]:
    env_path = ROOT / ".env"
    result = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                result[k.strip()] = v.strip().strip('"')
    return result


def get_workspace_version() -> str:
    return _load_dotenv().get("WORKSPACE_VERSION", "1")


# ── agent directive patterns (shared with extract-human-agents-md.py) ─────


AGENT_FNMATCH_PATTERNS = [
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", "COPILOT.md",
    ".cursorrules", ".clinerules", ".windsurfrules", ".roomodes",
    ".cursor/rules/*.mdc", ".cursor/rules/*.md",
    ".claude/commands/*.md", ".claude/skills/*.md",
    ".claude/skills/*/*.md", ".claude/skills/*/SKILL.md",
    ".codex/instructions.md",
    ".qwen/instructions.md",
    ".roo/rules/*.md", ".roo/rules-*/*.md",
    ".junie/guidelines.md", ".junie/*.md",
    ".augment/*.md", ".augment/instructions/*.md",
    ".trae/rules/*.md", ".trae/rules/*.mdc",
    ".goose/*.md", ".idx/airules.md", ".v0/*.md",
    ".bolt/prompt",
    ".github/copilot-instructions.md",
    ".github/copilot-setup-steps.yml",
]


# ── LLM model mapping ────────────────────────────────────────────────────


LLM_MODEL_MAP = {
    "codex": "gpt-5.3-codex-2026-02-24.md",
    "claude": "anthropic/claude-sonnet-4.5.md",
    "qwen": "qwen/qwen3.5-397b-a17b.md",
    "gemini": "gemini-3-pro-preview-new.md",
}


# ── data ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorkspaceSpec:
    manifest: str
    repo: str       # e.g. "pallets/flask"
    url: str
    path: str       # e.g. "repo/pallets/flask"
    commit: str
    variant: str    # e.g. "vanilla", "llm-codex"
    cleanup_commands: list[str]  # shell commands for nodocs cleanup

    @property
    def short_repo(self) -> str:
        return self.repo.split("/")[-1]

    @property
    def short_sha(self) -> str:
        return self.commit[:12]

    @property
    def owner(self) -> str:
        return self.repo.split("/")[0]

    @property
    def repo_name(self) -> str:
        return self.repo.split("/")[-1]


# ── git helper ────────────────────────────────────────────────────────────


def run_git(args: list[str], *, cwd: Path | None = None, check: bool = True) -> str:
    r = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
    )
    if check and r.returncode != 0:
        raise subprocess.CalledProcessError(
            r.returncode, r.args, output=r.stdout, stderr=r.stderr,
        )
    return r.stdout.strip()


def _is_ancestor(candidate: str, target: str, cwd: Path) -> bool:
    r = subprocess.run(
        ["git", "merge-base", "--is-ancestor", candidate, target],
        cwd=cwd, capture_output=True,
    )
    return r.returncode == 0


# ── manifest loading ──────────────────────────────────────────────────────


def discover_manifests() -> list[Path]:
    return sorted(p for p in REPO_DIR.glob("*.jsonl") if p.is_file())


def resolve_manifests(requested: list[str] | None) -> list[Path]:
    if not requested:
        return discover_manifests()
    resolved: list[Path] = []
    for name in requested:
        for c in (Path(name), REPO_DIR / name, REPO_DIR / f"{name}.jsonl"):
            if c.exists():
                resolved.append(c.resolve())
                break
        else:
            raise SystemExit(f"Manifest not found: {name}")
    return sorted(dict.fromkeys(resolved))


def load_specs_from_manifest(
    path: Path,
) -> list[tuple[str, str, str, str, list[str], list[str]]]:
    """Returns list of (manifest, repo, url, path, [commits], cleanup_commands)."""
    specs = []
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            raw = line.strip()
            if not raw:
                continue
            obj = json.loads(raw)
            for k in ("repo", "url", "path"):
                if not obj.get(k):
                    raise ValueError(f"{path}:{n} missing {k!r}")
            commits = obj.get("used_commits") or [obj["commit"]]
            cleanup = obj.get("cleanup_commands", [])
            specs.append((path.stem, obj["repo"], obj["url"], obj["path"], commits, cleanup))
    return specs


# ── workspace path ────────────────────────────────────────────────────────


def workspace_dest(spec: WorkspaceSpec, ws: Path, version: str) -> Path:
    return ws / f"{spec.short_repo}_{spec.short_sha}_{spec.variant}_{version}"


# ── local cache management ────────────────────────────────────────────────


def _is_partial_clone(repo: Path) -> bool:
    r = subprocess.run(
        ["git", "config", "--get", "remote.origin.partialclonefilter"],
        cwd=repo, capture_output=True, text=True,
    )
    return r.returncode == 0 and bool(r.stdout.strip())


def _ensure_full_clone_cache(url: str, cache: Path) -> None:
    if not (cache / ".git").exists():
        return
    if not _is_partial_clone(cache):
        return
    print(f"[reclone] {cache} (upgrading partial clone to full)")
    shutil.rmtree(cache)
    cache.parent.mkdir(parents=True, exist_ok=True)
    run_git(["clone", "--no-checkout", url, str(cache)])


# ── ref helpers ───────────────────────────────────────────────────────────


def _branch_tips(cwd: Path) -> list[tuple[str, str]]:
    raw = run_git(
        ["for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads/"],
        cwd=cwd,
    )
    result = []
    for line in raw.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            result.append((parts[0], parts[1]))
    return result


def _remotes(cwd: Path) -> list[str]:
    raw = run_git(["remote"], cwd=cwd)
    return [r.strip() for r in raw.splitlines() if r.strip()]


def _tags(cwd: Path) -> list[str]:
    raw = run_git(["tag", "-l"], cwd=cwd)
    return [t.strip() for t in raw.splitlines() if t.strip()]


def _delete_non_local_refs(cwd: Path) -> None:
    raw = run_git(["for-each-ref", "--format=%(refname)"], cwd=cwd)
    for ref in raw.splitlines():
        ref = ref.strip()
        if not ref:
            continue
        if ref.startswith("refs/heads/") or ref.startswith("refs/tags/"):
            continue
        run_git(["update-ref", "-d", ref], cwd=cwd)


# ── base snapshot (git history truncation) ────────────────────────────────


def create_base_snapshot(
    repo: str, url: str, path: str, commit: str, dest: Path,
) -> None:
    local_cache = ROOT / path
    _ensure_full_clone_cache(url, local_cache)

    print(f"[clone]  {repo} @ {commit[:12]}")
    clone_cmd = ["clone", "--no-checkout"]
    if (local_cache / ".git").exists():
        clone_cmd += ["--reference-if-able", str(local_cache), "--dissociate"]
    clone_cmd += [url, str(dest)]
    run_git(clone_cmd)

    # Detach HEAD at target, remove remotes
    run_git(["checkout", "--detach", commit], cwd=dest)
    for remote in _remotes(dest):
        run_git(["remote", "remove", remote], cwd=dest)

    # Prune branches: keep those whose tip is an ancestor of target
    kept_branches = 0
    for branch, tip in _branch_tips(dest):
        if _is_ancestor(tip, commit, dest):
            kept_branches += 1
        else:
            run_git(["branch", "-D", branch], cwd=dest)

    # Ensure at least one branch at target commit
    surviving = _branch_tips(dest)
    if not any(tip == commit for _, tip in surviving):
        run_git(["branch", "snapshot", commit], cwd=dest)
        kept_branches += 1

    # Prune tags: keep those pointing to ancestors of target
    kept_tags = 0
    for tag in _tags(dest):
        tag_commit = run_git(["rev-list", "-1", tag], cwd=dest, check=False)
        if tag_commit and _is_ancestor(tag_commit, commit, dest):
            kept_tags += 1
        else:
            run_git(["tag", "-d", tag], cwd=dest)

    # Remove stray refs
    _delete_non_local_refs(dest)

    # GC
    print(f"[gc]     {repo}  (kept {kept_branches} branch(es), {kept_tags} tag(s))")
    run_git(["reflog", "expire", "--expire=now", "--all"], cwd=dest)
    run_git(["gc", "--prune=now", "--aggressive"], cwd=dest)

    # Checkout a branch at target commit
    surviving = _branch_tips(dest)
    target_branch = next(
        (name for name, tip in surviving if tip == commit), None,
    )
    if target_branch:
        run_git(["checkout", target_branch], cwd=dest)
    else:
        run_git(["checkout", commit], cwd=dest)


# ── verification ──────────────────────────────────────────────────────────


def verify(commit: str, dest: Path) -> None:
    errs: list[str] = []

    head = run_git(["rev-parse", "HEAD"], cwd=dest)
    if head != commit:
        errs.append(f"HEAD={head}, want {commit}")

    if _remotes(dest):
        errs.append("remotes still present")

    for branch, tip in _branch_tips(dest):
        if not _is_ancestor(tip, commit, dest):
            errs.append(f"branch {branch} @ {tip} is NOT an ancestor of target")

    for tag in _tags(dest):
        tag_commit = run_git(["rev-list", "-1", tag], cwd=dest, check=False)
        if tag_commit and not _is_ancestor(tag_commit, commit, dest):
            errs.append(f"tag {tag} @ {tag_commit} is NOT an ancestor of target")

    stray = run_git(["for-each-ref", "--format=%(refname)"], cwd=dest)
    for ref in stray.splitlines():
        ref = ref.strip()
        if ref and not (ref.startswith("refs/heads/") or ref.startswith("refs/tags/")):
            errs.append(f"stray ref: {ref}")

    all_commits = run_git(["rev-list", "--all"], cwd=dest).splitlines()
    for c in all_commits:
        c = c.strip()
        if c and not _is_ancestor(c, commit, dest):
            errs.append(f"reachable commit {c} is a descendant of target (data leak!)")
            break

    if errs:
        raise RuntimeError(
            f"Verification FAILED for {dest.name}:\n"
            + "\n".join(f"  · {e}" for e in errs)
        )


# ── variant: helpers ──────────────────────────────────────────────────────


def _find_agent_directive_files(workspace: Path) -> list[Path]:
    found = []
    for root, _dirs, files in os.walk(workspace):
        rel_root = Path(root).relative_to(workspace)
        for f in files:
            rel_path = str(rel_root / f) if str(rel_root) != "." else f
            for pat in AGENT_FNMATCH_PATTERNS:
                if fnmatch.fnmatch(rel_path, pat):
                    found.append(Path(root) / f)
                    break
    return found


def _remove_agent_directives(workspace: Path) -> int:
    files = _find_agent_directive_files(workspace)
    for f in files:
        f.unlink()
    # Clean up empty parent dirs
    for f in files:
        p = f.parent
        while p != workspace:
            try:
                p.rmdir()
            except OSError:
                break
            p = p.parent
    return len(files)


# ── variant: nodocs ──────────────────────────────────────────────────────


def _backup_agent_directives(workspace: Path) -> dict[str, str]:
    """Backup agent directive files before doc removal."""
    backup: dict[str, str] = {}
    for f in _find_agent_directive_files(workspace):
        rel = str(f.relative_to(workspace))
        try:
            backup[rel] = f.read_text(encoding="utf-8")
        except Exception:
            pass
    return backup


def _restore_agent_directives(workspace: Path, backup: dict[str, str]) -> None:
    """Restore agent directive files after doc removal."""
    for rel, content in backup.items():
        dest = workspace / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")


def apply_variant_nodocs(spec: WorkspaceSpec, workspace: Path) -> None:
    if not spec.cleanup_commands:
        print(f"[nodocs] no cleanup commands for {spec.repo}, skipping")
        return

    # Backup agent directives before cleanup (matches AgentBench behavior)
    backup = _backup_agent_directives(workspace)

    for cmd in spec.cleanup_commands:
        subprocess.run(cmd, shell=True, cwd=workspace, capture_output=True)

    # Restore agent directives (AgentBench preserves AGENTS.md/CLAUDE.md)
    _restore_agent_directives(workspace, backup)
    print(f"[nodocs] applied {len(spec.cleanup_commands)} command(s), preserved {len(backup)} directive(s)")


# ── variant: vanilla ─────────────────────────────────────────────────────


def apply_variant_vanilla(spec: WorkspaceSpec, workspace: Path) -> None:
    n = _remove_agent_directives(workspace)
    print(f"[vanilla] removed {n} agent directive file(s)")


# ── variant: human ───────────────────────────────────────────────────────


def apply_variant_human(spec: WorkspaceSpec, workspace: Path) -> None:
    if not HUMAN_DIRECTIVES_PATH.exists():
        print(f"[warn]   {HUMAN_DIRECTIVES_PATH.name} not found, skipping injection")
        return

    data = json.loads(HUMAN_DIRECTIVES_PATH.read_text(encoding="utf-8"))
    entry = None
    for item in data:
        if item["repo"] == spec.repo and item["commit"] == spec.commit:
            entry = item
            break

    if not entry or not entry.get("files"):
        print(f"[human]  no directives for {spec.repo} @ {spec.short_sha}")
        return

    # Inject all human directives (overwrites commit_tree copies, adds future_ref ones)
    injected = 0
    for filepath, info in entry["files"].items():
        dest = workspace / filepath
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(info["content"], encoding="utf-8")
        injected += 1
    print(f"[human]  injected {injected} directive(s)")


# ── variant: llm-{model} ────────────────────────────────────────────────


def apply_variant_llm(spec: WorkspaceSpec, workspace: Path, model: str) -> None:
    model_file = LLM_MODEL_MAP.get(model)
    if not model_file:
        raise SystemExit(
            f"Unknown LLM model: {model}. Available: {', '.join(LLM_MODEL_MAP)}"
        )

    md_path = (
        GENERATED_MD_DIR / spec.owner / spec.repo_name / spec.short_sha / model_file
    )
    if not md_path.exists():
        print(f"[warn]   generated AGENTS.md not found: {md_path}")
        return

    _remove_agent_directives(workspace)
    content = md_path.read_text(encoding="utf-8")
    (workspace / "AGENTS.md").write_text(content, encoding="utf-8")
    print(f"[llm-{model}] injected AGENTS.md ({len(content)} chars)")


# ── variant: ours ────────────────────────────────────────────────────────


def apply_variant_ours(spec: WorkspaceSpec, workspace: Path) -> None:
    _remove_agent_directives(workspace)
    print(f"[ours]   placeholder – no directives injected yet")


# ── variant dispatch ─────────────────────────────────────────────────────


def apply_variant(spec: WorkspaceSpec, workspace: Path) -> None:
    variant = spec.variant
    if variant == "nodocs":
        apply_variant_nodocs(spec, workspace)
    elif variant == "vanilla":
        apply_variant_vanilla(spec, workspace)
    elif variant == "human":
        apply_variant_human(spec, workspace)
    elif variant.startswith("llm-"):
        apply_variant_llm(spec, workspace, variant[4:])
    elif variant == "ours":
        apply_variant_ours(spec, workspace)
    else:
        raise SystemExit(f"Unknown variant: {variant}")

    # Commit variant changes so the agent sees a clean working tree
    # (matches AgentBench: git add . && git commit after env preparation)
    run_git(["add", "."], cwd=workspace)
    # Check if there's anything to commit
    r = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=workspace, capture_output=True,
    )
    if r.returncode != 0:  # there are staged changes
        run_git(
            ["commit", "-m", f"Prepare workspace: {variant}"],
            cwd=workspace,
        )


# ── main flow ─────────────────────────────────────────────────────────────


ALL_VARIANTS = (
    ["nodocs", "vanilla", "human", "ours"]
    + [f"llm-{m}" for m in LLM_MODEL_MAP]
)


def cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Prepare workspace snapshots for benchmarking.",
    )
    p.add_argument(
        "--manifest", action="append",
        help="Manifest name or path (repeatable).",
    )
    p.add_argument(
        "--repo", action="append",
        help="Process only named repositories (repeatable).",
    )
    p.add_argument(
        "--commit", action="append",
        help="Process only specific commits; supports full or 12-char short SHA.",
    )
    p.add_argument(
        "--variant", action="append",
        help=f"Experiment variant (repeatable). Options: {', '.join(ALL_VARIANTS)}",
    )
    p.add_argument(
        "--workspace", type=Path, default=DEFAULT_WORKSPACE,
        help=f"Output directory (default: {DEFAULT_WORKSPACE}).",
    )
    p.add_argument("--force", action="store_true", help="Re-create even if exists.")
    p.add_argument("--dry-run", action="store_true", help="Print plan only.")
    return p.parse_args()


def main() -> int:
    args = cli()
    version = get_workspace_version()

    paths = resolve_manifests(args.manifest)
    if not paths:
        raise SystemExit(f"No JSONL manifests under {REPO_DIR}")

    # Load and expand specs
    raw_specs: list[tuple[str, str, str, str, list[str], list[str]]] = []
    for p in paths:
        raw_specs.extend(load_specs_from_manifest(p))

    # Filter by repo
    if args.repo:
        want = set(args.repo)
        raw_specs = [s for s in raw_specs if s[1] in want]

    # Filter by commit (match full or short SHA)
    if args.commit:
        want_shorts = {c[:12] for c in args.commit}
        filtered = []
        for manifest, repo, url, path, commits, cleanup in raw_specs:
            matched = [c for c in commits if c[:12] in want_shorts]
            if matched:
                filtered.append((manifest, repo, url, path, matched, cleanup))
        raw_specs = filtered

    # Determine variants
    variants = args.variant or ["vanilla"]
    for v in variants:
        if v not in ALL_VARIANTS:
            raise SystemExit(
                f"Unknown variant: {v}. Options: {', '.join(ALL_VARIANTS)}"
            )

    # Expand into WorkspaceSpecs
    specs: list[WorkspaceSpec] = []
    for manifest, repo, url, path, commits, cleanup in raw_specs:
        for commit in commits:
            for variant in variants:
                specs.append(WorkspaceSpec(
                    manifest=manifest, repo=repo, url=url,
                    path=path, commit=commit, variant=variant,
                    cleanup_commands=cleanup,
                ))

    if not specs:
        raise SystemExit("Nothing to process.")

    print(f"Workspace version: {version}")
    print(f"Variants: {', '.join(variants)}")
    print(f"Total workspaces: {len(specs)}")
    print()

    if args.dry_run:
        for s in specs:
            print(f"[plan]   {workspace_dest(s, args.workspace, version).name}")
        return 0

    args.workspace.mkdir(parents=True, exist_ok=True)

    # Group by (repo, commit) to share the expensive base snapshot
    groups: dict[tuple[str, str], list[WorkspaceSpec]] = defaultdict(list)
    for s in specs:
        groups[(s.repo, s.commit)].append(s)

    for (repo, commit), group in groups.items():
        # Check which variants actually need work
        need_work: list[WorkspaceSpec] = []
        for s in group:
            dest = workspace_dest(s, args.workspace, version)
            if dest.exists() and not args.force:
                try:
                    if run_git(["rev-parse", "HEAD"], cwd=dest) == s.commit:
                        print(f"[skip]   {dest.name}")
                        continue
                except Exception:
                    pass
            need_work.append(s)

        if not need_work:
            continue

        first = need_work[0]

        if len(need_work) == 1:
            # Single variant: create directly at final destination
            s = need_work[0]
            dest = workspace_dest(s, args.workspace, version)
            if dest.exists():
                shutil.rmtree(dest)
            create_base_snapshot(s.repo, s.url, s.path, s.commit, dest)
            verify(s.commit, dest)
            apply_variant(s, dest)
            print(f"[ok]     {dest.name}")
        else:
            # Multiple variants: create base once, copy for each
            with tempfile.TemporaryDirectory(dir=args.workspace) as tmp:
                base_dir = Path(tmp) / "base"
                create_base_snapshot(
                    first.repo, first.url, first.path, first.commit, base_dir,
                )
                verify(first.commit, base_dir)

                for s in need_work:
                    dest = workspace_dest(s, args.workspace, version)
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(base_dir, dest, symlinks=True)
                    apply_variant(s, dest)
                    print(f"[ok]     {dest.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
