# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About tinygrad

tinygrad is a minimalist deep learning framework inspired by PyTorch (ergonomics), JAX (functional transforms and IR-based AD), and TVM (scheduling and codegen). The entire stack is intentionally tiny and hackable, with the entire compiler and IR visible and modifiable.

## Core Architecture

tinygrad has four main layers:

1. **Frontend (tinygrad/tensor.py)**: PyTorch-like Tensor API with autograd. All operations are syntactic sugar around constructing a graph of UOps.

2. **Scheduler (tinygrad/engine/schedule.py)**: Converts the graph of UOps into a list of `ExecItem`. Each `ExecItem` represents one kernel on the GPU. The scheduler breaks large compute graphs into subgraphs that fit in a kernel.

3. **Lowering (tinygrad/codegen/, tinygrad/uop/)**: Lowers `ExecItem` into executable code. The process is:
   - Lower AST to UOps (linear list of compute operations) - BEAM search happens here
   - Render UOps into code with a `Renderer`
   - Compile code to binary with a `Compiler`

4. **Runtime (tinygrad/runtime/)**: Device-specific implementations for memory allocation, program loading/launching, and device initialization. Each backend (CUDA, AMD, METAL, etc.) has its own `ops_*.py` file.

### Key Concepts

- **UOps**: The intermediate representation. Two types exist: `base` (compute into contiguous buffer) and `view` (a view of a buffer). Base UOps can have base or view inputs; view UOps can only have a single base input.

- **Lazy Execution**: All tensor operations are lazy until `.realize()` or `.numpy()` is called.

- **Device Abstraction**: Accelerators only need to implement ~25 low level ops to be supported.

## Development Commands

### Installation
```bash
python3 -m pip install -e .                    # Install tinygrad
python3 -m pip install -e '.[testing]'         # Install with testing deps
python3 -m pip install -e '.[linting]'         # Install with linting deps
```

### Running Tests
```bash
# Single test file
python3 test/test_ops.py
python3 test/test_tiny.py

# Full test suite
python3 -m pytest test/

# Run with pytest options
python3 -m pytest -n=6 test/test_ops.py        # Parallel execution with 6 workers

# Comprehensive test suite (used in pre-commit)
env OMP_NUM_THREADS=1 SKIP_SLOW_TEST=1 PYTHONPATH="." python3 -m pytest -n=6 \
  test/test_ops.py test/test_schedule.py test/test_assign.py test/test_tensor.py \
  test/test_jit.py test/unit/test_schedule_cache.py test/unit/test_pattern_matcher.py \
  test/unit/test_uop_symbolic.py test/unit/test_helpers.py

# Run specific test method
python3 -m pytest test/test_ops.py::TestOps::test_add
```

### Linting and Type Checking
```bash
# Pre-commit hooks (recommended)
pre-commit install                             # Install hooks
# Manually run pre-commit checks
pre-commit run --all-files

# Individual tools
python3 -m ruff check .                        # Linting
python3 -m mypy                                # Type checking
```

### Debugging and Visualization

Use environment variables to control runtime behavior:

```bash
# DEBUG levels (1-7)
DEBUG=3 python3 script.py                      # Show buffers and optimizations
DEBUG=4 python3 script.py                      # Show generated kernel code
DEBUG=5 python3 script.py                      # Show UOps (AST)
DEBUG=6 python3 script.py                      # Show linearized UOps
DEBUG=7 python3 script.py                      # Show assembly code

# Backend selection
CL=1 python3 script.py                         # Use OpenCL
CUDA=1 python3 script.py                       # Use CUDA
AMD=1 python3 script.py                        # Use AMD
METAL=1 python3 script.py                      # Use Metal
CPU=1 python3 script.py                        # Use CPU

# Other useful flags
VIZ=1 python3 script.py                        # Visualize computation graph
BEAM=5 python3 script.py                       # Set BEAM search width
JIT=0 python3 script.py                        # Disable JIT
```

Example: See kernel fusion with laziness:
```bash
DEBUG=3 python3 -c "from tinygrad import Tensor; \
  N = 1024; a, b = Tensor.empty(N, N), Tensor.empty(N, N); \
  (a.reshape(N, 1, N) * b.T.reshape(1, N, N)).sum(axis=2).realize()"
```

