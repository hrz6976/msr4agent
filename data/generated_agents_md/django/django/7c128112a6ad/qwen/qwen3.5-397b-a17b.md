# AGENTS.md

## Project Overview

This project is Django, a high-level Python web framework that encourages rapid development and clean, pragmatic design. It is a well-established open-source project with a large community. The repository contains the core Django framework, along with its documentation and test suite.

The project uses Python as its primary language and relies on `setuptools` for building the package. For JavaScript components, it uses `npm` to manage dependencies like `eslint`, `grunt`, and `qunit`.

## Building and Running

### Python

To install the Django package, you can run the following command from the root of the repository:

```bash
pip install -e .
```

To run the test suite, follow the instructions in the documentation under `docs/internals/contributing/writing-code/unit-tests.txt`.

### JavaScript

The project uses Grunt.js as a task runner for JavaScript code. The following commands are available:

*   **Install dependencies**:
    ```bash
    npm install
    ```
*   **Run tests**:
    ```bash
    npm test
    ```
    This command will run `eslint` to check for code quality and then execute the QUnit test suite using `grunt test`.

## Development Conventions

### Contributions

*   Contributions are welcome in the form of code patches, documentation improvements, and bug reports.
*   All non-trivial pull requests require a Trac ticket.
*   Contributors are expected to follow the `Django Code of Conduct`.

### Testing

*   The Python test suite is located in the `tests/` directory.
*   The JavaScript tests are located in the `js_tests/` directory and use QUnit for the test runner.
*   The project uses `puppeteer` for running the JavaScript tests in a headless browser.

### Documentation

*   The project documentation is located in the `docs/` directory.
*   To build the documentation, refer to the instructions in `docs/README`.
