---
name: github-context-bootstrap
description: Build agent cold-start memory from repository history with a Git-first mining workflow that emits a lightweight router, executable action packs, and on-demand evidence. Use when entering an unfamiliar codebase, refreshing stale `.agent_memory`, or before risky multi-file changes.
---

# Git-First Context Bootstrap

Use local Git history as the primary source. Load context in layers to keep token cost low.

## Quick Start

```bash
python3 skills/github-context-bootstrap/scripts/mine_git_context.py \
  --repo-path . \
  --out-dir .agent_memory
```

## Runtime-Budget Preset

```bash
python3 skills/github-context-bootstrap/scripts/mine_git_context.py \
  --repo-path . \
  --out-dir .agent_memory \
  --since-days 365 \
  --max-commits 5000 \
  --router-limit 120 \
  --router-load-k 5 \
  --preload-insights 2
```

## Agent Loading Protocol

1. Load `0_router/preload_router.jsonl` first.
2. Match planned file paths/intents/concepts against `0_router/intent_path_router.jsonl`.
3. Load only matched `1_action_bundles/<id>.md` files.
4. Load `2_evidence/<id>.json` only when action conflicts or fails.
5. Load `3_semantic_frames/*.jsonl` only when root-cause semantics are ambiguous.

## Output Contract

- `0_router/preload_router.jsonl` (tiny default load)
- `0_router/intent_path_router.jsonl` (full semantic router)
- `0_router/top_action_bundles.md`
- `1_action_bundles/*.md`
- `1_actions/packs/*.md` (backward compatibility mirror)
- `2_evidence/*.json`
- `3_semantic_frames/code_semantic_atoms.jsonl`
- `3_semantic_frames/change_intent_frames.jsonl`
- `3_semantic_frames/discussion_frames.jsonl`
- `1_conventions/git_workflow_conventions.md`
- `2_architecture/change_topology.md`
- `3_lessons/*.md`
- `4_team/expertise_map.md`
- `report.json`

## Quality Gates

Primary gates (agent-operability):
- `insight_count >= 30`
- `context_overhead_tokens_est <= 700`
- `coupling_rule_count >= 5`
- `bugfix_commit_count >= 8`

## Optional GitHub Supplement

Use this only when local history is shallow or issue/PR metadata is needed:

```bash
python3 skills/github-context-bootstrap/scripts/bootstrap_github_context.py \
  --repo owner/name \
  --out-dir .agent_memory
```

## Failure Handling

- If no commits are found, increase `--since-days` or `--max-commits`.
- If router is too noisy, lower `--router-limit`.
- If runtime context exceeds budget, reduce `--router-load-k` or `--preload-insights`.
- If policy lines are empty, manually seed hard rules in `1_conventions/`.

## References

- `references/git-signal-playbook.md`
- `references/minimal-signal-profile.md`
