"""Module for capturing screenshots of a specific application window."""

import numpy as np
from mss import mss
from utils import get_window_hwnd, get_client_rect


class ScreenCapture:
    """Class to handle screen capturing of a specific window."""

    def __init__(self, target_window_title: str):
        self.target_window_title = target_window_title
        self.hwnd = get_window_hwnd(self.target_window_title)
        if self.hwnd is None:
            raise RuntimeError(
                f"Window with title '{self.target_window_title}' not found.")

        rect = get_client_rect(self.hwnd)
        if rect is None:
            raise RuntimeError(
                f"Could not get client rect for window '{self.target_window_title}'. Is it minimized or not visible?")

        self.x, self.y, self.width, self.height = rect

    def grab(self):
        """Capture a screenshot of the target window."""
        with mss() as sct:
            monitor = {
                "top": self.y,
                "left": self.x,
                "width": self.width,
                "height": self.height
            }
            screenshot = sct.grab(monitor)
            np_image = np.array(screenshot)
            return np.ascontiguousarray(np_image)
            