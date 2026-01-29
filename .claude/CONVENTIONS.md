# Project Conventions

## File Naming

### Python Files
- **Modules:** `snake_case.py` (e.g., `main_window.py`, `event_handler.py`)
- **Entry point:** `main.py`
- **Config files:** `snake_case.json` (e.g., `config.json`, `bot_settings.json`)

### Directories
- **Lowercase with underscores:** `core/`, `gui/`, `utils/`, `assets/`
- **Nested structure:** `gui/tabs/`, `gui/dialogs/`, `gui/components/`

### Assets
- **Buttons:** `{name}_btn.png` (e.g., `training_btn.png`, `next_btn.png`)
- **Icons:** `{category}_{name}.png` (e.g., `train_spd.png`, `support_card_type_wit.png`)
- **Data files:** `{name}.json` or `{name}.csv`

---

## Component Structure

### Handler Classes (core/)
```python
class SomeHandler:
    """Handler for specific game action"""

    def __init__(self, check_stop_func, check_window_func, log_func):
        """Initialize with callback functions"""
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func

    def execute_action(self, *args):
        """Main action method"""
        if self.check_stop():
            return False
        # ... implementation
```

### GUI Classes (gui/)
```python
class SomeComponent:
    """GUI component description"""

    def __init__(self, parent, main_app, row=0):
        """Initialize with parent frame and main app reference"""
        self.parent = parent
        self.main_app = main_app
        self.setup_gui(row)

    def setup_gui(self, row):
        """Setup GUI elements"""
        # ... tkinter widgets
```

### Tab Classes (gui/tabs/)
```python
class SomeTab:
    """Tab for specific functionality"""

    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.init_variables()
        self.create_widgets()

    def init_variables(self):
        """Initialize tkinter variables"""
        self.some_var = tk.StringVar(value="default")

    def create_widgets(self):
        """Create tab widgets"""
        # ... tkinter widgets

    def get_settings(self) -> dict:
        """Return current settings"""
        return {"key": self.some_var.get()}

    def load_settings(self, settings: dict):
        """Load settings from dict"""
        self.some_var.set(settings.get("key", "default"))
```

---

## Code Style

### Imports Order
```python
# 1. Standard library
import re
import json
import time
from typing import Dict, Optional, Callable

# 2. Third-party libraries
import pyautogui
import numpy as np
from PIL import Image
import cv2

# 3. Local imports (relative)
from core.state import check_mood, check_turn
from utils.constants import MOOD_REGION, TURN_REGION
```

