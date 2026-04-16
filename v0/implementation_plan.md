MSR-Agent Memory 冷启动实现方案（V5，Semantic Decision Memory）

## 0. 问题定义（本轮纠偏）

当前实现主要基于结构化统计（共变、热点、风险）。它对“哪里可能有问题”有帮助，但对 Agent 最关键的三个问题回答不够：
- 这个改动背后的真实业务/架构意图是什么？
- 历史上为什么这样修、为什么拒绝那样修？
- 这次任务应该优先遵循哪条语义约束（而不是哪条频次最高）？

所以 V5 目标不是增加指标，而是引入 **深层语义抽取 + 语义决策编译**。

---

## 1. 目标重定义

把上下文系统从“统计记忆”升级为“语义决策记忆”：
- 不是只告诉 Agent “经常一起改什么”，
- 而是告诉 Agent “为什么必须这样改、不能怎样改、改完如何证明没破坏语义契约”。

成功标准：
- Agent 命中的上下文包含 **意图/约束/动作/验证/证据链** 五要素。
- Agent 在同类任务上回归率下降、一次通过率上升。
- 在相同 token 预算下，语义命中率优于纯统计方案。

---

## 2. 语义对象模型（核心）

引入 `Semantic Insight Unit`（SIU），替代“纯统计卡片”。

```yaml
id: SIU-BUG-017
trigger:
  paths: ["pydantic/json_schema.py"]
  intent: ["fix", "refactor"]
  concepts: ["json-schema", "typed-dict", "extras_schema"]
intent:
  task_goal: "修复 typed dict schema 行为"
  hidden_constraints:
    - "必须保留 extras_schema 语义"
decision:
  actions:
    - "同步修改 tests/test_json_schema.py"
    - "保留旧分支兼容行为，新增回归断言"
  verify:
    - "pytest tests/test_json_schema.py -q"
why:
  root_cause: "历史 Issue 指出 config-only 路径会丢失 extras_schema"
  rejected_alternatives:
    - "仅改文档，不改生成逻辑"
provenance:
  code_refs: ["pydantic/json_schema.py#L..."]
  issue_refs: ["#12809"]
  pr_refs: ["#12810"]
  commit_refs: ["<sha>"]
score:
  confidence: 0.82
  utility: 0.78
  freshness_days: 5
```

SIU 与旧卡片的关键区别：
- 多了 `intent/root_cause/rejected_alternatives`（语义动机）
- 强制 `provenance` 跨源证据链（代码 + Issue/PR + Commit）

---

## 3. 三条语义抽取流水线

### 3.1 代码语义流水线（Code Semantics)

输入：源码、类型注解、注释、测试、CI 失败日志（可选）。

抽取目标：
- 语义契约：前置条件/后置条件/不变量/兼容性边界
- 行为规格：由测试用例名、断言、fixture 组合反推出“系统承诺”
- 变更边界：API surface、跨模块调用路径、错误处理策略

建议工具：
- `tree-sitter` / `libcst` / `ast`（按语言选）
- `networkx` 构建符号依赖子图
- `pytest --collect-only` 获取测试拓扑（Python 仓库）

输出：`code_semantic_atoms`（语义原子）

---

### 3.2 Issue/PR 语义流水线（Discussion Semantics)

输入：Issue/PR title/body/comments/reviews/review threads。

抽取目标（结构化槽位）：
- Problem：问题定义与复现上下文
- Root Cause：根因假设与证据
- Decision：最终采用方案
- Non-goals：明确不做什么
- Rejected Alternatives：被否决方案与原因
- Redlines：review 明确质量红线（必须补测、必须更新文档等）

建议策略：
- 先规则提取（模板词、review 关键词）
- 再用小模型/LLM 做槽位归一化（仅对候选文本）

输出：`discussion_frames`

---

### 3.3 Commit Message + Diff 语义流水线（Change Intent Semantics)

输入：commit message + diff + 关联 PR/Issue。

抽取目标：
- 变更意图：fix/refactor/feature/perf/security/docs
- 影响语义：行为变化/接口变化/兼容性风险
- 修复模式：异常处理、边界检查、类型收窄、并发保护等
- 回滚信号：revert 链路反映的“高风险决策区域”

