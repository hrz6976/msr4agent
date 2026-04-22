#!/usr/bin/env python3
"""从仓库 git 历史中提取开发者编写的 agent directive 文件。

两阶段提取策略：
  1. commit_tree: 从指定 commit 的 tree 中提取（无数据泄露）
  2. future_ref:  从该 commit 的未来 ref（如 origin/main）中提取（参考 AgentBench HumanPlanner）
  每个文件都会记录来源 (source) 信息。

使用 fnmatch 匹配所有已知的 agent directive 文件。

输出格式 (JSON):
  [
    {
      "repo": "ansible/ansible",
      "path": "repo/ansible/ansible",
      "manifest": "agentbench",
      "commit": "fb7fd51b...",
      "files": {
        "AGENTS.md": { "content": "...", "source": "commit_tree", "source_ref": "fb7fd51b..." },
        "CLAUDE.md": { "content": "...", "source": "future_ref", "source_ref": "origin/main", "source_commit": "abc123..." }
      }
    },
    ...
  ]
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_DIR = ROOT / "repo"


# ============================================================
# fnmatch 模式，用于从 git ls-tree 全量输出中筛选
# 仅匹配包含自然语言指令的文件（含 skills），排除可执行
# 代码（hooks/*.py, *.sh）和机器配置（*.json, *.toml）
# ============================================================
AGENT_FNMATCH_PATTERNS = [
    # 根目录 markdown
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "COPILOT.md",
    # 根目录配置（自然语言规则文件）
    ".cursorrules",
    ".clinerules",
    ".windsurfrules",
    ".roomodes",
    # Cursor 规则（.mdc / .md）
    ".cursor/rules/*.mdc",
    ".cursor/rules/*.md",
    # Claude Code（commands 和 skills 是自然语言 markdown）
    ".claude/commands/*.md",
    ".claude/skills/*.md",
    ".claude/skills/*/*.md",
    ".claude/skills/*/SKILL.md",
    # Codex（仅 instructions.md，排除 hooks/、config.toml、hooks.json）
    ".codex/instructions.md",
    # Qwen（仅自然语言配置）
    ".qwen/instructions.md",
    # Roo Code 规则
    ".roo/rules/*.md",
    ".roo/rules-*/*.md",
    # 其他 agent 的自然语言指令
    ".junie/guidelines.md",
    ".junie/*.md",
    ".augment/*.md",
    ".augment/instructions/*.md",
    ".trae/rules/*.md",
    ".trae/rules/*.mdc",
    ".goose/*.md",
    ".idx/airules.md",
    ".v0/*.md",
    ".bolt/prompt",
    # GitHub
    ".github/copilot-instructions.md",
    ".github/copilot-setup-steps.yml",
]


def run_git(args: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
    )
    return result.returncode, result.stdout.strip()


def git_show_file(cwd: Path, ref: str, filepath: str) -> str | None:
    rc, output = run_git(["show", f"{ref}:{filepath}"], cwd)
    if rc != 0:
        return None
    return output


def git_ls_tree_all(cwd: Path, ref: str) -> list[str]:
    """列出指定 ref 的全部文件路径。"""
    rc, output = run_git(["ls-tree", "-r", "--name-only", ref], cwd)
    if rc != 0 or not output:
        return []
    return [l.strip() for l in output.splitlines() if l.strip()]


def is_agent_directive(filepath: str) -> bool:
    """用 fnmatch 判断一个文件路径是否是 agent directive。"""
    for pat in AGENT_FNMATCH_PATTERNS:
        if fnmatch.fnmatch(filepath, pat):
            return True
    return False


def find_directives_at_ref(cwd: Path, ref: str) -> dict[str, str]:
    """从指定 ref 的 tree 中找到所有 agent directive 文件并读取内容。"""
    all_files = git_ls_tree_all(cwd, ref)
    results: dict[str, str] = {}
    for fp in all_files:
        if is_agent_directive(fp):
            content = git_show_file(cwd, ref, fp)
            if content is not None:
                results[fp] = content
    return results


# ============================================================
# 未来 ref 查找逻辑（参考 AgentBench HumanPlanner）
# ============================================================

def ref_exists(cwd: Path, ref: str) -> bool:
    rc, _ = run_git(["rev-parse", "--verify", ref], cwd)
    return rc == 0


def is_ancestor(cwd: Path, ancestor: str, ref: str) -> bool:
    rc, _ = run_git(["merge-base", "--is-ancestor", ancestor, ref], cwd)
    return rc == 0


def find_future_ref(cwd: Path, commit: str) -> str | None:
    """查找包含 commit 的未来 ref（commit 是该 ref 的祖先）。

    优先级：origin/main > origin/master > origin/dev > 其他远程分支。
    """
    candidates = [
        "refs/remotes/origin/main",
        "refs/remotes/origin/master",
        "refs/remotes/origin/dev",
        "refs/remotes/origin/devel",
        "origin/main",
        "origin/master",
    ]
    for ref in candidates:
        if ref_exists(cwd, ref) and is_ancestor(cwd, commit, ref):
            return ref

    # 回退：枚举所有包含该 commit 的 ref
    rc, output = run_git(
        ["for-each-ref", "--contains", commit,
         "--format=%(refname)", "refs/heads", "refs/remotes"],
        cwd,
    )
    if rc == 0 and output:
        refs = [l.strip() for l in output.splitlines() if l.strip()]
        preferred = [r for r in refs if r.startswith("refs/remotes/origin/")]
        preferred.extend(r for r in refs if not r.startswith("refs/remotes/origin/"))
        if preferred:
            return preferred[0]

    return None


def find_directive_in_future(
    cwd: Path, commit: str, future_ref: str, filepath: str,
) -> tuple[str | None, str | None]:
    """在 commit..future_ref 之间找到首次添加 filepath 的 commit 并读取内容。

    返回 (content, source_commit)。
    """
    rc, log_output = run_git(
        ["log", "--reverse", "--first-parent", "--format=%H",
         "--diff-filter=A", f"{commit}..{future_ref}", "--", filepath],
        cwd,
    )
    if rc == 0 and log_output:
        for c in log_output.splitlines():
            c = c.strip()
            if not c:
                continue
            content = git_show_file(cwd, c, filepath)
            if content is not None:
                return content, c

    # 也检查 future_ref 的最新版本（可能文件一直存在）
    content = git_show_file(cwd, future_ref, filepath)
    if content is not None:
        rc2, resolved = run_git(["rev-parse", future_ref], cwd)
        return content, resolved if rc2 == 0 else future_ref

    return None, None


def extract_at_commit(
    repo: str,
    path: str,
    manifest: str,
    commit: str,
    repo_dir: Path,
    verbose: bool = True,
) -> dict:
    """两阶段提取：先 commit_tree，再 future_ref 兜底。"""

    files: dict[str, dict] = {}

    # ---- 阶段 1: 从当前 commit 的 tree 中提取 ----
    commit_directives = find_directives_at_ref(repo_dir, commit)
    for fp, content in commit_directives.items():
        files[fp] = {
            "content": content,
            "source": "commit_tree",
            "source_ref": commit,
        }
        if verbose:
            print(f"    [commit_tree] {fp} ({len(content)} chars)")

    # ---- 阶段 2: 从未来 ref 中补充缺失的文件 ----
    future_ref = find_future_ref(repo_dir, commit)
    if future_ref:
        future_directives = find_directives_at_ref(repo_dir, future_ref)
        for fp, content in future_directives.items():
            if fp in files:
                continue  # 已从 commit_tree 获取，不覆盖
            # 精确找到首次添加该文件的 commit
            exact_content, source_commit = find_directive_in_future(
                repo_dir, commit, future_ref, fp,
            )
            if exact_content is not None:
                files[fp] = {
                    "content": exact_content,
                    "source": "future_ref",
                    "source_ref": future_ref,
                    "source_commit": source_commit,
                }
                if verbose:
                    print(f"    [future_ref]  {fp} ({len(exact_content)} chars) via {future_ref}")
    elif verbose and not files:
        print(f"    (无 future ref，且 commit_tree 无文件)")

    if not files and verbose:
        print(f"    (无 agent directive 文件)")

    return {
        "repo": repo,
        "path": path,
        "manifest": manifest,
        "commit": commit,
        "files": files,
    }


def load_manifest(path: Path) -> list[dict]:
    entries = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            entries.append(json.loads(raw))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从仓库 git 历史中提取开发者编写的 agent directive 文件"
    )
    parser.add_argument(
        "--manifest", action="append",
        help="要处理的 manifest JSONL 文件路径（默认处理 repo/*.jsonl）",
    )
    parser.add_argument(
        "--output", default=str(ROOT / "data" / "human_agent_directives.json"),
        help="输出 JSON 文件路径",
    )
    parser.add_argument(
        "--repo", action="append",
        help="只处理指定仓库（如 ansible/ansible）",
    )
    parser.add_argument(
        "--no-future", action="store_true",
        help="禁用 future_ref 兜底，只从 commit_tree 提取",
    )
    args = parser.parse_args()

    if args.manifest:
        manifest_paths = [Path(m) for m in args.manifest]
    else:
        manifest_paths = sorted(REPO_DIR.glob("*.jsonl"))

    if not manifest_paths:
        print(f"未找到 JSONL manifest 文件（在 {REPO_DIR} 下）")
        return 1

    all_results: list[dict] = []

    for manifest_path in manifest_paths:
        manifest_name = manifest_path.stem
        entries = load_manifest(manifest_path)
        print(f"\n{'='*60}")
        print(f"处理 {manifest_name} ({len(entries)} 个仓库)")
        print(f"{'='*60}")

        for entry in entries:
            repo = entry["repo"]
            if args.repo and repo not in args.repo:
                continue

            path = entry["path"]
            repo_dir = ROOT / path

            if not (repo_dir / ".git").exists():
                print(f"\n[{repo}] 仓库未 clone，跳过")
                continue

            # 确定要提取的 commit 列表
            used_commits: list[str] = entry.get("used_commits", [])
            base_commit: str = entry["commit"]

            if used_commits:
                commits_to_extract = used_commits
                print(f"\n[{repo}] {len(commits_to_extract)} 个实例 commit")
            else:
                commits_to_extract = [base_commit]
                print(f"\n[{repo}] 单个 commit: {base_commit[:12]}...")

            # 如果指定了 --no-future，临时禁用 future_ref 查找
            original_find_future = None
            if args.no_future:
                original_find_future = globals()["find_future_ref"]
                globals()["find_future_ref"] = lambda _cwd, _commit: None

            try:
                for commit in commits_to_extract:
                    rc, _ = run_git(["cat-file", "-e", f"{commit}^{{commit}}"], repo_dir)
                    if rc != 0:
                        print(f"  commit {commit[:12]}... 不存在，跳过")
                        continue

                    print(f"  commit {commit[:12]}...")
                    result = extract_at_commit(
                        repo=repo, path=path, manifest=manifest_name,
                        commit=commit, repo_dir=repo_dir,
                    )
                    all_results.append(result)
            finally:
                if original_find_future is not None:
                    globals()["find_future_ref"] = original_find_future

    # 输出
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # 统计
    total_entries = len(all_results)
    with_files = sum(1 for r in all_results if r["files"])
    total_files = sum(len(r["files"]) for r in all_results)
    unique_repos = len({r["repo"] for r in all_results})
    repos_with_any = len({r["repo"] for r in all_results if r["files"]})

    # 按来源统计
    from_commit = sum(
        1 for r in all_results
        for f in r["files"].values() if f["source"] == "commit_tree"
    )
    from_future = sum(
        1 for r in all_results
        for f in r["files"].values() if f["source"] == "future_ref"
    )

    print(f"\n{'='*60}")
    print(f"完成")
    print(f"{'='*60}")
    print(f"共 {unique_repos} 个仓库，{total_entries} 个 commit 条目")
    print(f"  有文件的条目: {with_files}/{total_entries}")
    print(f"  有文件的仓库: {repos_with_any}/{unique_repos}")
    print(f"  提取文件总数: {total_files}")
    print(f"    来自 commit_tree: {from_commit}")
    print(f"    来自 future_ref:  {from_future}")
    print(f"结果保存到: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
