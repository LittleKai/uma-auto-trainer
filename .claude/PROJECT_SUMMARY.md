# Project Summary
**Last Updated:** 2025-01-21 (Initial Setup)
**Updated By:** Claude Code Initial Setup

---

## 1. Project Overview
- **Name:** Uma Musume Auto Train
- **Type:** Game Automation Tool (Desktop Application)
- **Author:** LittleKai
- **Tech Stack:** Python 3.x + Tkinter GUI + OpenCV + OCR (Tesseract/EasyOCR)
- **i18n:** None (Japanese game with English UI)
- **Deployment:** Standalone Windows executable (PyInstaller)

**Description:**
Automated training bot for the mobile/PC game "Uma Musume: Pretty Derby". Uses OCR and computer vision to detect game state and make intelligent training decisions based on configurable scoring algorithms.

---

## 2. Current Architecture

### File Structure (Key Files Only)
```
uma-auto-trainer/
├── main.py                      # Entry point - launches UmaAutoGUI
├── config.json                  # Scoring config, stat caps, energy thresholds
├── bot_settings.json            # User preferences, presets, filters
├── requirements.txt             # Python dependencies (~40 packages)
├── build_exe.py                 # PyInstaller build script
│
├── core/                        # Core automation logic (~4,500 lines)
│   ├── execute.py               # Main bot loop (BotController, GameStateManager)
│   ├── execute_helpers.py       # Helper classes (EventHandler, CareerLobbyManager)
│   ├── state.py                 # Game state detection via OCR
│   ├── logic.py                 # Training decision scoring algorithm
│   ├── training_handler.py      # Training action execution
│   ├── race_handler.py          # Race navigation and execution
│   ├── rest_handler.py          # Rest/recreation actions
│   ├── event_handler.py         # Event choice automation with database
│   ├── race_manager.py          # Race database and date parsing
│   ├── click_handler.py         # Enhanced click with template matching
│   ├── recognizer.py            # OpenCV template matching
│   └── ocr.py                   # OCR integration (Tesseract + EasyOCR)
│
├── gui/                         # Tkinter GUI (~2,000 lines)
│   ├── main_window.py           # Main application window
│   ├── window_manager.py        # Window persistence
│   ├── bot_controller.py        # Bot control + hotkeys (F1/F3/F5)
│   ├── tabs/                    # Tab components
│   │   ├── strategy_tab.py      # Race filters, stop conditions
│   │   ├── event_choice_tab.py  # Event handling, support cards, presets
│   │   └── team_trials_tab.py   # Team trials mode
│   ├── dialogs/                 # Configuration dialogs
│   └── components/              # Reusable GUI components
│
├── utils/                       # Utilities (~800 lines)
│   ├── constants.py             # UI regions, icons, file paths
│   ├── constants_support.py     # Mood patterns, OCR configs
│   └── screenshot.py            # Screen capture utilities
│
└── assets/                      # Game automation assets
    ├── buttons/                 # Button template images
    ├── icons/                   # UI icons for detection
    ├── event_map/               # Event databases (JSON per character)
    ├── race_list.json           # Race database
    └── uma_musume_data.csv      # Character data
```

### Component Dependencies
```
main.py
  └── gui/main_window.py (UmaAutoGUI)
        ├── gui/window_manager.py (WindowManager)
        ├── gui/bot_controller.py (BotController)
        ├── gui/tabs/*.py (StrategyTab, EventChoiceTab, TeamTrialsTab)
        ├── gui/components/*.py (StatusSection, LogSection)
        └── core/execute.py
              ├── core/training_handler.py (TrainingHandler)
              ├── core/race_handler.py (RaceHandler)
              ├── core/rest_handler.py (RestHandler)
              ├── core/event_handler.py (EventChoiceHandler)
              ├── core/state.py (OCR state detection)
              ├── core/logic.py (Decision scoring)
              └── core/click_handler.py (Click automation)
```

---

## 3. Key Decisions & Patterns

