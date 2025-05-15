"""Module for handling errors.

Functions to set up handling of contract violation.
By default, the contract violation will be silenced.

.. important::

    By default, the decorators will be attached to the functions, but
    **they will not run**. This ensures that production code is not affected.

    The method :meth:`~pandas_contract.mode.set_mode` can be used to set the
    global mode.

    >>> import pandas_contract as pc
    >>> # print warn messages on standard log.
    >>> pc.set_mode("warn") # doctest: +SKIP

    Alternatively, the environment variable PANDAS_CONTRACT_MODE can be set to one of
    the values of

    It is recommended to set the mode once in the main module of your application.
    For tests, this can be overwritten in the test-setup.

For specific runs, the context generators :meth:`~pandas_contract.mode.as_mode` and the
short-cuts :meth:`pc.raises() <pandas_contract.mode.raises>` and
:meth:`pc.silent() <pandas_contract.mode.silent>` can be used to set the mode.

>>> import pandas_contract as pc
>>> # print warn messages on standard log.
>>> pc.set_mode("warn") # # doctest: +SKIP
>>> with pc.as_mode("raise"): # Within the context, raise a ValueError on violation.
...     pass


"""

from __future__ import annotations

import enum
import os
from contextlib import contextmanager
from logging import getLogger
from typing import TYPE_CHECKING, Literal, Union

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable, Iterator

ModesT = Union[
    "Modes",
    Literal[
        "skip", "silent", "trace", "debug", "info", "warn", "error", "critical", "raise"
    ],
]

logger = getLogger(__name__)
_LOG_LEVELS = {
    "trace": 1,
    "debug": 10,
    "info": 20,
    "warn": 30,
    "error": 40,
    "critical": 50,
}


class Modes(enum.Enum):
    """Modes for handling errors.

    The possible modes are

    * **silent** Register the function at import, but do not run check during runtime.
    * **skip** Do not register the function at import, and do not run check during
      runtime. When this is set, it's not possible to change the mode later on since we
      don't even register the function at all.
    * **trace, debug, info, warn, error, critical** Log the error message at the
      specified level.
    * **raise** Raise an exception with the error message.

    Environment
    -----------

    The environment variable `PANDAS_CONTRACT_MODE` can be used to set the initial mode
    """

    SKIP = "skip"
    SILENT = "silent"
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"
    RAISE = "raise"

    def handle(self, msgs: Iterable[str], prefix: str) -> None:
        """Handle the error messages."""
        if self.no_handling():
            return
        if self == Modes.RAISE:
            msg = "\n".join(f"{prefix}{m}" for m in msgs)
            if msg:
                raise ValueError(msg)
        for msg in msgs:
            full_msg = f"{prefix}{msg}"
            logger.log(level=_LOG_LEVELS[self.value], msg=full_msg)

    def no_handling(self) -> bool:
        """Check if the mode does not handle errors."""
        return self in (Modes.SKIP, Modes.SILENT)

    def __eq__(self, other: object) -> bool:
        """Compare the mode with a string."""
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


_MODE: Modes = Modes(os.getenv("PANDAS_CONTRACT_MODE", "silent"))


def get_mode() -> Modes:
    """Get the global mode for handling errors."""
    return _MODE


@contextmanager
def as_mode(mode: ModesT) -> Iterator[None]:
    """Context manager to temporarily set the global mode for handling errors.

    >>> import pandas as pd
    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.same_index_as("df"))
    ... def problematic_call(df):
    ...    return df.reset_index(drop=True)

    >>> with as_mode("warn"):
    ...     problematic_call(pd.DataFrame({"a": [1]}, index=[10]))
       a
    0  1
    """
    prev_mode = _MODE
    set_mode(mode)
    try:
        yield
    finally:
        set_mode(prev_mode)


def set_mode(mode: ModesT) -> Modes:
    """Set the global mode for handling errors.
    This function should be set at initialization of the application.

    Note that if mode == "skip", then once a module has been imported once, the
    decorator cannot be activated anymore.

    **Example to set the mode to raise an exception on error**

    >>> set_mode("raise")
    <Modes.RAISE: 'raise'>

    """
    global _MODE  # noqa: PLW0603
    if isinstance(mode, str):
        mode = Modes(mode)
    _MODE = mode
    return mode


@contextmanager
def raises() -> Iterator[None]:
    """Context decorator to raise errors on failed dataframe tests.

    >>> import pandas_contract as pc
    >>> import pandas as pd
    >>> @pc.result(pc.checks.same_index_as("df"))
    ... def foo(df):
    ...    return df.reset_index(drop=True)
    >>>
    >>> with raises():
    ...    foo(pd.DataFrame({"a": [1]}, index=[10]))
    Traceback (most recent call last):
    ValueError: foo: Output: Index not equal to index of df.
    """
    with as_mode(Modes.RAISE):
        yield


@contextmanager
def silent() -> Iterator[None]:
    """Context decorator to silence errors on failed dataframe tests.

    >>> import pandas as pd
    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.same_index_as("df"))
    ... def foo(df):
    ...    return df.reset_index(drop=True)
    >>>
    >>> with silent():  # silence errors
    ...     foo(pd.DataFrame({"a": [1]}, index=[10]))
       a
    0  1
    """
    with as_mode(Modes.SILENT):
        yield
