"""
Uma Musume Auto Train - Fixed Event Manager
Handles UI events following original code logic and assets
"""

import time
import pyautogui


class EventManager:
    """Handles UI events following original code patterns"""

    def __init__(self, controller):
        self.controller = controller

    def handle_ui_elements(self, gui=None) -> bool:
        """Handle various UI elements using original code logic"""

        # Priority 1: Handle event choices (using original logic)
        if self._handle_event_choice():
            return True

        # Priority 2: Handle inspiration
        if self._handle_inspiration():
            return True

        # Priority 3: Handle common dialog buttons
        if self._handle_common_dialogs():
            return True

        return False

    def _handle_event_choice(self) -> bool:
        """Handle event choices using original code logic"""
        try:
            # Use exact same logic as original execute.py
            choice_btn = pyautogui.locateOnScreen(
                "assets/icons/event_choice_1.png",
                confidence=0.8,
                minSearchTime=0.2
            )

            if choice_btn:
                pyautogui.click(choice_btn)
                self.controller.log_message("[INFO] Event found, automatically select top choice.")
                return True

            return False

        except Exception as e:
            self.controller.log_message(f"Error handling event choice: {e}")
            return False

    def _handle_inspiration(self) -> bool:
        """Handle inspiration using original code logic"""
        try:
            # Use exact same logic as original execute.py
            inspiration_btn = pyautogui.locateOnScreen(
                "assets/buttons/inspiration_btn.png",
                confidence=0.8,
                minSearchTime=0.2
            )

            if inspiration_btn:
                pyautogui.click(inspiration_btn)
                self.controller.log_message("[INFO] Inspiration found.")
                return True

            return False

        except Exception as e:
            self.controller.log_message(f"Error handling inspiration: {e}")
            return False

    def _handle_common_dialogs(self) -> bool:
        """Handle common dialog buttons using original code logic"""
        dialog_buttons = [
            "assets/buttons/next_btn.png",
            "assets/buttons/cancel_btn.png",
            "assets/buttons/next2_btn.png"
        ]

        for button_asset in dialog_buttons:
            try:
                button_location = pyautogui.locateOnScreen(
                    button_asset,
                    confidence=0.8,
                    minSearchTime=0.2
                )

                if button_location:
                    pyautogui.click(button_location)
                    self.controller.log_message(f"Clicked dialog button: {button_asset}")
                    return True

            except Exception:
                continue

        return False