### Handler Pattern (Separation of Concerns)
Each game action has a dedicated handler class:
- `TrainingHandler` - Training selection and execution
- `RaceHandler` - Race navigation and participation
- `RestHandler` - Rest/recreation actions
- `EventChoiceHandler` - Event database lookup and choice selection

All handlers share common callback interface:
- `check_stop_func` - Check if bot should stop
- `check_window_func` - Check if game window is active
- `log_func` - Logging callback

### Scoring Algorithm (core/logic.py)
Unified scoring system for training decisions:
- Base score per support card type
- Stage multipliers (Pre-Debut/Early/Mid/Late)
- Rainbow card bonuses at mid/late stages
- Friend card multipliers
- WIT training special handling
- Energy shortage penalties

Key thresholds (from config.json):
- Pre-Debut: Day <= 16
- Early Stage: Day <= 24
- Mid Stage: Day <= 48
- Late Stage: Day > 48

### State Management
- Global state in `core/state.py` using module-level variables
- `current_date_info` - Current game date
- `_support_card_state` - Cached support card counts
- GUI state managed via Tkinter variables

### OCR Pipeline
1. Capture screen region using PIL/MSS
2. Image preprocessing (contrast, threshold, denoise)
3. Primary OCR with Tesseract
4. Fallback to EasyOCR if needed
5. Text cleaning and validation

### Configuration System
- `config.json` - Core scoring parameters (developer-facing)
- `bot_settings.json` - User preferences (GUI-facing)
- `region_settings.json` - Screen region coordinates (adjustable)

---

## 4. Active Features & Status

| Feature | Status | Files Involved | Notes |
|---------|--------|----------------|-------|
| URA Final Training | ✅ | core/execute.py, training_handler.py | Main game mode |
| Unity Cup | ✅ | core/execute.py, constants.py | Different turn/year regions |
| Event Automation | ✅ | event_handler.py, assets/event_map/ | Database per character |
| Race Filtering | ✅ | race_handler.py, strategy_tab.py | G1/G2/G3, turf/dirt, distance |
| Stop Conditions | ✅ | execute.py, strategy_tab.py | Mood, energy, month, URA Final |
| Preset System | ✅ | event_choice_tab.py | 20 presets with support cards |
| Team Trials | 🚧 | team_trials_tab.py, team_trials_logic.py | Basic implementation |

---

## 5. Known Issues & TODOs

### High Priority
- [ ] None currently identified

### Medium Priority
- [ ] Event database needs expansion for more characters
- [ ] EasyOCR fallback can be slow on first load

### Low Priority
- [ ] Consider async/await for non-blocking OCR
- [ ] Add unit tests for scoring logic

---

## 6. Important Context for Claude

### When making changes:
1. Always update this file's "Last Updated" timestamp
2. Create new history entry in `.claude/history/`
3. Follow naming conventions in CONVENTIONS.md
4. Test with both URA Final and Unity Cup scenarios
5. Verify OCR regions if modifying state detection

### Critical Files (read before major changes):
- `config.json` - Scoring parameters and thresholds
- `utils/constants.py` - All UI regions and file paths
- `core/state.py` - OCR-based state detection
- `core/logic.py` - Training decision algorithm
- `core/execute.py` - Main bot loop

### Keyboard Shortcuts (Global):
- **F1** - Start bot
- **F3** - Stop bot (graceful)
- **F5** - Force exit program

### Game Scenarios:
- **URA Final** - Standard training mode (72 days)
- **Unity Cup** - Different UI regions for turn/year

---

## 7. Recent Changes (Last 3 Sessions)

1. **2025-01-21** - Initial project documentation and Claude Code setup

---

## 8. Quick Commands
```bash
# Development
python main.py

# Build executable
python build_exe.py

# Install dependencies
pip install -r requirements.txt

# Output location after build
dist/UmaAutoTrain.exe
```

---

**NOTE TO CLAUDE CODE:**
Read this file FIRST before making any changes.
Update Section 4, 5, 7 after each session.
Create history entry with details of changes made.
