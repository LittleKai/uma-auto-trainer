import json
from utils.constants_support import (
    # Import mood patterns và configs từ support file
    MOOD_PATTERNS,
    GOOD_BAD_CONFUSION_MAP,
    MOOD_CONFIDENCE_LEVELS,
    MOOD_OCR_CONFIG,
    MOOD_DETECTION_PRIORITY,
    MOOD_DEBUG_CONFIG,
    MOOD_FALLBACK_CONFIG,
    DEFAULT_REGIONS
)

# Career Stage Constants
PRE_DEBUT_DAY_THRESHOLD = 24
RAINBOW_STAGE_DAY_THRESHOLD = 24
EARLY_STAGE_DAY_THRESHOLD = 16
CAREER_RESTRICTION_DAY_THRESHOLD = 16
TOTAL_CAREER_DAYS = 75

# Score Constants
HINT_SCORE_EARLY = 1.0  # Day < 36
HINT_SCORE_LATE = 0.5   # Day >= 36
NPC_SCORE_VALUE = 0.5   # Each NPC support card (grouped)
RAINBOW_MULTIPLIER = 2  # Rainbow cards in rainbow stage

# UI Click Constants
DEFAULT_CLICK_CONFIDENCE = 0.7
DEFAULT_SEARCH_TIME = 2.0
RANDOM_CLICK_PADDING_RATIO = 0.1  # 10% padding for random clicks

# System Constants
MAX_CAREER_LOBBY_ATTEMPTS = 12
EVENT_WAIT_TIMEOUT = 120  # 5 minutes
STABILITY_CHECK_RETRIES = 3

# UI Region Constants
SUPPORT_CARD_ICON_REGION = (820, 155, 120, 700)
MOOD_REGION = (700, 123, 120, 27)
ENERGY_BAR = (440, 136, 710, 136)  # Energy bar endpoints (x1, y1, x2, y2)
RACE_REGION = (260, 588, 580, 266)

TURN_REGION = (260, 84, 112, 47)
YEAR_REGION = (255, 35, 165, 22)
UNITY_CUP_TURN_REGION = (265, 57, 60, 47)
UNITY_CUP_YEAR_REGION = (390, 37, 165, 16)

FAILURE_REGION = (275, 780, 551, 33)
CRITERIA_REGION = (450, 64, 300, 25)

# Event Choice Regions
EVENT_REGIONS = {
    "EVENT_REGION": (240, 173, 240, 25),
    "EVENT_NAME_REGION": (240, 200, 360, 40)
}

# Stat regions for OCR recognition
STAT_REGIONS = {
    "spd": (310, 723, 55, 20),
    "sta": (405, 723, 55, 20),
    "pwr": (500, 723, 55, 20),
    "guts": (595, 723, 55, 20),
    "wit": (690, 723, 55, 20)
}

# Mood Recognition Constants
MOOD_LIST = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT", "UNKNOWN"]

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

# File Paths
RACE_DATA_FILE = "assets/race_list.json"
CONFIG_FILE = "config.json"
BOT_SETTINGS_FILE = "bot_settings.json"
REGION_SETTINGS_FILE = "region_settings.json"

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

# Status Icons
HINT_ICON = f"{ICONS_DIR}/hint.png"
RAINBOW_ICON = f"{ICONS_DIR}/rainbow.png"

# Race Type Icons
TURF_ICON = f"{ICONS_DIR}/turf.png"
DIRT_ICON = f"{ICONS_DIR}/dirt.png"

# Distance Icons
SPRINT_ICON = f"{ICONS_DIR}/sprint.png"
MILE_ICON = f"{ICONS_DIR}/mile.png"
MEDIUM_ICON = f"{ICONS_DIR}/medium.png"
LONG_ICON = f"{ICONS_DIR}/long.png"

# Race Grade Icons
G1_ICON = f"{ICONS_DIR}/g1.png"
G2_ICON = f"{ICONS_DIR}/g2.png"
G3_ICON = f"{ICONS_DIR}/g3.png"
OP_ICON = f"{ICONS_DIR}/op.png"

