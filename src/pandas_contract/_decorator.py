from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any, cast

from pandera.api.base.schema import BaseSchema

from pandas_contract._decorator_v1 import argument as argument1
from pandas_contract._decorator_v1 import result as result1
from pandas_contract._decorator_v2 import argument as argument2
from pandas_contract._decorator_v2 import result as result2

from ._lib import UNDEFINED, ValidateDictT, WrappedT

if TYPE_CHECKING:
    import pandas_contract._private_checks as _checks


def argument(
    arg: str,
    /,
    *checks_: _checks.Check | BaseSchema,
    key: Any = UNDEFINED,
    validate_kwargs: ValidateDictT | None = None,
    **_legacy_args: Any,
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


    Ensure same index on both DataFrames
    ------------------------------------
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
    if _legacy_args:
        warnings.warn(
            "Deprecated API in use. See doc for new API.",
            DeprecationWarning,
            stacklevel=1,
        )
        schema = _legacy_args.get("schema")
        if schema is None and len(checks_) == 1 and isinstance(checks_[0], BaseSchema):
            # schema can be a positional argument - then it has to be the first element
            # *checks_.
            schema = cast("BaseSchema", checks_[0])
            checks_ = checks_[1:]
            if checks_ or validate_kwargs:
                raise ValueError("Can not combine v1 and v2 style of arguments")
        return argument1(
            arg,
            schema,
            key=key,
            head=_legacy_args.get("head"),
            tail=_legacy_args.get("tail"),
            sample=_legacy_args.get("sample"),
            random_state=_legacy_args.get("random_state"),
            same_index_as=_legacy_args.get("same_index_as", ()),
            same_size_as=_legacy_args.get("same_size_as", ()),
            extends=_legacy_args.get("extends"),
        )
    return argument2(
        arg,
        *checks_,
        key=key,
        validate_kwargs=validate_kwargs,
    )


def result(
    *checks_: _checks.Check | BaseSchema,
    key: Any = UNDEFINED,
    validate_kwargs: ValidateDictT | None = None,
    **_legacy_args: Any,
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
    ...    pc.checks.extends("df", pa.DataFrameSchema({"b": pa.Column(int)}))
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
    ...     pc.checks.extends("df", pa.DataFrameSchema({"a": pa.Column(int)})),
    ... )
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(out=1)

    """
    if _legacy_args:
        warnings.warn(
            "Deprecated API in use. See doc for new API.",
            DeprecationWarning,
            stacklevel=1,
        )
        schema = _legacy_args.get("schema")
        if schema is None and len(checks_) == 1 and isinstance(checks_[0], BaseSchema):
            schema = cast("BaseSchema", checks_[0])
            checks_ = checks_[1:]
        if checks_ or validate_kwargs:
            raise ValueError("Can not combine v1 and v2 style of arguments")
        return result1(
            schema,
            key=key,
            head=_legacy_args.get("head"),
            tail=_legacy_args.get("tail"),
            sample=_legacy_args.get("sample"),
            random_state=_legacy_args.get("random_state"),
            same_index_as=_legacy_args.get("same_index_as", ()),
            same_size_as=_legacy_args.get("same_size_as", ()),
            extends=_legacy_args.get("extends"),
            is_=_legacy_args.get("is_"),
            is_not=_legacy_args.get("is_not", ()),
        )
    return result2(
        *checks_,
        key=key,
        validate_kwargs=validate_kwargs,
    )
