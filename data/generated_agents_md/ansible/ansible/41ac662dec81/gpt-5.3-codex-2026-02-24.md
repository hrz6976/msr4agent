# Repository Guidelines

## Project Structure & Module Organization
- Core Python source lives in `lib/ansible/`.
- Test harness and internal test tooling live in `test/lib/ansible_test/`.
- Test suites are split by type: `test/units/`, `test/integration/`, and `test/sanity/`.
- Developer utilities are in `hacking/` (environment setup and helper scripts).
- Release notes use fragments in `changelogs/fragments/` and are compiled into `changelogs/`.
- Packaging metadata and build config are in `pyproject.toml`, `requirements.txt`, and `packaging/`.

## Build, Test, and Development Commands
- `python -m pip install -r requirements.txt`: install runtime/dev prerequisites.
- `source hacking/env-setup`: run Ansible directly from this checkout (required for most local work).
- `ansible --version`: verify your shell is using the checkout environment.
- `ansible-test sanity --test black --test mypy`: run key static/style checks.
- `ansible-test units --changed`: run unit tests for files touched in your branch.
- `ansible-test integration <target>`: run integration coverage for a specific target.
- `./hacking/test-module.py -m lib/ansible/modules/command.py -a "echo hi"`: quickly execute a module during development.

## Coding Style & Naming Conventions
- Python 3.11+ is required; use 4-space indentation and keep changes `black`-clean.
- Follow existing module/plugin patterns under `lib/ansible/modules/` and `lib/ansible/plugins/`.
- Prefer descriptive snake_case for Python functions/files and clear, scope-based test names (`test_*.py`).
- Keep lint/type issues at zero for changed code; use `ansible-test sanity` locally before opening a PR.

## Testing Guidelines
- Primary test entrypoint is `ansible-test`; do not rely on ad-hoc `pytest` runs alone.
- Add or update unit tests in `test/units/` for logic changes.
- Add integration tests in `test/integration/targets/<feature>/` for behavior across real execution paths.
- For user-visible changes, add a changelog fragment in `changelogs/fragments/`.

## Commit & Pull Request Guidelines
- Commit messages are short, imperative, and scoped when useful (for example: `Fix ansible-doc metadata dump for relative imports (#85801)`).
- Keep commits focused; separate refactors from behavior changes.
- Open PRs against `devel` unless you are preparing an approved backport.
- PRs should include: problem statement, change summary, test evidence (`ansible-test` commands run), and linked issue(s).
