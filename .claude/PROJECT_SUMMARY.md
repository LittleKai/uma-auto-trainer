# Project Summary

**Last Updated:** 2026-02-19 12:00
**Updated By:** Claude Code

---

## 1. Project Overview

- **Name:** Uma Musume Auto Train
- **Type:** Windows Desktop Automation Tool
- **Purpose:** Automate character training in "Uma Musume: Pretty Derby" game
- **Developer:** LittleKai
- **Tech Stack:** Python 3.x, Tkinter, OpenCV, Tesseract/EasyOCR, PyAutoGUI
- **Package Manager:** pip (requirements.txt)
- **i18n:** None (Japanese game content, English UI)
- **State Management:** Module-level globals + class instances
- **Styling:** Tkinter native (ttk)
- **Deployment:** PyInstaller executable

**Requirements:**
- Windows 10/11 64-bit
- 1920x1080 screen resolution
- Tesseract OCR installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`

---

## 2. File Structure

### Key Directories
```
uma-auto-trainer/
├── core/                    # Bot logic, OCR, state detection, handlers
│   ├── execute.py           # Main BotController orchestration
│   ├── state.py             # Game state detection via OCR
│   ├── ocr.py               # OCR pipeline (Tesseract + EasyOCR)
│   ├── logic.py             # Training scoring algorithm
│   ├── recognizer.py        # Template matching & image recognition
│   ├── click_handler.py     # Click operations with randomization
│   ├── race_manager.py      # Race scheduling and date management
│   ├── execute_helpers.py   # EventHandler, CareerLobbyManager helpers
│   ├── training_handler.py  # Training selection and execution
│   ├── race_handler.py      # Race navigation and filtering
│   ├── rest_handler.py      # Rest/recreation operations
│   ├── event_handler.py     # Event choice automation
│   └── updater.py           # Auto-update via GitHub Releases
│
├── gui/                     # Tkinter GUI interface
│   ├── main_window.py       # Main application window (UmaAutoGUI)
│   ├── bot_controller.py    # Bot control (keyboard shortcuts, threading)
│   ├── window_manager.py    # Window settings and file I/O
│   ├── tabs/                # Tabbed interface components
│   │   ├── strategy_tab.py      # Race filters, stop conditions
│   │   ├── event_choice_tab.py  # Event automation, 20 presets
│   │   ├── team_trials_tab.py   # Team Trials (PvP) automation
│   │   └── team_trials_logic.py # Team Trials battle logic
│   ├── dialogs/             # Dialog windows
│   │   ├── support_card_dialog.py
│   │   ├── preset_dialog.py
│   │   ├── stop_conditions_dialog.py
│   │   ├── uma_musume_dialog.py
│   │   ├── config_dialog.py
│   │   ├── update_dialog.py
│   │   ├── event_update_dialog.py
│   │   └── check_update_dialog.py
│   ├── components/          # GUI components
│   │   ├── status_section.py    # Status display panel
│   │   └── log_section.py       # Scrollable log output
│   └── utils/
│       └── game_window_monitor.py  # Game window detection
│
├── utils/                   # Utility modules
│   ├── constants.py         # Global constants and configuration
│   ├── constants_support.py # Mood patterns and OCR config
│   └── screenshot.py        # Screenshot capture functions
│
├── assets/                  # Game assets
│   ├── buttons/             # Button templates (PNG)
│   ├── icons/               # Support card and training icons
│   ├── skills/              # Skill icons
│   ├── scenario/            # Scenario buttons
│   ├── support_cards/       # Support card images
│   ├── event_map/           # Event databases (JSON)
│   │   ├── common.json
│   │   ├── other_sp_event.json
│   │   ├── uma_musume/      # 30+ character event maps
│   │   └── support_card/    # Support card events (spd/sta/pwr/guts/wit/frd)
│   └── race_list.json       # Race database
│
├── main.py                  # Entry point
├── version.py               # Version constant (APP_VERSION, GITHUB_REPO)
├── build_exe.py             # PyInstaller build script
├── key_validator.py         # License key validation
├── region_settings.py       # OCR region tuning utility
├── config.json              # Scoring parameters (developer)
├── bot_settings.json        # User preferences (auto-generated)
├── region_settings.json     # OCR coordinates (user-tunable)
└── requirements.txt         # Python dependencies
```

### Critical Files
| File | Purpose | Notes |
|------|---------|-------|
| `main.py` | Entry point | Launches UmaAutoGUI |
| `core/execute.py` | Bot orchestration | BotController class |
| `core/state.py` | State detection | Module-level globals |
| `core/logic.py` | Scoring algorithm | Load from config.json |
| `gui/main_window.py` | Main GUI | UmaAutoGUI class |
| `config.json` | Dev config | DO NOT modify casually |
| `bot_settings.json` | User settings | Auto-generated |
| `region_settings.json` | OCR regions | User-tunable |

---

## 3. Architecture & Patterns

### Entry Flow
```
main.py → UmaAutoGUI.__init__() → BotController → GUI Setup
                                       ↓
                           F1 → career_lobby() → Main Loop
