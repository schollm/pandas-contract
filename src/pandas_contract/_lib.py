from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol, TypedDict, cast

if TYPE_CHECKING:  # pragma: no cover
    import types
    from collections.abc import Iterable, Sequence

    import pandas as pd


class MyFunctionType(Protocol):  # pragma: no cover
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    __code__: types.CodeType
    __name__: str
    __defaults__: tuple[Any, ...] | None
    __kwdefaults__: dict[str, Any]
    __qualname__: str


class ValidateDictT(TypedDict, total=False):
    head: int | None
    tail: int | None
    sample: int | None
    random_state: int | None


UNDEFINED = object()
"""Mark a parameter as undefined."""


def ensure_list(value: str | Sequence[str]) -> list[str]:
    """Ensure that the value is a list of strings."""
    if isinstance(value, str):
        return [value]
    return list(value)


def split_or_list(value: str | Iterable[str] | None) -> list[str]:
    """Split the value by comma and return a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",")]
    return list(value)


ORIGINAL_FUNCTION_ATTRIBUTE = "_pandas_contract_original_function"


def from_arg(arg: str) -> Callable[[MyFunctionType, tuple[Any], dict[str, Any]], Any]:
    """Get the named argument from the function call via a call-back.

    Returns a call-back function that can be used to get the named argument from the
    function call.
    """

    def wrapper(
        fn: MyFunctionType, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> object:
        """Get the named argument from the function call."""
        fn = getattr(fn, ORIGINAL_FUNCTION_ATTRIBUTE, fn)
        return get_fn_arg(fn, arg, args, kwargs)

    return wrapper


def get_fn_arg(
    func: MyFunctionType, arg_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> object:
    """Get the named argument from function call (either from *args or **kwargs)."""
    if arg_name in kwargs:
        return kwargs[arg_name]
    co = func.__code__
    for var_name, arg in zip(co.co_varnames, args):
        if arg_name == var_name:
            return arg
    if func.__defaults__:
        for var_name, arg in zip(
            func.__code__.co_varnames[co.co_argcount - len(func.__defaults__) :],
            func.__defaults__,
        ):
            if arg_name == var_name:
                return arg
    if func.__kwdefaults__ is not None and arg_name in func.__kwdefaults__:
        return func.__kwdefaults__[arg_name]
    msg = f"{func.__qualname__} does mot have argument '{arg_name}'"
    raise ValueError(msg)


def get_df_arg(
    func: MyFunctionType, arg_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> pd.DataFrame:
    res = get_fn_arg(func, arg_name, args, kwargs)
    return cast("pd.DataFrame", res)


def has_fn_arg(func: MyFunctionType, arg_name: str) -> bool:
    """Check if the function has the named argument."""
    co = func.__code__
    return arg_name in co.co_varnames[: co.co_argcount + co.co_kwonlyargcount]
