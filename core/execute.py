import pyautogui
import time
import json
import pygetwindow as gw

pyautogui.useImageNotFoundException(False)

from core.state import check_support_card, check_failure, check_turn, check_mood, check_current_year, check_criteria, get_current_date_info, check_energy_percentage
from core.logic import do_something
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

MINIMUM_MOOD = config["minimum_mood"]
PRIORITIZE_G1_RACE = config["prioritize_g1_race"]
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

def check_training(energy_percentage=100):
  if not is_game_window_active():
    return {}

  # Check if we're in Pre-Debut period
  from core.state import get_current_date_info
  current_date = get_current_date_info()
  is_pre_debut = current_date and current_date.get('absolute_day', 0) < 24

  # Define which training types to check based on energy level
  if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
    # Critical energy: no training check at all
    log_message(f"Critical energy ({energy_percentage}%), skipping all training checks")
    return {}
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
      support_counts = check_support_card(is_pre_debut=is_pre_debut, training_type=key)
      total_support = sum(support_counts.values())

      results[key] = {
        "support": support_counts,
        "total_support": total_support
      }

      if is_pre_debut:
        log_message(f"[{key.upper()}] → {support_counts} (Pre-Debut)")
      else:
        log_message(f"[{key.upper()}] → {support_counts}")
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
  if not is_game_window_active():
    return False

  rest_btn = pyautogui.locateCenterOnScreen("assets/buttons/rest_btn.png", confidence=0.8)
  rest_summber_btn = pyautogui.locateCenterOnScreen("assets/buttons/rest_summer_btn.png", confidence=0.8)

  if rest_btn:
    pyautogui.moveTo(rest_btn, duration=0.15)
    pyautogui.click(rest_btn)
    return True
  elif rest_summber_btn:
    pyautogui.moveTo(rest_summber_btn, duration=0.15)
    pyautogui.click(rest_summber_btn)
    return True
  return False

def do_recreation():
  if not is_game_window_active():
    return False

  recreation_btn = pyautogui.locateCenterOnScreen("assets/buttons/recreation_btn.png", confidence=0.8)
  recreation_summer_btn = pyautogui.locateCenterOnScreen("assets/buttons/rest_summer_btn.png", confidence=0.8)

  if recreation_btn:
    pyautogui.moveTo(recreation_btn, duration=0.15)
    pyautogui.click(recreation_btn)
    return True
  elif recreation_summer_btn:
    pyautogui.moveTo(recreation_summer_btn, duration=0.15)
    pyautogui.click(recreation_summer_btn)
    return True
  return False

