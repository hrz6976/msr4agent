#!/usr/bin/env python3
"""用 coding agent CLI 为仓库生成 AGENTS.md（模仿 AgentBench）。

支持 codex / gemini CLI，通过 --cli 切换。
输出: data/generated_agents_md/<owner>/<repo>/<commit[:12]>/<model>.md
索引: data/generated_agents_md/manifest.jsonl
去重键: (repo, commit, model)
"""
from __future__ import annotations

import argparse
import json
import os
import selectors
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_DIR = ROOT / "repo"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "generated_agents_md"

INIT_PROMPTS = {
    "codex": """Generate a file named AGENTS.md that serves as a contributor guide for this repository.
Your goal is to produce a clear, concise, and well-structured document with descriptive headings and actionable explanations for each section.
Follow the outline below, but adapt as needed — add sections if relevant, and omit those that do not apply to this project.

Document Requirements

- Title the document "Repository Guidelines".
- Use Markdown headings (#, ##, etc.) for structure.
- Keep the document concise. 200-400 words is optimal.
- Keep explanations short, direct, and specific to this repository.
- Provide examples where helpful (commands, directory paths, naming patterns).
- Maintain a professional, instructional tone.

Recommended Sections

Project Structure & Module Organization

- Outline the project structure, including where the source code, tests, and assets are located.

Build, Test, and Development Commands

- List key commands for building, testing, and running locally (e.g., npm test, make build).
- Briefly explain what each command does.

Coding Style & Naming Conventions

- Specify indentation rules, language-specific style preferences, and naming patterns.
- Include any formatting or linting tools used.

Testing Guidelines

- Identify testing frameworks and coverage requirements.
- State test naming conventions and how to run tests.

Commit & Pull Request Guidelines

- Summarize commit message conventions found in the project's Git history.
- Outline pull request requirements (descriptions, linked issues, screenshots, etc.).

(Optional) Add other sections if relevant, such as Security & Configuration Tips, Architecture Overview, or Agent-Specific Instructions.""",

    "gemini": """You are an AI agent that brings the power of Gemini directly into the terminal. Your task is to analyze the current directory and generate a comprehensive GEMINI.md file to be used as instructional context for future interactions.

**Analysis Process:**

1.  **Initial Exploration:**
    *   Start by listing the files and directories to get a high-level overview of the structure.
    *   Read the README file (e.g., `README.md`, `README.txt`) if it exists. This is often the best place to start.

2.  **Iterative Deep Dive (up to 10 files):**
    *   Based on your initial findings, select a few files that seem most important (e.g., configuration files, main source files, documentation).
    *   Read them. As you learn more, refine your understanding and decide which files to read next. You don't need to decide all 10 files at once. Let your discoveries guide your exploration.

3.  **Identify Project Type:**
    *   **Code Project:** Look for clues like `package.json`, `requirements.txt`, `pom.xml`, `go.mod`, `Cargo.toml`, `build.gradle`, or a `src` directory. If you find them, this is likely a software project.
    *   **Non-Code Project:** If you don't find code-related files, this might be a directory for documentation, research papers, notes, or something else.

**GEMINI.md Content Generation:**

**For a Code Project:**

*   **Project Overview:** Write a clear and concise summary of the project's purpose, main technologies, and architecture.
*   **Building and Running:** Document the key commands for building, running, and testing the project. Infer these from the files you've read (e.g., `scripts` in `package.json`, `Makefile`, etc.). If you can't find explicit commands, provide a placeholder with a TODO.
*   **Development Conventions:** Describe any coding styles, testing practices, or contribution guidelines you can infer from the codebase.

**For a Non-Code Project:**

*   **Directory Overview:** Describe the purpose and contents of the directory. What is it for? What kind of information does it hold?
*   **Key Files:** List the most important files and briefly explain what they contain.
*   **Usage:** Explain how the contents of this directory are intended to be used.

**Final Output:**

Write the complete content to the `GEMINI.md` file. The output must be well-formatted Markdown.""",

    "qwen": """You are Qwen Code, an interactive CLI agent. Analyze the current directory and generate a comprehensive AGENTS.md file to be used as instructional context for future interactions.

**Analysis Process:**

1.  **Initial Exploration:**
    *   Start by listing the files and directories to get a high-level overview of the structure.
    *   Read the README file (e.g., `README.md`, `README.txt`) if it exists. This is often the best place to start.

2.  **Iterative Deep Dive (up to 10 files):**
    *   Based on your initial findings, select a few files that seem most important (e.g., configuration files, main source files, documentation).
    *   Read them. As you learn more, refine your understanding and decide which files to read next. You don't need to decide all 10 files at once. Let your discoveries guide your exploration.

3.  **Identify Project Type:**
    *   **Code Project:** Look for clues like `package.json`, `requirements.txt`, `pom.xml`, `go.mod`, `Cargo.toml`, `build.gradle`, or a `src` directory. If you find them, this is likely a software project.
    *   **Non-Code Project:** If you don't find code-related files, this might be a directory for documentation, research papers, notes, or something else.

**AGENTS.md Content Generation:**

**For a Code Project:**

*   **Project Overview:** Write a clear and concise summary of the project's purpose, main technologies, and architecture.
*   **Building and Running:** Document the key commands for building, running, and testing the project. Infer these from the files you've read (e.g., `scripts` in `package.json`, `Makefile`, etc.). If you can't find explicit commands, provide a placeholder with a TODO.
*   **Development Conventions:** Describe any coding styles, testing practices, or contribution guidelines you can infer from the codebase.

**For a Non-Code Project:**

*   **Directory Overview:** Describe the purpose and contents of the directory. What is it for? What kind of information does it hold?
*   **Key Files:** List the most important files and briefly explain what they contain.
*   **Usage:** Explain how the contents of this directory are intended to be used.

**Final Output:**

Write the complete content to the `AGENTS.md` file. The output must be well-formatted Markdown.""",

    "claude": """Please analyze this codebase and create a CLAUDE.md file, which will be given to future instances of Claude Code to operate in this repository.

What to add:
1. Commands that will be commonly used, such as how to build, lint, and run tests. Include the necessary commands to develop in this codebase, such as how to run a single test.
2. High-level code architecture and structure so that future instances can be productive more quickly. Focus on the "big picture" architecture that requires reading multiple files to understand.

Usage notes:
- If there's already a CLAUDE.md, suggest improvements to it.
- When you make the initial CLAUDE.md, do not repeat yourself and do not include obvious instructions like "Provide helpful error messages to users", "Write unit tests for all new utilities", "Never include sensitive information (API keys, tokens) in code or commits".
- Avoid listing every component or file structure that can be easily discovered.
- Don't include generic development practices.
- If there are Cursor rules (in .cursor/rules/ or .cursorrules) or Copilot rules (in .github/copilot-instructions.md), make sure to include the important parts.
- If there is a README.md, make sure to include the important parts.
- Do not make up information such as "Common Development Tasks", "Tips for Development", "Support and Documentation" unless this is expressly included in other files that you read.
- Be sure to prefix the file with the following text:

```
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
```""",
}


