# Feature Requirements: Advanced Automation

**Created:** 2026-02-04
**Purpose:** Requirements for implementing 4 new features using OpenCV (referenced from Umaplay project)
**Priority:** Medium - Enhancement features

---

## Overview

Implement 4 advanced automation features adapted from the Umaplay project, using **OpenCV template matching and color detection** instead of YOLO to keep the application lightweight and compatible with low-spec machines.

### Features to Implement
1. **Shop Preferences** - Auto-purchase items from shop
2. **Skills to Buy** - Auto-purchase skills based on priority list
3. **Race Scheduler** - Enhanced race filtering and scheduling
4. **Junior Style Selection** - Auto-select style at debut

---

## 1. Shop Preferences

### Purpose
Automatically detect when shop is available and purchase preferred items.

### Detection Method (OpenCV)
```python
# Template matching for shop button/icon
def detect_shop_available(screen):
    template = cv2.imread('assets/buttons/shop_button.png')
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    return np.max(result) > 0.8

# Color detection for exchange button (orange/yellow)
def detect_exchange_button(screen):
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    lower_orange = np.array([10, 100, 100])
    upper_orange = np.array([25, 255, 255])
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    # Find contours and return button location
```

### Required Assets
- `assets/buttons/shop_button.png` - Shop button template
- `assets/buttons/shop_exchange.png` - Exchange button template
- `assets/shop/` - Shop item templates (create directory)
  - Item icons for each purchasable item

### UI Requirements
- Add "Shop Preferences" section in Strategy Tab or new tab
- Checkbox: "Auto-purchase from shop"
- Listbox: Selectable shop items with priority order
- Checkbox: "Stop if shop available" (already exists in Team Trials)

### Implementation Files
| File | Changes |
|------|---------|
| `core/shop_handler.py` | NEW - Shop detection and purchase logic |
| `gui/tabs/strategy_tab.py` | Add shop preferences UI section |
| `assets/shop/` | NEW - Shop item templates |
| `bot_settings.json` | Add shop_preferences settings |

### Integration Points
- Call from `career_lobby()` when shop is detected
- Add shop detection to screen state detection in `core/state.py`
- Follow existing handler pattern with dependency injection

---

## 2. Skills to Buy

### Purpose
Automatically purchase skills from skill menu based on priority list.

### Detection Method (OpenCV)
```python
# Detect skill menu screen
def detect_skill_screen(screen):
    # Template match skill menu header/icon
    template = cv2.imread('assets/buttons/skill_menu.png')
    return cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)

# OCR for skill names + fuzzy matching
def extract_skill_names(screen, skill_region):
    roi = screen[y1:y2, x1:x2]
    text = pytesseract.image_to_string(roi, lang='jpn')
    return fuzzy_match_skills(text, skill_database)

# Detect buy button (green button)
def detect_skill_buy_button(screen):
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 100, 100])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    # Find button-shaped contours
```

### Required Assets
- `assets/buttons/skill_menu.png` - Skill menu button template
- `assets/buttons/skill_buy.png` - Skill buy button template
- `assets/skills/skill_database.json` - Skill name database for fuzzy matching

### UI Requirements
- Add "Skills to Buy" section in Event Choice Tab or new tab
- Listbox: Priority-ordered skill list
- Add/Remove buttons for skill management
- Checkbox: "Auto-buy skills"
- Number input: "Max skill points to spend"

### Implementation Files
| File | Changes |
|------|---------|
| `core/skill_handler.py` | NEW - Skill detection and purchase logic |
| `gui/tabs/event_choice_tab.py` | Add skills to buy UI section |
| `assets/skills/skill_database.json` | NEW - Skill name database |
| `bot_settings.json` | Add skill_preferences settings |

### Fuzzy Matching Implementation
```python
from difflib import SequenceMatcher

def fuzzy_match_skill(detected_name, skill_database, threshold=0.85):
    best_match = None
    best_ratio = 0

    for skill in skill_database:
        ratio = SequenceMatcher(None, detected_name, skill).ratio()
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = skill

    return best_match, best_ratio
```

