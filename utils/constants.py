import json

# UI Region Constants
SUPPORT_CARD_ICON_REGION = (845, 155, 180, 700)
MOOD_REGION = (700, 123, 120, 27)
TURN_REGION = (260, 84, 108, 47)
ENERGY_BAR = (440, 136, 705, 136)  # Energy bar endpoints (x1, y1, x2, y2)
RACE_REGION = (260, 588, 580, 266)
FAILURE_REGION = (275, 780, 551, 33)
YEAR_REGION = (255, 35, 165, 22)
CRITERIA_REGION = (455, 85, 170, 26)

# Event Choice Regions
EVENT_REGIONS = {
    "EVENT_REGION": (240, 173, 240, 25),
    "EVENT_NAME_REGION": (240, 200, 400, 40)
}

# Stat regions for OCR recognition
STAT_REGIONS = {
    "spd": (310, 723, 55, 20),
    "sta": (405, 723, 55, 20),
    "pwr": (500, 723, 55, 20),
    "guts": (595, 723, 55, 20),
    "wit": (690, 723, 55, 20)
}

# Default regions for settings reset
DEFAULT_REGIONS = {
    'SUPPORT_CARD_ICON_REGION': (845, 155, 180, 700),
    'MOOD_REGION': (700, 123, 120, 27),
    'TURN_REGION': (260, 84, 108, 47),
    'ENERGY_BAR': (440, 136, 705, 136),
    'RACE_REGION': (260, 588, 580, 266),
    'FAILURE_REGION': (275, 780, 551, 33),
    'YEAR_REGION': (255, 35, 165, 22),
    'CRITERIA_REGION': (455, 85, 170, 26),
    'STAT_REGIONS': {
        "spd": (310, 723, 55, 20),
        "sta": (405, 723, 55, 20),
        "pwr": (500, 723, 55, 20),
        "guts": (595, 723, 55, 20),
        "wit": (690, 723, 55, 20)
    },
    'EVENT_REGIONS': {
        "EVENT_REGION": (240, 173, 240, 25),
        "EVENT_NAME_REGION": (240, 200, 400, 40)
    }
}

# Mood Recognition Constants
MOOD_LIST = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT", "UNKNOWN"]

# Enhanced Mood Pattern Mapping for OCR Error Handling with improved GOOD vs BAD logic
MOOD_PATTERNS = {
    'AWFUL': [
        'AWFUL', 'AWUL', 'AWFL', 'AVVFUL', 'AWFUI', 'AWFU', 'AWF', 'AWFULL',
        'AWEFUL', 'AWFAL', 'AWFOL', 'WFL', 'FUL', 'WFUL', 'AVFUL', 'AWFIL', 'WFUL',
        'AWFUI', 'AWFAL', 'AVVUL', 'AWFOL', 'AVFUL', 'AWFOL', 'AWFIL'
    ],
    'BAD': [
        'BAD', 'BD', 'BaD', 'BAO', 'BAP', 'B4D', 'BA', 'BAC', 'BAN',
        'BAT', 'BRD', 'BED', 'BID', 'BOD', 'BUD'
        # Note: Removed 'AD' alone as it's too ambiguous and can be part of GOOD partials
        # Strict BAD detection to prevent confusion with GOOD
    ],
    'NORMAL': [
        'NORMAL', 'NORMAI', 'NORMOL', 'NORMALL', 'NORMM', 'NORRMAL', 'NORML',
        'NORAL', 'NORHAL', 'NORMAL', 'NORNIAL', 'NORMIL', 'NORMAEL', 'NORMUL',
        'NCRMAL', 'NORAML', 'NORMIAL', 'NOEMAL', 'NORMAI', 'HORMAL', 'NGRMAL', 'ORMAL',
        'NORAML', 'NORMSL', 'NORMEAL', 'NORMAI', 'NORNAL', 'NORMLA'
    ],
    'GOOD': [
        'GOOD', 'GOD', 'GOOO', 'GOOP', 'GOoD', 'G00D', 'COOO', 'GOAD',
        'GOID', 'GOCD', 'GCOD', 'GORD', 'GOKD', 'GOUD', 'GOBD', 'GPOD','OOD',
        'GOO', 'GOOD', 'GODD', 'GODO', 'GODOD', 'GOQD', 'GOOT', 'GOOF',
        # Additional patterns for GOOD that are commonly misread
        'G0OD', 'GO0D', 'GOO0', 'GOCD', 'GQOD', 'GOOS', 'GOOL', 'COOD',
        'GOOQ', 'GOOC', 'GOOB', 'GOON', 'GOODD', 'GOOOD'
    ],
    'GREAT': [
        'GREAT', 'CREAT', 'GRAT', 'GREAI', 'GRRAT', 'GRFAT', 'CRFAT', 'GREAK',
        'GREMT', 'GRIAT', 'GRDAT', 'GBEAT', 'TREAT', 'GREET', 'GREAT', 'GRAET',
        'GRELT', 'GRAAT', 'GRERT', 'GREHT', 'GREOT', 'GREIT', 'REAT',
        'GREAI', 'GREATE', 'CREAT', 'GRFAT', 'GREAL', 'GRFAT', 'GRENT'
    ]
}

