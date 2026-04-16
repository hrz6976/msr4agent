# Git Signal Playbook

## Mapping to CONTEXT.md

### 1) 背景认知

- 代码拓扑图谱（Git可近似）:
  - 用“模块热点 + 文件共变图”近似跨文件依赖。
  - 输出: `2_architecture/change_topology.md` + `3_lessons/implicit_couplings.md`。
- 业务需求映射:
  - 从 commit subject 中抽 issue key（`#123`, `ABC-123`）建立需求线索。
  - 输出: `report.json.metrics.issue_linked_commit_ratio`。
- 制度化规约:
  - 抽取 `AGENTS.md`/`CONTRIBUTING.md`/`.cursorrules` 强约束句。
  - 输出: `1_conventions/git_workflow_conventions.md`。

### 2) 演进经验

- 变更耦合与隐式依赖:
  - 同提交共改文件对，计算 support/confidence。
- 历史缺陷与修复模式:
  - 用 bugfix/revert 语义提交构建“高复发路径”和高频问题词。
- 代码健康度与风险感知:
  - 风险分 = 变更频率 + bugfix/revert 权重 + 贡献者集中度。
- 运行轨迹的 Git 替代指标:
  - 通过 revert 峰值、CI 文件波动、发布前后 churn 波动做弱替代。

### 3) 协作语境

- 代码审查与协作标准:
  - 统计 commit message 规范率、issue 关联率、code-test 同改率。
- 架构决策动机（近似）:
  - 通过同主题提交串（关键词聚类）追踪决策演进。
- 版本管理规范:
  - 统计 branch 前缀与 merge 风格分布。
- 开发者专长地图:
  - 作者-模块触达矩阵 + 模块熵（专精/泛化程度）。

## Runtime Presentation (Agent-Friendly)

- L0 Router:
  - `0_router/preload_router.jsonl` for tiny default context load.
  - `0_router/intent_path_router.jsonl` for scoped semantic matching.
- L1 Action Packs:
  - `1_action_bundles/<id>.md` with strict `WHEN/DO/VERIFY/WATCHOUT/WHY/PROOF`.
- L2 Evidence:
  - `2_evidence/<id>.json` loaded only on conflict/failure.
- Semantic Frames (on-demand):
  - `3_semantic_frames/code_semantic_atoms.jsonl`
  - `3_semantic_frames/change_intent_frames.jsonl`
  - `3_semantic_frames/discussion_frames.jsonl`

Default objective:
- Keep runtime context overhead under ~700 tokens/task.

## Divergent Signals (Optional Extensions)

- Revert Loop Detector:
  - 发现“同文件短周期修复-回滚-再修复”循环，标注为高回归风险。
- Blast Radius Predictor:
  - 由共变图估算某文件改动的潜在影响半径（2-hop 邻接文件数）。
- Review Load Balancer:
  - 用作者活跃度和模块专精度给 reviewer 候选打分，避免单点过载。
- Release Stress Meter:
  - 结合 tag 时间与发布窗口前后 churn，识别“赶发布”风险模块。

## Suggested Tooling (Optional)

The current script uses pure git CLI + Python stdlib for portability.
Optional packages for future expansion:
- `PyDriller`: richer commit abstractions and easier mining pipelines
- `networkx`: community detection over co-change graph
- `pandas`/`polars`: faster aggregations for very large histories
