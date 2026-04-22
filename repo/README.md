This directory stores local repository checkouts used by benchmark tooling.

It is a local cache, not something we commit to git.

The pinned revisions live in JSONL manifests directly under `repo/`.

Use `repo/sync_repositories.py` to sync clones from those manifests.
By default it reads every `repo/*.jsonl` file.

SWD-Bench checkouts live under `repo/swd-bench/<owner>/<name>`.
AgentBench checkouts live under `repo/agentbench/<owner>/<name>`.