# ============================================================
# CLI 配置
# ============================================================

CLI_CONFIGS = {
    "codex": {
        "bin": "codex",
        "default_model": "gpt-5.3-codex-2026-02-24",
        "output_files": ["AGENTS.md"],
        "env_base_url": "OPENAI_BASE_URL",
        "env_api_key": "OPENAI_API_KEY",
    },
    "gemini": {
        "bin": "gemini",
        "default_model": "gemini-2.5-pro",
        "output_files": ["GEMINI.md", "AGENTS.md"],
        "env_base_url": "OPENAI_BASE_URL",
        "env_api_key": "OPENAI_API_KEY",
    },
    "qwen": {
        "bin": "qwen",
        "default_model": "gemini-3-pro-preview-new",
        "output_files": ["AGENTS.md", "GEMINI.md"],
        "env_base_url": "OPENAI_BASE_URL",
        "env_api_key": "OPENAI_API_KEY",
    },
    "claude": {
        "bin": "claude",
        "default_model": "anthropic/claude-sonnet-4.5",
        "output_files": ["CLAUDE.md", "AGENTS.md"],
        "env_base_url": "ANTHROPIC_BASE_URL",
        "env_api_key": "ANTHROPIC_AUTH_TOKEN",
    },
}


def build_cli_cmd(cli: str, model: str) -> tuple[list[str], dict | None, bool]:
    """构建 CLI 命令和环境变量。返回 (cmd, env_override, prompt_via_stdin)。"""
    cfg = CLI_CONFIGS[cli]
    base_url = os.environ.get(cfg["env_base_url"], "")
    api_key = os.environ.get(cfg["env_api_key"], "")

    if cli == "codex":
        cmd = ["codex", "exec", "--yolo", "--skip-git-repo-check",
               "--ignore-user-config", "--ignore-rules", "--ephemeral"]
        if base_url:
            cmd += ["-c", "model_provider=custom",
                    "-c", "model_providers.custom.name=custom",
                    "-c", f"model_providers.custom.base_url={base_url}",
                    "-c", "model_providers.custom.env_key=CODEX_API_KEY",
                    "-c", "model_providers.custom.wire_api=responses"]
            env = {**os.environ, "CODEX_API_KEY": api_key}
        else:
            env = None
        cmd += ["-m", model]
        cmd.append("-")  # prompt via stdin
        return cmd, env, True

    elif cli == "gemini":
        # AgentBench 方式: GEMINI_API_KEY + GOOGLE_GEMINI_BASE_URL + GEMINI_MODEL 环境变量
        cmd = ["gemini", "--yolo", "-p"]
        env = {**os.environ}
        if api_key:
            env["GEMINI_API_KEY"] = api_key
        if base_url:
            # Gemini API base URL 不需要 /v1 后缀，自动去除
            gemini_base = base_url.rstrip("/")
            if gemini_base.endswith("/v1"):
                gemini_base = gemini_base[:-3]
            env["GOOGLE_GEMINI_BASE_URL"] = gemini_base
        env["GEMINI_MODEL"] = model
        # gemini: -p <prompt>，prompt 作为命令行参数
        return cmd, env, False

    elif cli == "qwen":
        # AgentBench 方式: OPENAI_API_KEY + OPENAI_BASE_URL + OPENAI_MODEL 环境变量
        # qwen 使用 OpenAI Chat Completions 协议，-p <prompt> 传 prompt
        cmd = ["qwen", "--yolo", "-p"]
        env = {**os.environ}
        if api_key:
            env["OPENAI_API_KEY"] = api_key
        if base_url:
            env["OPENAI_BASE_URL"] = base_url
        env["OPENAI_MODEL"] = model
        return cmd, env, False

    elif cli == "claude":
        # AgentBench 方式: ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN 环境变量
        # claude --dangerously-skip-permissions --model <model> -p <prompt>
        cmd = ["claude", "--dangerously-skip-permissions", "--model", model, "-p"]
        env = {**os.environ}
        if base_url:
            env["ANTHROPIC_BASE_URL"] = base_url
        if api_key:
            env["ANTHROPIC_AUTH_TOKEN"] = api_key
        return cmd, env, False

    else:
        raise ValueError(f"unknown cli: {cli}")


