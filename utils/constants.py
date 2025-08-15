import json

# UI Region Constants
SUPPORT_CARD_ICON_REGION = (845, 155, 945, 700)
# MOOD_REGION = (733, 123, 807 - 740, 153 - 123)
MOOD_REGION = (740, 123, 806 - 740, 150 - 123)
TURN_REGION = (260, 88, 371 - 263, 135 - 88)
ENERGY_BAR = (441, 136, 685, 136)  # Hex Color 767576
RACE_REGION = (260, 588, 840 - 260, 854 - 588)
FAILURE_REGION = (275, 780, 826 - 275, 813 - 780)
YEAR_REGION = (255, 35, 420 - 255, 60 - 35)
CRITERIA_REGION = (455, 85, 625 - 455, 115 - 85)

# Mood Recognition Constants
MOOD_LIST = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT", "UNKNOWN"]

# Enhanced Mood Pattern Mapping for OCR Error Handling
MOOD_PATTERNS = {
    'AWFUL': [
        'AWFUL', 'AWUL', 'AWFL', 'AVVFUL', 'AWFUI', 'AWFU', 'AWF', 'AWFULL',
        'AWEFUL', 'AWFAL', 'AWFOL', 'WFL', 'FUL', 'WFUL', 'AVFUL', 'AWFIL', 'WFUL'
    ],
    'BAD': [
        'BAD', 'BD', 'BaD', 'BAO', 'BAP', 'B4D', 'BA', 'AD', 'BAC', 'BAN',
        'BAT', 'BRD', 'BED', 'BID', 'BOD', 'BUD', 'AD'
    ],
    'NORMAL': [
        'NORMAL', 'NORMAI', 'NORMOL', 'NORMALL', 'NORMM', 'NORRMAL', 'NORML',
        'NORAL', 'NORHAL', 'NORMAL', 'NORNIAL', 'NORMIL', 'NORMAEL', 'NORMUL',
        'NCRMAL', 'NORAML', 'NORMIAL', 'NOEMAL', 'NORMAI', 'HORMAL', 'NGRMAL', 'ORMAL',
    ],
    'GOOD': [
        'GOOD', 'GOD', 'GOOO', 'GOOP', 'GOoD', 'G00D', 'COOO', 'GOAD',
        'GOID', 'GOCD', 'GCOD', 'GORD', 'GOKD', 'GOUD', 'GOBD', 'GPOD','OOD',
    ],
    'GREAT': [
        'GREAT', 'CREAT', 'GRAT', 'GREAI', 'GRRAT', 'GRFAT', 'CRFAT', 'GREAK',
        'GREMT', 'GRIAT', 'GRDAT', 'GBEAT', 'TREAT', 'GREET', 'GREAT', 'GRAET',
        'GRELT', 'GRAAT', 'GRERT', 'GREHT', 'GREOT', 'GREIT', 'REAT'
    ]
}

