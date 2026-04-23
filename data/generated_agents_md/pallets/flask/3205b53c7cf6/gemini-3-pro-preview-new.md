# Project Overview

This is the Flask web framework. It's a lightweight WSGI web application framework in Python, designed to be easy to use and scale. It uses Werkzeug for the WSGI layer and Jinja for templating.

# Building and Running

## Initial setup

1.  **Create a virtualenv:**
    ```bash
    python3 -m venv .venv
    . .venv/bin/activate
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements/dev.txt
    pip install -e .
    ```
3.  **Install pre-commit hooks:**
    ```bash
    pre-commit install
    ```

## Running the tests

Run the basic test suite with `pytest`:

```bash
pytest
```

Run the full test suite with `tox`:

```bash
tox
```

## Running the app

A simple "Hello, World" example can be run with:

```bash
flask run
```

# Development Conventions

-   Code is formatted with **Black**.
-   **pre-commit** is used to run checks before committing.
-   Tests are written with **pytest**.
-   Docs are built with **Sphinx**.
-   Changes should be added to `CHANGES.rst`.
