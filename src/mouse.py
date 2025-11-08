"""Module for mouse control functions on Windows."""

from win32api import GetCursorPos, mouse_event  # type: ignore
from win32con import MOUSEEVENTF_MOVE


def move_mouse_relative(dx: int, dy: int) -> None:
    """Move the mouse cursor by the specified relative amounts."""
    mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)

def get_mouse_position() -> tuple[int, int]:
    """Get the current position of the mouse cursor."""
    return GetCursorPos()