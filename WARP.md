# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Aimbot-V3 is a Python-based computer vision application that tracks specific colors in Windows application windows. It uses OpenCV for image processing, MSS for screen capture, and win32api for window management and mouse control.

**Core Functionality Flow:**
1. `config.py` loads settings from `config.yml` (target window, color, FOV, sensitivity)
2. `tracker.py` runs two concurrent threads:
   - **Capture thread**: Continuously screenshots the target window's client area
   - **Detection thread**: Processes frames to find colored targets, calculates velocity prediction, and moves the mouse
3. `utils.py` handles Windows-specific window management (HWND retrieval, client rect calculations)
4. `mouse.py` provides low-level mouse control via win32api

## Development Commands

### Environment Setup
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```powershell
# From the src directory
python src/main.py

# Or from project root
python -m src.main
```

**Runtime Controls:**
- Press `F1` to exit the application
- Press `F2` to toggle aimbot on/off

### Code Quality

**Linting:**
```powershell
# Lint all Python files
pylint src/*.py

# Lint specific file
pylint src/tracker.py
```

**Type Checking:**
```powershell
# Type check all source files
mypy src/
```

**Code Formatting:**
```powershell
# Sort imports
isort src/*.py
```

## Architecture Notes

### Configuration System
- `config.yml` is loaded via a typed configuration system with validation
- `ColorHex` class handles 24-bit RGB hex colors (0xRRGGBB format) and provides `.r`, `.g`, `.b` properties
- Configuration is organized into sections: `general`, `aimbot`, `offset`, `sensitivity`
- Type hints are used to convert YAML values to proper Python types during loading

### Threading Model
The `Tracker` class uses two independent threads that communicate via a shared numpy array (`self.frame`):
- **Capture thread** (`capture_thread`): Grabs screenshots from the target window's FOV region using MSS
- **Detection thread** (`detect_thread`): Uses OpenCV color masking and contour detection to find targets

Both threads run until `self.exit` Event is cleared. This is NOT a producer-consumer pattern with a queue—both threads run at maximum speed with the detection thread reading whatever frame is currently available.

### Target Tracking Algorithm
1. Create color mask using `cv.inRange()` with tolerance-adjusted bounds
2. Find contours in mask, select largest by area
3. Calculate centroid using OpenCV moments
4. Apply velocity smoothing with exponential moving average
5. Predict future position using lead factor: `Pred = Current + Offset + Velocity × LeadFactor`
6. Calculate dynamic sensitivity based on distance to target
7. Move mouse using relative coordinates via win32 API

### Windows-Specific Considerations
- **Window handling**: Uses `win32gui` to get HWND and client rect. Handles minimized/invisible windows gracefully
- **Screen capture**: MSS library captures the client area (excludes title bar and borders)
- **Mouse control**: `mouse_event` with `MOUSEEVENTF_MOVE` for relative movement (not absolute positioning)
- **Keyboard input**: `GetAsyncKeyState` polls F1/F2 without blocking

### FOV Calculation
The FOV setting reduces the capture area symmetrically from all sides:
- Capture starts at `(x + fov//2, y + fov//2)`
- Size is reduced by `fov//2` on width and height
- Target centroid coordinates are adjusted back to screen space

## Configuration Parameters

**Key config.yml settings:**
- `general.target_win`: Exact window title to track (e.g., "Roblox")
- `general.fov`: Field of view reduction in pixels (smaller = faster but less coverage)
- `general.color`: Target color in hex format (0xRRGGBB)
- `aimbot.tolerance`: Color matching tolerance (higher = more lenient matching)
- `aimbot.lead_factor`: Velocity prediction multiplier for moving targets
- `offset.x/y`: Static pixel offset applied to target centroid
- `sensitivity.smoothness`: Velocity smoothing factor (0-1, higher = smoother but slower response)

## Common Development Patterns

### Adding New Configuration Options
1. Add field to appropriate config class in `config.py` with type hint and default value
2. Update `config.yml` with the new setting
3. The `Config.load()` method will automatically validate and convert the type

### Modifying Detection Logic
All color detection happens in `tracker.py`'s `detect_thread()` method. Key points:
- Color bounds are precomputed in `__init__` for performance
- Centroid calculations use OpenCV moments (M["m10"]/M["m00"] for x-coordinate)
- Velocity tracking uses exponential moving average: `new_vel = smooth × old_vel + (1-smooth) × delta`

### Working with Windows API
- Always check if HWND is valid before operations
- `GetClientRect` returns window-relative coordinates; use `ClientToScreen` to convert
- Mouse movements are in "mickeys" (relative units), not pixels
