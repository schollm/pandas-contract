# Development Guide
## Development flow
After editing the source, run `make test` to run the full test-suite. This will
not only run `pytest`, including `doctest`, but also `ruff` for linting and
`pyright` for type-checking.

Additionally, `make docs` generates the sphinx documentation. The generated
documentation is located at `docs/_out/build/html/index.html`

## How to add a new check
To add a new check to
[](project:#pandas_contract.checks)
see the documentation in the protocol class
[](project:#pandas_contract._private_checks.Check).

## Coding Standards

| **Type**       | Package   | Comment                      |
|----------------|-----------|------------------------------|
| **Automation** | `make`    |                              |
| **Logging**    | `logger`  | Minimize additional packages |
| **Packaging**  | `uv`      |                              |
| **Tests**      | `pytest`  | Including doctests           |
| **Typing**     | `pyright` | Type all methods             |
| **Linting**    | `ruff`    | Also used for formatting     |