# ============================================================
# Helpers
# ============================================================

def load_dotenv(path: Path | None = None) -> None:
    if path is None:
        path = ROOT / ".env"
    if not path.exists():
        return
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            for ek, ev in os.environ.items():
                value = value.replace(f"${ek}", ev)
            if key not in os.environ:
                os.environ[key] = value


def sh(args, cwd=None, timeout=300, input_data=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       timeout=timeout, input=input_data)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def git(args, cwd):
    rc, out, _ = sh(["git", *args], cwd=cwd)
    return rc, out


def cleanup(workdir: Path) -> None:
    sh(["find", ".", "-type", "f", "(", "-name", "AGENTS.md",
        "-o", "-name", "CLAUDE.md", "-o", "-name", "GEMINI.md", ")", "-delete"],
       cwd=workdir)
    for d in [".github", ".cursor", ".claude", ".codex", ".qwen", ".gemini",
              ".roo", ".bolt", ".trae", ".goose", ".v0", ".augment", ".junie"]:
        p = workdir / d
        if p.exists():
            shutil.rmtree(p)
    for f in [".cursorrules", ".clinerules", ".windsurfrules", ".roomodes"]:
        p = workdir / f
        if p.exists():
            p.unlink()
    rc, out = git(["remote"], workdir)
    if rc == 0:
        for r in out.splitlines():
            if r.strip():
                git(["remote", "remove", r.strip()], workdir)


