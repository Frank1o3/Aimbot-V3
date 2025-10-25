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
from win32con import VK_F1, VK_F2, VK_F3

# Custom Made Modules
from utils import get_window_hwnd, get_client_rect
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

        # Precompute the lower and upper bounds for color detection
        self.lower_bound = np.clip(
            self.color - config.aimbot.tolerance, 0, 255)
        self.upper_bound = np.clip(
            self.color + config.aimbot.tolerance, 0, 255)

        self.frame = np.ascontiguousarray(np.zeros((1, 1, 3), dtype=np.uint8))

        # pre set the client_rect
        self.monitor = {"top": 0, "left": 0, "bottom": 0, "right": 0}
        self.PrevX = 0.0
        self.PrevY = 0.0
        self.VelX = 0.0
        self.VelY = 0.0
        self.exit = Event()
        self.exit.set()
        self.debug_mode = False  # Toggle with F3

    # Implement the screenshot thread
    def capture_thread(self) -> None:
        """Continuously captures screenshots of the target window."""
        if self.hwnd is None:
            raise ValueError("Invalid window handle.")

        sct = mss()  # Create mss instance per thread for thread safety
        while self.exit.is_set():
            client_rect = get_client_rect(self.hwnd)
            if client_rect is None:
                continue  # Skip if the window is minimized or not visible

            x, y, width, height = client_rect
            center_x = x + width // 2
            center_y = y + height // 2
            fov_half = self.config.general.fov//2 // 2

            self.monitor = {
                "top": max(y, center_y - fov_half),
                "left": max(x, center_x - fov_half),
                "width": min(x + width, center_x + fov_half)
                - max(x, center_x - fov_half),
                "height": min(y + height, center_y + fov_half)
                - max(y, center_y - fov_half),
            }

            screenshot = sct.grab(self.monitor)

            img = np.array(screenshot)
            img = cv.cvtColor(img, cv.COLOR_BGRA2BGR)
            self.frame = np.ascontiguousarray(img)

    def detect_thread(self) -> None:
        """Continuously detects the target color in the captured frames."""
        while self.exit.is_set():
            mouse_X, mouse_Y = get_mouse_position()
            frame = self.frame.copy()
            if frame.size == 0:
                continue

            mask = cv.inRange(frame, self.lower_bound, self.upper_bound)
            contours, _ = cv.findContours(
                mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

            if contours and self.monitor and self.config.aimbot.enabled:
                frame_h, frame_w = frame.shape[:2]
                center_x, center_y = frame_w // 2, frame_h // 2

                # Select contour closest to the frame center
                def contour_distance_sq(cnt):
                    M = cv.moments(cnt)
                    if M["m00"] == 0 or M["m10"] == 0 or M["m01"] == 0:
                        return float("inf")  # Skip empty contours
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx - center_x)**2 + (cy - center_y)**2

                closest_contour = min(contours, key=contour_distance_sq)
                M = cv.moments(closest_contour)

                if M["m00"] == 0 or M["m10"] == 0 or M["m01"] == 0:
                    continue

                cX_frame = int(M["m10"] / M["m00"])
                cY_frame = int(M["m01"] / M["m00"])

                # Convert to screen coordinates
                cX = cX_frame + self.monitor["left"]
                cY = cY_frame + self.monitor["top"]

                if self.debug_mode:
                    debug_frame = frame.copy()
                    cv.drawContours(
                        debug_frame, [closest_contour], -1, (0, 255, 0), 2)
                    cv.circle(debug_frame, (cX_frame, cY_frame),
                              5, (0, 0, 255), -1)
                    cv.putText(debug_frame, f"Target: ({cX_frame},{cY_frame})",
                               (cX_frame + 10, cY_frame - 10),
                               cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    cv.imshow("Target Tracking", debug_frame)
                    cv.waitKey(1)

                dX = cX - self.PrevX
                dY = cY - self.PrevY
                self.VelX = (self.config.sensitivity.smoothness * self.VelX) + \
                            ((1 - self.config.sensitivity.smoothness) * dX)
                self.VelY = (self.config.sensitivity.smoothness * self.VelY) + \
                            ((1 - self.config.sensitivity.smoothness) * dY)

                PredX = cX + self.config.offset.x + self.VelX * self.config.aimbot.lead_factor
                PredY = cY + self.config.offset.y + self.VelY * self.config.aimbot.lead_factor

                dist = math.hypot(PredX - mouse_X, PredY - mouse_Y)
                sens = self.config.sensitivity.min_sensitivity + (dist / self.config.general.fov) * (
                    self.config.sensitivity.max_sensitivity - self.config.sensitivity.min_sensitivity)
                sens = max(self.config.sensitivity.min_sensitivity,
                           min(sens, self.config.sensitivity.max_sensitivity))

                moveX = math.ceil((PredX - mouse_X) / sens)
                moveY = math.ceil((PredY - mouse_Y) / sens)

                move_mouse_relative(moveX, moveY)
                self.PrevX = cX
                self.PrevY = cY
            else:
                self.PrevX = 0
                self.PrevY = 0

    def run(self) -> None:
        print(f"[STARTUP] Aimbot enabled: {self.config.aimbot.enabled}")
        print(f"[STARTUP] Target window: '{self.config.general.target_win}'")
        print(
            f"[STARTUP] Target color: RGB{self.color} (tolerance: {self.config.aimbot.tolerance})")
        print(
            f"[STARTUP] Press F1 to exit, F2 to toggle aimbot, F3 to toggle debug view\n")

        thread1 = Thread(target=self.capture_thread)
        thread2 = Thread(target=self.detect_thread)

        thread1.start()
        thread2.start()

        while True:
            if GetAsyncKeyState(VK_F1):
                print("\n[EXIT] F1 pressed, shutting down...")
                self.exit.clear()
                break
            if GetAsyncKeyState(VK_F2):
                self.config.aimbot.enabled = not (self.config.aimbot.enabled)
                print(
                    f"[TOGGLE] Aimbot {'ENABLED' if self.config.aimbot.enabled else 'DISABLED'}")
                sleep(0.2)  # Debounce to prevent multiple toggles
            if GetAsyncKeyState(VK_F3):
                self.debug_mode = not self.debug_mode
                print(
                    f"[DEBUG] Debug view {'ENABLED' if self.debug_mode else 'DISABLED'}")
                if not self.debug_mode:
                    cv.destroyAllWindows()
                sleep(0.2)  # Debounce to prevent multiple toggles
            sleep(0.15)

        cv.destroyAllWindows()  # Clean up windows on exit
        thread1.join()
        thread2.join()