# Additional UI Elements
START_BUTTON = f"{UI_DIR}/start_btn.png"
RETIRE_BUTTON = f"{UI_DIR}/retire_btn.png"
CONFIRM_BUTTON = f"{UI_DIR}/confirm_btn.png"

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

# Event Choice Icons
EVENT_CHOICE_1 = f"{ICONS_DIR}/event_choice_1.png"
EVENT_CHOICE_2 = f"{ICONS_DIR}/event_choice_2.png"
EVENT_CHOICE_3 = f"{ICONS_DIR}/event_choice_3.png"
EVENT_CHOICE_4 = f"{ICONS_DIR}/event_choice_4.png"
EVENT_CHOICE_5 = f"{ICONS_DIR}/event_choice_5.png"

# Event Type Icons
TRAIN_EVENT_SCENARIO = f"{ICONS_DIR}/train_event_scenario.png"
TRAIN_EVENT_UMA_MUSUME = f"{ICONS_DIR}/train_event_uma_musume.png"
TRAIN_EVENT_SUPPORT_CARD = f"{ICONS_DIR}/train_event_support_card.png"

# UI Elements
TAZUNA_HINT = f"{UI_DIR}/tazuna_hint.png"
MATCH_TRACK = f"{UI_DIR}/match_track.png"
G1_RACE = f"{UI_DIR}/g1_race.png"
G2_RACE = f"{UI_DIR}/g2_race.png"
G3_RACE = f"{UI_DIR}/g3_race.png"

# Event Icons
EVENT_CHOICE_1_OLD = f"{ICONS_DIR}/event_choice_1.png"

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

# Backward compatibility aliases
NPC_SUPPORT_AKIKAWA_ICON = SUPPORT_NPC_AKIKAWA
NPC_SUPPORT_ETSUKO_ICON = SUPPORT_NPC_ETSUKO

# Event Choice Icon Mapping
EVENT_CHOICE_ICONS = {
    1: EVENT_CHOICE_1,
    2: EVENT_CHOICE_2,
    3: EVENT_CHOICE_3,
    4: EVENT_CHOICE_4,
    5: EVENT_CHOICE_5
}

# Event Type Icon Mapping
EVENT_TYPE_ICONS = {
    "train_event_scenario": TRAIN_EVENT_SCENARIO,
    "train_event_uma_musume": TRAIN_EVENT_UMA_MUSUME,
    "train_event_support_card": TRAIN_EVENT_SUPPORT_CARD
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
    "Train Score 2+",
    "Train Score 2.5+",
    "Train Score 3+",
    "Train Score 3.5+",
    "Train Score 4+"
]

MINIMUM_MOODS = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"]

# Energy Status Colors for GUI
ENERGY_COLORS = {
    'high': 'green',    # >= minimum_energy
    'medium': 'orange', # critical_energy to minimum_energy
    'critical': 'red'   # < critical_energy
}

# Global scenario selection
SCENARIO_NAME = "URA Final"  # Default value

# =============================================================================
# DECK & STAT CAPS MANAGEMENT
# =============================================================================

# Default stat caps
DEFAULT_STAT_CAPS = {
    "spd": 1200,
    "sta": 1100,
    "pwr": 1200,
    "guts": 1200,
    "wit": 1200
}

# Current deck information (set from GUI presets)
CURRENT_DECK = {
    "uma_musume": "None",
    "support_cards": ["None"] * 6,
    "stat_caps": DEFAULT_STAT_CAPS.copy(),
    "card_type_counts": {
        "spd": 0,
        "sta": 0,
        "pwr": 0,
        "pow": 0,  # Alias for pwr
        "guts": 0,
        "gut": 0,  # Alias for guts
        "wit": 0,
        "frd": 0,
        "friend": 0  # Alias for frd
    }
}


