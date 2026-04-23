# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the Django web framework (https://www.djangoproject.com/), a high-level Python framework for rapid web development. The repository contains ~880 Python files in the `django/` package and ~1,900 test files in `tests/`.

## Development Workflow

### Testing

**Run all tests:**
```bash
cd tests
python runtests.py
```

**Run specific test modules:**
```bash
cd tests
python runtests.py i18n                                    # Run entire i18n module
python runtests.py i18n.tests.TranslationTests             # Run specific test class
python runtests.py i18n.tests.TranslationTests.test_lazy  # Run specific test method
```

**Common test options:**
- `--parallel N` - Run tests in N parallel processes
- `--keepdb` - Preserve test database between runs (faster subsequent runs)
- `--failfast` - Stop on first failure
- `-v 2` or `-v 3` - Increase verbosity
- `--settings=test_sqlite` - Use specific settings (default is test_sqlite)
- `--bisect <test_name>` - Bisect test suite to find interaction failures
- `--shuffle` - Run tests in random order

**Database-specific tests:**
```bash
cd tests
python runtests.py --settings=test_postgres  # PostgreSQL
python runtests.py --settings=test_mysql     # MySQL
python runtests.py --settings=test_oracle    # Oracle
```

First install database-specific requirements from `tests/requirements/`.

### Code Quality

**Run linters before committing:**
```bash
# Black (code formatting) - MUST match version 24.10.0
black --check --diff .

# isort (import sorting)
isort --check-only --diff django tests scripts

# flake8 (style checking)
flake8 .

# JavaScript linting
npm install
npm test
```

**Auto-format code:**
```bash
black .
isort django tests scripts
```

### Using Tox

```bash
tox -e py3      # Run tests with Python 3
tox -e black    # Check black formatting
tox -e flake8   # Run flake8
tox -e isort    # Check isort
tox -e docs     # Build and spell-check docs
```

### Pre-commit Hooks

This repository uses pre-commit. Install hooks with:
```bash
pre-commit install
```

Hooks run: black, blacken-docs, isort, flake8, eslint.

## Architecture

### Core Components

**Request/Response Flow:**
1. WSGI/ASGI handlers (`django/core/handlers/`) receive requests
2. URL routing (`django/urls/`) matches URLs to views via URLconf patterns
3. Middleware (`django/middleware/`) processes requests/responses
4. Views execute and return responses
5. Template system (`django/template/`) renders HTML (if applicable)

**Database Layer (ORM):**
- Core ORM: `django/db/models/`
- Query construction: `django/db/models/sql/`
- Backends: `django/db/backends/` - base classes with sqlite3, postgresql, mysql, oracle implementations
- Migrations: `django/db/migrations/`

Each backend inherits from `django/db/backends/base/` and implements database-specific operations, schema manipulation, and introspection.

**Management Commands:**
- Framework: `django/core/management/`
- Built-in commands: `django/core/management/commands/`
- Apps can add commands via `<app>/management/commands/<command>.py`
- Entry point: `django-admin` / `manage.py`

**Template System:**
- Engine: `django/template/engine.py` (Django Template Language)
- Loaders: `django/template/loaders/` - filesystem, app_directories, cached
- Built-in tags/filters: `django/template/defaulttags.py`, `defaultfilters.py`
- Backends: Supports both Django templates and Jinja2

**Forms:**
- Base: `django/forms/forms.py`, `django/forms/models.py` (ModelForms)
- Fields: `django/forms/fields.py`
- Widgets: `django/forms/widgets.py`

**Contrib Apps:**
Located in `django/contrib/`, these are optional bundled applications:
- `admin` - Automatic admin interface
- `auth` - Authentication framework
- `contenttypes` - Generic relations system
- `sessions` - Session framework
- `messages` - Messaging framework
- `staticfiles` - Static file management
- `gis` - Geographic add-ons (GeoDjango)
- `postgres` - PostgreSQL-specific features
- Plus: admindocs, flatpages, humanize, redirects, sitemaps, sites, syndication

### Configuration

- Global settings: `django/conf/global_settings.py` (defaults)
- Settings object: `django/conf/__init__.py` - lazy settings proxy
- User settings override globals via `DJANGO_SETTINGS_MODULE` environment variable

### App System

- Registry: `django/apps/` - manages installed applications
- Apps define models, views, URLs, management commands, templates, static files
- AppConfig classes provide app metadata and initialization hooks

## Contribution Guidelines

**IMPORTANT:** Non-trivial pull requests require a Trac ticket.

1. File a ticket at https://code.djangoproject.com/newticket
2. Reference the ticket number in commits and PRs
3. Follow the contributing guide: https://docs.djangoproject.com/en/dev/internals/contributing/

Django uses Trac for issue tracking, not GitHub Issues. Pull requests without tickets will be closed.

**Testing Requirements:**
- Add tests for all new features and bug fixes
- Tests must pass for all supported databases (SQLite, PostgreSQL, MySQL, Oracle)
- Consider edge cases and backward compatibility

**Code Style:**
- Black formatting (version 24.10.0 exactly) - enforced in CI
- isort for imports (black-compatible profile)
- flake8 compliance (max line length 88)
- Pre-commit hooks will check automatically

## Python Version Support

Current support: Python 3.10, 3.11, 3.12 (see `setup.cfg`).

Test changes across all supported versions when possible.

## Documentation

Located in `docs/` directory, built with Sphinx:
```bash
cd docs
make html        # Build HTML documentation
make spelling    # Check spelling
```

Online docs: https://docs.djangoproject.com/

## Common Patterns

**Adding a new database backend feature:**
1. Add to base class in `django/db/backends/base/`
2. Implement in each backend: sqlite3, postgresql, mysql, oracle
3. Add feature detection via `connection.features`
4. Add tests in `tests/backends/`

**Adding a management command:**
1. Create `<app>/management/commands/<name>.py`
2. Subclass `BaseCommand` from `django.core.management.base`
3. Implement `handle()` method
4. Add tests in `tests/admin_scripts/` or appropriate test app

**Modifying ORM behavior:**
- Query construction: `django/db/models/sql/`
- Manager/QuerySet: `django/db/models/manager.py`, `query.py`
- Field types: `django/db/models/fields/`
- Lookups/Transforms: `django/db/models/lookups.py`

## Project Structure Notes

- `django/` - Framework source code
- `tests/` - Comprehensive test suite (organized by feature area)
- `docs/` - Sphinx documentation
- `scripts/` - Development/release scripts
- `extras/` - Additional resources
- `js_tests/` - JavaScript tests for admin interface

Tests are organized by feature (e.g., `tests/migrations/`, `tests/admin_views/`, `tests/forms_tests/`) with each directory typically containing `tests.py` or multiple test modules.
