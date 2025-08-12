import pyautogui
import time
import json
import pygetwindow as gw

pyautogui.useImageNotFoundException(False)

from core.state import check_support_card, check_failure, check_turn, check_mood, check_current_year, check_criteria
from core.logic import do_something
from utils.constants import MOOD_LIST
from core.recognizer import is_infirmary_active, match_template
from utils.scenario import ura

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

def check_training():
  if not is_game_window_active():
    return {}

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
      support_counts = check_support_card()
      total_support = sum(support_counts.values())
      failure_chance = check_failure()
      results[key] = {
        "support": support_counts,
        "total_support": total_support,
        "failure": failure_chance
      }
      log_message(f"[{key.upper()}] → {support_counts}, Fail: {failure_chance}%")
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

  # Check if running with GUI
  if gui:
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
      if not career_lobby_iteration():
        time.sleep(1)
  else:
    # Original standalone mode
    while True:
      if not career_lobby_iteration():
        time.sleep(1)

def career_lobby_iteration():
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

    log_message("=" * 50)
    log_message(f"Year: {year}")
    log_message(f"Mood: {mood}")
    log_message(f"Turn: {turn}")

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

    # Check if goals is not met criteria AND it is not Pre-Debut AND turn is less than 10 AND Goal is already achieved
    if criteria.split(" ")[0] != "criteria" and year != "Junior Year Pre-Debut" and turn < 10 and criteria != "Goal Achievedl":
      race_found = do_race()
      if race_found:
        return True
      else:
        # If there is no race matching to aptitude, go back and do training instead
        click(img="assets/buttons/back_btn.png", text="Race not found. Proceeding to training.")
        time.sleep(0.5)

    year_parts = year.split(" ")
    # If Prioritize G1 Race is true, check G1 race every turn
    if PRIORITIZE_G1_RACE and year_parts[0] != "Junior" and len(year_parts) > 3 and year_parts[3] not in ["Jul", "Aug"]:
      g1_race_found = do_race(PRIORITIZE_G1_RACE)
      if g1_race_found:
        return True
      else:
        # If there is no G1 race, go back and do training
        click(img="assets/buttons/back_btn.png", text="G1 race not found. Proceeding to training.")
        time.sleep(0.5)

    # Check training button
    if not go_to_training():
      log_message("Training button is not found.")
      return True

    # Last, do training
    time.sleep(0.5)
    results_training = check_training()

    best_training = do_something(results_training)
    if best_training:
      go_to_training()
      time.sleep(0.5)
      do_train(best_training)
      log_message(f"Training: {best_training.upper()}")
    else:
      do_rest()
      log_message("Resting")
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