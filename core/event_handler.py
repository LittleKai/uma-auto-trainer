import pyautogui
import json
import os
import glob
from difflib import SequenceMatcher
from typing import Optional, Dict, List, Tuple, Any
from core.ocr import extract_text
from core.recognizer import find_template_position
from utils.screenshot import enhanced_screenshot
from utils.constants import get_current_regions

class EventChoiceHandler:
    """Handles automatic event choice selection based on event maps"""

    def __init__(self, check_stop_func, check_window_func, log_func):
        """
        Initialize event choice handler

        Args:
            check_stop_func: Function to check if should stop
            check_window_func: Function to check if game window is active
            log_func: Function to log messages
        """
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func

        # Load event maps
        self.common_events = self.load_common_events()
        self.uma_musume_events = {}
        self.support_card_events = {}

        self.load_uma_musume_events()
        self.load_support_card_events()

    def load_common_events(self) -> Dict[str, List[Dict]]:
        """Load common event maps from assets/event_map/common.json"""
        try:
            common_path = "assets/event_map/common.json"
            if os.path.exists(common_path):
                with open(common_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.log(f"[WARNING] Common event file not found: {common_path}")
                return {"train_event_uma_musume": [], "train_event_scenario": []}
        except Exception as e:
            self.log(f"[ERROR] Failed to load common events: {e}")
            return {"train_event_uma_musume": [], "train_event_scenario": []}

    def load_uma_musume_events(self):
        """Load Uma Musume specific event maps"""
        try:
            uma_folder = "assets/event_map/uma_musume"
            if os.path.exists(uma_folder):
                json_files = glob.glob(os.path.join(uma_folder, "*.json"))
                for file_path in json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.uma_musume_events[filename] = json.load(f)
                        self.log(f"[DEBUG] Loaded Uma Musume events for: {filename}")
        except Exception as e:
            self.log(f"[ERROR] Failed to load Uma Musume events: {e}")

    def load_support_card_events(self):
        """Load Support Card specific event maps"""
        try:
            support_folder = "assets/event_map/support_card"
            if os.path.exists(support_folder):
                json_files = glob.glob(os.path.join(support_folder, "*.json"))
                for file_path in json_files:
                    filename = os.path.basename(file_path).replace('.json', '')
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.support_card_events[filename] = json.load(f)
                        self.log(f"[DEBUG] Loaded Support Card events for: {filename}")
        except Exception as e:
            self.log(f"[ERROR] Failed to load Support Card events: {e}")

    def find_similar_text(self, target_text: str, ref_text_list: List[str], threshold: float = 0) -> str:
        """
        Find similar text from reference list using sequence matching

        Args:
            target_text: Text to match
            ref_text_list: List of reference texts
            threshold: Minimum similarity threshold

        Returns:
            Best matching text or empty string if no match
        """
        result = ""
        best_ratio = threshold

        for ref_text in ref_text_list:
            s = SequenceMatcher(None, target_text.upper(), ref_text.upper())
            ratio = s.ratio()
            if ratio > best_ratio:
                result = ref_text
                best_ratio = ratio

        return result

    def detect_event_type(self) -> Optional[str]:
        """
        Detect event type from event region using template matching

        Returns:
            Event type string or None if not detected
        """
        try:
            current_regions = get_current_regions()
            event_regions = current_regions.get('EVENT_REGIONS', {})
            event_region = event_regions.get('EVENT_REGION')

            if not event_region:
                self.log("[WARNING] EVENT_REGION not configured")
                return None

            # Check for event type icons using template matching with OpenCV
            event_types = [
                ("assets/icons/train_event_scenario.png", "train_event_scenario"),
                ("assets/icons/train_event_uma_musume.png", "train_event_uma_musume"),
                ("assets/icons/train_event_support_card.png", "train_event_support_card")
            ]

            for icon_path, event_type in event_types:
                if os.path.exists(icon_path):
                    try:
                        position = find_template_position(
                            template_path=icon_path,
                            region=event_region,
                            threshold=0.8,
                            return_center=True,
                            region_format='xywh'
                        )
                        if position:
                            self.log(f"[DEBUG] Detected event type: {event_type}")
                            return event_type
                    except Exception as e:
                        continue

            self.log("[DEBUG] No event type icon detected")
            return None

        except Exception as e:
            self.log(f"[ERROR] Failed to detect event type: {e}")
            return None

    def extract_event_name(self) -> Optional[str]:
        """
        Extract event name from event name region using OCR

        Returns:
            Event name text or None if not extracted
        """
        try:
            current_regions = get_current_regions()
            event_regions = current_regions.get('EVENT_REGIONS', {})
            event_name_region = event_regions.get('EVENT_NAME_REGION')

            if not event_name_region:
                self.log("[WARNING] EVENT_NAME_REGION not configured")
                return None

            # Capture and OCR the event name region
            event_name_img = enhanced_screenshot(event_name_region)
            event_name_text = extract_text(event_name_img)

            if event_name_text:
                self.log(f"[DEBUG] Extracted event name: '{event_name_text}'")
                return event_name_text.strip()
            else:
                self.log("[DEBUG] No event name text extracted")
                return None

        except Exception as e:
            self.log(f"[ERROR] Failed to extract event name: {e}")
            return None

    def get_current_mood(self) -> str:
        """
        Get current character mood using OCR

        Returns:
            Current mood string or "UNKNOWN" if detection fails
        """
        try:
            from core.state import check_mood
            mood = check_mood()
            self.log(f"[DEBUG] Current mood detected: {mood}")
            return mood
        except Exception as e:
            self.log(f"[ERROR] Failed to get current mood: {e}")
            return "UNKNOWN"

    def get_current_energy(self) -> int:
        """
        Get current energy percentage using energy detection

        Returns:
            Current energy percentage or 100 if detection fails
        """
        try:
            from core.state import check_energy_percentage
            energy = check_energy_percentage()
            self.log(f"[DEBUG] Current energy detected: {energy}%")
            return energy
        except Exception as e:
            self.log(f"[ERROR] Failed to get current energy: {e}")
            return 100

    def build_event_database(self, event_type: str, uma_musume: str, support_cards: List[str]) -> List[Dict]:
        """
        Build event database based on event type and selected cards

        Args:
            event_type: Type of event (scenario/uma_musume/support_card)
            uma_musume: Selected Uma Musume name
            support_cards: List of selected support cards

        Returns:
            Combined event list from appropriate sources
        """
        event_list = []

        if event_type == "train_event_scenario":
            # Only from common.json train_event_scenario
            event_list = self.common_events.get("train_event_scenario", [])
            self.log(f"[DEBUG] Loaded {len(event_list)} scenario events from common.json")

        elif event_type == "train_event_uma_musume":
            # Uma Musume specific events + common uma musume events
            if uma_musume != "None" and uma_musume in self.uma_musume_events:
                uma_events = self.uma_musume_events[uma_musume].get("events", [])
                event_list.extend(uma_events)
                self.log(f"[DEBUG] Loaded {len(uma_events)} events for Uma Musume: {uma_musume}")

            # Add common uma musume events
            common_uma_events = self.common_events.get("train_event_uma_musume", [])
            event_list.extend(common_uma_events)
            self.log(f"[DEBUG] Added {len(common_uma_events)} common uma musume events")

        elif event_type == "train_event_support_card":
            # Events from all selected support cards
            for support_card in support_cards:
                if support_card != "None" and support_card in self.support_card_events:
                    card_events = self.support_card_events[support_card].get("events", [])
                    event_list.extend(card_events)
                    self.log(f"[DEBUG] Loaded {len(card_events)} events for support card: {support_card}")

        self.log(f"[DEBUG] Total events in database: {len(event_list)}")
        return event_list

    def requires_mood_check(self, event_config: Dict) -> bool:
        """
        Check if event conditions require mood information

        Args:
            event_config: Event configuration dictionary

        Returns:
            True if mood check is required
        """
        for i in range(1, 6):
            mood_key = f"choice_{i}_if_mood_lt"
            if mood_key in event_config:
                return True
        return False

    def requires_energy_check(self, event_config: Dict) -> bool:
        """
        Check if event conditions require energy information

        Args:
            event_config: Event configuration dictionary

        Returns:
            True if energy check is required
        """
        for i in range(1, 6):
            energy_lte_key = f"choice_{i}_if_energy_lte"
            energy_gt_key = f"choice_{i}_if_energy_gt"
            if energy_lte_key in event_config or energy_gt_key in event_config:
                return True
        return False

    def find_event_choice(self, event_type: str, event_name: str,
                          uma_musume: str, support_cards: List[str]) -> Optional[int]:
        """
        Find appropriate event choice based on event type and configuration

        Args:
            event_type: Type of event (scenario/uma_musume/support_card)
            event_name: Name of the event
            uma_musume: Selected Uma Musume name
            support_cards: List of selected support cards

        Returns:
            Choice number (1-5) or None if not found
        """
        try:
            # Build event database based on type and selections
            event_list = self.build_event_database(event_type, uma_musume, support_cards)

            if not event_list:
                self.log(f"[DEBUG] No events in database for type: {event_type}")
                return None

            # Find matching event
            event_names = [event.get("name", "") for event in event_list]
            matched_name = self.find_similar_text(event_name, event_names, threshold=0.6)

            if not matched_name:
                self.log(f"[DEBUG] No matching event found for: '{event_name}'")
                return None

            # Find the event configuration
            matched_event = None
            for event in event_list:
                if event.get("name") == matched_name:
                    matched_event = event
                    break

            if not matched_event:
                return None

            self.log(f"[DEBUG] Found matching event: '{matched_name}' for '{event_name}'")

            # Check if we need mood information
            if self.requires_mood_check(matched_event):
                current_mood = self.get_current_mood()
                if current_mood == "UNKNOWN":
                    self.log("[WARNING] Event requires mood check but mood is UNKNOWN - waiting for user")
                    return None
            else:
                current_mood = "NORMAL"  # Default if not needed

            # Check if we need energy information
            if self.requires_energy_check(matched_event):
                current_energy = self.get_current_energy()
            else:
                current_energy = 100  # Default if not needed

            # Determine choice based on conditions
            choice = self.evaluate_event_conditions(matched_event, current_energy, current_mood, uma_musume)

            if choice:
                self.log(f"[DEBUG] Selected choice {choice} for event '{matched_name}' (Energy: {current_energy}%, Mood: {current_mood})")
                return choice
            else:
                self.log(f"[DEBUG] No valid choice determined for event '{matched_name}'")
                return None

        except Exception as e:
            self.log(f"[ERROR] Failed to find event choice: {e}")
            return None

    def evaluate_event_conditions(self, event_config: Dict, current_energy: Optional[int],
                                  current_mood: Optional[str], uma_musume: str) -> Optional[int]:
        """
        Evaluate event conditions and return appropriate choice
        Only uses energy/mood values if they were actually checked

        Args:
            event_config: Event configuration dictionary
            current_energy: Current energy percentage (None if not checked)
            current_mood: Current mood (None if not checked)
            uma_musume: Current Uma Musume name

        Returns:
            Choice number (1-5) or None
        """
        try:
            # Handle simple choice (should have been handled before this function)
            if "choice" in event_config:
                choice = event_config["choice"]
                if choice == "bottom":
                    return 5
                elif isinstance(choice, int):
                    return choice

            # Handle conditional choices
            mood_priority = ["AWFUL", "BAD", "NORMAL", "GOOD", "GREAT"]
            current_mood_index = None
            if current_mood and current_mood in mood_priority:
                current_mood_index = mood_priority.index(current_mood)

            # Check conditions for each choice (priority order 1-5)
            for i in range(1, 6):
                # Check energy less than or equal condition
                energy_lte_key = f"choice_{i}_if_energy_lte"
                if energy_lte_key in event_config and current_energy is not None:
                    if current_energy <= event_config[energy_lte_key]:
                        self.log(f"[DEBUG] Choice {i} selected: energy {current_energy} <= {event_config[energy_lte_key]}")
                        return i

                # Check energy greater than condition
                energy_gt_key = f"choice_{i}_if_energy_gt"
                if energy_gt_key in event_config and current_energy is not None:
                    if current_energy > event_config[energy_gt_key]:
                        self.log(f"[DEBUG] Choice {i} selected: energy {current_energy} > {event_config[energy_gt_key]}")
                        return i

                # Check mood condition
                mood_key = f"choice_{i}_if_mood_lt"
                if mood_key in event_config and current_mood_index is not None:
                    threshold_mood = event_config[mood_key]
                    if threshold_mood in mood_priority:
                        threshold_index = mood_priority.index(threshold_mood)
                        if current_mood_index < threshold_index:
                            self.log(f"[DEBUG] Choice {i} selected: mood {current_mood} < {threshold_mood}")
                            return i

                # Check Uma Musume specific condition
                uma_key = f"choice_{i}_if_uma"
                if uma_key in event_config:
                    if uma_musume == event_config[uma_key]:
                        self.log(f"[DEBUG] Choice {i} selected: uma musume matches {uma_musume}")
                        return i

            # Default fallback - return choice 1
            self.log("[DEBUG] No conditions met, using default choice 1")
            return 1

        except Exception as e:
            self.log(f"[ERROR] Failed to evaluate event conditions: {e}")
            return 1

    def handle_event_choice(self, event_settings: Dict) -> bool:
        """
        Handle automatic event choice selection

        Args:
            event_settings: Event choice settings from GUI

        Returns:
            True if event was handled, False otherwise
        """
        try:
            if self.check_stop():
                return False

            if not self.check_window():
                return False

            # Check if auto first choice is enabled
            if event_settings.get('auto_first_choice', False):
                self.log("[DEBUG] Auto first choice enabled - selecting choice 1")
                return self.click_choice(1)

            # Check if auto event map is enabled
            if not event_settings.get('auto_event_map', False):
                self.log("[DEBUG] Auto event map disabled")
                return False

            # Detect event type
            event_type = self.detect_event_type()
            if not event_type:
                self.log("[DEBUG] Could not detect event type")
                return False

            # Extract event name
            event_name = self.extract_event_name()
            if not event_name:
                self.log("[DEBUG] Could not extract event name")
                return False

            # Get configuration
            uma_musume = event_settings.get('uma_musume', 'None')
            support_cards = event_settings.get('support_cards', ['None'] * 6)

            # Find appropriate choice
            choice = self.find_event_choice(event_type, event_name, uma_musume, support_cards)

            if choice:
                return self.click_choice(choice)
            else:
                # Check unknown event action setting
                unknown_action = event_settings.get('unknown_event_action', 'Auto select first choice')
                if unknown_action == "Wait for user selection":
                    self.log(f"[INFO] Unknown event '{event_name}' - waiting for user selection as configured")
                    return False  # This will trigger manual handling
                else:
                    self.log(f"[WARNING] No choice found for event '{event_name}' - using choice 1 as fallback")
                    return self.click_choice(1)

        except Exception as e:
            self.log(f"[ERROR] Failed to handle event choice: {e}")
            return False

    def click_choice(self, choice_number: int) -> bool:
        """
        Click on the specified choice button

        Args:
            choice_number: Choice number (1-5)

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.check_stop():
                return False

            if not self.check_window():
                return False

            choice_number = max(1, min(5, choice_number))  # Clamp to 1-5

            choice_icon = f"assets/icons/event_choice_{choice_number}.png"

            if not os.path.exists(choice_icon):
                self.log(f"[WARNING] Choice icon not found: {choice_icon}")
                return False

            # Try to find and click the choice button
            choice_btn = pyautogui.locateCenterOnScreen(choice_icon, confidence=0.8, minSearchTime=1.0)

            if choice_btn:
                if self.check_stop():
                    return False

                pyautogui.moveTo(choice_btn, duration=0.2)
                pyautogui.click()
                self.log(f"[INFO] Selected event choice {choice_number}")
                return True
            else:
                self.log(f"[WARNING] Choice {choice_number} button not found on screen")
                return False

        except Exception as e:
            self.log(f"[ERROR] Failed to click choice {choice_number}: {e}")
            return False

    def is_event_choice_visible(self) -> bool:
        """
        Check if event choice buttons are visible on screen

        Returns:
            True if event choice is visible, False otherwise
        """
        try:
            # Check for first choice button
            choice_1_icon = "assets/icons/event_choice_1.png"
            if os.path.exists(choice_1_icon):
                choice_btn = pyautogui.locateOnScreen(choice_1_icon, confidence=0.8, minSearchTime=0.2)
                return choice_btn is not None
            return False
        except Exception as e:
            self.log(f"[ERROR] Failed to check event choice visibility: {e}")
            return False