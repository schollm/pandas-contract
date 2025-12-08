"""Ensure pandas dataframe fit the expectations of the function.

The two main entry points are the :meth:`@argument() <argument>` and the
:meth:`@result() <result>` decorators to specify pandas DataFrame or Series inputs
and outputs, respectively.

They can check directly against a
:external:class:`pandera.DataFrameSchema <pandera.api.pandas.container.DataFrameSchema>`
or use cross-argument checks like output
:meth:`pc.checks.extends <pandas_contract.checks.extends>` an input. See
:class:`pc.checks <pandas_contract.checks>` for the available checks.

The helper function :meth:`pc.from_arg <pandas_contract.from_arg>` can be used to
get the argument value from a function call. This is useful for checks that depend
on another function argument, e.g., to check that a DataFrame contains a column, which
is set as an argument to the function.
"""

try:
    import pandera.pandas as pa
except ImportError:  # pragma: no cover
    import sys

    import pandera as pa  # type: ignore[no-redef]

    sys.modules["pandera.pandas"] = pa


from . import checks
from ._decorator import argument, result
from ._lib import from_arg
from .mode import Modes, as_mode, get_mode, raises, set_mode, silent

del pa

__all__ = [
    "Modes",
    "argument",
    "as_mode",
    "checks",
    "from_arg",
    "get_mode",
    "raises",
    "result",
    "set_mode",
    "silent",
]
