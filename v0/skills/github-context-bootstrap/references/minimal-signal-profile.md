# Minimal Signal Profile

## Git-First Core Signals

From local Git history (`git log --numstat`):
- File hotspots: touch frequency + churn
- Implicit couplings: co-change file pairs with support/confidence
- Bugfix patterns: commits with fix/bug/regression semantics
- Risk hotspots: bugfix/revert concentration + ownership concentration
- Expertise map: contributor x module activity distribution
- Workflow signals: commit discipline, branch prefixes, merge styles

## Optional GitHub Supplement

When local history is incomplete:
- Pull recent PR/Issue labels and discussions using `bootstrap_github_context.py`
- Merge external bug language into `recent_bug_signals.md`

## Practical Thresholds

Treat a run as actionable when:
- `insight_count >= 30`
- `context_overhead_tokens_est <= 700`
- `coupling_rule_count >= 5`
- `bugfix_commit_count >= 8`
- `insight_router_tokens_runtime_est <= 250`
- `code_semantic_atom_count > 0`
- `change_intent_frame_count > 0`

## Output Discipline

Keep memory compact:
- Keep `0_router/preload_router.jsonl` tiny (`router-load-k` entries).
- Keep action bundles short (`WHEN/DO/VERIFY/WATCHOUT/WHY/PROOF` only).
- Put detailed evidence in `2_evidence/*.json` and load on demand.
