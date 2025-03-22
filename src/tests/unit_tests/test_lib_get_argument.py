"""Test _lib functions."""

from typing import NoReturn

import pytest

from pandas_contract._lib import MyFunctionType, get_fn_arg, has_fn_arg

DEFAULT = 2


def fn(a: int, b: int) -> NoReturn:
    """Test function with two arguments."""
    x = a + b
    raise ValueError(x)


def fn_with_default(a: int, b: int = DEFAULT) -> NoReturn:
    """Test function with two arguments, one with default value."""
    x = a + b
    raise ValueError(x)


def fn_pos_only(a: int, b: int = DEFAULT, /) -> NoReturn:
    """Test function with two positional only arguments, one with default value."""
    x = a + b
    raise ValueError(x)


def fn_kw_only(a: int, *, b: int = DEFAULT) -> NoReturn:
    """Test function with two keyword only arguments, one with default value."""
    x = a + b
    raise ValueError(x)


@pytest.mark.parametrize(
    "fn_",
    [
        fn_with_default,
        lambda a, b=DEFAULT: None,
    ],
)
@pytest.mark.parametrize(
    "args, kwargs, expected",
    [
        ((1, 20), {}, 20),
        ((1,), {"b": 20}, 20),
        ((), {"a": 1, "b": 20}, 20),
        ((1,), {}, DEFAULT),
        ((), {"a": 1}, DEFAULT),
    ],
)
def test(
    fn_: MyFunctionType, args: tuple[int], kwargs: dict[str, int], expected: int
) -> None:
    """Test get_fn_arg returns the correct argument."""
    _get_argument = get_fn_arg(fn_, "b", args, kwargs) == expected


@pytest.mark.parametrize(
    "fn_",
    [
        fn_with_default,
        fn_pos_only,
        fn_kw_only,
        lambda a=1, b=DEFAULT: None,
        lambda a=1, b=DEFAULT, /: None,
        lambda *, a=1, b=DEFAULT: None,
    ],
)
def test_default(fn_: MyFunctionType) -> None:
    """Test get_fn_arg returns the default value if the argument is not provided."""
    assert get_fn_arg(fn_, "b", (), {}) == DEFAULT


@pytest.mark.parametrize(
    "fn_",
    [
        lambda a: None,
        lambda a, b: None,
        lambda a=1: None,
    ],
)
def test_no_such_argument(fn_: MyFunctionType) -> None:
    """Test that ValueError is raised when the argument is not found."""
    with pytest.raises(ValueError, match="<lambda> does mot have argument 'b'"):
        get_fn_arg(fn_, "b", (1,), {})


@pytest.mark.parametrize(
    "fn_",
    [
        fn,
        fn_kw_only,
        fn_pos_only,
        fn_with_default,
        lambda a, b: None,
        lambda a, b=DEFAULT: None,
        lambda a, b=DEFAULT, /: None,
        lambda *, a, b=DEFAULT: None,
    ],
)
def test_has_fn_arg(fn_: MyFunctionType) -> None:
    """Test that has_fn_arg returns True if the function has the argument."""
    assert has_fn_arg(fn_, "b")
    assert not has_fn_arg(fn_, "x")