### Running Examples
```bash
# MNIST training
python3 examples/beautiful_mnist.py

# Test all devices work
python3 test/external/external_test_example.py
```

## Code Structure

### Core Modules
- `tinygrad/tensor.py`: Main Tensor class (largest file, ~190k lines)
- `tinygrad/device.py`: Device abstraction and management
- `tinygrad/dtype.py`: Data type definitions and conversions
- `tinygrad/helpers.py`: Utility functions used throughout
- `tinygrad/gradient.py`: Gradient computation

### Key Directories
- `tinygrad/nn/`: Neural network layers and optimizers (Linear, Conv2d, BatchNorm, SGD, Adam, etc.)
- `tinygrad/uop/`: UOp definitions and symbolic operations
- `tinygrad/codegen/`: Code generation and optimization passes
- `tinygrad/engine/`: Scheduling, JIT, memory planning, and realization
- `tinygrad/runtime/`: Device-specific runtime implementations
- `tinygrad/renderer/`: Code renderers for different targets
- `examples/`: Example models and training scripts
- `test/`: Comprehensive test suite
- `extra/`: Extra utilities, datasets, and models (less well-tested)

## Contributing Guidelines

### What Will Get Your PR Closed
- Code golf or reducing line count through obfuscation
- Docs/whitespace changes (unless you're a well-known contributor)
- Unsubstantiated "speedup" claims (must be benchmarked)
- Complex/large PRs without clear individual wins
- Changes to code outside `tinygrad/` without justification

### What We Want
- **Bug fixes with regression tests**: Include a test that would fail without your fix
- **Bounty solutions**: High quality, well-tested implementations (see bounty spreadsheet)
- **Features with test coverage**: Clear API (match PyTorch/NumPy when possible), minimal line count
- **Clear-win refactors**: Must improve readability while passing process replay tests
- **Tests/fuzzers**: Non-brittle tests that find real bugs
- **Dead code removal**: From core `tinygrad/` only

### Process Replay Tests
For refactors or speedups claiming no behavior change, include `[pr]` in your PR title. This triggers [process replay](test/external/process_replay/README.md) which compares generated kernels against master.

### Testing Requirements
- Bug fixes must include regression tests
- New features must have test coverage
- Refactors should pass all existing tests
- Use `@unittest.expectedFailure` for known broken tests

## Coding Conventions

- **Line length**: 150 characters (see `.ruff.toml`)
- **Indentation**: 2 spaces (not tabs)
- **Python version**: Requires Python 3.11+
- **Type hints**: Used throughout, checked with mypy
- **Imports**: Follow the pattern in existing files

### Important Notes
- Load/store ops are intentionally not supported natively - use masking with `arange` instead
- The code outside `tinygrad/` (in `extra/` and some other places) is less well tested
- Default float dtype is FLOAT32 (override with `DEFAULT_FLOAT` env var)
- The framework ships both the compiler AND the frontend (unlike TVM)

## Device Selection

Check your default device:
```bash
python3 -c "from tinygrad import Device; print(Device.DEFAULT)"
```

Programmatically specify device:
```python
from tinygrad import Tensor
x = Tensor([1, 2, 3], device="CPU")
```

## Model Weights

The standard weight format is safetensors:
```python
from tinygrad.nn.state import safe_save, safe_load, get_state_dict, load_state_dict

state_dict = get_state_dict(model)
safe_save(state_dict, "model.safetensors")
state_dict = safe_load("model.safetensors")
load_state_dict(model, state_dict)
```

Many models in `extra/models/` have `load_from_pretrained` methods.

## Additional Resources

- [Documentation](https://docs.tinygrad.org/)
- [Di Zhu's Tutorials](https://mesozoic-egg.github.io/tinygrad-notes/) - In-depth tinygrad internals
- [Discord](https://discord.gg/ZjZadyC7PK) - Ask questions in `#learn-tinygrad`
- [Process Replay README](test/external/process_replay/README.md)
