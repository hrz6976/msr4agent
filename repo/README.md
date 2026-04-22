This directory stores local repository checkouts used by benchmark tooling.

It is a local cache, not something we commit to git.

The pinned revisions live in JSONL manifests directly under `repo/`.

Use `repo/clone-repo.py` to sync clones from those manifests.
By default it reads every `repo/*.jsonl` file.
