from __future__ import annotations

import functools
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from pandas_contract.mode import Modes, get_mode

from ._checks import (
    Check,
    CheckExtends,
    CheckKeepIndex,
    CheckKeepLength,
    CheckSchema,
)
from ._lib import ensure_list, get_fn_arg, has_fn_arg

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    import pandas as pd
    import pandera as pa

    from ._lib import MyFunctionType

_UNDEFINED = object()

T = TypeVar("T", bound=Callable[..., Any])


@dataclass
class argument:  # noqa: N801
    """Decorator to check the input DataFrame for required columns using pandera.

    :param arg: The name of the argument to check. This must correspond to one of the
     arguments of the function.
    :param schema: The schema to validate the input DataFrame.
        See [pandera](https://pandera.readthedocs.io/).
    :param head: The number of rows to validate from the head. If None, all rows are
        used for validation.
    :param tail: The number of rows to validate from the tail. If None, all rows are
        used for validation.
    :param sample: The number of rows to validate randomly. If None, all rows are used
        for validation.
    :param random_state: The random state for the random sampling.


    """

    arg: str
    schema: pa.DataFrameSchema | pa.SeriesSchema | None = None
    head: int | None = None
    tail: int | None = None
    sample: int | None = None
    random_state: int | None = None
    fix: bool = False
    same_index_as: str | Sequence[str] = ()
    same_size_as: str | Sequence[str] = ()
    key: Any = _UNDEFINED
    extends: str | None = None

    def __post_init__(self) -> None:
        self.same_index_as = same_index_as = ensure_list(self.same_index_as) + (
            [self.extends] if self.extends else []
        )
        self.same_size_as = same_size_as = ensure_list(self.same_size_as)
        checks: list[Check] = [
            CheckSchema(
                self.schema,
                self.head,
                self.tail,
                self.sample,
                self.random_state,
            ),
            CheckKeepIndex(same_index_as),
            CheckKeepLength(same_size_as),
            CheckExtends(self.extends, self.schema),
        ]
        self.checks = [check for check in checks if check.is_active]

    def __call__(self, fn: T) -> T:
        if get_mode() == Modes.SKIP:
            return fn
        _check_fn_args(
            f"@argument(arg={self.arg!r})",
            fn,
            (self.arg, *self.same_index_as, *self.same_size_as),
        )

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if (mode := get_mode()).no_handling():
                return fn(*args, **kwargs)
            checkers = [check.mk_check(fn, args, kwargs) for check in self.checks]

            arg = get_fn_arg(fn, self.arg, args, kwargs)
            df = _get_from_key(self.key, arg)
            errs = chain.from_iterable(check(df) for check in checkers)

            mode.handle(errs, f"{fn.__name__}: Argument {self.arg}: ")
            return fn(*args, **kwargs)

        return cast("T", wrapper)


@dataclass
class result:  # noqa: N801
    """Validate a DataFrame result using pandera.

    The schema is used to validate the output DataFrame of the function.

    :param key: The key of the output to check. If None, the entire output is checked.
        This can be used if the function returns a tuple or a mapping.
    :param schema: The schema to validate the output DataFrame.
    :param head: The number of rows to validate from the head.
    :param tail: The number of rows to validate from the tail.
    :param sample: The number of rows to validate randomly.
    :param random_state: The random state for the random sampling.
    :param fix: Whether to fix the values instead of reporting them as an error.
    :param same_index_as: The name of the input argument(s) that should have the
        same index.
    :param same_size_as: The name of the input argument(s) that should have the same
        size.
    """

    schema: pa.DataFrameSchema | pa.SeriesSchema | None = None
    head: int | None = None
    tail: int | None = None
    sample: int | None = None
    random_state: int | None = None
    fix: bool = False
    same_index_as: str | Sequence[str] = ()
    same_size_as: str | Sequence[str] = ()
    key: Any = _UNDEFINED
    extends: str | None = None

    def __post_init__(self) -> None:
        self.same_index_as = same_index_as = ensure_list(self.same_index_as)
        self.same_size_as = same_size_as = ensure_list(self.same_size_as)
        checks: list[Check] = [
            CheckKeepIndex(same_index_as),
            CheckKeepLength(same_size_as),
            CheckExtends(self.extends, self.schema),
        ]
        self.checks: list[Check] = [check for check in checks if check.is_active]

    def __call__(self, fn: T) -> T:
        if get_mode() == Modes.SKIP:
            return fn
        _check_fn_args("result", fn, (*self.same_index_as, *self.same_size_as))

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if (mode := get_mode()).no_handling():
                return fn(*args, **kwargs)
            checkers = [check.mk_check(fn, args, kwargs) for check in self.checks]

            res = fn(*args, **kwargs)
            df = _get_from_key(self.key, res)
            errs = chain.from_iterable(check(df) for check in checkers)
            mode.handle(errs, f"{fn.__name__}: Output: ")
            return res

        return cast("T", wrapper)


def _get_from_key(key: Any, input_: Any) -> pd.DataFrame:
    """Get the DataFrame from the input and the key.

    If the key is `_UNDEFINED`, return the input.
    If it's a callable, call it with the input and return its result.
    Otherwise, return input[key].

    As an edge case, if the actual key is a callable, one has to wrap it with another
    callable, i.e.
      key=lambda x: x
    """
    if key is _UNDEFINED:
        return input_
    if callable(key):
        return key(input_)
    return input_[key]


def _check_fn_args(prefix: str, fn: MyFunctionType, args: Iterable[str]) -> None:
    """Check if the function has the required arguments."""
    if setup_errs := [
        f"{fn.__qualname__} {prefix} requires argument {arg!r} in function signature."
        for arg in args
        if not has_fn_arg(fn, arg)
    ]:
        raise ValueError("\n".join(setup_errs))