def run_agent(workdir, prompt, cli, model, timeout, log_dir=None):
    """运行 coding agent CLI，实时输出，返回 (returncode, stdout, stderr)。"""
    cmd, env, prompt_via_stdin = build_cli_cmd(cli, model)

    if not prompt_via_stdin:
        # gemini/qwen: prompt 作为 -p 的参数
        cmd.append(prompt)

    proc = subprocess.Popen(cmd, cwd=workdir, env=env,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    if prompt_via_stdin:
        proc.stdin.write(prompt)
    proc.stdin.close()

    sel = selectors.DefaultSelector()
    sel.register(proc.stdout, selectors.EVENT_READ)
    sel.register(proc.stderr, selectors.EVENT_READ)
    stdout_parts, stderr_parts = [], []
    open_streams = 2
    while open_streams > 0:
        for key, _ in sel.select(timeout=1):
            line = key.fileobj.readline()
            if not line:
                sel.unregister(key.fileobj)
                open_streams -= 1
                continue
            if key.fileobj is proc.stdout:
                print(f"  {line}", end="", flush=True)
                stdout_parts.append(line)
            else:
                print(f"  {line}", end="", flush=True)
                stderr_parts.append(line)
    proc.wait(timeout=timeout)

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "stdout.log").write_text("".join(stdout_parts))
        (log_dir / "stderr.log").write_text("".join(stderr_parts))

    return proc.returncode, "".join(stdout_parts).strip(), "".join(stderr_parts).strip()


# ============================================================
# Core
# ============================================================