def do_race(prioritize_g1 = False):
  if not is_game_window_active():
    return False

  click(img="assets/buttons/races_btn.png", minSearch=10)
  click(img="assets/buttons/ok_btn.png", minSearch=0.7)

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
  """Single iteration of career lobby logic"""
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
      time.sleep(1)  # Increased delay from 0.5s to 1s
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
    mood_index = MOOD_LIST.index(mood)
    minimum_mood = MOOD_LIST.index(MINIMUM_MOOD)
    turn = check_turn()
    year = check_current_year()
    criteria = check_criteria()
    energy_percentage = check_energy_percentage()

    # Get current date info
    current_date = get_current_date_info()

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

    if current_date:
      if current_date.get('is_pre_debut', False):
        log_message(f"Current Date: {current_date['year']} Year Pre-Debut (Day {current_date['absolute_day']}/72)")
      else:
        log_message(f"Current Date: {current_date['year']} {current_date['month']} {current_date['period']} (Day {current_date['absolute_day']}/72)")

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

    # If calendar is race day, do race
    if turn == "Race Day" and year != "Finale Season":
      log_message("Race Day.")
      race_day()
      return True

    # Mood check
    if mood_index < minimum_mood:
      log_message("Mood is low, trying recreation to increase mood")
      do_recreation()
      return True

    # Enhanced race logic with filters - check energy levels first
    if current_date:
      if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
        # Critical energy: prioritize race if available, otherwise rest
        should_race, available_races = race_manager.should_race_today(current_date)

        if should_race:
          log_message(f"Critical energy ({energy_percentage}%) - found {len(available_races)} matching races. Racing to avoid training.")
          race_found = do_race()
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

      elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
        # Low energy: check if we should race based on filters
        should_race, available_races = race_manager.should_race_today(current_date)

        if should_race:
          log_message(f"Low energy ({energy_percentage}%) but found {len(available_races)} matching races for today. Attempting race.")
          race_found = do_race()
          if race_found:
            return True
          else:
            # If there is no race matching to aptitude, go back and check WIT training
            click(img="assets/buttons/back_btn.png", text="Matching race not found in game. Low energy - will check WIT training.")
            time.sleep(0.5)
        else:
          log_message(f"Low energy ({energy_percentage}%) and no matching races today. Will check WIT training or rest.")

    # Normal energy race logic
    elif current_date and energy_percentage >= MINIMUM_ENERGY_PERCENTAGE:
      # Check if we should race based on filters and date
      should_race, available_races = race_manager.should_race_today(current_date)

      if should_race:
        log_message(f"Found {len(available_races)} matching races for today:")
        for race in available_races:
          props = race_manager.extract_race_properties(race)
          log_message(f"  - {race['name']} ({props['track_type']}, {props['distance_type']}, {props['grade_type']})")

        race_found = do_race()
        if race_found:
          return True
        else:
          # If there is no race matching to aptitude, go back and do training instead
          click(img="assets/buttons/back_btn.png", text="Matching race not found in game. Proceeding to training.")
          time.sleep(0.5)
      else:
        if DateManager.is_restricted_period(current_date):
          if current_date.get('is_pre_debut', False):
            log_message("In Pre-Debut period. No racing allowed.")
          else:
            log_message("In restricted racing period (Days 1-16 or Jul-Aug). No racing allowed.")
        else:
          log_message("No races match current filters for today.")

    # Check if goals is not met criteria AND it is not Pre-Debut AND it is not in restricted period AND turn is less than 10 AND Goal is already achieved
    if (current_date and not current_date.get('is_pre_debut', False) and
            not DateManager.is_restricted_period(current_date) and
            criteria.split(" ")[0] != "criteria" and
            year != "Junior Year Pre-Debut" and
            turn < 10 and
            criteria != "Goal Achievedl" and
            energy_percentage >= MINIMUM_ENERGY_PERCENTAGE):  # Only if energy is sufficient
      race_found = do_race()
      if race_found:
        return True
      else:
        # If there is no race matching to aptitude, go back and do training instead
        click(img="assets/buttons/back_btn.png", text="Race not found. Proceeding to training.")
        time.sleep(0.5)

    year_parts = year.split(" ")
    # If Prioritize G1 Race is true, check G1 race every turn - but not in restricted periods and only if energy is sufficient
    if (PRIORITIZE_G1_RACE and
            current_date and not current_date.get('is_pre_debut', False) and
            not DateManager.is_restricted_period(current_date) and
            year_parts[0] != "Junior" and
            len(year_parts) > 3 and
            year_parts[3] not in ["Jul", "Aug"] and
            energy_percentage >= MINIMUM_ENERGY_PERCENTAGE):  # Only if energy is sufficient
      g1_race_found = do_race(PRIORITIZE_G1_RACE)
      if g1_race_found:
        return True
      else:
        # If there is no G1 race, go back and do training
        click(img="assets/buttons/back_btn.png", text="G1 race not found. Proceeding to training.")
        time.sleep(0.5)

    # Skip training check if energy is critical
    if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
      log_message(f"Critical energy ({energy_percentage}%) - skipping training, resting instead")
      do_rest()
      return True

    # Check training button (only if energy allows training)
    if not go_to_training():
      log_message("Training button is not found.")
      return True

    # Last, do training (with energy consideration)
    time.sleep(0.5)
    results_training = check_training(energy_percentage)

    best_training = do_something(results_training, energy_percentage)
    if best_training:
      go_to_training()
      time.sleep(0.5)
      do_train(best_training)
      log_message(f"Training: {best_training.upper()}")
    else:
      # If no training is suitable, rest
      do_rest()
      if energy_percentage < CRITICAL_ENERGY_PERCENTAGE:
        log_message(f"Critical energy ({energy_percentage}%) - Resting")
      elif energy_percentage < MINIMUM_ENERGY_PERCENTAGE:
        log_message(f"Low energy ({energy_percentage}%) - WIT training not suitable, Resting")
      else:
        log_message("No suitable training found, Resting")
    time.sleep(1)
    return True

  except Exception as e:
    log_message(f"Error in career lobby iteration: {e}")
    return False

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