# Load energy constants from config
try:
    with open("config.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    MINIMUM_ENERGY_PERCENTAGE = config["minimum_energy_percentage"]
    CRITICAL_ENERGY_PERCENTAGE = config["critical_energy_percentage"]
except (FileNotFoundError, KeyError):
    # Fallback values if config is not available
    MINIMUM_ENERGY_PERCENTAGE = 40
    CRITICAL_ENERGY_PERCENTAGE = 25

# Training Constants
TRAINING_TYPES = ["spd", "sta", "pwr", "guts", "wit"]

# NPC Support Types (now grouped as 'npc')
NPC_TYPES = ["akikawa", "etsuko"]

# Race Constants
RACE_GRADES = ["G1", "G2", "G3", "OP", "Unknown"]
TRACK_TYPES = ["turf", "dirt"]
DISTANCE_CATEGORIES = ["sprint", "mile", "medium", "long"]

# Career Stage Constants
PRE_DEBUT_DAY_THRESHOLD = 24
RAINBOW_STAGE_DAY_THRESHOLD = 24
EARLY_STAGE_DAY_THRESHOLD = 16
CAREER_RESTRICTION_DAY_THRESHOLD = 16
TOTAL_CAREER_DAYS = 72

# Score Constants
HINT_SCORE_EARLY = 1.0  # Day < 36
HINT_SCORE_LATE = 0.5   # Day >= 36
NPC_SCORE_VALUE = 0.5   # Each NPC support card (grouped)
RAINBOW_MULTIPLIER = 2  # Rainbow cards in rainbow stage

# UI Click Constants
DEFAULT_CLICK_CONFIDENCE = 0.8
DEFAULT_SEARCH_TIME = 2.0
RANDOM_CLICK_PADDING_RATIO = 0.1  # 10% padding for random clicks

# System Constants
MAX_CAREER_LOBBY_ATTEMPTS = 20
EVENT_WAIT_TIMEOUT = 300  # 5 minutes
STABILITY_CHECK_RETRIES = 3

# File Paths
RACE_DATA_FILE = "assets/race_list.json"
CONFIG_FILE = "config.json"
BOT_SETTINGS_FILE = "bot_settings.json"

# Asset Paths
ASSETS_DIR = "assets"
ICONS_DIR = f"{ASSETS_DIR}/icons"
BUTTONS_DIR = f"{ASSETS_DIR}/buttons"
UI_DIR = f"{ASSETS_DIR}/ui"

# Button Assets
TRAINING_BUTTON = f"{BUTTONS_DIR}/training_btn.png"
RACES_BUTTON = f"{BUTTONS_DIR}/races_btn.png"
REST_BUTTON = f"{BUTTONS_DIR}/rest_btn.png"
RECREATION_BUTTON = f"{BUTTONS_DIR}/recreation_btn.png"
BACK_BUTTON = f"{BUTTONS_DIR}/back_btn.png"
NEXT_BUTTON = f"{BUTTONS_DIR}/next_btn.png"
OK_BUTTON = f"{BUTTONS_DIR}/ok_btn.png"
CANCEL_BUTTON = f"{BUTTONS_DIR}/cancel_btn.png"

# Training Icons
TRAIN_SPD_ICON = f"{ICONS_DIR}/train_spd.png"
TRAIN_STA_ICON = f"{ICONS_DIR}/train_sta.png"
TRAIN_PWR_ICON = f"{ICONS_DIR}/train_pwr.png"
TRAIN_GUTS_ICON = f"{ICONS_DIR}/train_guts.png"
TRAIN_WIT_ICON = f"{ICONS_DIR}/train_wit.png"

# Support Card Icons
SUPPORT_SPD_ICON = f"{ICONS_DIR}/support_card_type_spd.png"
SUPPORT_STA_ICON = f"{ICONS_DIR}/support_card_type_sta.png"
SUPPORT_PWR_ICON = f"{ICONS_DIR}/support_card_type_pwr.png"
SUPPORT_GUTS_ICON = f"{ICONS_DIR}/support_card_type_guts.png"
SUPPORT_WIT_ICON = f"{ICONS_DIR}/support_card_type_wit.png"
SUPPORT_FRIEND_ICON = f"{ICONS_DIR}/support_card_type_friend.png"
SUPPORT_HINT_ICON = f"{ICONS_DIR}/support_card_hint.png"

# NPC Support Icons (now grouped as 'npc')
SUPPORT_NPC_AKIKAWA = f"{ICONS_DIR}/support_npc_akikawa.png"
SUPPORT_NPC_ETSUKO = f"{ICONS_DIR}/support_npc_etsuko.png"

# UI Elements
TAZUNA_HINT = f"{UI_DIR}/tazuna_hint.png"
MATCH_TRACK = f"{UI_DIR}/match_track.png"
G1_RACE = f"{UI_DIR}/g1_race.png"
G2_RACE = f"{UI_DIR}/g2_race.png"
G3_RACE = f"{UI_DIR}/g3_race.png"

# Event Icons
EVENT_CHOICE_1 = f"{ICONS_DIR}/event_choice_1.png"

# Training Icon Mapping
TRAINING_ICONS = {
    "spd": TRAIN_SPD_ICON,
    "sta": TRAIN_STA_ICON,
    "pwr": TRAIN_PWR_ICON,
    "guts": TRAIN_GUTS_ICON,
    "wit": TRAIN_WIT_ICON
}

# Support Card Icon Mapping
SUPPORT_ICONS = {
    "spd": SUPPORT_SPD_ICON,
    "sta": SUPPORT_STA_ICON,
    "pwr": SUPPORT_PWR_ICON,
    "guts": SUPPORT_GUTS_ICON,
    "wit": SUPPORT_WIT_ICON,
    "friend": SUPPORT_FRIEND_ICON
}

# NPC Icon Mapping (individual detection but grouped as 'npc')
NPC_ICONS = {
    "akikawa": SUPPORT_NPC_AKIKAWA,
    "etsuko": SUPPORT_NPC_ETSUKO
}

# Race Grade Icon Mapping
RACE_GRADE_ICONS = {
    "G1": G1_RACE,
    "G2": G2_RACE,
    "G3": G3_RACE
}

# Strategy Mappings
PRIORITY_STRATEGIES = [
    "G1 (no training)",
    "G2 (no training)",
    "Train Score 2+",
    "Train Score 2.5+",
    "Train Score 3+",
    "Train Score 3.5+"
]

MINIMUM_MOODS = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"]

# Energy Status Colors for GUI
ENERGY_COLORS = {
    'high': 'green',    # >= minimum_energy
    'medium': 'orange', # critical_energy to minimum_energy
    'critical': 'red'   # < critical_energy
}