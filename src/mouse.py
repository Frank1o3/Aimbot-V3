"""Enhanced module for mouse control with curved movement on Windows."""

import math
import random
import time
from typing import Tuple

from win32api import GetCursorPos, mouse_event  # type: ignore
from win32con import MOUSEEVENTF_MOVE


def move_mouse_relative(dx: int, dy: int) -> None:
    """Move the mouse cursor by the specified relative amounts."""
    mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)


def get_mouse_position() -> Tuple[int, int]:
    """Get the current position of the mouse cursor."""
    return GetCursorPos()


def move_mouse_to(target_x: int, target_y: int) -> None:
    """
    Move the mouse smoothly and naturally to (target_x, target_y)
    using relative movement along a curved path.
    The curve intensity and duration depend on the travel distance.
    """
    start_x, start_y = get_mouse_position()
    dx = target_x - start_x
    dy = target_y - start_y
    distance = math.hypot(dx, dy)
    if distance < 1:
        return  # already there

    # --- Curve and timing parameters ---
    # more distance → more steps
    steps = max(10, int(distance / 5))
    duration = max(0.1, min(0.6, distance / 500))    # cap movement speed
    control_offset = distance / random.uniform(3, 5)  # curve amplitude

    # Random control point for Bezier curve
    control_x = start_x + dx / 2 + \
        random.uniform(-control_offset, control_offset)
    control_y = start_y + dy / 2 + \
        random.uniform(-control_offset, control_offset)

    last_x, last_y = start_x, start_y
    start_time = time.perf_counter()

    for i in range(1, steps + 1):
        t = i / steps
        # Quadratic Bezier interpolation
        x = (1 - t) ** 2 * start_x + 2 * (1 - t) * \
            t * control_x + t ** 2 * target_x
        y = (1 - t) ** 2 * start_y + 2 * (1 - t) * \
            t * control_y + t ** 2 * target_y

        # Calculate relative movement
        move_mouse_relative(int(x - last_x), int(y - last_y))
        last_x, last_y = round(x), round(y)

        # Adaptive timing to keep consistent overall duration
        elapsed = time.perf_counter() - start_time
        remaining = duration - elapsed
        sleep_time = max(0.001, remaining / (steps - i + 1))
        time.sleep(sleep_time)