def set_deck_info(uma_musume: str, support_cards: list, stat_caps: dict = None):
    """Set current deck information from GUI preset

    Args:
        uma_musume: Name of the selected Uma Musume
        support_cards: List of 6 support card strings (format: "type: Card Name (Rarity)")
        stat_caps: Dictionary of stat caps {spd, sta, pwr, guts, wit}
    """
    global CURRENT_DECK

    CURRENT_DECK["uma_musume"] = uma_musume
    CURRENT_DECK["support_cards"] = support_cards.copy() if support_cards else ["None"] * 6
    CURRENT_DECK["stat_caps"] = stat_caps.copy() if stat_caps else DEFAULT_STAT_CAPS.copy()

    # Calculate card type counts
    card_counts = {
        "spd": 0, "sta": 0, "pwr": 0, "pow": 0,
        "guts": 0, "gut": 0, "wit": 0,
        "frd": 0, "friend": 0
    }

    for card in support_cards:
        if card and card != "None" and ":" in card:
            card_type = card.split(":")[0].strip().lower()
            if card_type in card_counts:
                card_counts[card_type] += 1
                # Handle aliases
                if card_type == "pow":
                    card_counts["pwr"] += 1
                elif card_type == "pwr":
                    card_counts["pow"] += 1
                elif card_type == "gut":
                    card_counts["guts"] += 1
                elif card_type == "guts":
                    card_counts["gut"] += 1
                elif card_type == "frd":
                    card_counts["friend"] += 1
                elif card_type == "friend":
                    card_counts["frd"] += 1

    CURRENT_DECK["card_type_counts"] = card_counts

    print(f"[DECK] Updated deck info: {uma_musume}")
    print(f"[DECK] Card counts: {card_counts}")
    print(f"[DECK] Stat caps: {CURRENT_DECK['stat_caps']}")


def get_deck_info() -> dict:
    """Get current deck information

    Returns:
        Dictionary containing uma_musume, support_cards, stat_caps, card_type_counts
    """
    return CURRENT_DECK.copy()


def get_deck_card_count(card_type: str) -> int:
    """Get count of specific card type in current deck

    Args:
        card_type: Type of card (spd, sta, pwr/pow, guts/gut, wit, frd/friend)

    Returns:
        Number of cards of that type in the deck
    """
    card_type = card_type.lower()
    return CURRENT_DECK["card_type_counts"].get(card_type, 0)


def get_stat_caps() -> dict:
    """Get current stat caps from deck

    Returns:
        Dictionary of stat caps {spd, sta, pwr, guts, wit}
    """
    return CURRENT_DECK["stat_caps"].copy()


def deck_has_card_type(card_type: str, min_count: int = 1) -> bool:
    """Check if deck has at least min_count cards of specified type

    Args:
        card_type: Type of card to check
        min_count: Minimum number of cards required

    Returns:
        True if deck has at least min_count cards of that type
    """
    return get_deck_card_count(card_type) >= min_count

# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================

