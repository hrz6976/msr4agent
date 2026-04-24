#!/usr/bin/env python3
import argparse
import concurrent.futures
import subprocess
import sys

from datasets import get_dataset_split_names, load_dataset


DEFAULT_DATASET = "SWE-bench/SWE-bench_Lite"


def image_name(instance_id: str) -> str:
    return (
        f"swebench/sweb.eval.x86_64.{instance_id.lower()}:latest".replace(
            "__", "_1776_"
        )
    )


def parse_splits_arg(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    splits = [s.strip() for s in raw.split(",") if s.strip()]
    return splits or None


def collect_instance_ids(dataset_name: str, splits: list[str]) -> list[str]:
    ids: set[str] = set()
    for split in splits:
        rows = load_dataset(dataset_name, split=split)
        for row in rows:
            instance_id = row.get("instance_id")
            if isinstance(instance_id, str) and instance_id:
                ids.add(instance_id)
    return sorted(ids)


def docker_image_exists(image: str) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def pull_one(image: str) -> tuple[str, bool, str]:
    result = subprocess.run(
        ["docker", "pull", image],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    ok = result.returncode == 0
    output = (result.stdout or "").strip()
    return image, ok, output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pull all official SWE-bench Lite docker images using the naming rule "
            "swebench/sweb.eval.x86_64.{instance_id_lower}:latest with '__' "
            "replaced by '_1776_'."
        )
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_DATASET,
        help=f"Hugging Face dataset name (default: {DEFAULT_DATASET})",
    )
    parser.add_argument(
        "--splits",
        default=None,
        help=(
            "Comma-separated splits to use. Default is all available splits "
            "from the dataset."
        ),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of parallel docker pull workers (default: 8)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Retries per image after first failure (default: 1)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip images that already exist locally (via docker image inspect).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the resolved image list; do not call docker pull.",
    )

    args = parser.parse_args(argv)
    if args.workers < 1:
        print("--workers must be >= 1", file=sys.stderr)
        return 2
    if args.retries < 0:
        print("--retries must be >= 0", file=sys.stderr)
        return 2

    requested_splits = parse_splits_arg(args.splits)
    all_splits = get_dataset_split_names(args.dataset)
    splits = requested_splits or all_splits

    missing = [s for s in splits if s not in all_splits]
    if missing:
        print(
            f"Unknown split(s): {missing}. Available splits: {all_splits}",
            file=sys.stderr,
        )
        return 2

    print(f"Dataset: {args.dataset}")
    print(f"Splits: {', '.join(splits)}")

    instance_ids = collect_instance_ids(args.dataset, splits)
    if not instance_ids:
        print("No instances found.")
        return 0

    images = [image_name(iid) for iid in instance_ids]
    images = sorted(set(images))

    print(f"Resolved instances: {len(instance_ids)}")
    print(f"Resolved unique images: {len(images)}")

    if args.skip_existing:
        kept = []
        skipped = 0
        for img in images:
            if docker_image_exists(img):
                skipped += 1
            else:
                kept.append(img)
        images = kept
        print(f"Skipped existing images: {skipped}")
        print(f"Images left to pull: {len(images)}")

    if args.dry_run:
        for img in images:
            print(img)
        return 0

    if not images:
        print("Nothing to pull.")
        return 0

    total_images = len(images)
    print(
        f"Start pulling {total_images} images with workers={args.workers}, "
        f"retries={args.retries}"
    )

    attempts = {img: 0 for img in images}
    pending = list(images)
    failures: dict[str, str] = {}
    successes: list[str] = []

    while pending:
        round_images = pending
        pending = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(pull_one, img) for img in round_images]
            for future in concurrent.futures.as_completed(futures):
                img, ok, output = future.result()
                attempts[img] += 1
                if ok:
                    successes.append(img)
                    resolved = len(successes) + len(failures)
                    pct = 100.0 * resolved / total_images
                    print(
                        f"[{resolved}/{total_images} {pct:5.1f}%] "
                        f"[OK] {img} (attempt {attempts[img]}/{args.retries + 1})"
                    )
                    continue

                if attempts[img] <= args.retries:
                    pending.append(img)
                    resolved = len(successes) + len(failures)
                    pct = 100.0 * resolved / total_images
                    print(
                        f"[{resolved}/{total_images} {pct:5.1f}%] "
                        f"[RETRY] {img} (attempt {attempts[img]}/{args.retries + 1})"
                    )
                else:
                    failures[img] = output
                    resolved = len(successes) + len(failures)
                    pct = 100.0 * resolved / total_images
                    print(
                        f"[{resolved}/{total_images} {pct:5.1f}%] "
                        f"[FAIL] {img} (attempt {attempts[img]}/{args.retries + 1})"
                    )

    print("")
    print(f"Pull finished: success={len(successes)} fail={len(failures)}")
    if failures:
        print("Failed images and last output:")
        for img in sorted(failures):
            print(f"- {img}")
            last_lines = failures[img].splitlines()[-3:]
            for line in last_lines:
                print(f"    {line}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
