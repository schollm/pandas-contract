from __future__ import annotations

import copy
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Protocol, Union, cast

import pandas as pd
import pandera.errors as pa_errors
import pandera.pandas as pa

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Hashable

    from pandera.api.base.schema import BaseSchema


DataCheckFunctionT = Callable[[Union[pd.DataFrame, pd.Series]], Iterable[str]]


class Check(Protocol):  # pragma: no cover
    """Protocol for a DataFrame or Series check class.

    A check is a callable that returns a check function.

    The check function gets the wrapped function fn, its arguments and kwargs as input.
    It returns a function that takes a single argument, the value to check
    (the DataFrame/Series object) and yields a list of errors as strings.

    """

    def __call__(
        self, fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check function factory.

        This method is called at run-time to create a check based on the decorated
        function and its arguments.

        The returned function of type :class:DataCheckFunctionT must take a single
        DataFrame/DataSeries/object and returns a iterable of strings.
        The iterable's strings each represent an error, signifying a failed check.

        :param fn: The function for which the check is created.
        :param args: The positional arguments of the function.
        :param kwargs: The keyword arguments of the function.
        :return: A function that takes a single data-frame and returns an iterable of
            errors.
        """
        ...


@dataclass(frozen=True)
class CheckSchema(Check):
    """Check the DataFrame using the schema."""

    schema: BaseSchema | None
    head: int | None = None
    tail: int | None = None
    sample: int | None = None
    random_state: int | None = None

    def __call__(
        self, fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        if self.schema is None:
            return always_valid_check

        def check(df: pd.DataFrame | pd.Series | None) -> Iterable[str]:
            if df is None:  # pragma: no cover
                yield "Value is None"
                return
            try:
                parsed_schema = cast("Any", self.parse_schema(fn, args, kwargs))
                validate = parsed_schema.validate

                validate(
                    df,
                    head=self.head,
                    tail=self.tail,
                    sample=self.sample,
                    random_state=self.random_state,
                    lazy=True,
                    inplace=True,
                )
            except (pa_errors.SchemaErrors, pa_errors.SchemaError) as exc:
                yield from map(str, exc.args)
            except pa_errors.BackendNotFoundError:
                yield (
                    f"Backend {type(self.schema).__qualname__} not applicable to"
                    f" {type(df).__qualname__}"
                )

        return check

    def parse_schema(
        self,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> BaseSchema:
        """Replace column name functions with actual column names.

        Return either the original schema, untouched, or a copy of the schema
        where any callables column names are replaced with the actual values.

        :param fn: The function used to extract the column argument from.
        :param args: The positional arguments of the function.
        :param kwargs: The keyword arguments of the function.
        :return: The schema with the actual column names.
        """
        if self.schema is None:  # pragma: no cover
            raise RuntimeError(
                "schema: Schema must be provided (This should never happen)."
            )
        schema = cast("pa.DataFrameSchema", self.schema)
        for col in list(getattr(schema, "columns", {})):
            # col in ist to get a copy of schema.columns
            if callable(col):
                if schema is self.schema:  # lazy copy - only copy if needed
                    schema = copy.deepcopy(schema)
                col_schema = schema.columns.pop(col)
                col_arg = col(fn, args, kwargs)
                for col_val in (
                    cast("list[Hashable]", col_arg)
                    if isinstance(col_arg, list)
                    else [col_arg]
                ):
                    schema.columns[col_val] = col_schema
        return schema


def always_valid_check(
    df: pd.DataFrame | pd.Series,
) -> Iterable[str]:
    """Never complain check."""
    del df
    return []
