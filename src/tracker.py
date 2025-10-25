"""Module for tracking a specific color in a window."""

# Build in Modules
import math
from threading import Thread, Event
from time import sleep

# Third Party Modules
import cv2 as cv
import numpy as np
from mss import mss
from win32api import GetAsyncKeyState
from win32con import VK_F1, VK_F2

# Custom Made Modules
from src.utils import get_window_hwnd, get_client_rect
from mouse import get_mouse_position, move_mouse_relative
from config import Config


class Tracker:
    """Class for tracking a specific color in a window."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.color = np.array(config.general.color.rgb, dtype=np.uint8)
        self.hwnd = get_window_hwnd(config.general.target_win)
        if self.hwnd is None:
            raise ValueError(
                f"Window '{config.general.target_win}' not found.")
        self.sct = mss()

        # Precompute the lower and upper bounds for color detection
        self.lower_bound = np.clip(
            self.color - config.aimbot.tolerance, 0, 255)
        self.upper_bound = np.clip(
            self.color + config.aimbot.tolerance, 0, 255)

        self.frame = np.ascontiguousarray(np.zeros((1, 1, 3), dtype=np.uint8))

        # pre set the client_rect
        self.client_rect = get_client_rect(self.hwnd)
        self.PrevX = 0.0
        self.PrevY = 0.0
        self.VelX = 0.0
        self.VelY = 0.0
        self.exit = Event()
        self.exit.set()

    # Implement the screenshot thread
    def capture_thread(self) -> None:
        """Continuously captures screenshots of the target window."""
        if self.hwnd is None:
            raise ValueError("Invalid window handle.")

        while self.exit.is_set():
            self.client_rect = get_client_rect(self.hwnd)
            if self.client_rect is None:
                continue  # Skip if the window is minimized or not visible

            x, y, width, height = self.client_rect
            screenshot = self.sct.grab({
                "left": x + (self.config.general.fov//2),
                "top": y + (self.config.general.fov//2),
                "width": width - (self.config.general.fov//2),
                "height": height - (self.config.general.fov//2)
            })

            img = np.array(screenshot)
            img = cv.cvtColor(img, cv.COLOR_BGRA2BGR)
            self.frame = np.ascontiguousarray(img)

    def detect_thread(self) -> None:
        """Continuously detects the target color in the captured frames."""
        while self.exit.is_set():
            mouse_X, mouse_Y = get_mouse_position()
            frame = self.frame
            if frame.size == 0:
                continue  # Skip if no frame is available

            # Create a mask for the target color
            mask = cv.inRange(frame, self.lower_bound, self.upper_bound)

            # Find contours in the mask
            contours, _ = cv.findContours(
                mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

            if contours and self.client_rect and self.config.aimbot.enabled:
                # Find the largest contour
                largest_contour = max(contours, key=cv.contourArea)
                M = cv.moments(largest_contour)
                # Using the moments to find the centroid and use a var to offset the centoid on the x and y based on the config
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"]) + \
                        self.client_rect[0] + (self.config.general.fov//2)
                    cY = int(M["m01"] / M["m00"]) + \
                        self.client_rect[1] + (self.config.general.fov//2)

                    dX = cX - self.PrevX
                    dY = cY - self.PrevY
                    self.VelX = (self.config.sensitivity.smoothness * self.VelX) + \
                        ((1 - self.config.sensitivity.smoothness * self.VelX) * dX)

                    self.VelY = (self.config.sensitivity.smoothness * self.VelY) + \
                        ((1 - self.config.sensitivity.smoothness * self.VelY) * dY)

                    PredX = cX + self.config.offset.x + self.VelX * self.config.aimbot.lead_factor
                    PredY = cY + self.config.offset.y + self.VelY * self.config.aimbot.lead_factor

                    dist = math.hypot(PredX - mouse_X, PredY - mouse_Y)
                    sens = self.config.sensitivity.min_sensitivity + (dist / self.config.general.fov) * (
                        self.config.sensitivity.max_sensitivity - self.config.sensitivity.min_sensitivity)
                    sens = max(self.config.sensitivity.min_sensitivity, min(
                        sens, self.config.sensitivity.max_sensitivity))

                    moveX = math.ceil((PredX - mouse_X) / sens)
                    moveY = math.ceil((PredY - mouse_Y) / sens)

                    move_mouse_relative(moveX, moveY)
                    self.PrevX = cX
                    self.PrevY = cY
                else:
                    self.PrevX = 0
                    self.PrevY = 0

    def run(self) -> None:
        thread1 = Thread(target=self.capture_thread)
        thread2 = Thread(target=self.detect_thread)

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        while True:
            if GetAsyncKeyState(VK_F1):
                self.exit.clear()
                self.exit.wait()
                break
            if GetAsyncKeyState(VK_F2):
                self.config.aimbot.enabled = not (self.config.aimbot.enabled)
            sleep(0.15)