---

## 3. Race Scheduler

### Purpose
Enhanced race filtering with more criteria and auto-scheduling.

### Detection Method (OpenCV)
```python
# Template matching for race grade badges
def detect_race_grade(screen, grade_templates):
    grades = {}
    for grade in ['g1', 'g2', 'g3']:
        template = grade_templates[grade]
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val > 0.75:
            grades[grade] = {'location': max_loc, 'confidence': max_val}
    return grades

# OCR for race name and details
def extract_race_info(screen, race_region):
    roi = screen[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(binary, lang='jpn+eng')
    return parse_race_text(text)
```

### Required Assets
- `assets/buttons/race_g1.png` - G1 badge template
- `assets/buttons/race_g2.png` - G2 badge template
- `assets/buttons/race_g3.png` - G3 badge template
- Update `assets/race_list.json` with more race metadata

### UI Requirements (Enhance existing)
- Current filters already exist in Strategy Tab
- Add: "Preferred races" priority list
- Add: "Race value threshold" (fan gain, skill points)
- Add: "Auto-skip low-value races" checkbox

### Implementation Files
| File | Changes |
|------|---------|
| `core/race_handler.py` | Enhance with new filtering logic |
| `core/race_manager.py` | Add race value calculation |
| `gui/tabs/strategy_tab.py` | Enhance race filter UI |
| `assets/race_list.json` | Add race value metadata |

### Enhancement to Existing Code
```python
# In core/race_handler.py - add value-based filtering
def calculate_race_value(race_info, preferences):
    value = 0
    value += race_info.get('fan_gain', 0) * preferences.get('fan_weight', 1.0)
    value += race_info.get('skill_points', 0) * preferences.get('skill_weight', 1.0)

    if race_info['grade'] == 'G1':
        value *= preferences.get('g1_multiplier', 1.5)

    return value
```

---

## 4. Junior Style Selection (Debut)

### Purpose
Automatically select preferred running style at debut screen.

### Detection Method (OpenCV)
```python
# Detect debut/style selection screen
def detect_style_screen(screen):
    # Template match for style selection header
    template = cv2.imread('assets/scenario/style_selection.png')
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    return np.max(result) > 0.8

# Detect style buttons by color
def detect_style_buttons(screen):
    buttons = []
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

    # White/light buttons (unselected options)
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    white_mask = cv2.inRange(hsv, lower_white, upper_white)

    # Green button (confirm)
    lower_green = np.array([35, 100, 100])
    upper_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)

    # Find button contours and classify
    for mask, btn_type in [(white_mask, 'option'), (green_mask, 'confirm')]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            if 2.0 < aspect_ratio < 5.0 and w > 80:
                buttons.append({
                    'type': btn_type,
                    'bbox': (x, y, w, h),
                    'center': (x + w//2, y + h//2)
                })

    return buttons

# OCR to identify style names on buttons
def identify_style(button_region):
    text = pytesseract.image_to_string(button_region, lang='jpn')
    styles = {
        '逃げ': 'nige',      # Front runner
        '先行': 'senkou',    # Stalker
        '差し': 'sashi',     # Mid-pack
        '追込': 'oikomi'     # Closer
    }
    for jp, en in styles.items():
        if jp in text:
            return en
    return None
```

### Required Assets
- `assets/scenario/style_selection.png` - Style selection screen template
- `assets/buttons/style_nige.png` - Front runner button (optional)
- `assets/buttons/style_senkou.png` - Stalker button (optional)
- `assets/buttons/style_sashi.png` - Mid-pack button (optional)
- `assets/buttons/style_oikomi.png` - Closer button (optional)

### UI Requirements
- Add "Debut Style" dropdown in Event Choice Tab or Strategy Tab
- Options: "Front Runner (逃げ)", "Stalker (先行)", "Mid-pack (差し)", "Closer (追込)", "Auto (based on character)"
- Checkbox: "Auto-select style at debut"