# Additional mapping for common OCR confusions specifically for GOOD vs BAD
GOOD_BAD_CONFUSION_MAP = {
    # These should always map to GOOD, never BAD
    'GOD': 'GOOD',
    'OOD': 'GOOD',
    'GOO': 'GOOD',
    'GOOP': 'GOOD',
    'GOOO': 'GOOD',
    'COOO': 'GOOD',
    'G00D': 'GOOD',
    'GO0D': 'GOOD',
    'G0OD': 'GOOD',
    'COOD': 'GOOD',
    'GCOD': 'GOOD',

    # These should always map to BAD
    'BD': 'BAD',
    'B4D': 'BAD',
    'BAO': 'BAD',
    'BAP': 'BAD',
    'BRD': 'BAD',
    'BED': 'BAD',
}

# Confidence levels for mood detection
MOOD_CONFIDENCE_LEVELS = {
    'HIGH': ['AWFUL', 'NORMAL', 'GREAT'],    # These are usually detected correctly
    'MEDIUM': ['GOOD', 'BAD'],               # These are prone to confusion
    'LOW': ['UNKNOWN']                       # Fallback
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
DEFAULT_CLICK_CONFIDENCE = 0.7
DEFAULT_SEARCH_TIME = 2.0
RANDOM_CLICK_PADDING_RATIO = 0.1  # 10% padding for random clicks

# System Constants
MAX_CAREER_LOBBY_ATTEMPTS = 30
EVENT_WAIT_TIMEOUT = 300  # 5 minutes
STABILITY_CHECK_RETRIES = 3

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
    "G2 (no training)",
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

# OCR Enhancement Settings for Mood Detection
MOOD_OCR_CONFIG = {
    # Image preprocessing
    "resize_scale": 3,              # Scale factor for image resizing (1-5)
    "contrast_enhance": 2.0,        # Contrast enhancement factor (1.0-3.0)
    "brightness_adjust": 10,        # Brightness adjustment (-50 to +50)
    "sharpening": True,             # Apply sharpening filter
    "threshold": 128,               # Binary threshold (0-255)

    # OCR methods to try
    "ocr_methods": {
        "standard": {"psm": 6, "whitelist": None},
        "char_whitelist": {"psm": 8, "whitelist": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
        "single_word": {"psm": 7, "whitelist": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"},
        "raw_line": {"psm": 13, "whitelist": None},
    },

    # Confidence thresholds
    "min_text_length": 2,           # Minimum text length to consider
    "max_attempts": 4,              # Maximum OCR attempts per image
}

# Pattern matching priority for mood detection
MOOD_DETECTION_PRIORITY = {
    # High confidence patterns (rarely misread)
    "high_confidence": ["AWFUL", "NORMAL", "GREAT"],

    # Medium confidence (prone to OCR errors)
    "medium_confidence": ["GOOD", "BAD"],

    # Special handling patterns for GOOD vs BAD confusion
    "good_indicators": [
        "GOD", "OOD", "GOO", "GOOP", "GOOO", "COOO",
        "G00D", "GO0D", "G0OD", "GCOD", "GQOD", "COOD"
    ],

    "bad_indicators": [
        "BD", "B4D", "BAO", "BAP", "BRD", "BED"
    ],

    # Patterns that should never be confused
    "never_confuse": {
        "GOD": "GOOD",      # Never classify as BAD
        "OOD": "GOOD",      # Never classify as BAD
        "GOO": "GOOD",      # Never classify as BAD
    }
}

# Debug settings for mood detection
MOOD_DEBUG_CONFIG = {
    "enable_debug_logs": True,      # Enable detailed debug output
    "save_debug_images": False,     # Save processed images for debugging
    "debug_image_path": "debug/mood/",  # Path to save debug images
    "log_all_ocr_results": True,    # Log all OCR attempts
    "log_pattern_matching": True,   # Log pattern matching process
}

# Fallback behavior for mood detection
MOOD_FALLBACK_CONFIG = {
    "unknown_threshold": 0.7,       # If confidence < this, return UNKNOWN
    "prefer_previous_mood": False,  # Use previous mood if uncertain
    "default_mood": "NORMAL",       # Fallback mood if all else fails
    "retry_on_unknown": True,       # Retry if first attempt returns UNKNOWN
    "max_retries": 2,               # Maximum retry attempts
}

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

def get_current_regions():
    """Get current region values, loading from file if available"""
    global SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, ENERGY_BAR
    global RACE_REGION, FAILURE_REGION, YEAR_REGION, CRITERIA_REGION, STAT_REGIONS, EVENT_REGIONS

    settings = load_region_settings()

    # Update global variables with loaded settings
    SUPPORT_CARD_ICON_REGION = tuple(settings.get('SUPPORT_CARD_ICON_REGION', DEFAULT_REGIONS['SUPPORT_CARD_ICON_REGION']))
    MOOD_REGION = tuple(settings.get('MOOD_REGION', DEFAULT_REGIONS['MOOD_REGION']))
    TURN_REGION = tuple(settings.get('TURN_REGION', DEFAULT_REGIONS['TURN_REGION']))
    ENERGY_BAR = tuple(settings.get('ENERGY_BAR', DEFAULT_REGIONS['ENERGY_BAR']))
    RACE_REGION = tuple(settings.get('RACE_REGION', DEFAULT_REGIONS['RACE_REGION']))
    FAILURE_REGION = tuple(settings.get('FAILURE_REGION', DEFAULT_REGIONS['FAILURE_REGION']))
    YEAR_REGION = tuple(settings.get('YEAR_REGION', DEFAULT_REGIONS['YEAR_REGION']))
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
        'CRITERIA_REGION': CRITERIA_REGION,
        'STAT_REGIONS': STAT_REGIONS,
        'EVENT_REGIONS': EVENT_REGIONS
    }

def update_regions(new_regions):
    """Update region values and save to file"""
    global SUPPORT_CARD_ICON_REGION, MOOD_REGION, TURN_REGION, ENERGY_BAR
    global RACE_REGION, FAILURE_REGION, YEAR_REGION, CRITERIA_REGION, STAT_REGIONS, EVENT_REGIONS

    # Update global variables
    SUPPORT_CARD_ICON_REGION = tuple(new_regions.get('SUPPORT_CARD_ICON_REGION', SUPPORT_CARD_ICON_REGION))
    MOOD_REGION = tuple(new_regions.get('MOOD_REGION', MOOD_REGION))
    TURN_REGION = tuple(new_regions.get('TURN_REGION', TURN_REGION))
    ENERGY_BAR = tuple(new_regions.get('ENERGY_BAR', ENERGY_BAR))
    RACE_REGION = tuple(new_regions.get('RACE_REGION', RACE_REGION))
    FAILURE_REGION = tuple(new_regions.get('FAILURE_REGION', FAILURE_REGION))
    YEAR_REGION = tuple(new_regions.get('YEAR_REGION', YEAR_REGION))
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
        'CRITERIA_REGION': CRITERIA_REGION,
        'STAT_REGIONS': STAT_REGIONS,
        'EVENT_REGIONS': EVENT_REGIONS
    }

    return save_region_settings(current_regions)

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