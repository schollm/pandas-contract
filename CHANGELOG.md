# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
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