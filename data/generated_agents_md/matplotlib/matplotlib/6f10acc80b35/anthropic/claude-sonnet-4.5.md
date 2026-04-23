# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Matplotlib is a comprehensive library for creating static, animated, and interactive visualizations in Python. This is a large, mature codebase with over 220 C/C++ extension files and extensive Python code spanning visualization, rendering backends, and mathematical typesetting.

## Architecture

### Core Structure

- **lib/matplotlib/**: Main Python library code
  - **axes/**: The Axes class - highest level of OO access, where most plotting happens
  - **figure.py**: The Figure class that contains one or more Axes
  - **artist.py**: Base Artist class inherited by all drawable elements
  - **pyplot.py**: Procedural (MATLAB-like) interface wrapping the OO API
  - **backends/**: Multiple rendering backends (Qt, Gtk, Tk, Cairo, Agg, PDF, SVG, etc.)
  - **tests/**: Test suite organized by module (test_MODULE.py tests MODULE.py)
  - **testing/**: Testing infrastructure and utilities

- **lib/mpl_toolkits/**: Extension toolkits
  - **mplot3d/**: 3D plotting capabilities
  - **axes_grid1/**: Advanced axes grid layouts
  - **axisartist/**: Custom axis drawing

- **src/**: C/C++ extension modules for performance-critical rendering (Agg backend, path operations, image resampling)

- **doc/**: Sphinx documentation, examples gallery, and tutorials

### Key Concepts

- **Figure**: The top-level container holding one or more Axes
- **Axes** (singular form, not "axis"): A subplot within a Figure containing plot elements. Most plotting methods are Axes methods
- **Artist**: Any object that draws something (lines, text, patches, images, etc.)
- **Backend**: Rendering engine that draws to different targets (GUI windows, image files, PDFs, etc.)

Matplotlib has two interfaces:
1. **Explicit object-oriented API** (preferred for scripts): Create Figure/Axes explicitly, call methods on them
2. **Implicit pyplot API** (for interactive use): `plt.plot()` etc. manage Figure/Axes implicitly

### Important: C extensions require rebuilding

After modifying C/C++ files in `src/` or when switching git branches, you must rebuild:
```bash
python -m pip install -ve .
```

Pure Python changes (*.py files) take effect immediately in editable mode.

## Development Setup

### Initial Setup

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/matplotlib.git
   cd matplotlib
   ```

3. Create a development environment (choose one):
   ```bash
   # Using conda (recommended):
   conda env create -f environment.yml
   conda activate mpl-dev
   
   # Or using venv:
   python -m venv mpl-dev
   source mpl-dev/bin/activate  # Linux/macOS
   ```

4. Install in editable mode:
   ```bash
   python -m pip install -ve .
   ```

5. (Optional) Install pre-commit hooks:
   ```bash
   python -m pip install pre-commit
   pre-commit install
   ```

## Common Development Commands

### Testing

Run all tests:
```bash
python -m pytest
```

Run tests in parallel (faster):
```bash
python -m pytest -n auto
```

Run a specific test file:
```bash
pytest lib/matplotlib/tests/test_axes.py
```

Run a specific test function:
```bash
pytest lib/matplotlib/tests/test_simplification.py::test_clipping
```

Run with verbose output:
```bash
pytest -v
```

Run without capturing stdout (useful for debugging):
```bash
pytest -s
```

### Code Quality

Check code style with flake8:
```bash
flake8 /path/to/module.py
```

Run pre-commit hooks manually on all files:
```bash
pre-commit run --all-files
```

Run a specific pre-commit hook:
```bash
pre-commit run <hook-id> --all-files
```

### Building Documentation

Build HTML docs (with example plots):
```bash
cd doc
make html
```

Build docs without generating plots (much faster):
```bash
cd doc
make html-noplot
```

View built docs in browser:
```bash
cd doc
make show
```

Clean documentation build:
```bash
cd doc
make clean
```

## Code Style Guidelines

### Python Style

- Follow PEP 8, but **max line length is 88 characters** (not 80)
- Do NOT use the `black` auto-formatter (matplotlib intentionally avoids it)
- Use standard scipy import conventions:
  ```python
  import numpy as np
  import numpy.ma as ma
  import matplotlib as mpl
  import matplotlib.pyplot as plt
  import matplotlib.cbook as cbook
  import matplotlib.patches as mpatches
  ```
- Access rcParams as `mpl.rcParams`, not `from matplotlib import rcParams` (some modules load before rcParams is initialized)

### Docstrings

- All public methods need informative docstrings
- Follow NumPy docstring standard
- Include usage examples where appropriate
- For new features, consider adding examples to the gallery

### Git Workflow

- Work on feature branches, target PRs to `main`
- Commit messages should follow the repository's style (check `git log` for examples)
- When updating PRs, consider amending commits to keep history clean:
  ```bash
  git commit --amend --no-edit
  git push origin branch-name --force-with-lease
  ```

## Testing Guidelines

### Test Organization

- Tests live in `lib/matplotlib/tests/`
- Test files follow the pattern `test_MODULE.py` for testing `MODULE.py`
- Pytest finds functions starting with `test_` or classes starting with `Test`

### Random Data in Tests

Always seed random number generators with John Hunter's birthday:
```python
import numpy as np
rng = np.random.default_rng(19680801)
# Then use rng for all random number generation
```

### Image Comparison Tests

Two approaches for testing visual output:

1. **Baseline images** - Store expected output as PNG files:
   ```python
   from matplotlib.testing.decorators import image_comparison
   
   @image_comparison(baseline_images=['my_plot'], remove_text=True,
                     extensions=['png'], style='mpl20')
   def test_my_plot():
       fig, ax = plt.subplots()
       ax.plot([1, 2, 3])
   ```
   - First run will fail; copy result images to `baseline_images/test_MODULE/`
   - Use `style='mpl20'` for new tests (smaller, modern style)
   - Use `remove_text=True` if text content isn't part of the test

2. **Figure comparison** (preferred, no baseline files):
   ```python
   from matplotlib.testing.decorators import check_figures_equal
   
   @check_figures_equal(extensions=['png'])
   def test_plot_methods(fig_test, fig_ref):
       # Draw the same thing two different ways
       fig_test.subplots().plot([1, 2, 3])
       fig_ref.subplots().plot([1, 2, 3])
   ```

### Test Fixtures

The `mpl_test_settings` fixture automatically cleans up side effects (created figures, modified rcParams). Just write your test; cleanup is automatic.

## Pull Request Guidelines

### Before Submitting

- Ensure code follows style guidelines (flake8 passes)
- Add tests for new features and bug fixes
- Update documentation if adding/changing public APIs
- For major features: add an entry in `doc/users/next_whats_new/`
- For API changes: document in `doc/api/next_api_changes/behavior/`

### PR Title and Description

- Use descriptive titles (e.g., "Add ability to plot timedeltas")
- Reference issue numbers: "Closes #1234" or "Fixes #5678" to auto-close issues
- For WIP/incomplete PRs, mark as draft on GitHub

### Review Process

- Be patient; maintainers have limited bandwidth
- If no response in a few days, ping by commenting on the PR
- Reviewers will guide you through the process, especially for first-time contributors

## CI/Testing

- GitHub Actions runs tests automatically on PRs
- Tests run on multiple Python versions and platforms
- Workflow files are in `.github/workflows/`
- To manually trigger tests on your fork, use the GitHub web interface

## Important Notes

- **Terminology matters**: Use "Axes" (singular) for a subplot, not "axes" or "axis"
- **Backend selection**: Set backend before creating figures with `matplotlib.use()` or `MPLBACKEND` environment variable
- **Font and rendering**: Some features require external tools (LaTeX, GhostScript, ffmpeg for animations)
- **Platform differences**: Some tests are platform-specific; CI runs on Linux, macOS, and Windows

## Resources

- Contributing guide: https://matplotlib.org/devdocs/devel/contributing.html
- Development workflow: https://matplotlib.org/devdocs/devel/development_workflow.html
- API documentation: https://matplotlib.org/stable/api/index.html
- Discourse forum: https://discourse.matplotlib.org/
- Gitter chat: https://gitter.im/matplotlib/matplotlib
