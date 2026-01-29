# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Uma Musume Auto Train is a Windows desktop automation tool for the game "Uma Musume: Pretty Derby". It uses computer vision (OpenCV), OCR (Tesseract + EasyOCR), and intelligent decision-making algorithms to automate character training.

**Requirements:** Windows 10/11 64-bit, 1920x1080 screen resolution, Tesseract OCR installed

## Commands

```bash
# Run application
python main.py

# Build executable
python build_exe.py
# Output: dist/Uma_Musume_Auto_Train.exe
```

No automated tests exist - testing is done manually through the GUI.

## Architecture

### Entry Flow
```
main.py → UmaAutoGUI (gui/main_window.py) → BotController (core/execute.py)
```

### Core Components

**Handlers** (core/) - All follow this pattern:
```python
class SomeHandler:
    def __init__(self, check_stop_func, check_window_func, log_func):
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func
```
- `TrainingHandler` - Training selection and execution
- `RaceHandler` - Race navigation and filtering
- `RestHandler` - Rest/recreation actions
- `EventChoiceHandler` - Event database lookup and automation

**State Detection** (core/state.py) - Uses OCR to parse game state:
- Date, mood, energy, stats, support cards, failure count
- Module-level globals: `current_date_info`, `_support_card_state`

**Scoring Algorithm** (core/logic.py):
```
base_score × stage_multiplier + rainbow_bonus + friend_bonus - energy_penalty
```
Stage thresholds: Pre-Debut (≤16), Early (≤24), Mid (≤48), Late (>48)

**OCR Pipeline** (core/ocr.py):
1. Screen capture via PIL/MSS
2. Preprocess: contrast, threshold, denoise
3. Primary: Tesseract (Japanese)
4. Fallback: EasyOCR

### Configuration Files

| File | Purpose |
|------|---------|
| `config.json` | Scoring parameters, stat caps, thresholds (developer) |
| `bot_settings.json` | User preferences, presets, filters (auto-generated) |
| `region_settings.json` | Adjustable OCR coordinates (user-tunable) |

### Key Directories

- `core/` - Bot logic, OCR, state detection, handlers
- `gui/` - Tkinter GUI (main_window, tabs, dialogs, components)
- `utils/` - Constants, screenshot utilities
- `assets/` - Template images, event databases (JSON), race data

## Development Guidelines

### Before Changes
1. Read `.claude/PROJECT_SUMMARY.md` for current state
2. Check if similar functionality exists
3. Identify affected components

### When Changing
| Area | Files to check |
|------|----------------|
| Training logic | `core/logic.py`, `config.json` |
| OCR detection | `core/state.py`, `core/ocr.py` |
| UI regions | `utils/constants.py` |
| Event handling | `core/event_handler.py` |

### After Changes
- Create `.claude/history/YYYY-MM-DD_HH-MM.md` with change log
- Update `.claude/PROJECT_SUMMARY.md` timestamp and recent changes

### Constraints
- Don't modify `config.json` scoring values without discussion
- Don't change OCR regions without testing against actual game
- Don't hardcode configurable values
