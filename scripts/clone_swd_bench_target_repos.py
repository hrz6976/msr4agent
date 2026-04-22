#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST_PATH = ROOT / "manifests" / "repositories.jsonl"


@dataclass(frozen=True)
class CheckoutSpec:
    repo: str
    url: str
    path: str
    source: str
    requested_version: str
    resolved_ref: str
    commit: str
    commit_date: str
    resolution_strategy: str


def run_git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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
                    repo=item["repo"],
                    url=item["url"],
                    path=item["path"],
                    source=item.get("source", ""),
                    requested_version=item.get("requested_version", ""),
                    resolved_ref=item.get("resolved_ref", ""),
                    commit=item["commit"],
                    commit_date=item.get("commit_date", ""),
                    resolution_strategy=item.get("resolution_strategy", ""),
                )
            )

    return entries


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
    run_git(["clone", "--filter=blob:none", "--no-checkout", spec.url, str(destination)])


def sync_checkout(spec: CheckoutSpec, dry_run: bool) -> None:
    destination = ROOT / spec.path

    if dry_run:
        print(
            "[plan] "
            f"{spec.repo} -> {destination} @ {spec.commit} "
            f"(requested={spec.requested_version}, resolved={spec.resolved_ref})"
        )
        return

    ensure_clone(spec, destination)

    print(f"[fetch] {spec.repo}")
    run_git(["fetch", "origin", "--tags", "--force", "--prune"], cwd=destination)
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
            "Sync local repository checkouts from a committed JSONL manifest into repo/."
        )
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help=f"Path to the checkout manifest. Default: {DEFAULT_MANIFEST_PATH}",
    )
    parser.add_argument(
        "--repo",
        action="append",
        help="Sync only the specified repository name (for example pylint-dev/pylint).",
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
    entries = load_manifest(args.manifest)

    if args.repo:
        requested = set(args.repo)
        entries = [entry for entry in entries if entry.repo in requested]
        missing = sorted(requested - {entry.repo for entry in entries})
        if missing:
            raise SystemExit(f"Repositories not found in manifest: {', '.join(missing)}")

    if args.list:
        for entry in entries:
            print(
                json.dumps(
                    {
                        "repo": entry.repo,
                        "path": entry.path,
                        "requested_version": entry.requested_version,
                        "resolved_ref": entry.resolved_ref,
                        "commit": entry.commit,
                    }
                )
            )
        return 0

    for entry in entries:
        sync_checkout(entry, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
