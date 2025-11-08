from typing import Optional, Tuple

import win32con
import win32gui

# Constants for better readability
RECT = Tuple[int, int, int, int] # (left, top, right, bottom)
CLIENT_RECT = Tuple[int, int, int, int] # (x, y, width, height)

def get_window_hwnd(window_title: str) -> Optional[int]:
    """Get the handle of the window with the specified title."""
    # FindWindow returns 0 if no window is found
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd == 0:
        return None
    return hwnd

def get_client_rect(hwnd: int) -> Optional[CLIENT_RECT]:
    """
    Gets the size and position of the window's client area (inner content) 
    in screen coordinates (x, y, width, height).
    Returns None if the window is minimized or not visible.
    """
    
    # 1. Check if the window is visible and not minimized/cloaked
    # This helps avoid trying to capture non-existent or minimized areas
    if not win32gui.IsWindowVisible(hwnd):
        return None

    # Optional but good check for minimized or cloaked windows (e.g., UWP apps)
    # GetWindowLong returns the style, then check the minimize bit
    if win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE) & win32con.WS_MINIMIZE: # type: ignore
        return None

    # 2. Get the client area rectangle in *window-relative* coordinates (0, 0, width, height)
    # The rect is (left, top, right, bottom) relative to the client area's top-left corner
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    
    # Calculate width and height
    width = right - left
    height = bottom - top
    
    # 3. Convert the client area's (left, top) point to *screen* coordinates
    # This gives us the correct top-left corner of the content on the screen.
    screen_point = win32gui.ClientToScreen(hwnd, (left, top))
    screen_x, screen_y = screen_point
    
    # The final screenshot area is (x_on_screen, y_on_screen, width, height)
    return (screen_x, screen_y, width, height)
