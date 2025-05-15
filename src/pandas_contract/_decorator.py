from __future__ import annotations

import functools
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from pandera.api.base.schema import BaseSchema

import pandas_contract._private_checks as _checks
from pandas_contract.mode import Modes, get_mode

from ._lib import (
    ORIGINAL_FUNCTION_ATTRIBUTE,
    UNDEFINED,
    KeyT,
    ValidateDictT,
    WrappedT,
    get_fn_arg,
    has_fn_arg,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable

    import pandas as pd

    from ._lib import MyFunctionType

_T = TypeVar("_T", bound=Callable[..., Any])
""""Type variable for the function type."""


def argument(
    arg: str,
    /,
    *checks_: _checks.Check | BaseSchema,
    key: KeyT = UNDEFINED,
    validate_kwargs: ValidateDictT | None = None,
) -> WrappedT:
    """Check the input DataFrame.

    :param arg: The name of the argument to check. This must be the name of one of the
     arguments of the function to be decorated.
    :param checks_: Additional checks or the pandera schema verification to perform on
        the DataFrame. For checks, see module :class:`pandas_contract.checks`.
        For pandera, see the
        `pandera documentation <https://pandera.readthedocs.io/en/stable>`_ for
        `DataFrameSchema <https://pandera.readthedocs.io/en/stable/dataframe_schemas.html>`_
        and `SeriesSchema <https://pandera.readthedocs.io/en/stable/series_schemas.html>`_.
    :param key: The key of the input to check. See
        :class:`~pandas_contract._decorator_v2.KeyT`.
    :param validate_kwargs: Additional Keywords to provide to pandera validate.
        Valid keys are

        * **head**: The number of rows to validate from the head.  If None, all rows are
          used for validation. Used for pandera schema validation.
        * **tail**: The number of rows to validate from the tail. If None, all rows are
          used for validation. Used for pandera schema validation.
        * **sample**: The number of rows to validate randomly. If None, all rows are
          used for validation. Used for pandera schema validation.
        * **random_state**: The random state for the random sampling. Used for pandera
          schema validation.


    Examples
    ========

    Note that all examples use the following preamble:

    >>> import pandas as pd
    >>> import pandera as pa
    >>> import pandas_contract as pc

    Ensure columns exist in DataFrame
    -----------------------------------

    Ensure that input dataframe as a column "a" of type int and "b" of type float.

    >>> @argument(
    ...     "df",
    ...     pa.DataFrameSchema(
    ...         {"a": pa.Column(pa.Int), "b": pa.Column(pa.Float)}
    ...     ),
    ... )
    ... def func(df: pd.DataFrame) -> None:
    ...     ...


    Ensure same index
    -----------------
    Ensure that the dataframes arguments *df1* and *df2* have the same indices by
    checking argument *df1* against the argument *df2*.

    >>> @argument("df1", pc.checks.same_index_as("df2"))
    ... def func(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    ...     ...

    Ensure same size
    ----------------
    Ensure that the dataframe arguments *df1* and *df2* have the same size

    >>> @argument("df1", pc.checks.same_length_as("df2"))
    ... def func(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    ...     ...

    *All-together*

    Ensure that the input dataframe has a column `"a"` of type int, the same index as
    df2, and the same size as df3.

    >>> @argument(
    ...     "dfs",
    ...     pa.DataFrameSchema({"a": pa.Column(pa.Int)}),
    ...     pc.checks.same_index_as("df2"),
    ...     pc.checks.same_length_as("df3"),
    ... )
    ... def func(dfs: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame) -> None:
    ...     ...

    *Data Series*

    Instead of a DataFrame, one can also validate a Series. Then the schema must
    be of type pa.SeriesSchema.

    For example, to ensure that the input series is of type int, one can use:

    >>> @argument("ds", pa.SeriesSchema(pa.Int))
    ... def func(ds: pd.Series) -> None:
    ...     ...

    """
    checks_list: list[_checks.Check] = [
        _checks.CheckSchema(check, **validate_kwargs or {})
        if isinstance(check, BaseSchema)
        else check
        for check in checks_
    ]
    checks_clean = [check for check in checks_list if check.is_active]

    def wrapped(fn: _T) -> _T:
        if get_mode() == Modes.SKIP:
            return fn

        orig_fn = getattr(fn, ORIGINAL_FUNCTION_ATTRIBUTE, fn)
        _check_fn_args(f"@argument({arg!r})", orig_fn, _collect_args([arg], checks_))

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> _T:
            if (mode := get_mode()).no_handling():
                return fn(*args, **kwargs)

            checkers = [check.mk_check(orig_fn, args, kwargs) for check in checks_clean]
            arg_value = get_fn_arg(orig_fn, arg, args, kwargs)
            df = _get_from_key(key, arg_value)
            errs = chain.from_iterable(check(df) for check in checkers)

            mode.handle(errs, f"{fn.__name__}: Argument {arg}: ")
            return fn(*args, **kwargs)

        setattr(wrapper, ORIGINAL_FUNCTION_ATTRIBUTE, orig_fn)
        return cast("_T", wrapper)

    return wrapped


def result(
    *checks_: _checks.Check | BaseSchema,
    key: Any = UNDEFINED,
    validate_kwargs: ValidateDictT | None = None,
) -> WrappedT:
    """Validate a DataFrame result using pandera.

    :param checks_: Additional checks and the pandera schema verification to perform on
        the DataFrame. For checks, see module :class:`pandas_contract.checks`.

        If a pandera schema is provided, it is used to validate the output.
        For pandera, see the
        `pandera documentation <https://pandera.readthedocs.io/en/stable>`_ for
        `DataFrameSchema <https://pandera.readthedocs.io/en/stable/dataframe_schemas.html>`_
        and `SeriesSchema <https://pandera.readthedocs.io/en/stable/series_schemas.html>`_.
    :param key: The key of the input to check. See
        :class:`~pandas_contract._decorator_v2.KeyT`.

    :param validate_kwargs: Additional Keywords to provide to pandera validate.
        Valid keys are

        * **head**: The number of rows to validate from the head.  If None, all rows are
          used for validation. Used for pandera schema validation.
        * **tail**: The number of rows to validate from the tail. If None, all rows are
          used for validation. Used for pandera schema validation.
        * **sample**: The number of rows to validate randomly. If None, all rows are
          used for validation. Used for pandera schema validation.
        * **random_state**: The random state for the random sampling. Used for pandera
          schema validation.


    Examples
    ========
    Note that all examples use the following preamble:

    >>> import pandas as pd
    >>> import pandera as pa
    >>> import pandas_contract as pc

    Output column exists
    --------------------

    Ensure that the output dataframe has a column "a" of type int.

    >>> @result(pa.DataFrameSchema({"a": pa.Column(pa.Int)}))
    ... def func() -> pd.DataFrame:
    ...     return pd.DataFrame({"a": [1, 2]})


    Ensure that the output dataframe has a column "a" of type int and "b" of type float
    -----------------------------------------------------------------------------------

    >>> @result(
    ...     pa.DataFrameSchema(
    ...         {"a": pa.Column(pa.Int), "b": pa.Column(pa.Float)}
    ...    )
    ... )
    ... def func() -> pd.DataFrame:
    ...     return pd.DataFrame({"a": [1, 2], "b": [1.0, 2.0]})

    **Ensure that the output dataframe has the same index as df.**

    >>> @result(
    ...     pa.DataFrameSchema({"a": pa.Column(pa.Int)}, pc.checks.same_index_as("df"))
    ... )
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df

    **Ensure that the output dataframe has the same size as df.**

    >>> @result(
    ...     pa.DataFrameSchema({"a": pa.Column(pa.Int)}),
    ...     pc.checks.same_length_as("df"),
    ... )
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df

    **Ensure same index.**
    Ensure that the output dataframe has the same index as df1 and the same size as df2.

    >>> @result(
    ...     pa.DataFrameSchema({"a": pa.Column(pa.Int)}),
    ...     pc.checks.same_index_as("df1"),
    ...     pc.checks.same_length_as("df2"),
    ... )
    ... def func(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df1

    **Ensures that the output extends the input schema.**

    >>> @result(
    ...    pc.checks.extends("df", modified=pa.DataFrameSchema({"b": pa.Column(int)}))
    ... )
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(a=1)

    Note that any columns listed the result schema can be modified. To specify a column
    that is returned, but cannot be modified, use the schema argument of the input
    argument.

    Ensures that the output extends the input schema and has a column "a" of type int.
    The following will fail in any of the three cases:

    * df does not have a column "in" of type int
    * The result does not have a column "out" of type int
    * The column 'a' was changed.

    >>> @argument("df", pa.DataFrameSchema({"in": pa.Column(pa.Int)}))
    ... @result(
    ...     pa.DataFrameSchema({"out": pa.Column(pa.Int)}),
    ...     pc.checks.extends("df", modified=pa.DataFrameSchema({"a": pa.Column(int)})),
    ... )
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(out=1)

    """
    checks_lst: list[_checks.Check] = [
        _checks.CheckSchema(check, **validate_kwargs or {})
        if isinstance(check, BaseSchema)
        else check
        for check in checks_
    ]
    clean_checks: list[_checks.Check] = [
        check for check in checks_lst if check.is_active
    ]

    def wrapped(fn: _T) -> _T:
        if get_mode() == Modes.SKIP:
            return fn
        orig_fn = getattr(fn, ORIGINAL_FUNCTION_ATTRIBUTE, fn)
        _check_fn_args("@result", orig_fn, _collect_args([], checks_))

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if (mode := get_mode()).no_handling():
                return fn(*args, **kwargs)

            checkers = [check.mk_check(orig_fn, args, kwargs) for check in clean_checks]

            res = fn(*args, **kwargs)
            df = _get_from_key(key, res)
            errs = chain.from_iterable(check(df) for check in checkers)
            mode.handle(errs, f"{fn.__name__}: Output: ")
            return res

        setattr(wrapper, ORIGINAL_FUNCTION_ATTRIBUTE, orig_fn)
        return cast("_T", wrapper)

    return wrapped


def _get_from_key(key: Any, input_: Any) -> pd.DataFrame:
    """Get the DataFrame from the input and the key.

    If the key is `UNDEFINED`, return the input.
    If it's a callable, call it with the input and return its result.
    Otherwise, return input[key].

    As an edge case, if the actual key is a callable, one has to wrap it with another
    callable, i.e. key=lambda x: x
    """
    if key is UNDEFINED:
        return input_
    if callable(key):
        return cast("pd.DataFrame", key(input_))
    return input_[key]


def _check_fn_args(prefix: str, fn: MyFunctionType, args: Iterable[str]) -> None:
    """Check if the function has the required arguments."""
    if setup_errs := [
        f"{fn.__qualname__} {prefix} requires argument {arg!r} in function signature."
        for arg in args
        if not has_fn_arg(fn, arg)
    ]:
        raise ValueError("\n".join(setup_errs))


def _collect_args(args: Iterable[str], checks: Iterable[Any]) -> Iterable[str]:
    yield from args
    for check in checks:
        yield from getattr(check, "args", ())
