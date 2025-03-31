"""Module for handling errors."""

from __future__ import annotations

import enum
from contextlib import contextmanager
from logging import getLogger
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable


logger = getLogger(__name__)
_LOG_LEVELS = {
    "trace": 1,
    "debug": 10,
    "info": 20,
    "warn": 30,
    "error": 40,
    "critical": 50,
}


class Modes(enum.Enum):
    """Modes for handling errors."""

    SKIP = "skip"
    SILENT = "silent"
    TRACE = "trace"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"
    RAISE = "raise"

    def handle(self, msgs: Iterable[str], prefix: str) -> None:
        """Handle the error messages."""
        if self.no_handling():
            return
        if self == Modes.RAISE:
            msg = "\n".join(f"{prefix}{m}" for m in msgs)
            if msg:
                raise ValueError(msg)
        for msg in msgs:
            full_msg = f"{prefix}{msg}"
            logger.log(level=_LOG_LEVELS[self.value], msg=full_msg)

    def no_handling(self) -> bool:
        """Check if the mode does not handle errors."""
        return self in (Modes.SKIP, Modes.SILENT)

    def __eq__(self, other: object) -> bool:
        """Compare the mode with a string."""
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)


_MODE: Modes = Modes.RAISE


def get_mode() -> Modes:
    """Get the global mode for handling errors."""
    return _MODE


@contextmanager
def as_mode(
    mode: Modes
    | Literal["skip", "silent", "trace", "info", "warn", "error", "critical", "raise"],
) -> Generator[None, None, None]:
    """Context manager to temporarily set the global mode for handling errors."""
    prev_mode = _MODE
    set_mode(mode)
    try:
        yield
    finally:
        set_mode(prev_mode)


def set_mode(
    mode: Modes
    | Literal["skip", "silent", "trace", "info", "warn", "error", "critical", "raise"],
) -> Modes:
    """Set the global mode for handling errors."""
    global _MODE  # noqa: PLW0603
    if isinstance(mode, str):
        mode = Modes(mode)
    _MODE = mode
    return mode


@contextmanager
def raises() -> Generator[None, None, None]:
    """Context decorator to raise errors on failed dataframe tests."""
    with as_mode(Modes.RAISE):
        yield


@contextmanager
def silent() -> Generator[None, None, None]:
    """Context decorator to silence errors on failed dataframe tests."""
    with as_mode(Modes.SILENT):
        yield