### Implementation Files
| File | Changes |
|------|---------|
| `core/style_handler.py` | NEW - Style detection and selection |
| `gui/tabs/event_choice_tab.py` | Add debut style selection UI |
| `core/execute.py` | Integrate style selection into flow |
| `bot_settings.json` | Add debut_style preference |

### Character-Based Auto Selection
```python
# Map Uma Musume to their recommended styles
UMA_STYLE_MAP = {
    'Sakura Bakushin O': 'nige',
    'Silence Suzuka': 'nige',
    'Oguri Cap': 'sashi',
    'Gold Ship': 'oikomi',
    'Special Week': 'sashi',
    # ... more characters
}

def get_recommended_style(uma_name):
    return UMA_STYLE_MAP.get(uma_name, 'senkou')  # Default to stalker
```

---

## Common Utilities

### New Utility Functions (add to `core/cv_utils.py`)
```python
import cv2
import numpy as np

def template_match(screen, template, threshold=0.8):
    """Generic template matching with threshold"""
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    return list(zip(*locations[::-1]))

def color_mask_detect(screen, lower_hsv, upper_hsv, min_area=1000, max_area=10000):
    """Detect regions by HSV color range"""
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    results = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if min_area < area < max_area:
            x, y, w, h = cv2.boundingRect(contour)
            results.append({
                'bbox': (x, y, w, h),
                'center': (x + w//2, y + h//2),
                'area': area
            })
    return results

def preprocess_for_ocr(image, method='otsu'):
    """Preprocess image for better OCR accuracy"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if method == 'otsu':
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == 'adaptive':
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
    else:
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

    return binary
```

---

## Implementation Order (Recommended)

1. **Junior Style Selection** (Simplest)
   - Single screen detection
   - Button color detection + click
   - Minimal UI changes

2. **Race Scheduler Enhancement** (Build on existing)
   - Enhance existing race_handler.py
   - Add value-based filtering
   - UI already partially exists

3. **Shop Preferences** (Medium complexity)
   - New handler needed
   - Multiple screen states
   - Item template management

4. **Skills to Buy** (Most complex)
   - OCR + fuzzy matching
   - Scrolling skill list
   - Complex UI for skill priority

---

## Handler Pattern Template

Follow existing handler pattern:
```python
class NewFeatureHandler:
    """Handler for [Feature Name]"""

    def __init__(self, check_stop_func, check_window_func, log_func):
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func
        self.templates = self._load_templates()

    def _load_templates(self):
        """Load required template images"""
        templates = {}
        # Load templates from assets/
        return templates

    def detect_screen(self, screen):
        """Detect if feature screen is active"""
        # Template matching logic
        pass

    def execute(self, screen, preferences):
        """Execute the feature logic"""
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # Feature logic here
        self.log("Feature action completed")
        return True
```

---

## Settings Schema Addition

Add to `bot_settings.json`:
```json
{
  "shop_preferences": {
    "enabled": false,
    "stop_if_available": false,
    "items": ["item1", "item2"]
  },
  "skill_preferences": {
    "enabled": false,
    "max_points": 100,
    "priority_skills": ["skill1", "skill2"]
  },
  "race_scheduler": {
    "value_threshold": 0,
    "preferred_races": [],
    "skip_low_value": false
  },
  "debut_style": {
    "enabled": true,
    "style": "auto",
    "fallback": "senkou"
  }
}
```

---

## Testing Checklist

For each feature:
- [ ] Template images capture correctly at 1920x1080
- [ ] Color detection works with game's color scheme
- [ ] OCR accuracy meets threshold (>85% for text detection)
- [ ] Handler integrates with existing bot flow
- [ ] Settings save/load correctly
- [ ] UI displays properly in tabs
- [ ] Stop conditions work correctly

---

## Notes

