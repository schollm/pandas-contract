"""Pandas Check functions."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import zip_longest
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Union, cast

import pandas as pd
import pandera as pa

from pandas_contract._lib import get_df_arg, split_or_list
from pandas_contract._private_checks import Check

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Hashable

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
    another argument (or a list of arguments).

    *Example*

    >>> from pandas_contract import result2
    >>> @result2(same_index_as("df2"))
    ... def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df.join(df2)

    """

    __slots__ = ("all_args", "args")
    all_args: list[str]
    args: list[str]

    def __init__(self, args: str | Iterable[str] | None, /) -> None:
        """Ensure that the result has the same index as another dataframe.

        :param args: argument that the result should have the same index as.
            It can be either a string or an iterable of strings.
            If it is a string, it will be split by commas.
        """
        self.all_args = self.args = split_or_list(args)

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
    """Check that the argument has the same length.."""

    __slots__ = ("all_args", "args")
    all_args: list[str]
    args: list[str]

    def __init__(self, same_length_as: str | Iterable[str] | None) -> None:
        """Ensure that the result has the same length as another dataframe.

        :param same_length_as: argument that the result should have the same length as.
            It can be either a string or an iterable of strings.
            If it is a string, it will be split by commas.
        """
        self.all_args = self.args = split_or_list(same_length_as)

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
    a) only the columns are added that are also provided in `schema` and
    b) Any other columns have not been modified.

    *Example*

    >>> import pandas_contract as pc
    >>> @pc.result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), extends="df")
    ... def my_fn(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(a=1)

    >>> @pc.result2(pc.checks.extends("df", pa.DataFrameSchema({"a": pa.Column(int)})))
    ... def my_fn(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(a=1)

    """

    __slots__ = ("all_args", "arg", "schema")
    all_args: list[str]
    arg: str
    schema: pa.DataFrameSchema

    def __init__(
        self,
        arg: str | None,
        /,
        schema: pa.SeriesSchema | pa.DataFrameSchema | None,
    ) -> None:
        """Ensure that the result extends another dataframe.

        :param arg:
        :param schema:
        """
        self.all_args = []
        if arg is None:
            self.arg = ""
            self.schema = cast("pa.DataFrameSchema", None)
            return

        if not isinstance(schema, pa.DataFrameSchema):
            msg = (
                f"CheckExtends: If extends is set, then schema must be of type "
                f"pandera.DataFrameSchema, got {type(schema)}."
            )
            raise TypeError(msg)
        self.arg = arg
        self.all_args = [arg]
        self.schema = schema

    @property
    def is_active(self) -> bool:
        """Whether the check is active."""
        return bool(self.arg)

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        df_extends = get_df_arg(fn, self.arg, args, kwargs)
        hash_other = self._get_hash(df_extends)

        def check(df: pd.DataFrame | pd.Series) -> Iterable[str]:
            """Check the DataFrame and keep the index."""
            hash_self = self._get_hash(df)
            prefix = f"extends {self.arg}: "
            if isinstance(hash_self, _HashErr) or isinstance(hash_other, _HashErr):
                if isinstance(hash_self, _HashErr):
                    yield f"{prefix}<input> {hash_self.err}"
                if isinstance(hash_other, _HashErr):
                    yield f"{prefix}{self.arg} {hash_other.err}"
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
            return _HashErr(f"not a DataFrame, got {type(df)}.")

        df_hash = df[[c for c in df if c not in self.schema.columns]]
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


@dataclass(frozen=True)
class is_(Check):  # noqa: N801
    """Ensures that the result is identical (`is` operator) to another dataframe."""

    arg: str | None

    @property
    def all_args(self) -> list[str]:
        """Get all arguments used by this check."""
        return [self.arg] if self.arg else []

    @property
    def is_active(self) -> bool:
        """Whether the check is active."""
        return bool(self.arg)

    def mk_check(
        self, fn: Callable, args: tuple[Any], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Create a check function."""

        def check_fn(df: pd.DataFrame | pd.Series) -> list[str]:
            """Check if input is self,other."""
            if self.arg is None:
                return []
            other_df = get_df_arg(fn, self.arg, args, kwargs)
            return [f"is not {self.arg}"] if df is not other_df else []

        return check_fn


class is_not(Check):  # noqa: N801
    """Ensures that the result is not identical (`is` operator) to `others`."""

    __slots__ = ("all_args", "args")
    all_args: tuple[str, ...]
    args: tuple[str, ...]

    def __init__(self, args: str | Iterable[str] | None, /) -> None:
        """Ensure that the result is not identical (`is` operator) to `others`.

        :param arg: argument that the result should not be identical to.
            It can be either a string or an iterable of strings.
            If it is a string, it will be split by commas.
        """
        if args is None:
            self.args = ()
        elif isinstance(args, str):
            self.args = tuple(o.strip() for o in args.split(","))
        else:
            self.args = tuple(args)
        self.all_args = self.args

    @property
    def is_active(self) -> bool:
        """Check if the check is active."""
        return bool(self.args)

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Create the check function."""

        def check_fn(df: pd.DataFrame | pd.Series) -> list[str]:
            """Check if input is self,other."""
            return [
                f"is {other.strip()}"
                for other, other_df in zip(
                    self.args,
                    (
                        get_df_arg(fn, other.strip(), args, kwargs)
                        for other in self.args
                    ),
                )
                if other_df is df
            ]

        return check_fn