def load_region_settings():
    """Load region settings from file or return defaults"""
    try:
        with open(REGION_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_REGIONS.copy()

def save_region_settings(regions):
    """Save region settings to file"""
    try:
        with open(REGION_SETTINGS_FILE, 'w') as f:
            json.dump(regions, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving region settings: {e}")
        return False

def get_turn_year_regions():
    """Get TURN_REGION and YEAR_REGION based on global scenario selection"""
    settings = load_region_settings()

    # Load all turn/year regions
    turn_region = tuple(settings.get('TURN_REGION', DEFAULT_REGIONS['TURN_REGION']))
    year_region = tuple(settings.get('YEAR_REGION', DEFAULT_REGIONS['YEAR_REGION']))
    unity_cup_turn_region = tuple(settings.get('UNITY_CUP_TURN_REGION', DEFAULT_REGIONS['UNITY_CUP_TURN_REGION']))
    unity_cup_year_region = tuple(settings.get('UNITY_CUP_YEAR_REGION', DEFAULT_REGIONS['UNITY_CUP_YEAR_REGION']))
    print(f'scenario: {SCENARIO_NAME}')
    # Select active regions based on global scenario
    if SCENARIO_NAME == "Unity Cup":
        active_turn_region = unity_cup_turn_region
        active_year_region = unity_cup_year_region
    else:  # "URA Final" or default
        active_turn_region = turn_region
        active_year_region = year_region

    return {
        'TURN_REGION': active_turn_region,
        'YEAR_REGION': active_year_region,
        'UNITY_CUP_TURN_REGION': unity_cup_turn_region,
        'UNITY_CUP_YEAR_REGION': unity_cup_year_region
    }

def get_current_regions():
    """Get current region values, loading from file if available"""
    global SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, ENERGY_BAR
    global RACE_REGION, FAILURE_REGION, YEAR_REGION, CRITERIA_REGION, STAT_REGIONS, EVENT_REGIONS
    global UNITY_CUP_TURN_REGION, UNITY_CUP_YEAR_REGION

    settings = load_region_settings()

    # Update global variables with loaded settings
    SUPPORT_CARD_ICON_REGION = tuple(settings.get('SUPPORT_CARD_ICON_REGION', DEFAULT_REGIONS['SUPPORT_CARD_ICON_REGION']))
    MOOD_REGION = tuple(settings.get('MOOD_REGION', DEFAULT_REGIONS['MOOD_REGION']))
    TURN_REGION = tuple(settings.get('TURN_REGION', DEFAULT_REGIONS['TURN_REGION']))
    ENERGY_BAR = tuple(settings.get('ENERGY_BAR', DEFAULT_REGIONS['ENERGY_BAR']))
    RACE_REGION = tuple(settings.get('RACE_REGION', DEFAULT_REGIONS['RACE_REGION']))
    FAILURE_REGION = tuple(settings.get('FAILURE_REGION', DEFAULT_REGIONS['FAILURE_REGION']))
    YEAR_REGION = tuple(settings.get('YEAR_REGION', DEFAULT_REGIONS['YEAR_REGION']))
    UNITY_CUP_TURN_REGION = tuple(settings.get('UNITY_CUP_TURN_REGION', DEFAULT_REGIONS['UNITY_CUP_TURN_REGION']))
    UNITY_CUP_YEAR_REGION = tuple(settings.get('UNITY_CUP_YEAR_REGION', DEFAULT_REGIONS['UNITY_CUP_YEAR_REGION']))
    CRITERIA_REGION = tuple(settings.get('CRITERIA_REGION', DEFAULT_REGIONS['CRITERIA_REGION']))
    STAT_REGIONS = settings.get('STAT_REGIONS', DEFAULT_REGIONS['STAT_REGIONS'])
    EVENT_REGIONS = settings.get('EVENT_REGIONS', DEFAULT_REGIONS['EVENT_REGIONS'])

    return {
        'SUPPORT_CARD_ICON_REGION': SUPPORT_CARD_ICON_REGION,
        'MOOD_REGION': MOOD_REGION,
        'TURN_REGION': TURN_REGION,
        'ENERGY_BAR': ENERGY_BAR,
        'RACE_REGION': RACE_REGION,
        'FAILURE_REGION': FAILURE_REGION,
        'YEAR_REGION': YEAR_REGION,
        'UNITY_CUP_TURN_REGION': UNITY_CUP_TURN_REGION,
        'UNITY_CUP_YEAR_REGION': UNITY_CUP_YEAR_REGION,
        'CRITERIA_REGION': CRITERIA_REGION,
        'STAT_REGIONS': STAT_REGIONS,
        'EVENT_REGIONS': EVENT_REGIONS
    }

def update_regions(new_regions):
    """Update region values and save to file"""
    global SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, ENERGY_BAR
    global RACE_REGION, FAILURE_REGION, YEAR_REGION, CRITERIA_REGION, STAT_REGIONS, EVENT_REGIONS
    global UNITY_CUP_TURN_REGION, UNITY_CUP_YEAR_REGION

    # Update global variables
    SUPPORT_CARD_ICON_REGION = tuple(new_regions.get('SUPPORT_CARD_ICON_REGION', SUPPORT_CARD_ICON_REGION))
    MOOD_REGION = tuple(new_regions.get('MOOD_REGION', MOOD_REGION))
    TURN_REGION = tuple(new_regions.get('TURN_REGION', TURN_REGION))
    ENERGY_BAR = tuple(new_regions.get('ENERGY_BAR', ENERGY_BAR))
    RACE_REGION = tuple(new_regions.get('RACE_REGION', RACE_REGION))
    FAILURE_REGION = tuple(new_regions.get('FAILURE_REGION', FAILURE_REGION))
    YEAR_REGION = tuple(new_regions.get('YEAR_REGION', YEAR_REGION))
    UNITY_CUP_TURN_REGION = tuple(new_regions.get('UNITY_CUP_TURN_REGION', UNITY_CUP_TURN_REGION))
    UNITY_CUP_YEAR_REGION = tuple(new_regions.get('UNITY_CUP_YEAR_REGION', UNITY_CUP_YEAR_REGION))
    CRITERIA_REGION = tuple(new_regions.get('CRITERIA_REGION', CRITERIA_REGION))
    STAT_REGIONS = new_regions.get('STAT_REGIONS', STAT_REGIONS)
    EVENT_REGIONS = new_regions.get('EVENT_REGIONS', EVENT_REGIONS)

    # Save to file
    current_regions = {
        'SUPPORT_CARD_ICON_REGION': SUPPORT_CARD_ICON_REGION,
        'MOOD_REGION': MOOD_REGION,
        'TURN_REGION': TURN_REGION,
        'ENERGY_BAR': ENERGY_BAR,
        'RACE_REGION': RACE_REGION,
        'FAILURE_REGION': FAILURE_REGION,
        'YEAR_REGION': YEAR_REGION,
        'UNITY_CUP_TURN_REGION': UNITY_CUP_TURN_REGION,
        'UNITY_CUP_YEAR_REGION': UNITY_CUP_YEAR_REGION,
        'CRITERIA_REGION': CRITERIA_REGION,
        'STAT_REGIONS': STAT_REGIONS,
        'EVENT_REGIONS': EVENT_REGIONS
    }

    return save_region_settings(current_regions)

def set_scenario(scenario_name):
    """Set global scenario name"""
    global SCENARIO_NAME
    SCENARIO_NAME = scenario_name

def get_scenario():
    """Get current scenario name"""
    return SCENARIO_NAME

def load_scenario_from_settings():
    """Load scenario from bot_settings.json and update global variable"""
    global SCENARIO_NAME
    try:
        with open('bot_settings.json', 'r') as f:
            bot_settings = json.load(f)
            SCENARIO_NAME = bot_settings.get('scenario', 'URA Final')
    except (FileNotFoundError, json.JSONDecodeError):
        SCENARIO_NAME = "URA Final"
    return SCENARIO_NAME

def get_mood_config():
    """Get current mood detection configuration"""
    return {
        "ocr": MOOD_OCR_CONFIG,
        "priority": MOOD_DETECTION_PRIORITY,
        "debug": MOOD_DEBUG_CONFIG,
        "fallback": MOOD_FALLBACK_CONFIG,
    }

def update_mood_config(**kwargs):
    """Update mood detection configuration"""
    global MOOD_OCR_CONFIG, MOOD_DETECTION_PRIORITY, MOOD_DEBUG_CONFIG, MOOD_FALLBACK_CONFIG

    if "ocr" in kwargs:
        MOOD_OCR_CONFIG.update(kwargs["ocr"])

    if "priority" in kwargs:
        MOOD_DETECTION_PRIORITY.update(kwargs["priority"])

    if "debug" in kwargs:
        MOOD_DEBUG_CONFIG.update(kwargs["debug"])

    if "fallback" in kwargs:
        MOOD_FALLBACK_CONFIG.update(kwargs["fallback"])

# =============================================================================
# INITIALIZATION
# =============================================================================

# Initialize regions on module import
_regions_initialized = False

def _initialize_regions():
    """Initialize regions from saved settings"""
    global _regions_initialized
    if not _regions_initialized:
        get_current_regions()
        _regions_initialized = True

# Ensure regions are loaded when module is imported
_initialize_regions()