def generate_one(repo, repo_dir, commit, manifest, cli, model, prompt_type,
                 output_dir, manifest_path, dry_run=False, timeout=600,
                 workdir_base=None):
    record = {"repo": repo, "commit": commit, "manifest": manifest,
              "cli": cli, "model": model, "prompt": f"{prompt_type}_agentsmd",
              "status": "pending", "file": None, "time_s": None, "error": None}
    if workdir_base is None:
        workdir_base = Path(tempfile.mkdtemp(prefix="agentsmd_"))
    workdir = workdir_base / repo.replace("/", "_") / commit[:12]
    workdir.parent.mkdir(parents=True, exist_ok=True)

    def save(rec):
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

    try:
        rc, _ = git(["cat-file", "-e", f"{commit}^{{commit}}"], repo_dir)
        if rc != 0 or sh(["git", "worktree", "add", "--detach", str(workdir), commit], cwd=repo_dir)[0] != 0:
            record.update(status="error", error="worktree failed")
            save(record)
            return record

        cleanup(workdir)
        git(["add", "-A"], workdir)
        git(["commit", "-m", "cleanup", "--allow-empty"], workdir)

        if dry_run:
            record["status"] = "dry_run"
            save(record)
            return record

        log_dir = output_dir / repo / commit[:12]
        t0 = time.time()
        rc, _, stderr = run_agent(workdir, INIT_PROMPTS[prompt_type], cli, model, timeout, log_dir)
        elapsed = round(time.time() - t0, 1)
        record["time_s"] = elapsed

        if rc != 0:
            record.update(status="error", error=f"exit {rc}: {stderr[:500]}")
            save(record)
            return record

        generated = {}
        for fname in CLI_CONFIGS.get(prompt_type, CLI_CONFIGS[cli])["output_files"] + ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]:
            fp = workdir / fname
            if fp.exists():
                c = fp.read_text()
                if c.strip():
                    generated[fname] = c

        if generated:
            # 优先使用 CLI 配置的 output_files（如 gemini 优先 GEMINI.md）
            content = None
            for pf in CLI_CONFIGS.get(prompt_type, CLI_CONFIGS[cli])["output_files"]:
                if pf in generated:
                    content = generated[pf]
                    break
            if content is None:
                content = next(iter(generated.values()))
            out_path = output_dir / repo / commit[:12] / f"{model}.md"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content)
            record.update(status="success", file=str(out_path.relative_to(output_dir)))
            print(f"  => {record['file']} ({len(content)} chars, {elapsed}s)")
        else:
            record["status"] = "no_output"

        save(record)
        return record

    except subprocess.TimeoutExpired:
        record.update(status="timeout", error=f"timeout {timeout}s")
        save(record)
        return record
    except Exception as e:
        record.update(status="error", error=str(e))
        save(record)
        return record
    finally:
        sh(["git", "worktree", "remove", "--force", str(workdir)], cwd=repo_dir)
        if workdir.exists():
            shutil.rmtree(workdir, ignore_errors=True)
        sh(["git", "worktree", "prune"], cwd=repo_dir)


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="用 coding agent CLI 为仓库生成 AGENTS.md"
    )
    parser.add_argument("--cli", default="codex", choices=list(CLI_CONFIGS),
                        help="使用哪个 CLI (默认 codex)")
    parser.add_argument("--model", default=None,
                        help="模型名（不指定则用 CLI 的默认模型）")
    parser.add_argument("--prompt", default=None, choices=list(INIT_PROMPTS),
                        help="使用哪个 prompt (默认跟 --cli 一致)")
    parser.add_argument("--manifest", action="append")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--repo", action="append")
    parser.add_argument("--per-repo", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--workdir")
    args = parser.parse_args()

    load_dotenv()

    cli = args.cli
    model = args.model or CLI_CONFIGS[cli]["default_model"]
    prompt_type = args.prompt or cli
    cfg = CLI_CONFIGS[cli]

    rc, ver, _ = sh([cfg["bin"], "--version"])
    if rc != 0:
        return print(f"{cfg['bin']} CLI not found") or 1
    print(f"{cli} {ver} | model: {model} | prompt: {prompt_type}")

    if not args.dry_run:
        key = os.environ.get(cfg["env_api_key"], "")
        if not key:
            return print(f"{cfg['env_api_key']} not set") or 1
        base = os.environ.get(cfg["env_base_url"], "")
        if base:
            print(f"base_url: {base}")

    manifests = [Path(m) for m in args.manifest] if args.manifest else sorted(REPO_DIR.glob("*.jsonl"))
    output_dir = Path(args.output_dir)
    mf = output_dir / "manifest.jsonl"
    existing = set()
    if mf.exists():
        for line in open(mf):
            r = json.loads(line)
            if r.get("status") == "success":
                existing.add((r["repo"], r["commit"], r["model"]))
    if existing:
        print(f"resuming, {len(existing)} done")

    wb = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="agentsmd_"))
    ok = err = skip = 0

    for mp in manifests:
        entries = [json.loads(l) for l in open(mp) if l.strip()]
        print(f"\n--- {mp.stem} ({len(entries)} repos) ---")

        for entry in entries:
            repo = entry["repo"]
            if args.repo and repo not in args.repo:
                continue
            repo_dir = ROOT / entry["path"]
            if not (repo_dir / ".git").exists():
                continue

            commits = entry.get("used_commits", []) or [entry["commit"]]
            if args.per_repo:
                commits = [commits[-1]]
            print(f"\n[{repo}] {len(commits)} commit(s)")

            for c in commits:
                if (repo, c, model) in existing:
                    skip += 1
                    continue
                print(f"  {c[:12]}")
                rec = generate_one(repo, repo_dir, c, mp.stem, cli, model,
                                   prompt_type, output_dir, mf,
                                   args.dry_run, args.timeout, wb)
                if rec["status"] == "success":
                    ok += 1
                elif rec["status"] != "dry_run":
                    err += 1

    print(f"\n--- done: {ok} ok, {err} err, {skip} skip ---")
    if not args.workdir and wb.exists():
        shutil.rmtree(wb, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
