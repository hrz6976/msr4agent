This directory stores local repository checkouts used by benchmark tooling.

It is a local cache, not something we commit to git.

The exact repositories and pinned revisions live in `manifests/repositories.jsonl`.
The sync script places SWD-Bench checkouts under `repo/swd-bench/<owner>/<name>`.
