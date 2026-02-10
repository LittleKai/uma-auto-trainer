# Project Conventions

**Last Updated:** 2026-01-30 09:00

---

## File & Folder Naming

### Files
- **Modules:** `snake_case.py` (e.g., `training_handler.py`, `click_handler.py`)
- **Classes:** One primary class per file, named after file
- **Constants:** `UPPER_CASE` in dedicated modules

### Folders
- Use lowercase, single words where possible
- Nested by feature: `gui/tabs/`, `gui/dialogs/`, `gui/components/`

**Examples:**
```
core/training_handler.py    # Contains TrainingHandler class
gui/tabs/strategy_tab.py    # Contains StrategyTab class
utils/constants.py          # Contains UPPER_CASE constants
assets/event_map/           # JSON event databases
```

---

## Component Structure

### Handler Class Template
```python
import pyautogui
import time
import json
from typing import Dict, Optional, Callable, Any

from core.state import check_support_card, get_current_date_info
from core.click_handler import enhanced_click, random_click_in_region
from utils.constants import MINIMUM_ENERGY_PERCENTAGE


class SomeHandler:
    """Brief description of handler purpose"""

    def __init__(self, check_stop_func: Callable, check_window_func: Callable, log_func: Callable):
        """
        Initialize handler

        Args:
            check_stop_func: Function to check if should stop
            check_window_func: Function to check if game window is active
            log_func: Function to log messages
        """
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func

    def some_operation(self) -> bool:
        """Perform an operation with stop check"""
        if self.check_stop():
            self.log("[STOP] Operation cancelled due to F3 press")
            return False

        # Operation logic here
        return True
```

### GUI Tab Template
```python
import tkinter as tk
from tkinter import ttk


class SomeTab:
    """Tab description"""

    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window

        # Initialize variables
        self.init_variables()

        # Create tab content
        self.create_content()

    def init_variables(self):
        """Initialize tab variables"""
        self.some_var = tk.StringVar(value="default")
        self.some_bool = tk.BooleanVar(value=False)

        self.bind_variable_changes()

    def bind_variable_changes(self):
        """Bind variable change events to auto-save"""
        variables = [self.some_var, self.some_bool]
        for var in variables:
            var.trace_add('write', lambda *args: self.main_window.save_settings())

    def create_content(self):
        """Create tab UI elements"""
        pass
```

---

## Code Style

### Imports Order
```python
# 1. Standard library imports
import time
import json
from typing import Dict, Optional, Callable, Any

# 2. Third-party library imports
import pyautogui
import cv2
import numpy as np
from PIL import Image

# 3. Local application imports - core
from core.state import check_support_card, get_current_date_info
from core.click_handler import enhanced_click

# 4. Local application imports - utils
from utils.constants import MINIMUM_ENERGY_PERCENTAGE
```

### Spacing & Formatting
- **Indentation:** 4 spaces
- **Line length:** ~100 characters (flexible)
- **Quotes:** Double quotes `"string"`
- **Trailing commas:** Yes, in multi-line structures

### Docstrings
```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
    pass
```

---

## TypeScript Conventions

*N/A - This is a Python project*

---

## Python Type Hints

### Type Definitions
- Use `typing` module imports
- Prefer `Optional[X]` over `X | None`
- Use `Callable` for function parameters

**Examples:**
```python
from typing import Dict, Optional, Callable, Any, List, Tuple

def some_func(
    callback: Callable,
    data: Dict[str, Any],
    items: Optional[List[str]] = None
) -> Tuple[bool, str]:
    pass
```

---

## CSS/Styling Conventions

*N/A - This project uses Tkinter native styling*

### Tkinter Patterns
```python
# Use ttk widgets when available
from tkinter import ttk

# Frame organization
frame = ttk.LabelFrame(parent, text="Section Title")
frame.pack(fill="x", padx=5, pady=5)

# Grid layout preferred for forms
label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

# Pack layout for simple stacking
button.pack(side="left", padx=5)
```

---

## Naming Conventions

### Variables
- **Boolean:** Prefix with `is_`, `has_`, `can_`, `should_` or just descriptive
  - `is_pre_debut`, `has_support`, `should_stop`
- **Functions:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Classes:** `PascalCase`

### Functions
- **Event handlers:** `on_` or `handle_` prefix
  - `on_button_click`, `handle_race_finish`
- **Check functions:** `check_` or `is_` prefix
  - `check_stop()`, `is_game_window_active()`
- **Get functions:** `get_` prefix
  - `get_current_date_info()`, `get_stage_thresholds()`
- **Click functions:** Descriptive with `_click` suffix
  - `enhanced_click()`, `random_click_in_region()`

### GUI Variables
- Use Tkinter variable classes
  ```python
  self.some_string = tk.StringVar(value="default")
  self.some_bool = tk.BooleanVar(value=False)
  self.some_int = tk.IntVar(value=0)
  ```

---

## Testing

*No automated tests exist - testing is done manually*

### Manual Testing Checklist
- [ ] Run `python main.py`
- [ ] Verify GUI loads correctly
- [ ] Test F1/F3/F5 keyboard shortcuts
- [ ] Test with actual game window
- [ ] Verify OCR detection accuracy
- [ ] Check log output for errors

---

## Imports & Exports

### Module Structure
- Each module should have clear exports
- Use `__init__.py` for package organization
- Import from package, not file when possible

**Examples:**
```python
# In gui/tabs/__init__.py
from gui.tabs.strategy_tab import StrategyTab
from gui.tabs.event_choice_tab import EventChoiceTab

# Usage
from gui.tabs import StrategyTab, EventChoiceTab
```

---

## Error Handling

### Pattern
```python
try:
    # Risky operation
    result = some_operation()
except SpecificException as e:
    self.log(f"[ERROR] Description: {e}")
    return default_value
except Exception as e:
    # Generic fallback
    print(f"Warning: Unexpected error: {e}")
    return default_value
```

### Logging Format
```python
self.log("[INFO] Informational message")
self.log("[WARNING] Warning message")
self.log("[ERROR] Error message")
self.log("[STOP] Stop condition message")
self.log(f"[{category.upper()}] Message with data: {data}")
```

---

## Avoid / Don't Do

- Don't modify `config.json` scoring values without discussion
- Don't change OCR regions without testing against actual game
- Don't hardcode values that should be configurable
- Don't skip stop checks in long-running operations
- Don't use `time.sleep()` without checking `check_stop()` around it
- Don't mix tab/space indentation
- Don't use bare `except:` - always specify exception type

---

## Best Practices

- Always check `self.check_stop()` in loops and before expensive operations
- Use `enhanced_click()` instead of raw `pyautogui.click()`
- Load config from JSON files, not hardcoded values
- Log meaningful messages with appropriate prefixes
- Use type hints for public method signatures
- Document classes and public methods with docstrings
- Keep handler classes focused on single responsibility
- Use dependency injection pattern (pass functions, not objects)

---

## Configuration Files

### config.json (Developer)
- Contains scoring parameters, thresholds
- DO NOT modify without discussion
- Changes require game testing

### bot_settings.json (User)
- Auto-generated by GUI
- User preferences, presets, filters
- Safe to modify programmatically

### region_settings.json (User-tunable)
- OCR region coordinates
- Can be adjusted by users for their setup
- Test changes with `region_settings.py`

---

**NOTE:** These conventions are derived from existing code patterns. When in doubt, follow the pattern of similar existing files.