### Naming Conventions
- **Classes:** `PascalCase` (e.g., `BotController`, `TrainingHandler`)
- **Functions:** `snake_case` (e.g., `check_mood()`, `get_current_date_info()`)
- **Variables:** `snake_case` (e.g., `energy_percentage`, `current_state`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MOOD_REGION`, `MAX_CAREER_LOBBY_ATTEMPTS`)
- **Private/Internal:** `_prefix` (e.g., `_support_card_state`, `_initialize_regions()`)

### Docstrings
```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
```

### Type Hints
- Use type hints for function signatures
- Import from `typing` module for complex types
```python
from typing import Dict, Optional, Callable, Any, List, Tuple

def process_data(data: Dict[str, Any], callback: Optional[Callable[[str], None]] = None) -> List[str]:
    ...
```

---

## Constants Pattern

### Region Definitions (utils/constants.py)
```python
# Format: (x, y, width, height) for regions
MOOD_REGION = (700, 123, 120, 27)

# Format: (x1, y1, x2, y2) for lines/bars
ENERGY_BAR = (440, 136, 705, 136)

# Nested regions
STAT_REGIONS = {
    "spd": (310, 723, 55, 20),
    "sta": (405, 723, 55, 20),
    # ...
}
```

### Asset Path Definitions
```python
# Base directories
ASSETS_DIR = "assets"
ICONS_DIR = f"{ASSETS_DIR}/icons"
BUTTONS_DIR = f"{ASSETS_DIR}/buttons"

# Specific assets
TRAINING_BUTTON = f"{BUTTONS_DIR}/training_btn.png"
SUPPORT_SPD_ICON = f"{ICONS_DIR}/support_card_type_spd.png"
```

### Mappings
```python
# Icon mappings
TRAINING_ICONS = {
    "spd": TRAIN_SPD_ICON,
    "sta": TRAIN_STA_ICON,
    # ...
}

# List constants
TRAINING_TYPES = ["spd", "sta", "pwr", "guts", "wit"]
MOOD_LIST = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT", "UNKNOWN"]
```

---

## Error Handling

### Pattern
```python
def some_function():
    try:
        # Main logic
        result = risky_operation()
        return result
    except SpecificException as e:
        self.log(f"[ERROR] Specific error: {e}")
        return fallback_value
    except Exception as e:
        self.log(f"[ERROR] Unexpected error in some_function: {e}")
        return safe_default
```

### Logging Format
```python
# Info messages
self.log(f"[INFO] Starting training on {training_type}")

# Warning messages
self.log(f"[WARNING] Config file not found, using defaults")

# Error messages
self.log(f"[ERROR] Failed to detect game window: {error}")

# Debug messages (print only, not GUI log)
print(f"DEBUG: OCR result = {text}")
```

---

## Configuration Files

### config.json (Developer Settings)
```json
{
  "priority_stat": ["spd", "pwr", "sta", "wit", "guts"],
  "minimum_energy_percentage": 43,
  "critical_energy_percentage": 20,
  "stat_caps": {
    "spd": 1130,
    "sta": 1100
  },
  "scoring_config": {
    "hint_score": {
      "early_stage": 1.0,
      "late_stage": 0.75,
      "day_threshold": 24
    }
  }
}
```

### bot_settings.json (User Settings)
```json
{
  "scenario": "URA Final",
  "race_filters": {
    "track_types": ["turf"],
    "distances": ["mile", "medium"],
    "grades": ["G1", "G2"]
  },
  "stop_conditions": {
    "on_infirmary": true,
    "on_low_mood": false,
    "target_month": null
  },
  "presets": {
    "set_1": {
      "name": "Speed Build",
      "uma_musume": "Special Week",
      "support_cards": ["card1", "card2"]
    }
  }
}
```

---

## GUI Conventions

### Tkinter Variable Naming
```python
# StringVar for text inputs
self.uma_musume_var = tk.StringVar(value="")

# BooleanVar for checkboxes
self.auto_event_var = tk.BooleanVar(value=True)

# IntVar for numeric inputs
self.min_mood_var = tk.IntVar(value=3)
```

### Widget Creation
```python
# Labels
ttk.Label(parent, text="Label Text:").grid(row=0, column=0, sticky=tk.W)

# Entry/Input
ttk.Entry(parent, textvariable=self.some_var, width=20).grid(row=0, column=1)

# Buttons
ttk.Button(parent, text="Action", command=self.on_action).grid(row=0, column=2)

# Checkboxes
ttk.Checkbutton(parent, text="Option", variable=self.bool_var).grid(row=1, column=0)
```

### Grid Layout
- Use `sticky` parameter for alignment
- Use `padx` and `pady` for spacing
- Use `columnspan` for spanning multiple columns
```python
widget.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5, columnspan=2)
```

---

## Testing

### No Formal Test Framework
- Currently no automated tests
- Manual testing through GUI
- Print statements for debugging

### Debug Patterns
```python
# Temporary debug prints
print(f"DEBUG: value = {value}")

# Conditional debugging
if DEBUG_MODE:
    print(f"State: {current_state}")
```

---

## Git Commit Messages

### Format
```
<type>: <short description>

<optional body with details>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `style`: Code style/formatting
- `chore`: Build/config changes

### Examples
```
feat: add Unity Cup support
fix: OCR detection for mood region
refactor: extract event handler to separate module
```
