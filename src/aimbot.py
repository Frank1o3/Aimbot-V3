"""Module for tracking a specific color in a window."""

# Build in Modules
import math
from threading import Event, Thread
from time import sleep

# Third Party Modules
import cv2 as cv
import numpy as np
from mss import mss
from win32api import GetAsyncKeyState
from win32con import VK_F1, VK_F2, VK_F3, VK_F4

# Custom Made Modules
from config import Config
from mouse import get_mouse_position, move_mouse_relative, move_mouse_to
from utils import get_client_rect, get_window_hwnd


class Tracker:
    """Class for tracking a specific color in a window."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.alternate_move = False
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

        self.frame: cv.typing.MatLike = np.zeros((1, 1), dtype=np.uint8)

        # pre set the client_rect
        self.monitor = {"top": 0, "left": 0, "bottom": 0, "right": 0}
        self.PrevX = 0.0
        self.PrevY = 0.0
        self.VelX = 0.0
        self.VelY = 0.0
        self.exit = Event()
        self.exit.set()
        self.fov = max(self.config.general.fov, 320)
        self.fov_half = self.fov // 2

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

            self.monitor = {
                "top": max(y, center_y - self.fov_half),
                "left": max(x, center_x - self.fov_half),
                "width": min(x + width, center_x + self.fov_half)
                - max(x, center_x - self.fov_half),
                "height": min(y + height, center_y + self.fov_half)
                - max(y, center_y - self.fov_half),
            }

            screenshot = sct.grab(self.monitor)

            img = np.array(screenshot)
            img = cv.cvtColor(img, cv.COLOR_BGRA2BGR)
            frame = np.ascontiguousarray(img)
            self.frame = cv.inRange(
                frame, self.lower_bound, self.upper_bound).astype(np.uint8)

    def contour_score(self, center_x: int, center_y: int, cnt: cv.typing.MatLike):
        area = cv.contourArea(cnt)
        if not (self.config.aimbot.min_area < area < self.config.aimbot.max_area):
            return float("inf")
        M = cv.moments(cnt)
        if M["m00"] == 0:
            return float("inf")
        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]
        dist_sq = (cx - center_x)**2 + (cy - center_y)**2
        return dist_sq / (area + 1)  # prioritize larger targets if desired

    def detect_thread(self) -> None:
        """Continuously detects the target color in the captured frames."""
        while self.exit.is_set():
            mouse_X, mouse_Y = get_mouse_position()
            frame = self.frame.copy()
            if frame.size == 0:
                continue

            contours, _ = cv.findContours(
                frame, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

            if contours and self.monitor and self.config.aimbot.enabled:
                frame_h, frame_w = frame.shape[:2]
                center_x, center_y = frame_w // 2, frame_h // 2

                # Select contour closest to the frame center
                # fix: pass center coords to the key function via a lambda
                closest_contour = min(
                    contours, key=lambda cnt: self.contour_score(
                        center_x, center_y, cnt)
                )
                M = cv.moments(closest_contour)

                if M["m00"] == 0:
                    continue

                cX_frame = int(M["m10"] / M["m00"])
                cY_frame = int(M["m01"] / M["m00"])

                # Convert to screen coordinates
                cX = cX_frame + self.monitor["left"]
                cY = cY_frame + self.monitor["top"]

                if self.config.general.debug_mode:
                    cv.drawContours(
                        frame, [closest_contour], -1, (0, 255, 0), 2)
                    cv.circle(frame, (cX_frame, cY_frame),
                              5, (0, 0, 255), -1)
                    cv.putText(frame, f"Target: ({cX_frame},{cY_frame})",
                               (cX_frame + 10, cY_frame - 10),
                               cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    cv.imshow("Target Tracking", frame)
                    cv.waitKey(1)
                else:
                    sleep(0.01)

                dX = cX - self.PrevX
                dY = cY - self.PrevY
                self.VelX = (self.config.sensitivity.smoothness * self.VelX) + \
                            ((1 - self.config.sensitivity.smoothness) * dX)
                self.VelY = (self.config.sensitivity.smoothness * self.VelY) + \
                            ((1 - self.config.sensitivity.smoothness) * dY)

                PredX = cX + self.config.offset.x + self.VelX * self.config.aimbot.lead_factor
                PredY = cY + self.config.offset.y + self.VelY * self.config.aimbot.lead_factor
                if not self.alternate_move:
                    dist = math.hypot(PredX - mouse_X, PredY - mouse_Y)
                    sens = self.config.sensitivity.min_sensitivity + (dist / self.fov) * (
                        self.config.sensitivity.max_sensitivity - self.config.sensitivity.min_sensitivity)
                    sens = max(self.config.sensitivity.min_sensitivity,
                            min(sens, self.config.sensitivity.max_sensitivity))

                    moveX = math.ceil((PredX - mouse_X) / sens)
                    moveY = math.ceil((PredY - mouse_Y) / sens)

                    move_mouse_relative(moveX, moveY)
                    self.PrevX = cX
                    self.PrevY = cY
                else:
                    move_mouse_to(math.ceil(PredX), math.ceil(PredY))
            else:
                self.PrevX = 0
                self.PrevY = 0

    def run(self) -> None:
        print(f"[STARTUP] Aimbot enabled: {self.config.aimbot.enabled}")
        print(f"[STARTUP] Target window: '{self.config.general.target_win}'")
        print(
            f"[STARTUP] Target color: RGB{self.color} (tolerance: {self.config.aimbot.tolerance})")
        print(
            f"[STARTUP] Press F1 to exit, F2 to enable the aimbot, F3 to toggle debug view, F4 To set Alternate move\n")

        thread1 = Thread(target=self.capture_thread)
        thread2 = Thread(target=self.detect_thread)

        thread1.start()
        thread2.start()

        while True:
            if GetAsyncKeyState(VK_F1):
                print("\n[EXIT] F1 pressed, shutting down...")
                self.exit.clear()
                break
            elif GetAsyncKeyState(VK_F2):
                self.config.aimbot.enabled = not self.config.aimbot.enabled
                print(f"[DEBUG] Aimbot: {'ENABLED' if self.alternate_move else 'DISABLED'}")
            elif GetAsyncKeyState(VK_F3):
                self.config.general.debug_mode = not self.config.general.debug_mode
                print(
                    f"[DEBUG] Debug view: {'ENABLED' if self.config.general.debug_mode else 'DISABLED'}")
                cv.destroyAllWindows()
            elif GetAsyncKeyState(VK_F4):
                self.alternate_move = not self.alternate_move
                print(f"[DEBUG] Alternate move: {'ENABLED' if self.alternate_move else 'DISABLED'}")
            sleep(0.01)

        cv.destroyAllWindows()  # Clean up windows on exit
        thread1.join()
        thread2.join()
