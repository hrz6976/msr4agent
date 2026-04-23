
# AGENTS.md

## Project Overview

This is the Wagtail project, a content management system (CMS) built on the Django framework. It provides a rich authoring experience, powerful content modeling, and a flexible architecture for building a wide range of websites and applications. The project uses Python for the backend and a combination of JavaScript, TypeScript, and React for the frontend.

## Building and Running

### Backend (Python/Django)

The backend is a standard Django project. Key dependencies are managed with `pip` and are listed in `pyproject.toml`.

**Installation:**

To get started, install the project in editable mode with the testing dependencies:

```bash
pip install -e ".[testing]"
```

**Running the development server:**

To run the development server, you'll need to set up a Django project and integrate Wagtail. For local development on the Wagtail project itself, you'll typically run the test suite or use the provided `wagtail` command-line script.

```bash
wagtail start my_wagtail_site
```

**Running tests:**

The project uses `tox` to run tests across a wide range of environments (different Python, Django, and database combinations).

To run the full test suite:

```bash
tox
```

To run tests for a specific environment (e.g., Python 3.12 with Django 4.2 and SQLite):

```bash
tox -e py312-dj42-sqlite
```

You can also run tests directly using the `runtests.py` script:

```bash
python runtests.py
```

### Frontend (JavaScript/TypeScript)

The frontend assets are managed with `npm` and built with `webpack`. The source files are located in the `client/` directory.

**Installation:**

To install the frontend dependencies:

```bash
npm install
```

**Building for development:**

To build the frontend assets and watch for changes:

```bash
npm start
```

**Building for production:**

To create a production-ready build of the frontend assets:

```bash
npm run build
```

**Running tests:**

The frontend has unit and integration tests managed with Jest.

To run the unit tests:

```bash
npm run test:unit
```

To run the integration tests:

```bash
npm run test:integration
```

## Development Conventions

### Code Style

-   **Python:** The project uses `ruff` for linting and formatting. The configuration can be found in `ruff.toml`.
-   **JavaScript/TypeScript:** The project uses `eslint` for linting and `prettier` for formatting. The configurations are in `.eslintrc.js` and `prettier.config.js`, respectively.

### Linting and Formatting

You can run the linters and formatters using the following `npm` scripts:

-   **Lint all files:** `npm run lint`
-   **Fix all files:** `npm run fix`
--  **Format all files:** `npm run format`

### Storybook

The project uses Storybook for developing and documenting UI components. To run the Storybook server:

```bash
npm run storybook
```

### Documentation

The project documentation is built with Sphinx. You can find the source files in the `docs/` directory. The project also generates API documentation from the TypeScript source code using `typedoc`.

To build the TypeScript documentation:

```bash
npm run build-docs
```
