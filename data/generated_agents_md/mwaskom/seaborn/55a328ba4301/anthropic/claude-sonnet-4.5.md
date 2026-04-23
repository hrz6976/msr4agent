# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Seaborn is a Python data visualization library built on top of matplotlib. It provides a high-level interface for creating attractive statistical graphics and is widely used in data science and research.

**Version:** 0.12.2  
**Python Support:** 3.7+  
**Core Dependencies:** numpy, pandas, matplotlib  
**Optional Dependencies:** scipy, statsmodels (for advanced statistical functionality)

## Development Setup

Install development dependencies:
```bash
pip install -e .[dev]
```

Install optional statistical dependencies:
```bash
pip install -e .[stats]
```

Install documentation dependencies:
```bash
pip install -e .[stats,docs]
```

## Common Commands

### Testing
```bash
# Run all tests with coverage (uses pytest-xdist for parallel execution)
make test

# Run specific test file
pytest tests/test_categorical.py

# Run specific test within a file
pytest tests/test_categorical.py::TestCategoricalPlotter::test_wide_df

# Run tests in parallel manually
pytest -n auto tests/

# Run tests with verbose output
pytest -v tests/test_categorical.py
```

### Linting
```bash
# Check code style with flake8
make lint

# Lint specific files
flake8 seaborn/categorical.py
```

### Type Checking
```bash
# Type check the new API modules (_core, _marks, _stats)
make typecheck

# Or run mypy directly
mypy --follow-imports=skip seaborn/_core seaborn/_marks seaborn/_stats
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks (runs linting and type checking on commit)
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files
```

### Documentation
```bash
# Build documentation (requires docs dependencies and NB_KERNEL env var)
cd doc
export NB_KERNEL="python3"
make notebooks html

# Clean documentation build
make clean

# View built docs
open _build/html/index.html
```

## Architecture

### Two-Track API Design

Seaborn has **two distinct APIs** that serve different purposes:

#### 1. Classic Function-Based API (seaborn/*.py)
The traditional API with function-based plotting:
- **relational.py**: `scatterplot()`, `lineplot()`, `relplot()`
- **categorical.py**: `boxplot()`, `violinplot()`, `barplot()`, `stripplot()`, `swarmplot()`, etc.
- **distributions.py**: `histplot()`, `kdeplot()`, `ecdfplot()`, `displot()`
- **matrix.py**: `heatmap()`, `clustermap()`
- **regression.py**: `regplot()`, `lmplot()`, `residplot()`

These functions use the older semantic mapping logic in `_oldcore.py` and `_statistics.py`.

#### 2. Objects Interface (seaborn.objects / seaborn/_core)
A newer, declarative, composable API introduced in v0.12:
- **_core/plot.py**: The `Plot` class - the main entry point
- **_marks/**: Visual mark classes (`Dot`, `Line`, `Bar`, `Area`, `Path`, etc.)
- **_stats/**: Statistical transformation classes (`Agg`, `Est`, `Count`, `Hist`, `KDE`, `PolyFit`, etc.)
- **_core/moves.py**: Position adjustment classes (`Dodge`, `Jitter`, `Stack`, `Shift`, etc.)
- **_core/scales.py**: Scale classes (`Continuous`, `Nominal`, `Temporal`, `Boolean`)

**Example usage:**
```python
from seaborn import objects as so

(
    so.Plot(data, x="var1", y="var2", color="category")
    .add(so.Dot())
    .add(so.Line(), so.PolyFit())
    .scale(color="viridis")
)
```

### Key Architectural Components

**Semantic Mapping (`_oldcore.py`):**
- `SemanticMapping` base class handles mapping data values to visual properties (colors, sizes, styles)
- Used by the classic function-based API

**Statistical Transformations:**
- `_statistics.py`: Older statistical classes for classic API (KDE, Histogram, etc.)
- `_stats/`: New modular stat classes for objects API

**Styling & Theming:**
- **rcmod.py**: Controls matplotlib rcParams with context managers (`axes_style()`, `plotting_context()`)
- **palettes.py**: Color palette generation and management
- **colors/**: Extended color definitions (xkcd colors, crayons)

**Grid-Based Layouts:**
- **axisgrid.py**: `FacetGrid`, `PairGrid`, `JointGrid` classes for complex multi-plot layouts

**Testing Infrastructure:**
- **tests/conftest.py**: Extensive pytest fixtures for different data shapes (wide_df, long_df, flat_series, etc.)
- Each module has corresponding test files (test_categorical.py, test_distributions.py, etc.)

### Module Organization

```
seaborn/
├── __init__.py           # Main namespace, imports all public functions
├── objects.py            # Objects API public namespace
├── _core/                # Objects API core (Plot, data handling, scales)
├── _marks/               # Visual marks for objects API
├── _stats/               # Statistical transforms for objects API
├── _oldcore.py           # Semantic mapping logic for classic API
├── categorical.py        # Categorical plots
├── relational.py         # Scatter and line plots
├── distributions.py      # Distribution plots
├── matrix.py             # Heatmaps and clustermaps
├── regression.py         # Regression plots
├── axisgrid.py           # Multi-plot grids
├── palettes.py           # Color palettes
├── rcmod.py              # Style management
└── utils.py              # Utility functions
```

## Code Style and Type Checking

- **Flake8** enforces style (max line length: 88, configured in setup.cfg)
- **Excluded from linting:** `seaborn/cm.py`, `seaborn/external/`
- **Type checking** with mypy is **only enforced** on new objects API modules: `_core/`, `_marks/`, `_stats/`
- Type checking ignores missing imports for pandas and matplotlib (see setup.cfg)

## Coverage Configuration

Coverage omits:
- `seaborn/widgets.py`
- `seaborn/external/*`
- `seaborn/colors/*`
- `seaborn/cm.py`
- `seaborn/conftest.py`

## Working with the Objects API

When modifying the objects interface:

1. **Plot class** (`_core/plot.py`) is the main orchestrator - it handles data, layers, scales, and rendering
2. **Marks** (`_marks/`) define how data is visually represented
3. **Stats** (`_stats/`) transform data before visualization (binning, aggregation, etc.)
4. **Moves** adjust position to reduce overplotting
5. All these modules **must pass type checking** with mypy

## Important Testing Notes

- Tests automatically close all matplotlib figures after each test (see `close_figs` fixture)
- Random seed is set globally for reproducibility (see `random_seed` fixture)
- Extensive fixtures provide data in multiple formats (DataFrame, array, list, Series)
- Tests use pytest with parallel execution (`-n auto`) for speed

## Build System

- Uses **flit** as the build backend (see pyproject.toml)
- Version is dynamic, read from `seaborn/__init__.py`
- No setup.py needed - everything is in pyproject.toml
