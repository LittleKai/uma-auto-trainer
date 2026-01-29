# Instructions for Claude Code

## Before Starting Any Task

### 1. Read Context Files (Every Session)
```
ALWAYS read these files first:
1. .claude/PROJECT_SUMMARY.md - Current project state
2. .claude/CONVENTIONS.md - Code patterns to follow
```

### 2. Understand the Request
- Clarify ambiguous requirements before coding
- Check if similar functionality exists
- Identify affected components

---

## While Working

### 3. Follow Existing Patterns
- Match the code style in existing files
- Use established handler/component patterns
- Import from correct locations

### 4. Keep Changes Minimal
- Only modify what's necessary
- Don't refactor unrelated code
- Avoid adding unnecessary features

### 5. Test Critical Paths
- OCR functions need real game window testing
- GUI changes need manual verification
- Scoring changes affect training decisions

---

## After Completing Work

### 6. Update Documentation
Create/update `.claude/history/YYYY-MM-DD_HH-MM.md`:
```markdown
# Change Log: [Date] [Time]

## Session Info
- **Request:** "[Brief description]"
- **Files Modified:** [Count]
- **Files Created:** [Count]

## Changes Made
### [Feature/Fix Name]
- **What:** [Description]
- **Why:** [Reason]
- **Files:** [List]

## Testing Notes
[How it was verified]
```

### 7. Update PROJECT_SUMMARY.md
- Update "Last Updated" timestamp
- Add entry to "Recent Changes" section
- Update feature status if applicable
- Add any new known issues

---

## Key Project Knowledge

### Architecture
- **Entry:** `main.py` -> `gui/main_window.py` (UmaAutoGUI)
- **Core loop:** `core/execute.py` (BotController)
- **Handlers:** Training, Race, Rest, EventChoice
- **State:** `core/state.py` via OCR

### Important Files to Check
| When changing... | Read first... |
|-----------------|---------------|
| Training logic | `core/logic.py`, `config.json` |
| OCR detection | `core/state.py`, `core/ocr.py` |
| UI regions | `utils/constants.py` |
| GUI components | `gui/main_window.py` |
| Event handling | `core/event_handler.py` |

### Callback Pattern
All handlers use these callbacks:
```python
check_stop_func: Callable[[], bool]  # Check if bot should stop
check_window_func: Callable[[], bool]  # Check game window active
log_func: Callable[[str], None]  # Log messages
```

### Scoring System
Training decisions based on:
- Support card types and counts
- Career stage (Pre-Debut/Early/Mid/Late)
- Energy levels
- Rainbow/Friend card bonuses

Day thresholds:
- Pre-Debut: <= 16
- Early: <= 24
- Mid: <= 48
- Late: > 48

---

## Common Tasks Quick Reference

### Adding a new handler
1. Create `core/new_handler.py`
2. Follow `TrainingHandler` pattern
3. Initialize in `core/execute.py`
4. Add callback connections

### Adding a new GUI tab
1. Create `gui/tabs/new_tab.py`
2. Follow `StrategyTab` pattern
3. Register in `gui/main_window.py`
4. Add settings persistence

### Modifying OCR regions
1. Check `utils/constants.py` for region definitions
2. Use `region_settings.json` for adjustable regions
3. Test with actual game screenshots

### Adding event database
1. Create JSON in `assets/event_map/[character_name]/`
2. Follow existing event JSON structure
3. Update `event_handler.py` if needed

---

## Don'ts

- Don't modify `config.json` scoring values without discussion
- Don't change OCR regions without testing
- Don't remove backward compatibility aliases
- Don't add dependencies without documenting
- Don't hardcode values that should be configurable
