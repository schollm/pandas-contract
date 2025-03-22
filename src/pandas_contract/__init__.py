"""pandas_contract: Ensure pandas dataframe fit the expectations of the function."""

from ._decorator import argument, result
from ._lib import from_arg
from .mode import as_mode, raises, set_mode, silent

__all__ = ["argument", "as_mode", "from_arg", "raises", "result", "set_mode", "silent"]
