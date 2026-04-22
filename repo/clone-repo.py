#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_DIR = ROOT / "repo"


@dataclass(frozen=True)
class CheckoutSpec:
    manifest: str
    repo: str
    url: str
    path: str
    commit: str
    source: str
    commit_date: str
    requested_version: str
    resolved_ref: str
    instance_count: int
    used_commits: tuple[str, ...]
    example_instance_id: str


def run_git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def discover_manifest_paths() -> list[Path]:
    return sorted(
        path
        for path in REPO_DIR.glob("*.jsonl")
        if path.is_file()
    )


def resolve_manifest_paths(requested: list[str] | None) -> list[Path]:
    if not requested:
        paths = discover_manifest_paths()
        if not paths:
            raise SystemExit(f"No JSONL manifests found under {REPO_DIR}")
        return paths

    resolved: list[Path] = []
    for item in requested:
        candidate = Path(item)
        if candidate.exists():
            resolved.append(candidate.resolve())
            continue

        repo_candidate = REPO_DIR / item
        if repo_candidate.exists():
            resolved.append(repo_candidate.resolve())
            continue

        if not item.endswith(".jsonl"):
            stem_candidate = REPO_DIR / f"{item}.jsonl"
            if stem_candidate.exists():
                resolved.append(stem_candidate.resolve())
                continue

        raise SystemExit(f"Manifest not found: {item}")

    return sorted(dict.fromkeys(resolved))


def load_manifest(path: Path) -> list[CheckoutSpec]:
    entries: list[CheckoutSpec] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue

            item = json.loads(raw)
            for key in ("repo", "url", "path", "commit"):
                if not item.get(key):
                    raise ValueError(
                        f"{path}:{line_number} is missing required field {key!r}"
                    )

            checkout_path = Path(item["path"])
            if checkout_path.is_absolute():
                raise ValueError(
                    f"{path}:{line_number} uses an absolute path for 'path': "
                    f"{item['path']}"
                )

            entries.append(
                CheckoutSpec(
                    manifest=path.stem,
                    repo=item["repo"],
                    url=item["url"],
                    path=item["path"],
                    commit=item["commit"],
                    source=item.get("source", ""),
                    commit_date=item.get("commit_date", ""),
                    requested_version=item.get("requested_version", ""),
                    resolved_ref=item.get("resolved_ref", ""),
                    instance_count=int(item.get("instance_count", 0)),
                    used_commits=tuple(item.get("used_commits", [])),
                    example_instance_id=item.get("example_instance_id", ""),
                )
            )

    return entries


def load_entries(manifest_paths: list[Path]) -> list[CheckoutSpec]:
    entries: list[CheckoutSpec] = []
    for path in manifest_paths:
        entries.extend(load_manifest(path))

    by_path: dict[str, CheckoutSpec] = {}
    for entry in entries:
        existing = by_path.get(entry.path)
        if existing is None:
            by_path[entry.path] = entry
            continue
        if existing != entry:
            raise SystemExit(
                f"Conflicting manifest entries for path {entry.path}: "
                f"{existing.manifest} vs {entry.manifest}"
            )

    return sorted(entries, key=lambda entry: (entry.manifest, entry.repo))


def ensure_clone(spec: CheckoutSpec, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if (destination / ".git").exists():
        current_remote = run_git(["remote", "get-url", "origin"], cwd=destination)
        if current_remote != spec.url:
            raise RuntimeError(
                f"{destination} already exists but points to {current_remote}, "
                f"not {spec.url}."
            )
        return

    if destination.exists():
        raise RuntimeError(f"{destination} exists but is not a git repository.")

    print(f"[clone] {spec.repo} -> {destination}")
    run_git(
        ["clone", "--filter=blob:none", "--no-checkout", spec.url, str(destination)]
    )


def verify_commit_presence(spec: CheckoutSpec, destination: Path) -> None:
    for commit in spec.used_commits:
        try:
            run_git(["cat-file", "-e", f"{commit}^{{commit}}"], cwd=destination)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"{spec.repo} is missing manifest commit {commit} after fetch."
            ) from exc


def sync_checkout(spec: CheckoutSpec, dry_run: bool) -> None:
    destination = ROOT / spec.path

    if dry_run:
        details: list[str] = [f"manifest={spec.manifest}", f"commit={spec.commit}"]
        if spec.requested_version:
            details.append(f"requested={spec.requested_version}")
        if spec.resolved_ref:
            details.append(f"resolved={spec.resolved_ref}")
        if spec.instance_count:
            details.append(f"instances={spec.instance_count}")
        if spec.used_commits:
            details.append(f"used_commits={len(spec.used_commits)}")
        print(f"[plan] {spec.repo} -> {destination} ({', '.join(details)})")
        return

    ensure_clone(spec, destination)

    print(f"[fetch] {spec.repo} [{spec.manifest}]")
    run_git(
        ["fetch", "--filter=blob:none", "origin", "--tags", "--force", "--prune"],
        cwd=destination,
    )
    if spec.used_commits:
        verify_commit_presence(spec, destination)

    run_git(["checkout", "--detach", "--force", spec.commit], cwd=destination)

    head_commit = run_git(["rev-parse", "HEAD"], cwd=destination)
    if head_commit != spec.commit:
        raise RuntimeError(
            f"{spec.repo} resolved to {head_commit}, expected {spec.commit}."
        )

    print(f"[ok] {spec.repo} @ {head_commit}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sync local repository checkouts from JSONL manifests stored in repo/."
        )
    )
    parser.add_argument(
        "--manifest",
        action="append",
        help=(
            "Manifest name or path. Repeatable. Defaults to all repo/*.jsonl "
            "(for example --manifest agentbench or --manifest repo/swd-bench.jsonl)."
        ),
    )
    parser.add_argument(
        "--repo",
        action="append",
        help="Sync only the specified repository name (for example ansible/ansible).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List manifest entries without syncing any repositories.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the sync plan without cloning or checking out anything.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_paths = resolve_manifest_paths(args.manifest)
    entries = load_entries(manifest_paths)

    if args.repo:
        requested = set(args.repo)
        entries = [entry for entry in entries if entry.repo in requested]
        missing = sorted(requested - {entry.repo for entry in entries})
        if missing:
            raise SystemExit(f"Repositories not found in manifests: {', '.join(missing)}")

    if args.list:
        for entry in entries:
            item = {
                "manifest": entry.manifest,
                "repo": entry.repo,
                "path": entry.path,
                "commit": entry.commit,
            }
            if entry.requested_version:
                item["requested_version"] = entry.requested_version
            if entry.resolved_ref:
                item["resolved_ref"] = entry.resolved_ref
            if entry.instance_count:
                item["instance_count"] = entry.instance_count
            if entry.example_instance_id:
                item["example_instance_id"] = entry.example_instance_id
            print(json.dumps(item, sort_keys=True))
        return 0

    for entry in entries:
        sync_checkout(entry, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
