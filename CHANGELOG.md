# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2025-05-20
### Changed
- Internal: pandas_contract.checks can now be a function. Removed attributes `args` and 
  `is_active` and renamed `mk_check` to `__call__` in the protocol.
### Added
- Official Python 3.13 support.

## [0.8.1] - 2025-05-17
### Added
- `checks.removed`: Define a column to be non-existent.
- Documentation: Links to source
- Documentation: Add development guide
- Test: Run doctest in CI
### Fixed
- Examples in docstrings

## [0.8.0] - 2025-05-16
### Changed
- Remove v1 decorators: Rename pandas_contract.argument2 to argument, pandas_contract.result2 to result.

## [0.7.1] - 2025-05-16
### Added
- Add migration guide [docs/migration.md](project:migration.md) to migrate to version 0.7.0 and prepare for 0.8.0
- Shorten README.md, most moved to [pandas-contract docs](https://pandas-contract.readthedocs.io/en/stable/details.html)
- Add more documentation

## [0.7.0] - 2025-05-15
### Changed
- pandas_contract.argument first argument is positional only (aligned with argument2)
- pandas_contract.argument/result V1 checks are keyword only.
- Rename checks.extends second argument from schema to modified.
- Improve error message in case of Pandera not able to find the correct schema to check the provided Series/DataFrame.
- Remove V1 documentation
- checks.is_not is a normal class instead of a dataclass.
### Added
- pandas_contract.argument/result is compatible with both v1 and v2 API.
- pandera schemas can be any BaseSchema.

## [0.6.4] - 2025-05-12
### Changed
- Documentation: Fixed multiple entries in TOC
- Documentation: Document use of PANDAS_CONTRACT_MODE

## [0.6.3] - 2025-05-11
### Changed
- Fix examples in docstrings.
### Added
- Add support for environmewnt variable PANDAS_CONTRACT_MODE
- Add docstring tests

## [0.6.2] - 2025-05-09
### Added
- New decorators `argument2` and `result2` with new API.
- New module checks with all publicly available checks

## [0.6.1] - 2025-04-17
### Added
- Documentation is now on [pandas-contract.readthedocs.io/](https://pandas-contract.readthedocs.io/en/latest/)
## [0.6.0] - 2025-04-17
### Changed
- `pa.result.inplace` renamed to `pa.result.is_`.
### Added
- Add `pa.result.is_not: str | Sequence[str]` to check if the result is not
  identical to the given parameters.
### Fixed
- Fix error message in case the `.extend` check does not get a valid argument. 
- Many documentation fixes to make docstrings sphinx compatible.

## [0.5.0] - 2025-04-15
### Changed
- **Internal** Add .github/workflow/testing.yml

## [0.5.0] - 2025-04-14
### Fixed
-  Correct error message in case other type is not correct in the extends check.
### Added
- Add `DEBUG` mode to `set_mode`/`as_mode` handler.

## [0.4.0] - 2025-04-14
### Added
- The decorator `result` got a new attribute `inplace`, wich can take the name
  of an input argument. It ensures that the dataframe is changed inplace, i.e.
  `res is $(result.inplace)` is true.

## [0.3.0] - 2025-04-14
### Fixed
- Allow multiple pandas contract checkers attached to a single function
### Changed
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
### Fixed
- Add docstring for argument `eztend` to result decorator

## [0.1.1] - 2025-03-31
### Fixed
- Fix project links in pyproject.toml

## [0.1.0] - 2025-03-31
_Initial release_
### Added
- Add module `pandas_contract`
- Add decorators `argument` and `result`
- Add helper method `from_arg`
- Add helper handlers `set_mode` and context generators `as_mode`, `raises`,  `silent`