建议工具：
- `pydriller`（可选）或 git CLI
- 轻量分类器（keyword + embedding + small model）

输出：`change_intent_frames`

---

## 4. 跨源语义对齐（最关键步骤）

建立 `Semantic Provenance Graph`：
- 节点：`code_symbol/file/test/issue/pr/comment/commit/decision`
- 边：`fixes / discusses / modifies / verifies / rejects / owned_by`

目的：
- 把“同一语义事实”在不同来源中的证据拼起来。
- 避免单源幻觉（例如只看 commit message 的误判）。

SIU 必须来自图中的跨源子图（至少 2 类来源）。

---

## 5. 从语义到 Agent 动作（编译层）

把语义图编译为 `Action Bundle`，而不是长卡片。

`Action Bundle` 模板（运行时最小单元）：
```text
WHEN: [路径 + 意图 + 语义概念]
DO: [最多3条动作]
VERIFY: [最多2条验证]
WATCHOUT: [1条不可违反约束]
WHY: [一句根因]
PROOF: [Issue/PR/Commit/Code 引用ID]
```

约束：
- DO/VERIFY 必须可执行。
- WHY 不超过 1 句。
- PROOF 只放引用键，不粘贴大段文本。

---

## 6. Agent 运行协议（主观能动性）

任务执行前：
1. 解析任务意图（fix/refactor/feature/docs/chore）
2. 识别目标路径 + 语义概念（例如 schema、serialization、concurrency）
3. 从 router 召回候选 SIU（稀疏匹配）
4. 对候选做语义重排（embedding / reranker）
5. 只注入 Top-3 Action Bundles 到计划

任务执行中：
- 若 VERIFY 失败，按 PROOF 进入 evidence 按需加载
- 若无命中，触发增量语义挖掘（最近 N 条变更 + 相关 Issue/PR）

任务完成后：
- 把结果回写为 feedback（哪些 bundle 有效/无效）用于下轮排序

---

## 7. 上下文与性能预算（语义版）

预算按风险等级动态分配：
- Low-risk 任务：<= 400 tokens
- Mid-risk 任务：<= 800 tokens
- High-risk 任务：<= 1400 tokens

默认加载顺序：
1. Router（极小）
2. Top-3 Action Bundles
3. 失败后才加载 Evidence Snippets

核心原则：
- “语义先压缩成动作，再按需展开证据”。

---

## 8. 输出结构（V5）

```text
.agent_memory/
├── index.md
├── 0_router/
│   ├── intent_path_router.jsonl
│   └── top_action_bundles.md
├── 1_action_bundles/
│   └── *.md
├── 2_evidence/
│   └── *.json
├── 3_semantic_frames/
│   ├── code_semantic_atoms.jsonl
│   ├── discussion_frames.jsonl
│   └── change_intent_frames.jsonl
├── 4_team/
│   └── reviewer_routing.md
└── report.json
```

---

## 9. 评估体系（必须新增“语义有效性”）

除了现有指标，再加入：
- Semantic Grounding Precision：SIU 的 why/proof 是否被证据支持
- Decision Usefulness@3：Top-3 bundle 是否直接影响正确决策
- Constraint Violation Rate：是否违反历史红线
- Rationale Hit Rate：Agent 解释是否命中历史真实动机

在线 A/B：
- Baseline：统计驱动（V4）
- Treatment：语义驱动（V5）
对比回归失败率、漏改率、一次通过率、token 开销。

---

## 10. 分阶段落地

### Phase A（先可用，2周）
- 在现有 Git 管道上增加：
  - commit message 语义分类
  - code semantic atoms（函数/测试层）
  - Action Bundle 编译器

### Phase B（语义闭环，2-4周）
- 接入 Issue/PR discussion frames（GraphQL 增量抓取 + 缓存）
- 构建 semantic provenance graph

### Phase C（自我改进）
- 引入任务后反馈，更新 bundle 排序
- 清理陈旧/冲突语义（staleness + contradiction checks）

---

## 11. 结论

下一版 implementation 的重点应该是：
- 从“统计相关性”升级为“语义因果性”
- 从“数据展示”升级为“决策动作编译”
- 在同等上下文预算下，让 Agent 拿到更少但更对的上下文