```

### Handler Pattern
All handlers use dependency injection:
```python
class XyzHandler:
    def __init__(self, check_stop_func, check_window_func, log_func):
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func
```

**Handlers:**
- `TrainingHandler` - Training selection and execution
- `RaceHandler` - Race navigation and filtering
- `RestHandler` - Rest/recreation actions
- `EventChoiceHandler` - Event database lookup and automation

### State Management
- **Module-level globals** in `core/state.py`:
  - `current_date_info` - Cached date information
  - `_support_card_state` - Support card detection state
- Thread-safe for read operations

### OCR Pipeline
```
Screen Region → MSS Capture → Preprocessing → Tesseract → EasyOCR (fallback)
```

### Configuration Hierarchy
1. `config.json` - Hard-coded dev parameters
2. `bot_settings.json` - User overrides
3. `region_settings.json` - OCR coordinate tuning
4. `utils/constants.py` - Runtime defaults

### Scoring Algorithm
```
score = base_score × stage_multiplier
      + hint_bonus + npc_bonus + special_training_bonus
      + spirit_explosion_bonus
      + friend_multiplier + rainbow_multiplier
      - energy_penalty + wit_early_stage_bonus
```

**Stage Thresholds:**
- Pre-Debut: day ≤ 16
- Early Stage: day ≤ 24
- Mid Stage: day ≤ 48
- Late Stage: day > 48

### Threading Model
- **Main GUI Thread:** Tkinter event loop
- **Bot Thread:** Background bot execution
- **Game Window Monitor:** Separate monitoring thread
- **Thread-Safe Flags:** `should_stop`, `is_running`

---

## 4. Active Features & Status

| Feature | Status | Files Involved | Notes |
|---------|--------|----------------|-------|
| Training Automation | ✅ Done | `core/training_handler.py`, `core/logic.py` | Score-based selection |
| Race Automation | ✅ Done | `core/race_handler.py`, `core/race_manager.py` | Filter support |
| Rest/Recreation | ✅ Done | `core/rest_handler.py` | Summer rest handling |
| Event Choice | ✅ Done | `core/event_handler.py`, `assets/event_map/` | 30+ characters |
| Support Card Detection | ✅ Done | `core/state.py`, `assets/icons/` | Template matching |
| Stop Conditions | ✅ Done | `gui/dialogs/stop_conditions_dialog.py` | Multiple triggers |
| 20 Presets | ✅ Done | `gui/tabs/event_choice_tab.py` | Save/load support |
| Team Trials | ✅ Done | `gui/tabs/team_trials_tab.py` | PvP automation |
| Legend Race | ✅ Done | `gui/tabs/team_trials_tab.py` | Special handling |
| OCR Region Tuning | ✅ Done | `region_settings.py`, `region_settings.json` | User adjustable |
| Per-Preset Stat Caps | ✅ Done | `gui/tabs/event_choice_tab.py`, `core/logic.py` | Each preset has own stat caps |
| Config Editor | ✅ Done | `gui/dialogs/config_dialog.py`, `gui/main_window.py` | Edit config.json via GUI |
| Global Deck Info | ✅ Done | `utils/constants.py` | Stores deck info globally |
| Deck-Based Events | ✅ Done | `core/event_handler.py` | Event choice based on deck composition |
| Uma Musume Dialog | ✅ Done | `gui/dialogs/uma_musume_dialog.py` | Search-enabled Uma Musume selection |
| Preset Dialog | ✅ Done | `gui/dialogs/preset_dialog.py` | Preset selection with deck summary |
| Auto-Update | ✅ Done | `core/updater.py`, `gui/dialogs/update_dialog.py`, `version.py` | GitHub Releases auto-update |
| Event Map Update | ✅ Done | `core/updater.py`, `gui/dialogs/event_update_dialog.py` | Check/download event maps from GitHub |
| Shop Preferences | ⏳ Planning | `.claude/FEATURE_REQUIREMENTS.md` | Auto-purchase shop items |
| Skills to Buy | ⏳ Planning | `.claude/FEATURE_REQUIREMENTS.md` | Auto-purchase skills |
| Race Scheduler Enhanced | ⏳ Planning | `.claude/FEATURE_REQUIREMENTS.md` | Value-based race filtering |
| Junior Style Selection | 🚧 In Progress | `core/style_handler.py`, `core/race_handler.py`, `gui/tabs/event_choice_tab.py` | Auto-select debut style at pre-debut race day (needs templates) |

**Legend:**
- ⏳ Planning / Not Started
- 🚧 In Progress / Incomplete
- ✅ Completed / Working

---

## 5. Known Issues & TODOs

### High Priority
- [ ] Junior Style Selection: Need template images (see assets/scenario/ and assets/buttons/)

### Medium Priority
- [ ] OCR can fail on non-standard resolutions
- [ ] Event database may need updates for new game content

### Low Priority / Nice to Have
- [ ] Add automated testing
- [ ] Support for additional screen resolutions
- [ ] Multi-language support for UI

---

## 6. Dependencies & External Resources

### Key Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| opencv-python | 4.12.0.88 | Computer vision |
| Pillow | 11.3.0 | Image processing |
| pytesseract | 0.3.10 | Tesseract wrapper |
| easyocr | 1.7.2 | Fallback OCR |
| pyautogui | 0.9.54 | Mouse/keyboard automation |
| mss | 10.0.0 | Screenshot capture |
| keyboard | 0.13.5 | Hotkey handling |
| pygetwindow | 0.0.9 | Window management |
| torch | 2.7.1 | EasyOCR backend |
| numpy | 2.2.6 | Numerical operations |

### External Services
- **Tesseract OCR:** Must be installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`

