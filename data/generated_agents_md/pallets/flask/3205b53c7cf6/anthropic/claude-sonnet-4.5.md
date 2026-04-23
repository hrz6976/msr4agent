# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is Flask, a lightweight WSGI web application framework built on top of Werkzeug and Jinja2. Flask is designed to be simple and flexible, with minimal enforced patterns while scaling to complex applications.

## Development Setup

Install development dependencies and the package in editable mode:
```bash
pip install -r requirements/dev.txt && pip install -e .
```

Install pre-commit hooks (required before making commits):
```bash
pre-commit install --install-hooks
```

## Common Commands

### Running Tests
```bash
# Run all tests (recommended for local development)
pytest

# Run a specific test file
pytest tests/test_basic.py

# Run a specific test function
pytest tests/test_basic.py::test_name

# Run tests with coverage
coverage run -m pytest
coverage html  # Generate HTML report in htmlcov/

# Run full test suite across all Python versions (used by CI)
tox
```

### Code Quality
```bash
# Run all pre-commit checks (Black, flake8, import sorting, etc.)
pre-commit run --all-files

# Individual tools (run by pre-commit)
black .
flake8
mypy
```

### Type Checking
```bash
tox -e typing
```

### Documentation
```bash
cd docs
make html
# View at docs/_build/html/index.html
```

### Running Flask Apps
```bash
# Development server
flask run

# With debug mode
flask --app myapp run --debug
```

## Architecture Overview

### Core Components

- **Flask (app.py)**: The main `Flask` class orchestrates the entire framework. It inherits from `Scaffold` and manages routing, configuration, request/response handling, error handlers, and the application context lifecycle.

- **Scaffold (scaffold.py)**: Base class providing shared functionality for `Flask` and `Blueprint` classes. Handles routes, template folders, static files, error handlers, before/after request hooks, and URL processors.

- **Blueprint (blueprints.py)**: Modular component for organizing application features. Blueprints register deferred setup functions that execute when the blueprint is registered with an app. They can have their own templates, static files, and URL prefixes.

- **Context Management (ctx.py)**: Flask uses two context types:
  - **Application Context**: Tracks application-level data (`current_app`, `g`). Created when handling a request or explicitly pushed.
  - **Request Context**: Tracks request-level data (`request`, `session`). Created for each incoming request.
  - Both contexts use `contextvars` for thread-safe storage and proper async support.

- **Globals (globals.py)**: Provides `LocalProxy` objects (`current_app`, `g`, `request`, `session`) that access context variables. These proxies allow accessing context-bound objects without explicitly passing them around.

- **Configuration (config.py)**: The `Config` class extends `dict` and supports loading from Python files, environment variables, and instance folders. Uses `ConfigAttribute` descriptors to read from the config dict.

- **Routing (app.py + Werkzeug)**: Uses Werkzeug's `Map` and `Rule` for URL routing. Routes are registered via `@app.route()` or `add_url_rule()`. The `MapAdapter` handles URL matching and building.

- **Sessions (sessions.py)**: Session interface abstraction with `SecureCookieSessionInterface` as the default implementation. Sessions are signed cookies using `itsdangerous`.

- **Templating (templating.py)**: Uses Jinja2 with `DispatchingJinjaLoader` to support loading templates from the app and all registered blueprints. Template context processors inject variables into all templates.

- **Signals (signals.py)**: Built on Blinker for event notifications. Core signals include request lifecycle events (`request_started`, `request_finished`, `request_tearing_down`) and application context events.

- **CLI (cli.py)**: Click-based command-line interface with `flask` command. Auto-discovers Flask apps and provides extensible command groups via `app.cli` and `blueprint.cli`.

### Request Lifecycle

1. WSGI server invokes Flask app (`__call__`)
2. Request context is pushed (creates `RequestContext`, pushes app context if needed)
3. Session is opened
4. `request_started` signal fires
5. URL routing matches request to view function
6. `before_request` functions execute
7. View function executes
8. Response is created (view return value → `Response` object)
9. `after_request` functions execute
10. Response is finalized
11. `request_finished` signal fires
12. Request context is popped
13. `request_tearing_down` signal fires
14. Session is saved

### Key Modules

- **helpers.py**: Utility functions like `url_for()`, `redirect()`, `send_file()`, `flash()`
- **wrappers.py**: `Request` and `Response` classes extending Werkzeug's wrappers
- **json/**: JSON encoding/decoding with `JSONProvider` interface for customization
- **testing.py**: `FlaskClient` (test client) and `FlaskCliRunner` for testing Flask apps
- **debughelpers.py**: Enhanced error messages for common developer mistakes

## Code Style and Practices

### Formatting
- **Black** for code formatting (line length up to 88, enforced at 80 by flake8 with B950)
- **reorder-python-imports** for import sorting with `--py38-plus`
- All formatting enforced by pre-commit hooks

### Type Hints
- Type hints required for all new code
- Uses `typing` module and `from __future__ import annotations`
- Custom typing module (`typing.py`) defines Flask-specific protocols
- Type checking with mypy (configuration in `pyproject.toml`)

### Testing
- `pytest` as the test framework
- Fixtures in `tests/conftest.py` provide `app`, `client`, `app_ctx`, `req_ctx`
- Tests should be isolated and not depend on execution order
- Use `app.test_client()` for request/response testing
- Use `app.test_cli_runner()` for CLI command testing

### Documentation
- Docstrings use reStructuredText format
- Wrap at 72 characters
- Include `.. versionadded::`, `.. versionchanged::`, `.. deprecated::` directives
- Update both docstrings and docs pages when changing functionality

### Commits and Changes
- Add entries to `CHANGES.rst` following the existing format
- Use descriptive commit messages
- Branch from `2.x.x` branch for bug fixes, `main` for features
- Link PRs to issues with `fixes #123` in PR description

## Important Notes

- **Python Support**: Requires Python 3.8+
- **WSGI**: Flask is WSGI-based (via Werkzeug), but supports async views with optional `asgiref` dependency
- **Thread Safety**: Context-local storage uses `contextvars` which is both thread-safe and async-safe
- **Werkzeug Dependency**: Flask is tightly coupled with Werkzeug's routing, HTTP abstractions, and utilities
- **Backward Compatibility**: Flask maintains strict backward compatibility. Deprecation warnings precede removals by at least one minor version.

## Common Patterns

### View Registration
```python
@app.route('/path')
def view():
    pass

# Or programmatically:
app.add_url_rule('/path', endpoint='view', view_func=view)
```

### Error Handlers
```python
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404
```

### Application Factory Pattern
```python
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(config or {})
    # Register blueprints, initialize extensions, etc.
    return app
```

### Blueprint Registration
```python
from flask import Blueprint
bp = Blueprint('name', __name__, url_prefix='/prefix')

@bp.route('/path')
def view():
    pass

app.register_blueprint(bp)
```

## Debugging

Flask uses Werkzeug's interactive debugger in debug mode. Never enable debug mode in production.

Enable debug mode:
```bash
flask --app myapp run --debug
```

Or via environment:
```bash
export FLASK_DEBUG=1
flask run
```
