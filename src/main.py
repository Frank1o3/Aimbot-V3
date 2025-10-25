""" Main entry point for the application. """

import cv2 as cv
import numpy as np
from mss import mss
from utils import get_window_hwnd, get_client_rect
from config import Config

config = Config()

config.load("config.yml")

if __name__ == "__main__":
    hwnd = get_window_hwnd(config.general.target_win)
    if hwnd is None:
        raise RuntimeError(
            f"Window with title '{config.general.target_win}' not found.")

    rect = get_client_rect(hwnd)
    if rect is None:
        raise RuntimeError(
            f"Could not get client rect for window '{config.general.target_win}'. Is it minimized or not visible?")

    x, y, width, height = rect
    print(
        f"Window Handle: {hwnd}, Left: {x}, Top: {y}, Right: {width}, Bottom: {height}")
    with mss() as sct:
        monitor = {
            "top": y,
            "left": x,
            "width": width,
            "height": height
        }
        screenshot = sct.grab(monitor)
        print(f"Captured screenshot of size: {screenshot.size}")

        # Convert the screenshot to a NumPy array
        img = np.array(screenshot)

        # Convert BGRA to BGR
        img = cv.cvtColor(img, cv.COLOR_BGRA2BGR)

        # Display the image
        cv.imshow("Screenshot", img)
        cv.waitKey(0)
        cv.destroyAllWindows()
