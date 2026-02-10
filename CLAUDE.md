# Instructions for Claude Code

**Last Updated:** 2026-01-30 09:00

---

## Quick Start Workflow

**IMPORTANT: Read in this order before making ANY changes:**

1. **Read** `.claude/PROJECT_SUMMARY.md` to understand current state
2. **Check** `.claude/CONVENTIONS.md` to follow coding standards
3. **Make changes** as requested
4. **Update** `.claude/PROJECT_SUMMARY.md` (sections 4, 5, 7)
5. **Create** history entry in `.claude/history/`

---

## Critical Rules

### Before ANY Changes:
- [ ] Read PROJECT_SUMMARY.md first
- [ ] Understand the affected components
- [ ] Check CONVENTIONS.md for standards

### After ALL Changes:
- [ ] Update PROJECT_SUMMARY.md timestamps
- [ ] Update "Active Features & Status" if relevant
- [ ] Add to "Known Issues & TODOs" if needed
- [ ] Create new history entry with details
- [ ] Update "Recent Changes" section

### Never:
- Skip documentation updates
- Modify files in `0. Temp/` folder
- Modify `config.json` scoring values without discussion
- Change OCR regions without testing against actual game
- Hardcode values that should be configurable

---

## Project Quick Reference

**Tech Stack:**
- **Language:** Python 3.x
- **GUI:** Tkinter
- **Computer Vision:** OpenCV 4.12.0
- **OCR:** Tesseract + EasyOCR 1.7.2
- **Automation:** PyAutoGUI 0.9.54
- **Screenshot:** MSS 10.0.0
- **Build:** PyInstaller

**Key Files:**
| File | Purpose |
|------|---------|
| `main.py` | Entry point |
| `core/execute.py` | Main bot orchestration (BotController) |
| `core/state.py` | Game state detection via OCR |
| `core/logic.py` | Training scoring algorithm |
| `gui/main_window.py` | Main GUI window (UmaAutoGUI) |
| `config.json` | Scoring parameters (developer) |
| `bot_settings.json` | User preferences (auto-generated) |
| `region_settings.json` | OCR coordinates (user-tunable) |

**Dev Commands:**
```bash
python main.py          # Run application
python build_exe.py     # Build executable (dist/Uma_Musume_Auto_Train.exe)
```

---

## Documentation Structure

```
project-root/
├── CLAUDE.md (this file)           # Instructions for Claude
└── .claude/
    ├── PROJECT_SUMMARY.md          # Detailed project state & architecture
    ├── CONVENTIONS.md              # Coding standards & patterns
    ├── history/                    # Change logs from each session
    │   └── YYYY-MM-DD_HHMM.md
    └── templates/
        └── change-log-template.md
```

---

## Handler Pattern

All handlers follow this pattern:
```python
class SomeHandler:
    def __init__(self, check_stop_func, check_window_func, log_func):
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func
```

---

## Area-Specific Guidelines

| Area | Files to Check |
|------|----------------|
| Training logic | `core/logic.py`, `config.json` |
| OCR detection | `core/state.py`, `core/ocr.py` |
| UI regions | `utils/constants.py`, `region_settings.json` |
| Event handling | `core/event_handler.py`, `assets/event_map/` |
| GUI components | `gui/tabs/`, `gui/components/` |
| Support cards | `assets/support_cards/`, `core/state.py` |

---

## Notes for Claude

- This is a Windows-only desktop automation tool
- OCR accuracy depends on 1920x1080 resolution
- Testing is manual - no automated test suite
- Event databases are in JSON format under `assets/event_map/`
- Support card icons must match exact template images
- Always prioritize stability over new features
- When in doubt, ask before making structural changes

---

**Remember:** Documentation = Single Source of Truth