---

## 7. Recent Changes (Last 5 Sessions)

### 2026-02-19 - Event Map Update & Check Update Dialog
- Added `check_event_updates()` and `download_event_files()` to `core/updater.py`
- Uses GitHub Contents API to compare local event map files with repository via git blob SHA
- Checks directories: uma_musume, support_card/{spd,sta,pow,gut,wit,frd}, and root JSON files
- Created `gui/dialogs/event_update_dialog.py` with EventUpdateDialog (Treeview file list, progress bar)
- Created `gui/dialogs/check_update_dialog.py` with CheckUpdateDialog:
  - Auto-check update toggle (saved to bot_settings.json as `auto_check_update`)
  - "Check Update" button for app version updates
  - "Check Uma Event" button for event map updates
- "Check Update" header button now opens CheckUpdateDialog instead of checking directly
- Startup auto-check respects `auto_check_update` setting in bot_settings.json
- Files created: `gui/dialogs/event_update_dialog.py`, `gui/dialogs/check_update_dialog.py`
- Files modified: `core/updater.py`, `gui/main_window.py`, `gui/dialogs/__init__.py`

### 2026-02-12 - GitHub Release Auto-Update System
- Created `version.py` with APP_VERSION, APP_NAME, GITHUB_REPO constants
- Created `core/updater.py` with check_for_update, download_update, apply_update functions
- Created `gui/dialogs/update_dialog.py` with UpdateDialog class
- Modified `gui/main_window.py`: version in title bar, "Check Update" button, auto-check on startup
- Modified `build_exe.py`: added create_release_zip() to build pipeline
- Updated `gui/dialogs/__init__.py` to export UpdateDialog
- Update flow: auto-check → dialog → download → batch script → restart (preserves user settings)
- Protected files: bot_settings.json, config.json, region_settings.json
- Files created: `version.py`, `core/updater.py`, `gui/dialogs/update_dialog.py`
- Files modified: `gui/main_window.py`, `build_exe.py`, `gui/dialogs/__init__.py`

