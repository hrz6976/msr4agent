# Repository Guidelines

## Project Structure & Module Organization
Core Python source code lives in `wagtail/` (admin, contrib apps, APIs, and test utilities). Frontend build tooling and shared assets live in `client/` (Webpack, TypeScript, SCSS, Storybook, Jest setup). Documentation is in `docs/`, while helper scripts are in `scripts/`. Python test apps and fixtures are under `wagtail/test/` and app-level `tests.py` / `test_*.py` files throughout the package.

## Build, Test, and Development Commands
- `make develop`: install editable Python deps (`.[testing,docs]`) and build frontend assets.
- `npm run build`: compile admin static assets once.
- `npm start`: watch/rebuild frontend assets during development.
- `make test` or `python runtests.py`: run Python test suite.
- `npm run test:unit`: run frontend unit tests (Jest).
- `make lint`: run server, client, and docs lint checks.
- `make format`: auto-fix Python/HTML/frontend formatting.
- `tox -l` / `tox -e <env> -- <target>`: run matrix tests across Django / DB / search backends.

## Coding Style & Naming Conventions
Follow `.editorconfig`: LF line endings, spaces, 4-space Python/HTML/Markdown indentation, 2-space JS/TS/CSS/SCSS indentation. Python uses Ruff (`line-length = 88`, `target-version = py310`) for linting and formatting. Frontend uses ESLint + TypeScript, Stylelint for SCSS, and Prettier for JS/TS/CSS/JSON/YAML. Template quality checks include Curlylint and `djhtml`. Run `pre-commit run --all-files` before opening a PR when possible.

## Testing Guidelines
Add or update tests with every behavior change. Prefer focused runs while iterating, for example:
- `python runtests.py wagtail.images`
- `python runtests.py wagtail.tests.test_blocks.TestIntegerBlock`
- `npm run test:unit -- --watch`
Use `--postgres`, `--mysql`, or Elasticsearch flags when touching backend-specific behavior. Keep fixtures deterministic and close to the relevant test app/module.

## Commit & Pull Request Guidelines
Recent history favors short, imperative commit subjects (often optionally referencing PRs), e.g. `Fix snippet-string-primary-key test...` or `Add overwrite_revision_id parameter... (#13631)`. Keep commits scoped to one logical change. PRs should include:
- clear title describing the actual change (not only an issue number),
- linked issue (for example `Fixes #1234`),
- test coverage updates,
- docs/release-note updates when behavior changes.
Avoid committing compiled frontend assets.
