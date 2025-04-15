# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
## [0.5.0] - 2025-04-15
### Changes
- Add .github/workflow/testing.yml (Internal change)
## [0.5.0] - 2025-04-14
### Bugfix
-  Correct error message in case other type is not correct in the extends check.
### Added
- Add `DEBUG` mode to `set_mode`/`as_mode` handler.

## [0.4.0] - 2025-04-14
### Added
- The decorator `result` got a new attribute `inplace`, wich can take the name  
  of an input argument. It ensures that the dataframe is changed inplace, i.e. 
  `res is $(result.inplace)` is true.

## [0.3.0] - 2025-04-14
### Bugfixes
- Allow multiple pandas contract checkers attached to a single function
### Changes
- By default, be silent. 
  - This means that if a contract check fails, it will not output anything.
  - You can still use the `raises` and `as_mode`. For tests, its recommended to
    call `set_mode(Modes.RAISES)` within the test setup.
- Improve error message in case one argument or the output does not extend another one.
  If the `pc.argument(extend=<arg>)` or `pc.result(extend=<arg>)` does not hold,
  the error message will provide a more detailed explanation.

## [0.2.0] - 2025-04-11
### Added
- Support multiple columns from function argument
  ```python
  import pandas as pd
  import pandas_contract as pc
  import pandera as pa
  
  @pc.argument("df", schema=pa.DataFrameSchema(
          {pc.from_arg("group_cols"): pa.Column()}
      )
  )
  def func(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
      return df.assign(**{col: df[col].astype(str) for col in group_cols})
  ```
### Fixes
- Add docstring for argument `eztend` to result decorator

## [0.1.1] - 2025-03-31
### Fix
- Fix project links in pyproject.toml

## [0.1.0] - 2025-03-31
_Initial release_
### Added
- Add module `pandas_contract`
- Add decorators `argument` and `result`
- Add helper method `from_arg`
- Add helper handlers `set_mode` and context generators `as_mode`, `raises`,  `silent`