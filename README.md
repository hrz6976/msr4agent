# MSR4Agent

This repository mixes our own research code with the benchmark resources we build on. The top level is organized by purpose so it is easier to see what belongs to the project and what is local support material.

## Directory overview

- `baseline/`: baseline projects we build on, including the `baseline/agentbench/` code submodule, the `baseline/agentbench_hf/` dataset submodule, and the local `baseline/swd-bench/` resources.
- `scripts/`: small helper scripts for local setup and data preparation.
- `manifests/`: committed JSONL files that pin external repositories to exact revisions.
- `repo/`: local repository checkouts used for experiments. This directory is a cache and should not be committed.
- `v0/`: the first proof-of-concept version of the project, plus notes and evaluation outputs.
- `data/`: local data files that are useful for experiments but should not live at the root.
- `jobs/`: Harbor run outputs. This stays at the root because Harbor expects it there.
- `paper/`: the Overleaf paper repository, tracked as a git submodule.
- `pyproject.toml` and `uv.lock`: Python project metadata and dependency lockfile.

## Repository checkouts

- `manifests/repositories.jsonl` records the repository URL, requested version, resolved ref, and exact commit we use.
- `scripts/clone_swd_bench_target_repos.py` syncs the local checkout cache from that manifest.
- The checkouts themselves live under `repo/swd-bench/<owner>/<name>`.

To rebuild the local checkout cache, run:

```bash
python scripts/clone_swd_bench_target_repos.py
```

## What is inside `data/`

- `data/artifacts/`: downloaded or generated artifacts that we want to keep locally without cluttering the root directory.

## Submodules

This repository currently uses these git submodules:

- `paper/` for the Overleaf paper repository.
- `baseline/agentbench/` for the AGENTBench baseline code.
- `baseline/agentbench_hf/` for the AGENTBench Hugging Face dataset snapshot.

For a fresh clone, use:

```bash
git clone --recurse-submodules <repository-url>
```

If you clone the repository without submodules, initialize it with:

```bash
git submodule update --init --recursive
```

The `--recursive` flag matters because this repository contains nested baseline dependencies under `baseline/`.