- **No YOLO dependency** - All detection uses OpenCV template matching and color detection
- **Tesseract/EasyOCR** - Use existing OCR infrastructure
- **Fuzzy matching** - Use `difflib.SequenceMatcher` for text matching
- **Screen resolution** - All coordinates assume 1920x1080
- **Handler pattern** - Follow existing dependency injection pattern
- **Assets** - Create template images from actual game screenshots

---

---

## Assets từ Umaplay có thể sử dụng

**Source:** `D:\Dev\Python\Umaplay-main\Umaplay-main`

### Shop Feature
| Asset | Path | Mô tả |
|-------|------|-------|
| UI Screenshot | `assets/doc/UI-shop.png` | Screenshot shop interface (45 KB) |
| Star Pieces | `web/dist/icons/shop_star_pieces.png` | Icon Star Pieces (43 KB) |
| Parfait | `web/dist/icons/shop_parfait.png` | Icon Parfait (45 KB) |
| Clock | `web/dist/icons/shop_clock.png` | Icon Clock item (49 KB) |
| Test Data | `tests/data/shop/shop_star_pieces.png` | Real shop screenshot (355 KB) |

### Skills Feature
| Asset | Path | Mô tả |
|-------|------|-------|
| Skill Icons | `web/dist/icons/skills/*.png` | 100+ skill icons (23-37 KB each) |
| Skill Database | `datasets/in_game/skills.json` | Full skill name database |
| Skill Matching | `core/utils/skill_matching.py` | Fuzzy matching reference code |

### Race Feature
| Asset | Path | Mô tả |
|-------|------|-------|
| UI Screenshot | `assets/doc/UI-races.png` | Screenshot race interface (92 KB) |
| G1 Badge | `web/dist/badges/G1.png` | G1 badge icon (4.1 KB) |
| G2 Badge | `web/dist/badges/G2.png` | G2 badge icon (5.1 KB) |
| G3 Badge | `web/dist/badges/G3.png` | G3 badge icon (5.7 KB) |
| Race Banners | `web/dist/race/G1/*.png` | 388 race banners by grade |
| Race Database | `datasets/in_game/races.json` | Full race database |

### Style/Scenario Feature
| Asset | Path | Mô tả |
|-------|------|-------|
| Unity Cup Icon | `web/dist/scenarios/unity_cup_icon.png` | Unity Cup scenario (17 KB) |
| URA Icon | `web/dist/scenarios/ura_icon.png` | URA Finale scenario (18 KB) |
| Mood Icons | `web/dist/mood/*.png` | 5 mood states (awful/bad/normal/good/great) |

### Support Card Assets
| Asset | Path | Mô tả |
|-------|------|-------|
| Type Icons | `web/dist/icons/support_card_type_*.png` | SPD/STA/PWR/GUTS/WIT/FRD icons |
| Card Images | `web/dist/events/support/*.png` | 85+ full support card images |
| Training Icons | `web/dist/events/support_icon_training/*.png` | 70+ training icons |

### Copy Commands
```bash
# Copy shop assets
copy "D:\Dev\Uma_Musume\Umaplay\assets\doc\UI-shop.png" "assets\reference\"
copy "D:\Dev\Uma_Musume\Umaplay\web\dist\icons\shop_*.png" "assets\shop\"

# Copy skill icons (selective)
xcopy "D:\Dev\Uma_Musume\Umaplay\web\dist\icons\skills" "assets\skills\icons" /E /I

# Copy race badges
copy "D:\Dev\Uma_Musume\Umaplay\web\dist\badges\G*.png" "assets\buttons\"

# Copy mood icons
xcopy "D:\Dev\Uma_Musume\Umaplay\web\dist\mood" "assets\mood" /E /I

# Copy scenario icons
copy "D:\Dev\Uma_Musume\Umaplay\web\dist\scenarios\*.png" "assets\scenario\"
```

---

**Reference:** Umaplay project at `D:\Dev\Uma_Musume\Umaplay` for detection logic patterns
