"""
Uma Musume Auto Train - Career Lobby Manager
Manages career lobby detection and navigation
"""

import pyautogui
from core.recognizer import is_infirmary_active


class CareerLobbyManager:
    """Manages career lobby detection and navigation"""

    def __init__(self, controller):
        self.controller = controller

    def verify_lobby_state(self, gui=None) -> bool:
        """Verify if currently in career lobby with improved stop condition handling"""
        tazuna_hint = pyautogui.locateCenterOnScreen(
            "assets/ui/tazuna_hint.png",
            confidence=0.8,
            minSearchTime=0.2
        )

        if tazuna_hint is None:
            self.controller.log_message("Should be in career lobby.")

            if self.controller.increment_career_lobby_counter():
                if gui:
                    gui.root.after(0, gui.stop_bot)
                return False

            return False
        else:
            self.controller.reset_career_lobby_counter()
            return True

    def handle_debuff_status(self, gui=None) -> bool:
        """Handle character debuff status with proper stop condition checking"""
        debuffed = pyautogui.locateOnScreen(
            "assets/buttons/infirmary_btn2.png",
            confidence=0.9,
            minSearchTime=1
        )

        if debuffed:
            if is_infirmary_active((debuffed.left, debuffed.top, debuffed.width, debuffed.height)):
                # Check stop conditions for infirmary - FIXED: now properly checks in lobby
                if (gui and gui.get_current_settings().get('enable_stop_conditions', False) and
                        gui.get_current_settings().get('stop_on_infirmary', False)):

                    # Get current date info
                    from core.state import get_current_date_info
                    current_date = get_current_date_info()
                    absolute_day = current_date.get('absolute_day', 0) if current_date else 0

                    # Only apply stop condition after day 24
                    if absolute_day > 24:
                        self.controller.log_message("Stop condition: Infirmary needed - Stopping bot")
                        if gui:
                            gui.root.after(0, gui.stop_bot)
                        return True

                if self.controller.check_should_stop():
                    return False

                pyautogui.click(debuffed)
                self.controller.log_message("Character has debuff, go to infirmary instead.")
                return True

        return False

    def handle_scenario_event(self, gui=None) -> bool:
        """Handle scenario-specific events"""
        # Check for scenario events that need handling
        scenario_events = [
            "assets/ui/scenario_event1.png",
            "assets/ui/scenario_event2.png"
        ]

        for event_asset in scenario_events:
            try:
                event_location = pyautogui.locateOnScreen(
                    event_asset,
                    confidence=0.8,
                    minSearchTime=0.5
                )

                if event_location:
                    self.controller.log_message(f"Scenario event detected: {event_asset}")
                    # Handle the event (implementation depends on specific event type)
                    return True
            except Exception:
                continue

        return False

    def navigate_to_lobby(self) -> bool:
        """Navigate back to career lobby if possible"""
        try:
            # Look for back button or close button
            back_buttons = [
                "assets/buttons/back_btn.png",
                "assets/buttons/close_btn.png",
                "assets/buttons/x_btn.png"
            ]

            for back_btn in back_buttons:
                try:
                    btn_location = pyautogui.locateOnScreen(
                        back_btn,
                        confidence=0.8,
                        minSearchTime=0.5
                    )

                    if btn_location:
                        pyautogui.click(btn_location)
                        self.controller.log_message(f"Clicked navigation button: {back_btn}")
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            self.controller.log_message(f"Error navigating to lobby: {e}")
            return False

    def check_completion_screens(self) -> bool:
        """Check for career completion or ending screens"""
        completion_screens = [
            "assets/ui/career_complete.png",
            "assets/ui/finale_complete.png",
            "assets/ui/graduation.png"
        ]

        for screen_asset in completion_screens:
            try:
                screen_location = pyautogui.locateOnScreen(
                    screen_asset,
                    confidence=0.8,
                    minSearchTime=0.5
                )

                if screen_location:
                    self.controller.log_message(f"Career completion screen detected: {screen_asset}")
                    return True
            except Exception:
                continue

        return False