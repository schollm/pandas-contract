"""Pandas Check functions."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Union, cast

import pandas as pd
import pandera as pa

from pandas_contract._lib import get_df_arg, split_or_list
from pandas_contract._private_checks import Check, CheckSchema

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Hashable

    from pandera.api.base.schema import BaseSchema

__all__ = [
    "extends",
    "is_",
    "is_not",
    "same_index_as",
    "same_length_as",
]

DataCheckFunctionT = Callable[[Union[pd.DataFrame, pd.Series]], Iterable[str]]


class same_index_as(Check):  # noqa: N801
    """Check that the DataFrame index is the same as another DataFrame.

    This check ensures that the index of the data-frame is identical to the dataframe of
    another argument (or a list of arguments). This can be useful for both arguments
    and results.

    The argument `arg` can be either a single argument name, a comma-separated list of
    argument names or an iterable of argument names.

    **Examples**

    >>> import pandas_contract as pc
    >>> @pc.result2(pc.checks.same_index_as("df, df2"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    The following will check the same, but by first ensuring that the indices of the
    inputs are the same, and then that the resulting index is the same as the input
    index of df.

    >>> @pc.argument2("df", pc.checks.same_index_as("df2"))
    ... @pc.result2(pc.checks.same_index_as("df"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    """

    __slots__ = ("args",)
    args: list[str]

    def __init__(self, args: str | Iterable[str] | None, /) -> None:
        """Ensure that the result has the same index as another dataframe.

        :param args: Argument that the result should have the same index as.
            It can be either a string or an iterable of strings.
            If it is a string, it will be split by commas.
        """
        self.args = split_or_list(args)

    @property
    def is_active(self) -> bool:
        """Whether the check is active."""
        return bool(self.args)

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        indices = [(arg, get_df_arg(fn, arg, args, kwargs).index) for arg in self.args]
        return lambda df: (
            f"Index not equal to index of {other_arg}."
            for other_arg, other_idx in indices
            if not df.index.equals(other_idx)
        )


class same_length_as(Check):  # noqa: N801
    """Check that the DataFrame length is the same as another DataFrame.

    This check ensures that the lenth of the data-frames are identical.
    This can be useful for both arguments and results.

    The argument `arg` can be either a single argument name, a comma-separated list of
    argument names or an iterable of argument names.

    **Examples**

    >>> import pandas_contract as pc
    >>> @pc.result2(pc.checks.same_length_as("df, df2"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    The following will check the same, but by first ensuring that the lengths of the
    inputs are the same, and then that the resulting length is the same as the input
    length of df.

    >>> @pc.argument2("df", pc.checks.same_length_as("df2"))
    ... @pc.result2(pc.checks.same_length_as("df"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    """

    __slots__ = ("args",)
    args: list[str]

    def __init__(self, args: str | Iterable[str] | None, /) -> None:
        """Ensure that the result has the same length as another dataframe.

        :param same_length_as: Argument that the result should have the same length as.
            It can be either a string or an iterable of strings.
            If it is a string, it will be split by commas.
        """
        self.args = split_or_list(args)

    @property
    def is_active(self) -> bool:
        """Whether the check is active."""
        return bool(self.args)

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        lengths = [(arg, len(get_df_arg(fn, arg, args, kwargs))) for arg in self.args]

        return lambda df: (
            f"Length of {other_arg} = {other_len} != {len(df)}."
            for other_arg, other_len in lengths
            if len(df) != other_len
        )


class extends(Check):  # noqa: N801
    """Ensures the resulting DataFrame extends another dataframe.

    Check that the resulting dataframe extends another dataframe (provided
    via argument name). It ensures that
    a) only the columns are added that are also provided in `modified` and
    b) Any other columns have not been modified.

    *Example*

    >>> import pandas_contract as pc
    >>> @pc.result(pc.checks.extends("df", pa.DataFrameSchema({"x": pa.Column(int)})))
    ... def my_fn(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(x=1)

    **Define a function that requires a column "a" and adds a column "x"
     to the data frame**

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
    """

    __slots__ = ("args", "modified")
    args: tuple[str, ...]
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
        if arg is None:
            self.modified = cast("CheckSchema", None)
            self.args = ()
            return

        if not isinstance(modified, pa.DataFrameSchema):
            msg = (
                f"CheckExtends: If modified is set, then it must be of type "
                f"pandera.DataFrameSchema, got {type(modified)}."
            )
            raise TypeError(msg)
        self.args = (arg,)
        self.modified = CheckSchema(modified)

    @property
    def is_active(self) -> bool:
        """Whether the check is active."""
        return bool(self.args and self.args[0])

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        arg = self.args[0]
        df_extends = get_df_arg(fn, arg, args, kwargs)
        hash_other = self._get_hash(df_extends)
        check_modified = self.modified.mk_check(fn, args, kwargs)

        def check(df: pd.DataFrame | pd.Series) -> Iterable[str]:
            """Check the DataFrame and keep the index."""
            # Ensure the modified columns are correct
            prefix = f"extends {arg}: "
            yield from (f"{prefix}{err}" for err in check_modified(df))

            hash_self = self._get_hash(df)
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

    def _get_hash(self, df: Any) -> _HashErr | _HashDf:
        if not isinstance(df, pd.DataFrame):
            return _HashErr(f"not a DataFrame, got {type(df).__qualname__}.")

        df_hash = df[
            [
                c
                for c in df
                if c not in cast("pa.DataFrameSchema", self.modified.schema).columns
            ]
        ]
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


class is_(Check):  # noqa: N801
    """Ensures that the result is identical (`is` operator) to another dataframe.

    This check is most useful for the :class:`@result <pandas_contract.result2>`
    decorator as it ensures that the output is changed in-place.
    It is the opposite of the :class:`is_not() <pandas_contract.checks.is_not>` check.

    **Example**

    Ensure that the result is the same object as the input argument `df`, i.e. the
    function operats in-place.

    >>> import pandas_contract as pc
    >>> @pc.result2(pc.checks.is_("df"))
    ... def fn(df):
    ...    df["x"] = 1  # change df in-place
    ...    return df

    """

    __slots__ = ("args", "is_active")
    args: tuple[str, ...]
    is_active: bool

    def __init__(self, arg: str | None) -> None:
        """Ensure result is identical to another DataFrame.

        :param arg: Name of argument of the decorated function that contains the other
            DataFrame.
        """
        self.args = (arg,) if arg else ()
        self.is_active = bool(self.args)

    def mk_check(
        self, fn: Callable, args: tuple[Any], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Create a check function."""
        return lambda df: (
            f"is not {arg_name}"
            for arg_name in self.args
            if df is not get_df_arg(fn, arg_name, args, kwargs)
        )


class is_not(Check):  # noqa: N801
    """Ensures that the result is not identical (`is not` operator) to `others`.

    This check is most useful for the :class:`@result <pandas_contract.result2>`
    decorator as it ensures that the output is not changed in-place.
    It is the opposite of the :func:`is_() <pandas_contract.checks.is_>` check.

    **Examples**

    >>> import pandas_contract as pc
    >>> @pc.result2(pc.checks.is_not("df"))
    ... def fn(df):
    ...    return df.assign(x=1)  # .assign creates a copy

    """

    __slots__ = ("args", "is_active")
    args: tuple[str, ...]
    is_active: bool

    def __init__(self, args: str | Iterable[str] | None, /) -> None:
        """Ensure that the result is not identical (`is` operator) to `others`.

        :param args: Argument that the result should not be identical to.
            It can be either a string or an iterable of strings.
            If it is a string, it will be split by commas.
        """
        if args is None:
            self.args = ()
        elif isinstance(args, str):
            self.args = tuple(o.strip() for o in args.split(","))
        else:
            self.args = tuple(args)
        self.is_active = bool(self.args)

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Create the check function."""
        return lambda df: (
            f"is {other}"
            for other in self.args
            if get_df_arg(fn, other.strip(), args, kwargs) is df
        )
