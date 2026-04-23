# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About Wagtail

Wagtail is an open-source content management system built on Django. It's a Python/Django application with a React/TypeScript frontend for the admin interface.

**Version compatibility:**
- Python: 3.10, 3.11, 3.12, 3.13, 3.14
- Django: 4.2, 5.2, 6.0
- Node: >=22 (see `.nvmrc` for exact version)

## Development Setup

### Initial setup
```sh
# Install Python dependencies in development mode
pip install -e ".[testing,docs]" --config-settings editable-mode=strict -U

# Install Node dependencies
npm ci

# Build frontend assets
npm run build
```

### Development commands
```sh
# Start webpack watch mode for frontend development
npm start

# Build production assets
npm run build
```

## Testing

### Python tests
```sh
# Run all tests
python runtests.py

# Run tests for a specific module
python runtests.py wagtail.admin

# Run a specific test class
python runtests.py wagtail.tests.test_blocks.TestIntegerBlock

# Run tests with PostgreSQL
python runtests.py --postgres

# Run tests with Elasticsearch
python runtests.py --elasticsearch8

# Run with coverage
coverage run --source wagtail runtests.py
coverage report -m
```

### JavaScript tests
```sh
# Run all JS unit tests
npm run test:unit

# Run JS tests in watch mode
npm run test:unit:watch

# Run with coverage
npm run test:unit:coverage

# Run integration tests
npm run test:integration
```

### Makefile shortcuts
```sh
make develop    # Install all dependencies and build assets
make test       # Run Python tests
make lint       # Lint Python, JS, CSS, and docs
make format     # Auto-format code
```

## Linting and Formatting

```sh
# Python - uses ruff, curlylint, djhtml, semgrep
make lint-server
make format-server

# JavaScript/CSS - uses eslint, prettier, stylelint
make lint-client
make format-client

# All
make lint
make format
```

## Architecture

### Core Models (`wagtail/models/`)

The models package is organized into submodules for maintainability. All public APIs are exported through `wagtail/models/__init__.py`.

**Key components:**
- `pages.py` - Core `Page` model and page tree functionality (uses django-treebeard)
- `revisions.py` - `RevisionMixin` for version control of models
- `draft_state.py` - `DraftStateMixin` for draft/live state management
- `i18n.py` - `TranslatableMixin` for multi-language support
- `locking.py` - `LockableMixin` for content locking during editing
- `preview.py` - `PreviewableMixin` for preview functionality
- `media.py` - `Collection` model for organizing media assets
- `workflows.py` - Workflow and approval system
- `sites.py` - Multi-site support

### Admin Interface (`wagtail/admin/`)

The admin UI is a Django app with extensive React/TypeScript components for rich interactions.

**Key areas:**
- `views/` - Django views for the admin interface
- `viewsets/` - Class-based view sets for CRUD operations
- `panels/` - Edit interface panels (FieldPanel, InlinePanel, etc.)
- `static_src/` - TypeScript/React source code
- `widgets/` - Custom form widgets

### Blocks System (`wagtail/blocks/`)

StreamField's flexible content blocks system.

**Core files:**
- `base.py` - Base block classes
- `stream_block.py` - StreamBlock and StreamField implementation
- `field_block.py` - Basic field blocks (CharBlock, IntegerBlock, etc.)
- `struct_block.py` - Structured blocks with named child blocks

### Frontend (`client/`)

Modern JavaScript tooling with webpack, React 16, and TypeScript.

**Structure:**
- `client/src/` - TypeScript/React source code
- `client/scss/` - Sass stylesheets
- `client/tests/` - Frontend unit tests
- `client/storybook/` - Storybook component documentation

### API (`wagtail/api/`)

RESTful API built on Django REST Framework for headless CMS usage.

### Search (`wagtail/search/`)

Pluggable search backend supporting:
- Database search (PostgreSQL full-text search)
- Elasticsearch (versions 7, 8, 9)
- OpenSearch (versions 2, 3)

### Contrib Apps (`wagtail/contrib/`)

Optional modules:
- `forms/` - Form builder
- `frontend_cache/` - Cache invalidation (Cloudflare, Varnish, etc.)
- `redirects/` - Redirect management
- `routable_page/` - URL routing within pages
- `search_promotions/` - Promoted search results
- `settings/` - Site-specific settings
- `simple_translation/` - Translation management
- `sitemaps/` - XML sitemap generation
- `styleguide/` - Admin UI style guide
- `table_block/` - Table blocks
- `typed_table_block/` - Table blocks with typed columns

## Development Guidelines

### Django compatibility
Always check Django version when using version-specific APIs:
```python
from django import VERSION as DJANGO_VERSION

if DJANGO_VERSION >= (5, 0):
    # New Django 5.0+ code
else:
    # Fallback for older versions
```

Use `>=` comparisons (not `try/except`) to make version requirements explicit.

### Testing requirements
- All new functionality must include tests
- Modified functionality requires updated tests
- Tests should cover edge cases and error conditions
- Run the test suite before submitting changes

### Code style
- Python: PEP8 via ruff (4 spaces, configured in `ruff.toml`)
- JavaScript: eslint + prettier (2 spaces)
- HTML: 4 spaces, validated with djhtml and curlylint
- Line endings: LF (configure `git config core.autocrlf true` on Windows)

### Migration creation
```sh
django-admin makemigrations --settings=wagtail.test.settings
```

## Important Conventions

### Model imports
Import public models from `wagtail.models`, not from submodules:
```python
# Correct
from wagtail.models import Page, Site, RevisionMixin

# Incorrect
from wagtail.models.pages import Page
from wagtail.models.sites import Site
```

### Test settings
Tests run with settings from `wagtail/test/settings.py`. This includes test-specific models in `wagtail/test/` and `wagtail/tests/`.

### Hooks system
Wagtail uses a hooks system for extensibility. Hooks are registered in `*_hooks.py` files:
```python
from wagtail import hooks

@hooks.register('register_admin_menu_item')
def register_custom_menu_item():
    # Hook implementation
```

### Asset compilation
Frontend assets must be built before testing admin UI changes. Static assets are generated into `wagtail/admin/static/` and other app static directories.

## Common Patterns

### Working with Pages
Pages use django-treebeard's Materialized Path tree implementation:
- Pages are hierarchical with a single root page
- Each site points to a root page in the tree
- Tree operations: `add_child()`, `move()`, `get_children()`, `get_ancestors()`, etc.

### StreamField usage
StreamField provides flexible content without custom models:
```python
from wagtail.blocks import StreamBlock, CharBlock, RichTextBlock
from wagtail.fields import StreamField

body = StreamField([
    ('heading', CharBlock()),
    ('paragraph', RichTextBlock()),
], use_json_field=True)
```

### Revisions and drafts
Models can inherit `RevisionMixin` for automatic version control:
- Call `save_revision()` to create a revision
- Use `overwrite_revision_id` parameter to update existing revisions
- `DraftStateMixin` adds draft/published workflow

## Notes for AI Assistants

- When making changes to admin UI, rebuild assets with `npm run build` or `npm start`
- Python test discovery finds tests in `wagtail/*/tests/` directories
- The codebase uses Django's settings override for different test scenarios
- Search backends require external services (Elasticsearch/OpenSearch) - tests skip if not available
- Many tests use the `wagtail.test.testapp` Django app with test-specific models
