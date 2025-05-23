"""Test the mode module."""

from collections.abc import Generator
from typing import TYPE_CHECKING, cast

import pytest

from pandas_contract import set_mode
from pandas_contract.mode import (
    PANDAS_CONTRACT_MODE_ENV,
    Modes,
    _get_mode_from_env,
    as_mode,
    get_mode,
    raises,
    silent,
)
from pandas_contract.mode import logger as mode_logger

if TYPE_CHECKING:
    from pandas_contract.mode import ModesT


@pytest.fixture(autouse=True)
def set_default_mode() -> Generator[None, None, None]:
    """Set the default mode to raise."""
    level = mode_logger.getEffectiveLevel()
    mode_logger.setLevel(-10)
    with as_mode("raise"):
        yield
    mode_logger.setLevel(level)


@pytest.mark.parametrize(
    "mode", (m for m in Modes if m not in (Modes.RAISE, Modes.SKIP, Modes.SILENT))
)
def test_modes_handler_logging(caplog: pytest.LogCaptureFixture, mode: Modes) -> None:
    """Test that the mode handler logs the messages."""
    mode.handle(["test-msg"], "prefix: ")
    assert "prefix: test-msg" in caplog.text


def test_as_mode() -> None:
    """Test as_mode context manager."""
    with as_mode("silent"):
        assert get_mode() == Modes.SILENT
    assert get_mode() == Modes.RAISE


def test_as_mode_raises() -> None:
    """Test that the mode is set back to raise after an exception."""
    try:
        with as_mode("silent"):
            assert get_mode() == "silent"
            err_msg = ""
            raise ValueError(err_msg)  # noqa: TRY301
    except ValueError:
        pass
    assert get_mode() == "raise"


def test_silent_2() -> None:
    """Test silent context manager."""
    with silent():
        assert get_mode() == Modes.SILENT
    with silent():
        assert get_mode() == Modes.SILENT
    assert get_mode() == "raise"


def test_raises() -> None:
    """Test silent context manager."""
    with silent():
        assert get_mode() == Modes.SILENT
        with raises():
            assert get_mode() == Modes.RAISE
    assert get_mode() == Modes.RAISE


@pytest.mark.parametrize(
    "left, right",
    [(Modes.SKIP, Modes.SKIP), (Modes.SKIP, "skip")],
)
def test_is___eq__(left: Modes, right: Modes) -> None:
    """Test that the mode is equal to another mode."""
    assert left == right


@pytest.mark.parametrize(
    "left, right",
    [(Modes.SKIP, Modes.SILENT), (Modes.SKIP, "ignore")],
)
def test_is_not___eq__(left: Modes, right: Modes) -> None:
    """Test that the mode is not equal to another mode."""
    assert left != right


@pytest.mark.parametrize("mode", [Modes.SILENT, Modes.SKIP, "silent", "skip"])
def test_mode_no_handling(mode: Modes, caplog: pytest.LogCaptureFixture) -> None:
    """Test SILENT handling."""
    Modes(mode).handle(["err"], "prefix")
    assert caplog.text == ""


@pytest.mark.parametrize(
    "mode",
    [Modes.TRACE, Modes.DEBUG, Modes.INFO, Modes.WARN, Modes.CRITICAL, Modes.ERROR],
)
def test_mode_logging(mode: Modes, caplog: pytest.LogCaptureFixture) -> None:
    """Test SILENT handling."""
    mode.handle(["err"], "prefix: ")
    assert "prefix: err" in caplog.text


def test_set_mode_invalid() -> None:
    """Test that an invalid mode raises a ValueError."""
    with pytest.raises(ValueError, match="invalid"):
        set_mode(cast("ModesT", "invalid"))


@pytest.mark.parametrize(
    "env, expected, log_msg",
    [
        ("silent", Modes.SILENT, ""),
        ("error", Modes.ERROR, ""),
        (
            "invalid",
            Modes.SILENT,
            "Environment variable PANDAS_CONTRACT_MODE contains invalid value. Setting"
            " to default mode: silent",
        ),
        (
            "",
            Modes.SILENT,
            "No environment variable PANDAS_CONTRACT_MODE set. Default to silent.",
        ),
    ],
)
def test_mode_from_env(
    env: str,
    expected: Modes,
    log_msg: str,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test _get_mode_from_env."""
    monkeypatch.setenv(PANDAS_CONTRACT_MODE_ENV, env)
    assert _get_mode_from_env() == expected
    assert log_msg in caplog.text
