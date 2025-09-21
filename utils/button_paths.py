# This file contains all button image paths for Team Trials feature

import os

class TeamTrialsButtons:
    """Team Trials button image paths"""

    BASE_PATH = "assets/buttons/home/team_trials/"

    # Navigation buttons
    RACE_TAB = os.path.join(BASE_PATH, "race_tab.png")
    TEAM_TRIAL_BTN = os.path.join(BASE_PATH, "team_trial_btn.png")
    TEAM_RACE_BTN = os.path.join(BASE_PATH, "team_race_btn.png")

    # Battle related buttons
    PVP_WIN_GIFT = os.path.join(BASE_PATH, "pvp_win_gift.png")
    PARFAIT = os.path.join(BASE_PATH, "parfait.png")
    RACE_BTN = os.path.join(BASE_PATH, "race_btn.png")

    # Result handling buttons
    SEE_RESULT = os.path.join(BASE_PATH, "see_result.png")
    RACE_AGAIN_BTN = os.path.join(BASE_PATH, "race_again_btn.png")
    SHOP_BTN = os.path.join(BASE_PATH, "shop_btn.png")

    # Common buttons (should already exist in main assets)
    NEXT_BTN = "assets/buttons/next_btn.png"
    NEXT2_BTN = "assets/buttons/next2_btn.png"
    CANCEL_BTN = "assets/buttons/cancel_btn.png"
    NO_BTN = "assets/buttons/no_btn.png"

class ButtonRegions:
    """Screen regions for button detection"""

    # Home screen race tab area
    RACE_TAB_REGION = (200, 780, 680, 860)

    # PVP gift detection area
    PVP_GIFT_REGION = (200, 150, 700, 720)

    # Left half of screen for general checks
    LEFT_HALF_SCREEN = (0, 0, 960, 1080)

    # Opponent selection coordinates
    OPPONENT_COORDS = {
        "Opponent 1": (450, 230),
        "Opponent 2": (450, 420),
        "Opponent 3": (450, 600)
    }

    # Common click positions
    RESULT_CLICK_POS = (480, 240)

def ensure_button_directories():
    """Create button directories if they don't exist"""
    directories = [
        "assets/buttons/home/team_trials/",
        "assets/buttons/",
        "utils/"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def check_required_buttons():
    """Check if all required button images exist"""
    required_buttons = [
        TeamTrialsButtons.RACE_TAB,
        TeamTrialsButtons.TEAM_TRIAL_BTN,
        TeamTrialsButtons.TEAM_RACE_BTN,
        TeamTrialsButtons.PVP_WIN_GIFT,
        TeamTrialsButtons.PARFAIT,
        TeamTrialsButtons.RACE_BTN,
        TeamTrialsButtons.SEE_RESULT,
        TeamTrialsButtons.RACE_AGAIN_BTN,
        TeamTrialsButtons.SHOP_BTN,
        TeamTrialsButtons.NEXT_BTN,
        TeamTrialsButtons.NEXT2_BTN,
        TeamTrialsButtons.CANCEL_BTN,
        TeamTrialsButtons.NO_BTN
    ]

    missing_buttons = []
    for button_path in required_buttons:
        if not os.path.exists(button_path):
            missing_buttons.append(button_path)

    if missing_buttons:
        print("Missing button images:")
        for button in missing_buttons:
            print(f"  - {button}")
        print("\nPlease capture and save these button images for the Team Trials feature to work properly.")
        return False
    else:
        print("All required button images are present.")
        return True

if __name__ == "__main__":
    # Create directories and check buttons
    ensure_button_directories()
    check_required_buttons()