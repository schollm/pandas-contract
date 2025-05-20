"""Pandas Check functions.

Check functions for DataFrames and Series that are not handled by Pandera checks.

This involves checks against multiple arguments, i.e., ensure that the length or indices
of two arguments match, or that an argument is changed in-place (or a copy is created).

"""

from __future__ import annotations

from collections.abc import Iterable
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Union, cast

import pandas as pd
import pandera as pa
from pandera import DataFrameSchema

from pandas_contract._lib import MyFunctionType, get_df_arg, split_or_list
from pandas_contract._private_checks import Check, CheckSchema

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Hashable, Sequence

    from pandera.api.base.schema import BaseSchema

__all__ = ["extends", "is_", "is_not", "removed", "same_index_as", "same_length_as"]

DataCheckFunctionT = Callable[[Union[pd.DataFrame, pd.Series]], Iterable[str]]


def same_index_as(args_: str | Iterable[str] | None, /) -> Check | None:
    """Check that the DataFrame index is the same as another DataFrame.

    This check ensures that the index of the data-frame is identical to the dataframe of
    another argument (or a list of arguments). This can be useful for both arguments
    and results.

    The argument `arg` can be either a single argument name, a comma-separated list of
    argument names or an iterable of argument names.

    :param args_: Argument that the result should have the same index as.
        It can be either a string or an iterable of strings.
        If it is a string, it will be split by commas.

    **Example**
    Simple example, checking that the result has the same index as both df1 and df2

    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.same_index_as("df, df2"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    The following will check the same, but by first ensuring that the indices of the
    inputs are the same, and then that the resulting index is the same as the input
    index of df.

    >>> @pc.argument("df", pc.checks.same_index_as("df2"))
    ... @pc.result(pc.checks.same_index_as("df"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    """
    arg_names = split_or_list(args_)
    if not arg_names:
        return None

    def mk_check(
        fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        # must be a list - we must keep a copy of the index
        indices = [get_df_arg(fn, arg, args, kwargs).index.copy() for arg in arg_names]
        return lambda df: (
            f"Index not equal to index of {other_arg}."
            for other_arg, other_idx in zip(arg_names, indices)
            if not df.index.equals(other_idx)
        )

    return mk_check


def same_length_as(args_: str | Iterable[str] | None, /) -> Check | None:
    """Check that the DataFrame length is the same as another DataFrame.

    This check ensures that the lenth of the data-frames are identical.
    This can be useful for both arguments and results.

    The argument `arg` can be either a single argument name, a comma-separated list of
    argument names or an iterable of argument names.

    :param args_: Argument that the result should have the same length as.
        It can be either a string or an iterable of strings.
        If it is a string, it will be split by commas.

    **Example** Simple check that the result length is the same as both df1 and df2.

    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.same_length_as("df, df2"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    The following will check the same, but by first ensuring that the lengths of the
    inputs are the same, and then that the resulting length is the same as the input
    length of df.

    >>> @pc.argument("df", pc.checks.same_length_as("df2"))
    ... @pc.result(pc.checks.same_length_as("df"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    """
    arg_names = split_or_list(args_)
    if not arg_names:
        return None

    def mk_check(
        fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        lengths = [(arg, len(get_df_arg(fn, arg, args, kwargs))) for arg in arg_names]

        return lambda df: (
            f"Length of {other_arg} = {other_len} != {len(df)}."
            for other_arg, other_len in lengths
            if len(df) != other_len
        )

    return mk_check


class extends(Check):  # noqa: N801
    """Ensures the resulting DataFrame extends another dataframe.

    Check that the resulting dataframe extends another dataframe (provided
    via argument name). It ensures that
    a) only the columns are added that are also provided in `modified` and
    b) Any other columns have not been modified.

    **Example**
    Simple example, output must set a column `"x"`

    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.extends("df", pa.DataFrameSchema({"x": pa.Column(int)})))
    ... def my_fn(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(x=1)

    **Example**
    Define a function that requires a column "a" and adds a column "x" to the data frame

    >>> import pandas_contract as pc
    >>> @pc.argument("df", pa.DataFrameSchema({"a": pa.Column()}))
    ... @pc.result(pc.checks.extends("df", pa.DataFrameSchema({"x": pa.Column(int)})))
    ... def my_fn(df):
    ...   return df.assign(x=df["a"] + 1)
    >>> my_fn(pd.DataFrame({"a": [1]}))
       a  x
    0  1  2

    >>> my_fn(pd.DataFrame({"y": [1]}))
    Traceback (most recent call last):
    ValueError: my_fn: Argument df: ...

    **Example**
    Define a function that adds a column `x_col` to the DataFrame.

    >>> import pandas_contract as pc
    >>> @pc.result(
    ...    pc.checks.extends(
    ...        "df",
    ...        pa.DataFrameSchema({pc.from_arg("col"): pa.Column(int)}),
    ...     )
    ... )
    ... def my_fn(df, col="x"):
    ...   return df.assign(**{col: 1})
    >>> my_fn(pd.DataFrame(index=[0]))
       x
    0  1


    """

    __slots__ = ("arg", "modified")
    arg: str
    modified: CheckSchema

    def __init__(
        self,
        arg: str | None,
        /,
        modified: BaseSchema | None,
    ) -> None:
        """Ensure that the result extends another dataframe.

        :param arg: Argument that this DataFrame extends.
        :param modified: Pandera SchemaDefinition.
        """
        if not arg:
            self.modified = cast("CheckSchema", modified)
            self.arg = ""
            return

        if modified is not None and not isinstance(modified, pa.DataFrameSchema):
            msg = (
                f"CheckExtends: If modified is set, then it must be of type "
                f"pandera.DataFrameSchema, got {type(modified)}."
            )
            raise TypeError(msg)
        self.arg = arg
        self.modified = CheckSchema(modified)

    def __call__(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        arg = self.arg
        df_extends = get_df_arg(fn, arg, args, kwargs)
        modified_cols = self._get_modified_columns(fn, args, kwargs)
        hash_other = self._get_hash(df_extends, modified_cols)
        check_modified = self.modified(fn, args, kwargs)

        def check(df: pd.DataFrame | pd.Series) -> Iterable[str]:
            """Check the DataFrame and keep the index."""
            # Ensure the modified columns are correct
            prefix = f"extends {arg}: "
            yield from (f"{prefix}{err}" for err in check_modified(df))

            hash_self = self._get_hash(df, modified_cols)
            if isinstance(hash_self, _HashErr) or isinstance(hash_other, _HashErr):
                if isinstance(hash_self, _HashErr):
                    yield f"{prefix}<input> {hash_self.err}"
                if isinstance(hash_other, _HashErr):
                    yield f"{prefix}{arg} {hash_other.err}"
                return
            if hash_self == hash_other:
                return  # early exit

            if hash_self.index_ != hash_other.index_:
                yield f"{prefix}index differ"

            if hash_self.columns != hash_other.columns:
                yield (
                    f"{prefix}Columns differ: "
                    f"{hash_self.columns} != {hash_other.columns}"
                )

            for (col1, val1), (col2, val2) in zip_longest(
                hash_self.data, hash_other.data, fillvalue=("<missing>", -1)
            ):
                if col1 == col2 and val1 != val2:
                    yield f"{prefix}Column {col1!r} was changed."

        return check

    def _get_modified_columns(
        self, fn: Callable, args: Any, kwargs: Any
    ) -> list[Hashable]:
        if self.modified.schema is None:
            return []
        parsed = cast("DataFrameSchema", self.modified.parse_schema(fn, args, kwargs))
        return list(parsed.columns)

    def _get_hash(self, df: Any, modified_cols: list[Hashable]) -> _HashErr | _HashDf:
        if not isinstance(df, pd.DataFrame):
            return _HashErr(f"not a DataFrame, got {type(df).__qualname__}.")
        df_hash = df[[c for c in df if c not in modified_cols]]
        return _HashDf(
            type=pd.DataFrame,
            index_=hash(df.index.to_numpy().tobytes()),
            columns=list(df_hash.columns),
            data=[(col, hash(df_hash[col].to_numpy().tobytes())) for col in df_hash],
        )


class _HashDf(NamedTuple):
    """Helper for Extends: Tuple containing the hash of a DataFrame."""

    type: type
    index_: int
    columns: list[str]
    data: list[tuple[Hashable, int]]


class _HashErr(NamedTuple):
    """Helper for Extends: Error tuple if hashing fails."""

    err: str


def is_(arg: str, /) -> Check | None:
    """Ensure that the result is identical (`is` operator) to another dataframe.

    This check is most useful for the :class:`@result <pandas_contract.result>`
    decorator as it ensures that the output is changed in-place.
    It is the opposite of the :class:`is_not() <pandas_contract.checks.is_not>` check.

    **Example**
    Ensure that the result is the same object as the input argument `df`, i.e. the
    function operats in-place.

    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.is_("df"))
    ... def fn(df):
    ...    df["x"] = 1  # change df in-place
    ...    return df

    """
    if not arg:
        return None

    return lambda fn, args, kwargs: (
        lambda df: (
            [f"is not {arg}"] if df is not get_df_arg(fn, arg, args, kwargs) else []
        )
    )


def is_not(args: Sequence[str] | str, /) -> Check | None:
    """Ensure that the result is not identical (`is not` operator) to `others`.

    This check is most useful for the :class:`@result <pandas_contract.result>`
    decorator as it ensures that the output is not changed in-place.
    It is the opposite of the :func:`is_() <pandas_contract.checks.is_>` check.

    :param args: Argument that the result should not be identical to.
        It can be either a string or an iterable of strings.
        If it is a string, it will be split by commas.

    **Example**
    Simple example, ensure that a copy is created.

    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.is_not("df"))
    ... def fn(df):
    ...    return df.assign(x=1)  # .assign creates a copy

    """
    arg_names = split_or_list(args)
    if not arg_names:
        return None

    return lambda fn, args, kwargs: (
        lambda df: (
            f"is {other}"
            for other in arg_names
            if get_df_arg(fn, other.strip(), args, kwargs) is df
        )
    )


def removed(columns: list[Any]) -> Check | None:
    """Ensure given columns are removed.

    :arg columns: List of columns that must not exist in the DataFrame. They can
        also be dynamically created via :meth:`~pandas_contract.from_arg`.

    **Example** Mark drop_x as dropping column x

    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.removed(["x"]))
    ... def drop_x(df: pd.DataFrame):
    ...    return df.drop(columns=["x"])

    **Example** Mark drop_cols as dropping columns from function argument `arg`.

    >>> @pc.result(pc.checks.removed([pc.from_arg("cols")]))
    ... def drop_cols(df: pd.DataFrame, cols: list[str]):
    ...    return df.drop(columns=cols)
    >>> df = pd.DataFrame([[0, 1, 2]], columns=["a", "b", "c"])
    >>> drop_cols(df, cols=["a", "b"])
       c
    0  2
    """
    columns_ = set(columns)
    if not columns_:
        return None

    def _get_columns(
        fn: MyFunctionType, arg: tuple, kwargs: dict[str, Any]
    ) -> Iterable[Hashable]:
        for col in columns_:
            if callable(col):
                col_from_fn = col(fn, arg, kwargs)
                if isinstance(col_from_fn, list):
                    yield from col_from_fn
                else:
                    yield col_from_fn
            else:
                yield col

    return lambda fn, args, kwargs: (
        lambda df: (
            f"Column {col!r} still exists in DataFrame"
            for col in _get_columns(fn, args, kwargs)
            if col in df
        )
    )
