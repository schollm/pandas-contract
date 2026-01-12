# Copilot Instructions for pandas-contract

## Project Overview

**pandas-contract** is a Python library providing decorators to validate pandas
DataFrame and Series inputs/outputs using Pandera schemas. It enables runtime
contract enforcement for functions working with tabular data, with support for
dynamic schema generation based on function arguments.

## Core Concepts

### Purpose
- **Runtime validation**: Enforce DataFrame structure (columns, types, constraints) on function inputs and outputs
- **Decorator-based API**: Clean, readable contract specifications using `@pc.argument()` and `@pc.result()`
- **Dynamic schemas**: Support runtime column selection via `pc.from_arg()` for flexible validation
- **Development vs Production**: Decorators can be disabled in production (silent mode) or enabled for testing/development

### Key Features
- **Cross-argument checks**: Output can reference input (e.g., `extends="df"`, `same_index_as="df"`)
- **Complex argument unwrapping**: Extract DataFrames from nested structures using `key` parameter
- **Multiple validation modes**: Raises exceptions, silent mode, or custom error handling
- **Pandera integration**: Full access to Pandera's rich schema DSL

## Architecture

### Module Structure
```
src/pandas_contract/
  __init__.py          # Public API exports
  _decorator.py        # Core @argument() and @result() decorators
  _lib.py              # Utility functions (from_arg, etc.)
  checks.py            # Cross-check helpers (extends, same_index_as, is_not)
  mode.py              # Validation mode management (Modes enum, set_mode, etc.)
  _private_checks.py   # Internal validation logic
  py.typed             # PEP 561 type marker
```

### Public API (in `__init__.py`)
- **`argument(schema, *checks, name=None, key=None)`**: Validate function argument
- **`result(schema, *checks, key=None, **named_checks)`**: Validate function return value
- **`from_arg(arg_name)`**: Create dynamic column reference to function argument
- **`checks`**: Module with cross-check utilities (extends, same_index_as, is_not)
- **`Modes`**: Enum with SILENT, RAISES modes
- **`set_mode(mode)`**: Global mode setter
- **`get_mode()`**: Get current validation mode
- **`as_mode(mode)`**: Context manager for temporary mode changes
- **`silent`**: Context manager shortcut for silent mode
- **`raises`**: Context manager shortcut for raises mode

## Critical Patterns

### Basic Validation
```python
import pandas as pd
import pandas_contract as pc
import pandera.pandas as pa

@pc.argument("df", pa.DataFrameSchema({"x": pa.Column(int)}))
@pc.result(pa.DataFrameSchema({"y": pa.Column(str)}))
def transform(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(y=df["x"].astype(str))
```

### Dynamic Column References
```python
# Single column from argument
@pc.argument("df", pa.DataFrameSchema({pc.from_arg("col"): pa.Column()}))
@pc.result(pa.DataFrameSchema({pc.from_arg("col"): pa.Column(str)}))
def col_to_string(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df.assign(**{col: df[col].astype(str)})

# Multiple columns from list argument
@pc.argument("df", pa.DataFrameSchema({pc.from_arg("cols"): pa.Column()}))
@pc.result(pa.DataFrameSchema({pc.from_arg("cols"): pa.Column(str)}))
def cols_to_string(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.assign(**{c: df[c].astype(str) for c in cols})
```

### Cross-Argument Checks
```python
# Result extends input (adds columns)
@pc.result(extends="df")
def add_column(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(new_col=1)

# Result has same index as another argument
@pc.result(same_index_as="df2")
def merge_data(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    return df1.join(df2)

# Result is not the same object (no in-place mutation)
@pc.result(is_not="df")
def safe_transform(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()
```

### Complex Argument Unwrapping
```python
# Extract DataFrame from dict
@pc.result(pa.DataFrameSchema({"x": pa.Column(int)}), key="data")
def returns_wrapped() -> dict:
    return {"data": pd.DataFrame({"x": [1, 2, 3]})}

# Extract DataFrame using callable
@pc.argument("config", 
    pa.DataFrameSchema({"id": pa.Column(int)}),
    key=lambda cfg: cfg.dataframe)
def process_config(config: Config) -> None:
    ...
```

### Validation Modes
```python
# Default: silent mode (no validation in production)
import pandas_contract as pc

# Enable validation for testing
pc.set_mode(pc.Modes.RAISES)

# Temporary mode change
with pc.raises:
    result = my_validated_function(df)  # Raises on validation error

with pc.silent:
    result = my_validated_function(df)  # No validation
```

## Code Quality Standards

### Type Checking
- **Type checker**: Use pyrefly
- **Type annotations**: Full type hints required on public API
- **Type stubs**: Includes `py.typed` marker for PEP 561 compliance
- **pandas-stubs**: Dev dependency for pandas type checking

### Formatting & Linting
- **Formatter**: `ruff format` (line-length = 88)
- **Linter**: `ruff check --fix`
- **Ruff config**: Extensive rule set in pyproject.toml
  - Selects ALL rules, then ignores specific ones (D213, D203, COM812, etc.)
  - Test files: Allows asserts (S101), unused fixtures (ARG), boolean positional args (FBT)
- **Run**: `uv run ruff format .` and `uv run ruff check --fix .`

### Testing
- **Framework**: pytest with coverage
- **Location**: `src/tests/` (sibling to pandas_contract/)
- **Config**: pytest.ini_options in pyproject.toml
  - Coverage reports: XML, HTML, terminal
  - JUnit XML output for CI
  - Doctest enabled (`--doctest-modules`)
- **Run**: `uv run pytest src/tests/`
- **Dev dependency**: pytest-cov for coverage tracking

