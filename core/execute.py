# Cải tiến core/execute.py
import pyautogui
import time
import json
import pygetwindow as gw

pyautogui.useImageNotFoundException(False)

from core.state import check_support_card, check_failure, check_turn, check_mood, check_current_year, check_criteria, get_current_date_info, check_energy_percentage
from core.logic import do_something, get_stat_priority
from utils.constants import MOOD_LIST
from core.recognizer import is_infirmary_active, match_template
from utils.scenario import ura
from core.race_manager import RaceManager, DateManager

# Global variables for GUI integration
log_callback = None
gui_instance = None

def set_log_callback(callback):
    """Set the logging callback function"""
    global log_callback
    log_callback = callback

def log_message(message):
    """Log message using callback if available"""
    if log_callback:
        log_callback(message)
    else:
        print(message)

def is_game_window_active():
    """Check if Umamusume window is currently active"""
    try:
        windows = gw.getWindowsWithTitle("Umamusume")
        if windows:
            return windows[0].isActive
        return False
    except:
        return False

def safe_action(func, *args, **kwargs):
    """Execute action only if game window is active"""
    if not is_game_window_active():
        log_message("Game window not active, skipping action")
        return False
    return func(*args, **kwargs)

with open("config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

# Only load energy settings from config now
MINIMUM_ENERGY_PERCENTAGE = config["minimum_energy_percentage"]
CRITICAL_ENERGY_PERCENTAGE = config["critical_energy_percentage"]

def click(img, confidence = 0.8, minSearch = 2, click = 1, text = ""):
    if not is_game_window_active():
        return False

    btn = pyautogui.locateCenterOnScreen(img, confidence=confidence, minSearchTime=minSearch)
    if btn:
        if text:
            log_message(text)
        pyautogui.moveTo(btn, duration=0.175)
        pyautogui.click(clicks=click)
        return True

    return False

def go_to_training():
    return click("assets/buttons/training_btn.png")

def check_training_support_stable(training_type, max_retries=3):
    """
    Check training support with stability verification
    Performs multiple checks ONLY if total support > 6 to ensure accuracy
    """
    # Get current date info to check if in Pre-Debut period
    current_date = get_current_date_info()
    is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

    # First check
    support_counts = check_support_card(is_pre_debut=is_pre_debut, training_type=training_type)
    total_support = sum(support_counts.values())

    first_result = {
        'support': support_counts,
        'total_support': total_support
    }

    # If total support <= 6, return immediately (no need for multiple checks)
    if total_support <= 6:
        return first_result

    # If total support > 6, perform additional checks for stability
    log_message(f"[{training_type.upper()}] High support count ({total_support}), performing additional checks for accuracy...")

    support_results = [first_result]

    for attempt in range(1, max_retries):
        # Small delay between checks for stability
        time.sleep(0.1)

        support_counts = check_support_card(is_pre_debut=is_pre_debut, training_type=training_type)
        total_support = sum(support_counts.values())

        support_results.append({
            'support': support_counts,
            'total_support': total_support
        })

    # Use the result with median total support count
    support_results.sort(key=lambda x: x['total_support'])
    median_index = len(support_results) // 2
    result = support_results[median_index]

    log_message(f"[{training_type.upper()}] Multiple checks completed, using median result: {result['support']} (total: {result['total_support']})")
    return result

def ensure_main_menu():
    """
    Ensure we're at the main career lobby menu
    Returns True if we're at main menu, False if failed
    """
    if not is_game_window_active():
        return False

    max_attempts = 5
    for attempt in range(max_attempts):
        # Check if we're already at main menu by looking for tazuna hint
        tazuna_hint = pyautogui.locateCenterOnScreen("assets/ui/tazuna_hint.png", confidence=0.8, minSearchTime=0.3)

        if tazuna_hint:
            log_message(f"[INFO] At main menu (attempt {attempt + 1})")
            return True

        # If not at main menu, try to go back
        log_message(f"[DEBUG] Not at main menu, clicking back button (attempt {attempt + 1})")

        # Try different back buttons
        back_buttons = [
            "assets/buttons/back_btn.png",
            "assets/buttons/cancel_btn.png"
        ]

        back_clicked = False
        for back_btn in back_buttons:
            if click(img=back_btn, minSearch=0.3):
                back_clicked = True
                break

        if back_clicked:
            time.sleep(0.5)  # Wait for UI transition
        else:
            # If no back button found, try pressing ESC key
            log_message(f"[DEBUG] No back button found, trying ESC key")
            pyautogui.press('esc')
            time.sleep(0.5)

    log_message(f"[ERROR] Failed to reach main menu after {max_attempts} attempts")
    return False

def handle_critical_energy_rest():
    """Handle resting when critical energy after failed race attempt"""
    log_message("[INFO] Critical energy - attempting to rest after failed race")

    # First ensure we're at main menu
    if not ensure_main_menu():
        log_message("[ERROR] Could not return to main menu")
        return False

    # Now try to rest
    if do_rest():
        log_message("[SUCCESS] Critical energy - Successfully rested")
        return True
    else:
        log_message("[WARNING] Rest failed, trying recreation as fallback")
        if do_recreation():
            log_message("[SUCCESS] Critical energy - Used recreation as fallback")
            return True
        else:
            log_message("[ERROR] Both rest and recreation failed")
            return False

def check_training(energy_percentage=100):
    if not is_game_window_active():
        return {}

    # Check if we're in Pre-Debut period
    from core.state import get_current_date_info
    current_date = get_current_date_info()
    is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

    # Define which training types to check based on energy level
    if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
        should_race, available_races = race_manager.should_race_today(current_date)
        if should_race:
            log_message(f"Critical energy ({energy_percentage}%) - found {len(available_races)} matching races. Racing to avoid training.")
            race_found = do_race(allow_continuous_racing=allow_continuous_racing)
            if race_found:
                return True
            else:
                # Use improved helper function for critical energy rest
                return handle_critical_energy_rest()
        else:
            log_message(f"Critical energy ({energy_percentage}%) and no matching races today. Resting immediately.")
            return handle_critical_energy_rest()
    elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
        # Low energy: only check WIT
        training_types = {
            "wit": "assets/icons/train_wit.png"
        }
        log_message(f"Low energy ({energy_percentage}%), only checking WIT training")
    else:
        # Normal energy: check all training types
        training_types = {
            "spd": "assets/icons/train_spd.png",
            "sta": "assets/icons/train_sta.png",
            "pwr": "assets/icons/train_pwr.png",
            "guts": "assets/icons/train_guts.png",
            "wit": "assets/icons/train_wit.png"
        }

    results = {}

    for key, icon_path in training_types.items():
        pos = pyautogui.locateCenterOnScreen(icon_path, confidence=0.8)
        if pos:
            pyautogui.moveTo(pos, duration=0.1)
            pyautogui.mouseDown()

            # Use improved support checking with stability verification
            training_result = check_training_support_stable(key)
            results[key] = training_result

            if is_pre_debut:
                log_message(f"[{key.upper()}] → {training_result['support']} (Pre-Debut)")
            else:
                log_message(f"[{key.upper()}] → {training_result['support']}")
            time.sleep(0.1)

    pyautogui.mouseUp()
    click(img="assets/buttons/back_btn.png")
    return results

def do_train(train):
    if not is_game_window_active():
        return False

    train_btn = pyautogui.locateCenterOnScreen(f"assets/icons/train_{train}.png", confidence=0.8)
    if train_btn:
        pyautogui.tripleClick(train_btn, interval=0.1, duration=0.2)
        return True
    return False

def do_rest():
    """Improved rest function with better error handling"""
    if not is_game_window_active():
        log_message("[WARNING] Game window not active, cannot rest")
        return False

    # Get current date to check if in summer period
    from core.state import get_current_date_info
    current_date = get_current_date_info()

    # Check if in Jul-Aug period (summer vacation)
    is_summer = False
    if current_date:
        month_num = current_date.get('month_num', 0)
        if month_num == 7 or month_num == 8:  # July or August
            is_summer = True
            log_message(f"[INFO] Summer period detected (Month {month_num})")

    # Try to find rest buttons with more attempts
    rest_attempts = [
        ("assets/buttons/rest_btn.png", "Regular rest button"),
        ("assets/buttons/rest_summer_btn.png", "Summer rest button"),
        ("assets/buttons/recreation_btn.png", "Recreation button (fallback)")
    ]

    for button_path, button_name in rest_attempts:
        log_message(f"[DEBUG] Trying to find {button_name}")

        # Try to find the button with increased search time
        btn = pyautogui.locateCenterOnScreen(button_path, confidence=0.8, minSearchTime=1.0)

        if btn:
            log_message(f"[INFO] Found {button_name} at {btn}")
            pyautogui.moveTo(btn, duration=0.15)
            pyautogui.click(btn)

            # If in summer period, handle vacation dialog
            if is_summer and "rest" in button_path:
                log_message("[INFO] Summer period - waiting for vacation dialog")
                time.sleep(0.8)  # Wait a bit longer for dialog to appear

                # Try to click OK button for vacation confirmation
                ok_found = False
                for attempt in range(3):
                    if click(img="assets/buttons/ok_btn.png", minSearch=0.5, text="Summer vacation - clicking OK"):
                        log_message("[INFO] Summer vacation dialog confirmed")
                        ok_found = True
                        break
                    time.sleep(0.3)

                if not ok_found:
                    log_message("[WARNING] Summer vacation dialog OK button not found")

            log_message(f"[SUCCESS] {button_name} clicked successfully")
            return True
        else:
            log_message(f"[DEBUG] {button_name} not found")

    # If all buttons failed, try a more aggressive search
    log_message("[WARNING] All rest buttons failed, trying screenshot analysis")

    # Take a screenshot and look for any button-like elements
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save("debug_rest_fail.png")
        log_message("[DEBUG] Screenshot saved as debug_rest_fail.png for analysis")
    except:
        pass

    log_message("[ERROR] All rest attempts failed")
    return False

def do_recreation():
    """Improved recreation function"""
    if not is_game_window_active():
        log_message("[WARNING] Game window not active, cannot do recreation")
        return False

    recreation_attempts = [
        ("assets/buttons/recreation_btn.png", "Recreation button"),
        ("assets/buttons/rest_summer_btn.png", "Summer recreation button")
    ]

    for button_path, button_name in recreation_attempts:
        log_message(f"[DEBUG] Trying to find {button_name}")

        btn = pyautogui.locateCenterOnScreen(button_path, confidence=0.8, minSearchTime=1.0)

        if btn:
            log_message(f"[INFO] Found {button_name} at {btn}")
            pyautogui.moveTo(btn, duration=0.15)
            pyautogui.click(btn)
            log_message(f"[SUCCESS] {button_name} clicked successfully")
            return True
        else:
            log_message(f"[DEBUG] {button_name} not found")

    log_message("[ERROR] All recreation attempts failed")
    return False

def do_race(prioritize_g1=False, allow_continuous_racing=True):
    """
    Enhanced race function with continuous racing control
    """
    if not is_game_window_active():
        return False

    click(img="assets/buttons/races_btn.png", minSearch=10)

    # Check for OK button first (indicates more than 3 races recently)
    ok_btn_found = click(img="assets/buttons/ok_btn.png", minSearch=0.7)

    if ok_btn_found and not allow_continuous_racing:
        # If OK button found and continuous racing not allowed, cancel instead
        log_message("Continuous racing disabled - canceling race due to recent racing limit")
        click(img="assets/buttons/cancel_btn.png", minSearch=0.2)
        return False

    found = race_select(prioritize_g1=prioritize_g1)
    if not found:
        log_message("No race found.")
        return False

    race_prep()
    time.sleep(1)
    after_race()
    return True

def race_day():
    if not is_game_window_active():
        return False

    click(img="assets/buttons/race_day_btn.png", minSearch=10)

    click(img="assets/buttons/ok_btn.png", minSearch=0.7)
    time.sleep(0.5)

    for i in range(2):
        click(img="assets/buttons/race_btn.png", minSearch=2)
        time.sleep(0.5)

    race_prep()
    time.sleep(1)
    after_race()
    return True

def race_select(prioritize_g1 = False):
    if not is_game_window_active():
        return False

    pyautogui.moveTo(x=560, y=680)
    time.sleep(0.2)

    if prioritize_g1:
        log_message("Looking for G1 race.")
        for i in range(2):
            race_card = match_template("assets/ui/g1_race.png", threshold=0.9)

            if race_card:
                for x, y, w, h in race_card:
                    region = (x, y, 310, 90)
                    match_aptitude = pyautogui.locateCenterOnScreen("assets/ui/match_track.png", confidence=0.8, minSearchTime=0.7, region=region)
                    if match_aptitude:
                        log_message("G1 race found.")
                        pyautogui.moveTo(match_aptitude, duration=0.2)
                        pyautogui.click()
                        for i in range(2):
                            race_btn = pyautogui.locateCenterOnScreen("assets/buttons/race_btn.png", confidence=0.8, minSearchTime=2)
                            if race_btn:
                                pyautogui.moveTo(race_btn, duration=0.2)
                                pyautogui.click(race_btn)
                                time.sleep(0.5)
                        return True

            for i in range(4):
                pyautogui.scroll(-300)

        return False
    else:
        log_message("Looking for race.")
        for i in range(4):
            match_aptitude = pyautogui.locateCenterOnScreen("assets/ui/match_track.png", confidence=0.8, minSearchTime=0.7)
            if match_aptitude:
                log_message("Race found.")
                pyautogui.moveTo(match_aptitude, duration=0.2)
                pyautogui.click(match_aptitude)

                for i in range(2):
                    race_btn = pyautogui.locateCenterOnScreen("assets/buttons/race_btn.png", confidence=0.8, minSearchTime=2)
                    if race_btn:
                        pyautogui.moveTo(race_btn, duration=0.2)
                        pyautogui.click(race_btn)
                        time.sleep(0.5)
                return True

            for i in range(4):
                pyautogui.scroll(-300)

        return False

def race_prep():
    if not is_game_window_active():
        return False

    view_result_btn = pyautogui.locateCenterOnScreen("assets/buttons/view_results.png", confidence=0.8, minSearchTime=20)
    if view_result_btn:
        pyautogui.click(view_result_btn)
        time.sleep(0.5)
        for i in range(3):
            pyautogui.tripleClick(interval=0.2)
            time.sleep(0.5)
    return True

def after_race():
    if not is_game_window_active():
        return False

    click(img="assets/buttons/next_btn.png", minSearch=5)
    time.sleep(0.3)
    pyautogui.click()
    click(img="assets/buttons/next2_btn.png", minSearch=5)
    return True

def career_lobby(gui=None):
    """Main career lobby function - can work with or without GUI"""
    global gui_instance
    gui_instance = gui

    # Initialize race manager
    race_manager = RaceManager()

    # Check if running with GUI
    if gui:
        # Get race manager from GUI
        race_manager = gui.race_manager

        while gui.is_running:
            # Check if paused
            while gui.is_paused and gui.is_running:
                time.sleep(0.1)

            if not gui.is_running:
                break

            # Check if game window is active
            if not gui.check_game_window():
                gui.log_message("Waiting for game window to be active...")
                time.sleep(2)
                continue

            # Run one iteration of the main loop
            if not career_lobby_iteration(race_manager, gui):
                time.sleep(1)
    else:
        # Original standalone mode
        while True:
            if not career_lobby_iteration(race_manager):
                time.sleep(1)

def career_lobby_iteration(race_manager, gui=None):
    """Single iteration of career lobby logic - COMPLETE FIXED VERSION"""
    try:
        # First check, event
        if click(img="assets/icons/event_choice_1.png", minSearch=0.2, text="Event found, automatically select top choice."):
            return True

        # Second check, inspiration
        if click(img="assets/buttons/inspiration_btn.png", minSearch=0.2, text="Inspiration found."):
            return True

        if click(img="assets/buttons/next_btn.png", minSearch=0.2):
            return True

        if click(img="assets/buttons/cancel_btn.png", minSearch=0.2):
            return True

        # Check if current menu is in career lobby
        tazuna_hint = pyautogui.locateCenterOnScreen("assets/ui/tazuna_hint.png", confidence=0.8, minSearchTime=0.2)

        if tazuna_hint is None:
            log_message("Should be in career lobby.")
            time.sleep(1)
            return True

        time.sleep(0.5)

        # Check if there is debuff status
        debuffed = pyautogui.locateOnScreen("assets/buttons/infirmary_btn2.png", confidence=0.9, minSearchTime=1)
        if debuffed:
            if is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
                pyautogui.click(debuffed)
                log_message("Character has debuff, go to infirmary instead.")
                return True

        mood = check_mood()
        turn = check_turn()
        year = check_current_year()
        criteria = check_criteria()
        energy_percentage = check_energy_percentage()

        # Handle date parsing failure gracefully
        current_date = get_current_date_info()
        if current_date is None:
            log_message("[ERROR] Date parsing failed, using safe fallback behavior")
            # Safe fallback - assume it's not pre-debut and continue with basic logic
            current_date = {
                'year': 'Classic',  # Safe assumption
                'absolute_day': 50,  # Mid-game assumption
                'is_pre_debut': False,
                'is_finale': False
            }

        # Check if career is completed (Finale Season)
        if current_date.get('is_finale', False):
            log_message("🎉 CAREER COMPLETED! Finale Season detected.")
            log_message("🎊 Congratulations! Your Uma Musume has finished their career!")
            log_message("🏆 Bot will now stop automatically.")

            # Stop the bot gracefully
            if gui:
                gui.root.after(0, gui.stop_bot)
                gui.root.after(0, lambda: gui.log_message("🎉 Career completed! Bot stopped automatically."))

            return False  # End the iteration loop

        # Get strategy settings from GUI
        strategy_settings = {'minimum_mood': 'NORMAL', 'priority_strategy': 'G1', 'allow_continuous_racing': True}
        if gui:
            strategy_settings = gui.get_current_settings()

        # Convert mood string to list for comparison
        MOOD_LIST = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT", "UNKNOWN"]
        mood_index = MOOD_LIST.index(mood) if mood in MOOD_LIST else 0
        minimum_mood_index = MOOD_LIST.index(strategy_settings.get('minimum_mood', 'NORMAL'))

        # Update GUI with current date and energy if available
        if gui and current_date:
            gui.update_current_date(current_date)
        if gui:
            gui.update_energy_display(energy_percentage)

        log_message("=" * 50)
        log_message(f"Year: {year}")
        log_message(f"Mood: {mood}")
        log_message(f"Turn: {turn}")
        log_message(f"Energy: {energy_percentage}%")
        log_message(f"Strategy: {strategy_settings.get('priority_strategy', 'G1')}")

        if current_date:
            if current_date.get('is_finale', False):
                log_message(f"Current Date: Finale Season (Career Completed)")
            elif current_date.get('is_pre_debut', False):
                log_message(f"Current Date: {current_date['year']} Year Pre-Debut (Day {current_date['absolute_day']}/72)")
            else:
                log_message(f"Current Date: {current_date['year']} {current_date['month']} {current_date['period']} (Day {current_date['absolute_day']}/72)")

            # Display only races that match current filters
            available_races = race_manager.get_available_races(current_date)
            all_filtered_races = race_manager.get_filtered_races_for_date(current_date)

            if DateManager.is_restricted_period(current_date):
                if current_date.get('is_pre_debut', False):
                    log_message("📍 Racing Status: Disabled (Pre-Debut period)")
                else:
                    absolute_day = current_date['absolute_day']

                    if absolute_day <= 16:
                        log_message(f"📍 Racing Status: Disabled (Career days 1-16 restriction, current: Day {absolute_day}/72)")
                    else:
                        log_message("📍 Racing Status: Disabled (July-August restriction)")

                # Show filtered races that would be available if not restricted
                if all_filtered_races:
                    log_message(f"📍 Today's Races: {len(all_filtered_races)} matching filters (restricted)")
                    for race in all_filtered_races[:3]:  # Show max 3
                        race_props = race_manager.extract_race_properties(race)
                        log_message(f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
                    if len(all_filtered_races) > 3:
                        log_message(f"  ... and {len(all_filtered_races) - 3} more")
                else:
                    log_message("📍 Today's Races: None match current filters")
            else:
                # Normal racing periods - only show races that match filters
                if available_races:
                    log_message(f"📍 Today's Races: {len(available_races)} matching filters")
                    for race in available_races:
                        race_props = race_manager.extract_race_properties(race)
                        log_message(f"  - {race['name']} ({race_props['grade_type'].upper()}, {race_props['track_type']}, {race_props['distance_type']})")
                else:
                    log_message("📍 Today's Races: None match current filters")

        # URA SCENARIO
        if year == "Finale Season" and turn == "Race Day":
            log_message("URA Finale")
            ura()
            for i in range(2):
                if click(img="assets/buttons/race_btn.png", minSearch=2):
                    time.sleep(0.5)

            race_prep()
            time.sleep(1)
            after_race()
            return True

        # If calendar is race day, do race (always allow continuous racing for race day)
        if turn == "Race Day" and year != "Finale Season":
            log_message("Race Day.")
            race_day()
            return True

        # Mood check using strategy settings with Pre-Debut/Junior Year restriction
        if mood_index < minimum_mood_index:
            # Check if in Pre-Debut period or Junior Year - skip recreation
            is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24
            is_junior_year = "Junior Year" in year

            if is_pre_debut:
                log_message(f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. Skipping recreation (Pre-Debut period)")
            elif is_junior_year:
                log_message(f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. Skipping recreation (Junior Year)")
            else:
                log_message(f"Mood is {mood}, below minimum {strategy_settings.get('minimum_mood', 'NORMAL')}. Trying recreation to increase mood")
                do_recreation()
                return True

        # Enhanced race logic with priority strategy
        priority_strategy = strategy_settings.get('priority_strategy', 'G1')
        allow_continuous_racing = strategy_settings.get('allow_continuous_racing', True)

        # Critical energy handling
        if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)
            if should_race:
                log_message(f"Critical energy ({energy_percentage}%) - found {len(available_races)} matching races. Racing to avoid training.")
                race_found = do_race(allow_continuous_racing=allow_continuous_racing)
                if race_found:
                    return True
                else:
                    click(img="assets/buttons/back_btn.png", text="Race not found. Critical energy - will rest.")
                    time.sleep(0.5)
                    do_rest()
                    log_message("Critical energy - Resting")
                    return True
            else:
                log_message(f"Critical energy ({energy_percentage}%) and no matching races today. Resting immediately.")
                do_rest()
                log_message("Critical energy - Resting")
                return True

        # Low energy handling (but not critical)
        elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)
            if should_race:
                log_message(f"Low energy ({energy_percentage}%) but found {len(available_races)} matching races for today. Racing instead of training.")
                race_found = do_race(allow_continuous_racing=allow_continuous_racing)
                if race_found:
                    return True
                else:
                    click(img="assets/buttons/back_btn.png", text="Matching race not found in game. Low energy - will check WIT training.")
                    time.sleep(0.5)
            else:
                log_message(f"Low energy ({energy_percentage}%) and no matching races today. Will check WIT training or rest.")

        # Normal energy logic with priority strategy
        if current_date and energy_percentage >= MINIMUM_ENERGY_PERCENTAGE:
            should_race, available_races = race_manager.should_race_today(current_date)

            if should_race and available_races:
                log_message(f"Found {len(available_races)} races matching filters today:")
                for race in available_races:
                    props = race_manager.extract_race_properties(race)
                    log_message(f"  - {race['name']} ({props['track_type']}, {props['distance_type']}, {props['grade_type']})")

                # Check if any available race matches priority strategy
                race_matches_priority = False

                if priority_strategy == "G1":
                    # Only race if there's a G1 race available
                    g1_races = [race for race in available_races
                                if race_manager.extract_race_properties(race)['grade_type'] == 'g1']
                    if g1_races:
                        race_matches_priority = True
                        log_message(f"G1 priority: Found {len(g1_races)} G1 races matching filters - Racing immediately")
                    else:
                        log_message(f"G1 priority: No G1 races found, will check training first")

                elif priority_strategy == "G2":
                    # Race if there's a G1 or G2 race available
                    high_grade_races = [race for race in available_races
                                        if race_manager.extract_race_properties(race)['grade_type'] in ['g1', 'g2']]
                    if high_grade_races:
                        race_matches_priority = True
                        log_message(f"G2 priority: Found {len(high_grade_races)} G1/G2 races matching filters - Racing immediately")
                    else:
                        log_message(f"G2 priority: No G1/G2 races found, will check training first")

                elif "Rainbow" in priority_strategy:
                    # For rainbow strategies, always check training first
                    log_message(f"{priority_strategy}: Will check training first, then race if requirements not met")
                    race_matches_priority = False

                # If race matches priority, attempt race immediately
                if race_matches_priority:
                    race_found = do_race(allow_continuous_racing=allow_continuous_racing)
                    if race_found:
                        return True
                    else:
                        click(img="assets/buttons/back_btn.png", text="Matching race not found in game. Proceeding to training.")
                        time.sleep(0.5)
            else:
                if DateManager.is_restricted_period(current_date):
                    if current_date.get('is_pre_debut', False):
                        log_message("In Pre-Debut period. No racing allowed.")
                    elif current_date['absolute_day'] <= 16:
                        log_message("In restricted racing period (Career days 1-16). No racing allowed.")
                    else:
                        log_message("In restricted racing period (Jul-Aug). No racing allowed.")

        # Check training button (only if energy allows training)
        if not go_to_training():
            log_message("Training button is not found.")
            return True

        # Check training with strategy settings
        time.sleep(0.5)
        results_training = check_training(energy_percentage)

        # FIXED: Use enhanced training decision with proper rainbow scoring
        best_training = enhanced_training_decision(results_training, energy_percentage, strategy_settings, current_date)

        if best_training:
            # Training found that meets strategy requirements
            go_to_training()
            time.sleep(0.5)
            do_train(best_training)
            log_message(f"Training: {best_training.upper()}")
        else:
            # No suitable training found based on strategy
            log_message(f"No training meets {priority_strategy} strategy requirements")

            # If we haven't tried racing yet, try now
            if current_date and energy_percentage >= MINIMUM_ENERGY_PERCENTAGE:
                should_race, available_races = race_manager.should_race_today(current_date)

                if should_race:
                    log_message(f"Attempting race from {len(available_races)} available races as fallback.")
                    race_found = do_race(allow_continuous_racing=allow_continuous_racing)
                    if race_found:
                        return True
                    else:
                        click(img="assets/buttons/back_btn.png", text="Race not found.")
                        time.sleep(0.5)

            # If energy is low (< 40%), rest
            if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
                do_rest()
                log_message(f"Low energy ({energy_percentage}%) - Resting")
            else:
                # Energy is normal but no suitable strategy training found
                # Do normal training (fallback to most support card logic)
                log_message(f"Normal energy but no {priority_strategy} training found - doing fallback training")

                # Use fallback training logic with proper rainbow scoring
                if results_training:
                    fallback_training = enhanced_fallback_training(results_training, current_date)
                    if fallback_training:
                        best_key, score_info = fallback_training
                        go_to_training()
                        time.sleep(0.5)
                        do_train(best_key)
                        log_message(f"Fallback Training: {best_key.upper()} {score_info}")
                    else:
                        do_rest()
                        log_message("No support cards found in any training - Resting")
                else:
                    do_rest()
                    log_message("No training available - Resting")

        time.sleep(1)
        return True

    except Exception as e:
        log_message(f"Error in career lobby iteration: {e}")
        return False

def enhanced_training_decision(results_training, energy_percentage, strategy_settings, current_date):
    """
    Enhanced training decision with proper rainbow scoring
    """
    if not results_training:
        return None

    # Get current stats for caps filtering
    from core.state import stat_state
    current_stats = stat_state()

    # Filter by stat caps
    def filter_by_stat_caps(results, current_stats):
        STAT_CAPS = {
            "spd": 1120,
            "sta": 1120,
            "pwr": 1120,
            "guts": 300,
            "wit": 500
        }
        return {
            stat: data for stat, data in results.items()
            if current_stats.get(stat, 0) < STAT_CAPS.get(stat, 1200)
        }

    filtered_results = filter_by_stat_caps(results_training, current_stats)
    if not filtered_results:
        log_message("[INFO] All stats capped.")
        return None

    # Check energy level for low energy logic
    if energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
        return low_energy_training_logic(filtered_results, current_date)

    # Get strategy and date info
    priority_strategy = strategy_settings.get('priority_strategy', 'G1')
    is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

    # For Pre-Debut or Junior Year, use most support card logic
    year = check_current_year()
    if is_pre_debut or "Junior Year" in year:
        return most_support_card_logic(filtered_results, current_date)

    # For Classic/Senior years with Rainbow strategy
    if "Rainbow" in priority_strategy:
        return check_rainbow_strategy(filtered_results, priority_strategy, current_date)

    # For G1/G2 strategies, return None to prioritize racing
    return None

def low_energy_training_logic(results, current_date):
    """Low energy training - only WIT with 3+ support cards"""
    wit_data = results.get("wit")
    if not wit_data:
        return None

    if wit_data["total_support"] >= 3:
        log_message(f"Low energy - WIT training selected with {wit_data['total_support']} support cards")
        return "wit"

    log_message(f"Low energy - WIT has insufficient support cards ({wit_data['total_support']}/3)")
    return None

def most_support_card_logic(results, current_date):
    """Most support card logic with stage-based scoring"""
    is_early_stage = current_date and current_date.get('absolute_day', 0) < 16
    is_rainbow_stage = current_date and current_date.get('absolute_day', 0) > 24

    def calculate_score(training_key, training_data):
        support_counts = training_data["support"]

        if is_rainbow_stage:
            # After day 24: Rainbow support cards get 2 points
            rainbow_count = support_counts.get(training_key, 0)
            rainbow_score = rainbow_count * 2
            other_support_score = sum(count for stat, count in support_counts.items() if stat != training_key)
            return rainbow_score + other_support_score, rainbow_count
        else:
            # Before/at day 24: All support cards count equally
            total_support = sum(support_counts.values())
            rainbow_count = support_counts.get(training_key, 0)
            return total_support, rainbow_count

    def get_priority(stat_key):
        if is_early_stage:
            # Day < 16: WIT > SPD > STA > PWR > GUTS
            early_priority = ["wit", "spd", "sta", "pwr", "guts"]
            return early_priority.index(stat_key) if stat_key in early_priority else 999
        else:
            # Normal priority from config
            return get_stat_priority(stat_key)

    # Find best training
    best_training = max(
        results.items(),
        key=lambda x: (
            calculate_score(x[0], x[1])[0],  # Score
            -get_priority(x[0])  # Priority (negative for max)
        )
    )

    best_key, best_data = best_training
    best_score, rainbow_count = calculate_score(best_key, best_data)

    if best_score <= 1:
        if best_key == "wit":
            log_message("Only 1 support and it's WIT. Skipping.")
            return None
        log_message(f"Only 1 support. Selected: {best_key.upper()}")
        return best_key

    # Display info based on stage
    if is_rainbow_stage:
        score_info = f"(score: {best_score} - {rainbow_count} rainbow × 2 + {best_data['total_support'] - rainbow_count} others × 1)"
    elif is_early_stage:
        score_info = f"({best_data['total_support']} support cards - Early stage WIT priority)"
    else:
        score_info = f"({best_data['total_support']} support cards)"

    log_message(f"Best training: {best_key.upper()} {score_info}")
    return best_key

def check_rainbow_strategy(results, priority_strategy, current_date):
    """Check rainbow training strategy requirements"""
    # Extract required rainbow count
    if "1+" in priority_strategy:
        required_count = 1
    elif "2+" in priority_strategy:
        required_count = 2
    elif "3+" in priority_strategy:
        required_count = 3
    else:
        return None

    # Find rainbow candidates
    rainbow_candidates = {
        stat: data for stat, data in results.items()
        if data["support"].get(stat, 0) >= required_count
    }

    if not rainbow_candidates:
        log_message(f"No training with {required_count}+ rainbow supports found")
        return None

    # Calculate scores with rainbow bonus (if day > 24)
    is_rainbow_stage = current_date and current_date.get('absolute_day', 0) > 24

    def calculate_rainbow_score(training_key, training_data):
        support_counts = training_data["support"]

        if is_rainbow_stage:
            rainbow_count = support_counts.get(training_key, 0)
            rainbow_score = rainbow_count * 2
            other_support_score = sum(count for stat, count in support_counts.items() if stat != training_key)
            return rainbow_score + other_support_score, rainbow_count
        else:
            total_support = sum(support_counts.values())
            rainbow_count = support_counts.get(training_key, 0)
            return total_support, rainbow_count

    # Find best rainbow training
    best_rainbow = max(
        rainbow_candidates.items(),
        key=lambda x: (
            calculate_rainbow_score(x[0], x[1])[0],
            -get_stat_priority(x[0])
        )
    )

    best_key, best_data = best_rainbow
    rainbow_count = best_data['support'][best_key]
    best_score, _ = calculate_rainbow_score(best_key, best_data)

    if is_rainbow_stage:
        score_info = f"(score: {best_score} - {rainbow_count} rainbow × 2 + {best_data['total_support'] - rainbow_count} others × 1)"
    else:
        score_info = f"({rainbow_count} rainbow supports)"

    log_message(f"{priority_strategy} strategy satisfied: {best_key.upper()} {score_info}")
    return best_key

def enhanced_fallback_training(results, current_date):
    """Enhanced fallback training with proper scoring"""
    is_rainbow_stage = current_date and current_date.get('absolute_day', 0) > 24
    is_early_stage = current_date and current_date.get('absolute_day', 0) < 16

    def calculate_fallback_score(training_key, training_data):
        support_counts = training_data["support"]

        if is_rainbow_stage:
            rainbow_count = support_counts.get(training_key, 0)
            rainbow_score = rainbow_count * 2
            other_support_score = sum(count for stat, count in support_counts.items() if stat != training_key)
            return rainbow_score + other_support_score, rainbow_count
        else:
            total_support = sum(support_counts.values())
            rainbow_count = support_counts.get(training_key, 0)
            return total_support, rainbow_count

    def get_fallback_priority(stat_key):
        if is_early_stage:
            early_priority = ["wit", "spd", "sta", "pwr", "guts"]
            return early_priority.index(stat_key) if stat_key in early_priority else 999
        else:
            return get_stat_priority(stat_key)

    # Find best fallback training
    fallback_training = max(
        results.items(),
        key=lambda x: (
            calculate_fallback_score(x[0], x[1])[0],
            -get_fallback_priority(x[0])
        )
    )

    best_key, best_data = fallback_training
    best_score, rainbow_count = calculate_fallback_score(best_key, best_data)

    if best_score <= 0:
        return None

    # Generate score info
    if is_rainbow_stage:
        score_info = f"(score: {best_score} - {rainbow_count} rainbow × 2 + {best_data['total_support'] - rainbow_count} others × 1)"
    elif is_early_stage:
        score_info = f"({best_data['total_support']} support cards - Early stage WIT priority)"
    else:
        score_info = f"({best_data['total_support']} support cards)"

    return best_key, score_info

def focus_umamusume():
    """Original focus function for compatibility"""
    windows = gw.getWindowsWithTitle("Umamusume")
    if not windows:
        raise Exception("Umamusume not found.")
    win = windows[0]
    if win.isMinimized:
        win.restore()
    win.activate()
    win.maximize()
    time.sleep(0.5)