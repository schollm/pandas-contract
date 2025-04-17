# Installation and Setup
## Installation
```bash
(.venv) pip install pandas-contract
```

## Setup package
By default, the `pandas_contract.argument` and `pandas_contract.result`
are attached to the function, but the checks are not called.
This is to ensure that production code will not be affected.

One method, `pa.set_mode` and one context generator, `pa.as_mode` are available to define if and how the checks ar
run. Both take either a `pa.Modes` enum value or a literal string as an argument.
The string value must be one of the `pa.Modes` values.

Example:
```python
from pandas_contract import set_mode, as_mode, Modes

set_mode(Modes.WARN)
with as_mode(Modes.SILENT):
    ...

# Raise, use string name of Modes.RAISE
with as_mode("raise"):
    ...
```

### List of all modes

| Modes value | String          | Description                  |
|-------------|-----------------|------------------------------|
| `SKIP`      | `"skip"`        | Do not attach the decorator. |
| `SILENT`    | `"silent"`      | Do not run the checks.       |
| `TRACE`     | `"trace"`       | Trace level debug            |
| `DEBUG`     | `"debug"`       | Debug level debug            |
| `INFO`      | `"info"`        | Info level debug             |
| `WARN`      | `"warn"`        | Warn level debug             |
| `ERROR`     | `"error"`       | Error level debug            |
| `CRITICAL`  | `"critical"`    | Critical level debug         |
| `RAISE`     | `"raise"`       | Raise an exception           |
