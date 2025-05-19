from __future__ import annotations

import copy
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Protocol, Union, cast

import pandas as pd
import pandera as pa
import pandera.errors as pa_errors

if TYPE_CHECKING:  # pragma: no cover
    from pandera.api.base.schema import BaseSchema

    from ._lib import MyFunctionType


DataCheckFunctionT = Callable[[Union[pd.DataFrame, pd.Series]], Iterable[str]]


class Check(Protocol):  # pragma: no cover
    """Protocol for a DataFrame or Series check class.

    A check is a callable that returns a check function.

    The check function gets the wrapped function fn, its arguments and kwargs as input.
     It returns a function that takes a single argument, the value to check
    (the DataFrame/Series object) and yields a list of errors as strings.

    """

    def __call__(
        self, fn: MyFunctionType, args: tuple, kwargs: dict[str, Any]
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


@dataclass(frozen=True)  # type: ignore[call-overload]
class CheckSchema(Check):
    """Check the DataFrame using the schema."""

    schema: BaseSchema | None
    head: int | None = None
    tail: int | None = None
    sample: int | None = None
    random_state: int | None = None

    def __call__(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        if self.schema is None:
            return lambda _: []

        def check(df: pd.DataFrame | pd.Series) -> Iterable[str]:
            try:
                parsed_schema = self.parse_schema(fn, args, kwargs)
                parsed_schema.validate(
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
        fn: Callable,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> BaseSchema:
        """Replace column name functions with actual column names.

        Return a copy of the schema where any callables column names are replaced with
        the actual values.

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
                if schema is self.schema:  # lazy copy
                    schema = copy.deepcopy(schema)
                col_arg = col(fn, args, kwargs)
                col_schema = schema.columns.pop(col)
                for col_val in col_arg if isinstance(col_arg, list) else [col_arg]:
                    schema.columns[col_val] = col_schema
        return schema
