# Project Overview

This is the repository for Wagtail, a content management system (CMS) built on the Django web framework. It is designed to provide a simple and user-friendly interface for content authors, while giving developers and designers a high degree of control over the website's design and structure. The backend is Python-based, leveraging the power of Django, while the frontend uses a modern JavaScript stack with tools like React, Webpack, and Storybook.

## Key Technologies

*   **Backend:** Python, Django
*   **Frontend:** JavaScript, TypeScript, React, Stimulus, Webpack, Babel, Sass, Tailwind CSS
*   **Testing:** Jest (JavaScript), Pytest (Python), Ruff, Selenium
*   **Package Management:** pip (Python), npm (JavaScript)

# Building and Running

## Installation and Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -e .[testing,docs] --config-settings editable-mode=strict
    ```
3.  **Install front-end dependencies:**
    ```bash
    npm install
    ```
4.  **Build the front-end assets:**
    ```bash
    npm run build
    ```
5.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```

## Running Tests

*   **Run all tests:**
    ```bash
    make test
    ```
    or
    ```bash
    python runtests.py
    ```
*   **Run Python tests:**
    ```bash
    python runtests.py
    ```
*   **Run JavaScript tests:**
    ```bash
    npm test
    ```

## Linting and Formatting

*   **Lint all code:**
    ```bash
    make lint
    ```
*   **Format all code:**
    ```bash
    make format
    ```

# Development Conventions

## Coding Style

*   **Python:** The project uses `ruff` for linting and formatting. The configuration can be found in `ruff.toml`.
*   **JavaScript/TypeScript:** The project uses `eslint` for linting and `prettier` for formatting. Configurations are in `.eslintrc.js` and `prettier.config.js`.
*   **CSS/SCSS:** `stylelint` is used for linting, with configuration in `stylelint.config.mjs`.

## Branching and Committing

The project uses `pre-commit` to run checks before each commit. The configuration is in `.pre-commit-config.yaml`. It is recommended to install the pre-commit hooks to ensure contributions adhere to the project's standards:
```bash
pre-commit install
```

## Storybook

The project uses Storybook for developing and testing UI components in isolation. To run Storybook:
```bash
npm run storybook
```
