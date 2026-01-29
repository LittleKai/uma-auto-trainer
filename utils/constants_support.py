"""
Constants Support File
Contains detailed configurations, patterns, and helper data for the main constants module
"""

# Default regions for settings reset
DEFAULT_REGIONS = {
    'SUPPORT_CARD_ICON_REGION': (820, 155, 120, 700),
    'MOOD_REGION': (700, 123, 120, 27),
    'ENERGY_BAR': (440, 136, 710, 136),
    'RACE_REGION': (260, 588, 580, 266),
    'TURN_REGION': (260, 84, 112, 47),
    'YEAR_REGION': (255, 35, 165, 22),
    'UNITY_CUP_TURN_REGION': (265, 57, 60, 47),
    'UNITY_CUP_YEAR_REGION': (390, 37, 165, 16),
    'FAILURE_REGION': (275, 780, 551, 33),
    'CRITERIA_REGION': (223, 290, 150, 770),
    'STAT_REGIONS': {
        "spd": (310, 723, 55, 20),
        "sta": (405, 723, 55, 20),
        "pwr": (500, 723, 55, 20),
        "guts": (595, 723, 55, 20),
        "wit": (690, 723, 55, 20)
    },
    'EVENT_REGIONS': {
        "EVENT_REGION": (240, 173, 240, 25),
        "EVENT_NAME_REGION": (240, 200, 360, 40)
    }
}

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