### 2026-02-12 - Preset Reorder (Move Up/Down) in Preset Dialog
- Added arrow buttons (▲ ▼) on the right side of each preset item for reordering
- Arrows have hover effect (gray → blue) for visual feedback
- Buttons swap all preset data between adjacent positions (name, uma_musume, support_cards, stat_caps, debut_style, stop_conditions)
- Current preset indicator follows the swap correctly
- If presets are reordered and user cancels, changes are still saved
- Scroll follows the moved preset for visual continuity
- Refactored `_select_preset` to use recursive `_set_frame_bg` for deeper widget nesting
- Changed edit pencil icon color from blue (#0066CC) to gray (#888888)
- Files modified: `gui/dialogs/preset_dialog.py`, `gui/tabs/event_choice_tab.py`

### 2026-02-10 - Stat Cap Penalty Hybrid Formula + Day-based Adjustments
- Replaced ratio-based penalty with hybrid formula (% OR absolute gap)
- **Hybrid trigger**: penalty starts when EITHER condition met:
  - Stat reaches 80% of effective cap, OR
  - Stat is within 200 points of effective cap
- **Removed taper**: penalty no longer reduces in last days
- **Day-based effective caps**: base cap adjusted by day
  - Day ≤73: cap - 60
  - Day 74: cap - 45
  - Day 75: cap - 30
- **New default stat caps**: spd=1200, sta=1100, pwr=1200, guts=1200, wit=1200
- Activity log shows effective caps for days 73, 74, 75
- New functions: `get_effective_stat_cap()`, `get_all_effective_stat_caps()`
- Config params: `start_penalty_percent`, `start_penalty_gap`, `day_cap_adjustments`
- Files modified: `core/logic.py`, `config.json`, `utils/constants.py`, `bot_settings.json`

### 2026-02-10 - Fix stat_state() redundant OCR reads
- `stat_state()` was being called up to 7 times per training cycle (once per training type in penalty loop + training_decision + fallback_training), causing ~35 OCR reads for unchanged stats
- Now reads stats only once in `check_all_training()` and passes `current_stats` through the entire call chain
- `check_all_training()` returns `(results, current_stats)` tuple
- `apply_single_training_penalty()`, `training_decision()`, `fallback_training()` accept optional `current_stats` param (fallback to `stat_state()` if None)
- Files modified: `core/training_handler.py`, `core/logic.py`, `core/execute.py`

### 2026-02-10 - DecisionEngine Refactor (Reusable Helpers)
- Extracted 6 helper methods in `DecisionEngine` to eliminate code duplication:
  - `_stopped()`, `_log()`: Short aliases for `check_should_stop()` and `log_message()`
  - `_stop_bot(gui, message)`: Combines logging + GUI stop (replaces 5 occurrences)
  - `_navigate_and_train(key, label)`: Navigate to training + execute + log (replaces 3 occurrences)
  - `_try_race_or_rest(...)`: Try race, fallback to rest (replaces 2 occurrences)
  - `_try_race_or_training_fallback(...)`: Try race, fallback to training flow (replaces 1 occurrence)
- Split `_handle_energy_based_action` (106 lines) into thin dispatcher + `_handle_critical_energy` + `_handle_medium_energy`
- Simplified `_execute_selected_training` to one-liner via `_navigate_and_train`
- No behavioral changes - pure refactoring
- Files modified: `core/execute.py`

### 2026-02-06 - Stat Cap Penalty Rework
- Replaced Algorithm B with percentage-based + time factor approach
- Added cross-training penalty: training X considers secondary stat gains (SPD→PWR 30%, etc.)
  - If both primary and secondary have penalty, only the larger one applies (not cumulative)
- Added `enabled` flag to config with checkbox in config dialog
- Max day changed to 73
- Config params: `enabled`, `max_penalty_percent`, `start_penalty_percent`
- Files modified: `core/logic.py`, `config.json`, `gui/dialogs/config_dialog.py`

### 2026-02-05 10:00 - Style Selection Moved to Race Handler + Click Refactoring
- Moved style selection from `execute_helpers.py` to `race_handler.py`
  - Style selection now triggers in `prepare_race()` before view_results click
  - Condition: Pre-debut race day (`is_pre_debut=True` + style != 'none')
  - Removed StyleHandler from EventHandler (execute_helpers.py)
  - Added StyleHandler to RaceHandler (race_handler.py)
- Refactored `core/race_handler.py` click handling:
  - Replaced all `enhanced_click()` calls with `find_and_click(max_attempts=3, delay_between=2)`
  - `_click_race_buttons_original()` now uses `find_and_click` instead of `pyautogui.locateCenterOnScreen`
  - `prepare_race()`: view_results uses `find_and_click(max_attempts=10, delay_between=2)` for race animation wait
  - `handle_after_race()`: next_btn and next2_btn found with random_screen_click between attempts (max 5)
  - `prepare_race()`: random_screen_click changed from 3 to 5 iterations with 1s delay
- Updated `core/execute.py`:
  - `make_decision()` passes `style_settings` and `is_pre_debut` to `handle_race_day()`
  - Style settings fetched from GUI event_choice_settings when in pre-debut
- Files modified: `core/race_handler.py`, `core/execute_helpers.py`, `core/execute.py`

### 2026-02-04 14:00 - Junior Style Selection Feature Implementation
- Implemented Junior Style Selection feature for auto-selecting running style at debut
- Created `core/style_handler.py` with StyleHandler class
  - Template matching for style selection screen detection
  - Style names: Front, Pace, Late, End (+ None to disable)
  - Style button assets in `assets/buttons/style/` subfolder
  - Position-based fallback selection if templates not found
- Updated `gui/tabs/event_choice_tab.py`:
  - Added debut style dropdown (None, Front, Pace, Late, End)
  - No checkbox needed - None disables the feature
  - Auto-resets to None when Uma Musume selection changes
  - Settings saved to bot_settings.json under `debut_style`
- **PENDING:** Template images need to be created from game screenshots
- Files created: `core/style_handler.py`
- Files modified: `gui/tabs/event_choice_tab.py`, `core/execute_helpers.py`

### 2026-02-04 10:00 - Feature Requirements Document
- Created comprehensive FEATURE_REQUIREMENTS.md for 4 new features
- Features planned: Shop Preferences, Skills to Buy, Race Scheduler Enhanced, Junior Style Selection
- All features use OpenCV (template matching + color detection) instead of YOLO
- Documented detection methods, required assets, UI requirements, implementation files
- Added handler pattern template and common utilities
- Reference: Umaplay project patterns adapted for lightweight implementation
- Files created: `.claude/FEATURE_REQUIREMENTS.md`

### 2026-01-31 17:00 - Stat Cap Penalty System
- Implemented stat cap penalty for reducing training score when stats approach target
- Penalty based on: fill_factor × time_factor × max_penalty, with cross-training awareness
- Max penalty: 40% (configurable), starts at 60% target fill (configurable), toggleable
- Only applies after `stat_cap_threshold_day`
- Functions: `_calculate_single_stat_penalty()`, `apply_stat_cap_penalties()`
- Config parameters: enabled, max_penalty_percent, start_penalty_percent
- Score logging shows penalty info: "score: 2.50 (was 3.50 - Cap penalty: -28.5%)"
- Files modified: `core/logic.py`, `config.json`, `gui/dialogs/config_dialog.py`

### 2026-01-31 16:00 - Config Dialog Auto-fit Height & Help Tooltips
- Config dialog now auto-fits height to content instead of fixed 590px
- Added (?) help icons next to each setting with tooltip explanations
- Created ToolTip class for hover-based help text display
- All settings now have descriptive help texts explaining their purpose
- Files modified: `gui/dialogs/config_dialog.py`

### 2026-01-31 15:30 - Preset Dialog with Summary Info
- Created PresetDialog for selecting presets with deck summary information
- Each preset shows: name (editable), Uma Musume, support cards summary, stat caps
- Preset selection changed from dropdown + edit button to clickable box + dialog
- Removed PresetNameDialog import (rename functionality now in PresetDialog)
- Files modified: `gui/tabs/event_choice_tab.py`
- Files created: `gui/dialogs/preset_dialog.py`

### 2026-01-31 15:00 - Event Choice Mode Moved to Config Dialog
- Moved Event Choice Mode section from Event Choice Tab to Config Dialog
- Event Choice Mode settings now saved to bot_settings.json via Config dialog
- Removed create_mode_selection() method from event_choice_tab.py
- Increased Config dialog height from 550px to 590px
- Created UmaMusumeDialog for selecting Uma Musume with search functionality
- Uma Musume selection changed from combobox to clickable box + dialog
- Files modified: `gui/dialogs/config_dialog.py`, `gui/tabs/event_choice_tab.py`
- Files created: `gui/dialogs/uma_musume_dialog.py`

### 2026-01-31 14:00 - Global Deck Info & Deck-Based Event Conditions
- Added `CURRENT_DECK` global variable in `utils/constants.py` to store deck info
- Functions: `set_deck_info()`, `get_deck_info()`, `get_deck_card_count()`, `deck_has_card_type()`
- Event handler now supports deck-based conditions:
  - `"choice_X_if_deck_has_Y_Z"`: choice X if deck has Y+ cards of type Z
  - Example: `"choice_1_if_deck_has_2_spd"` = choice 1 if deck has 2+ speed cards
- Config dialog priority stat uses horizontal drag-and-drop buttons
- Files modified: `utils/constants.py`, `core/event_handler.py`, `core/logic.py`, `gui/dialogs/config_dialog.py`

### 2026-01-31 12:00 - Stat Caps Per Preset & Config Editor
- Moved `stat_caps` from config.json to per-preset settings in Event Choice tab
- Each preset can now have its own stat cap values (SPD, STA, PWR, GUTS, WIT)
- Created `gui/dialogs/config_dialog.py` - new dialog for editing config.json values
- Added "Config" button next to "Region Settings" in header
- Updated `core/logic.py` with `set_stat_caps()` and `get_stat_caps()` functions
- Files modified: `config.json`, `core/logic.py`, `gui/tabs/event_choice_tab.py`, `gui/main_window.py`
- Files created: `gui/dialogs/config_dialog.py`

### 2026-01-30 09:00 - Initial Documentation Setup
- Created comprehensive documentation system
- Files created: PROJECT_SUMMARY.md, CONVENTIONS.md, history entry, templates
- Full project analysis completed

### Previous (from git history):
- b033e64: fix region setting
- 047c46c: fix g1 train
- 06f8a27: fix g1 train
- b5db34b: updated build exe
- ca76af8: updated build_exe

---

## 8. Important Notes for Claude

### When making changes to:
- **Training logic:** Check `config.json` scoring values, test with actual game
- **OCR regions:** Verify coordinates with `region_settings.py`, test on 1920x1080
- **Event handling:** Update JSON files in `assets/event_map/` if adding characters
- **GUI tabs:** Follow existing tab structure pattern

### Testing checklist:
- [ ] Run `python main.py` and verify GUI loads
- [ ] Test F1/F3/F5 keyboard shortcuts
- [ ] Verify OCR detection on actual game window
- [ ] Check log output for errors

### Don't forget to:
- Update this file's timestamp
- Create history entry
- Follow CONVENTIONS.md

---

## 9. Quick Commands

```bash
# Development
python main.py              # Run application

# Build
python build_exe.py         # Build executable
# Output: dist/Uma_Musume_Auto_Train.exe

# OCR Region Tuning
python region_settings.py   # Launch region tuning utility

# No automated tests available
# Testing is done manually through the GUI
```

---

**CRITICAL:** Read this entire file before making any changes to the project.