## Documentation Standards

### Sphinx Documentation
- **Location**: `docs/` directory
- **Build system**: Makefile with standard Sphinx targets
- **Theme**: sphinx-rtd-theme (Read the Docs theme)
- **Extensions**:
  - sphinx-autodoc2: Auto-generate API docs from docstrings
  - myst-parser: Markdown support in docs
- **Build**: `cd docs && make html` (output to `docs/_out/html/`)
- **Hosted**: [pandas-contract.readthedocs.io](https://pandas-contract.readthedocs.io/)

### Docstring Style
- **Format**: Google-style docstrings
- **Requirements**: 
  - Full descriptions for all public functions
  - Type hints in signatures (not duplicated in docstrings)
  - Examples in docstrings are tested via `--doctest-modules`
- **Ruff rules**: Enforces docstring conventions (D-series rules)

### Key Documentation Files
- `docs/index.rst`: Main entry point with quick start examples
- `docs/public-api.rst`: Complete API reference
- `docs/details.rst`: In-depth usage patterns
- `docs/module-mode.rst`: Setup and mode configuration
- `docs/migration.md`: Version migration guides
- `docs/development.md`: Contributor guidelines

## Build System

### UV Package Manager
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest src/tests/

# Format code
uv run ruff format .

# Lint code
uv run ruff check --fix .

# Build docs
cd docs && uv run sphinx-build -b html . _out/html
```

### Dependencies
- **Runtime**: pandas>=1.5.0, pandera[pandas]>=0.22.0
- **Dev**: pytest, ruff, pandas-stubs, pyrefly, pytest-cov
- **Docs**: sphinx, sphinx-rtd-theme, sphinx-autodoc2, myst-parser
- **Python versions**: 3.9 - 3.13 (including PyPy)

### Makefile
- **Purpose**: Primarily for Sphinx documentation builds
- **Targets**: `make html`, `make clean`, `make linkcheck`
- **Location**: `docs/Makefile`

## Testing Patterns

### Test Organization
```python
# src/tests/test_decorator.py
import pandas as pd
import pandas_contract as pc
import pandera.pandas as pa
import pytest

@pytest.mark.parametrize("input_val,expected", [
    (1, "1"),
    (2, "2"),
])
def test_conversion(input_val, expected):
    @pc.argument("df", pa.DataFrameSchema({"x": pa.Column(int)}))
    @pc.result(pa.DataFrameSchema({"x": pa.Column(str)}))
    def convert(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(x=df["x"].astype(str))
    
    with pc.raises:
        result = convert(pd.DataFrame({"x": [input_val]}))
        assert result["x"].iloc[0] == expected
```

### Coverage Requirements
- **Branch coverage**: Enabled via `--cov-branch`
- **Coverage target**: High coverage expected (src/pandas_contract/)
- **Reports**: HTML output in `.out/coverage-html/`, XML in `.out/coverage.xml`

## Common Workflows

### Development Setup
```bash
# Clone and setup
cd /workspaces/tg-priv/pandas-contract
uv sync

# Run tests with coverage
uv run pytest src/tests/ --cov=src/pandas_contract

# Format and lint
uv run ruff format .
uv run ruff check --fix .
```

### Building Documentation
```bash
cd docs
uv run sphinx-build -b html . _out/html
# Or using Makefile
make html
```

### Release Process
1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Run full test suite: `uv run pytest src/tests/`
4. Build docs and verify: `cd docs && make html`
5. Tag release and push to GitHub
6. ReadTheDocs automatically builds new version

## Design Philosophy

### Decorator Pattern
- **Non-invasive**: Decorators should not modify function behavior in production (silent mode)
- **Composable**: Multiple decorators can be stacked
- **Type-safe**: Decorators preserve function signatures for type checkers

### Schema Reusability
- **Shared schemas**: Define schemas as constants for reuse across multiple functions
- **Schema composition**: Use Pandera's schema inheritance and merging
- **Dynamic generation**: `from_arg()` enables schema parameterization

### Error Handling
- **Clear messages**: Validation errors should clearly indicate which check failed
- **Pandera integration**: Leverage Pandera's detailed error reporting
- **Mode-dependent**: Behavior changes based on global/contextual mode setting

## External Dependencies

- **Pandera**: Core validation engine (pandera[pandas]>=0.22.0)
  - Imported as `pandera.pandas` for clarity
  - Fallback to `pandera` for backward compatibility
- **Pandas**: DataFrame library (>=1.5.0)
- **pytest**: Testing framework
- **ruff**: Fast linter/formatter replacing Black + flake8 + isort

## File Locations

- Source: `src/pandas_contract/`
- Tests: `src/tests/` (sibling to source)
- Docs: `docs/`
- Config: `pyproject.toml` (all configuration centralized)
- Coverage output: `.out/`
- Type marker: `src/pandas_contract/py.typed`

## Common Issues & Solutions

### Import Patterns
```python
# Correct (recommended in docs)
import pandas as pd
import pandas_contract as pc
import pandera.pandas as pa

# Avoid
from pandas_contract import *  # Unclear what's imported
```

### Mode Confusion
- **Problem**: Validation not running in tests
- **Solution**: Explicitly set mode with `pc.set_mode(pc.Modes.RAISES)` or use `with pc.raises:` context

### Dynamic Schema Errors
- **Problem**: `from_arg()` references missing argument
- **Solution**: Ensure argument name matches exactly (case-sensitive)

### Complex Type Annotations
- **Problem**: Type checkers complain about decorator return types
- **Solution**: Decorators preserve original function signature (use `typing.cast` if needed)
