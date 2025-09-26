import pyautogui
import time
import threading


class TeamTrialsLogic:
    """Optimized Team Trials logic handler"""

    def __init__(self, main_window, ui_tab):
        self.main_window = main_window
        self.ui_tab = ui_tab
        self.is_team_trials_running = False
        self.team_trials_thread = None

    def start_team_trials(self):
        """Start team trials functionality"""
        if self.is_team_trials_running:
            return False

        self.is_team_trials_running = True

        self.main_window.status_section.set_bot_status("Team Trials Running", "green")
        self.main_window.set_running_state(True)

        self.team_trials_thread = threading.Thread(target=self.team_trials_loop, daemon=True)
        self.team_trials_thread.start()
        return True

    def stop_team_trials(self):
        """Stop team trials"""
        self.is_team_trials_running = False
        self.main_window.status_section.set_bot_status("Stopped", "red")
        self.main_window.set_running_state(False)
        self.main_window.log_message("Team Trials stopped")

    def find_and_click(self, image_path, region=None, max_attempts=1, delay_between=1, click=True, log_attempts=True):
        """Universal function to find and optionally click images"""
        time.sleep(1)
        if not region:
            # Default to left half of screen
            screen_width, screen_height = pyautogui.size()
            region = (0, 0, screen_width // 2, screen_height)

        filename = image_path.split('/')[-1].replace('.png', '')

        for attempt in range(max_attempts):
            try:
                button = pyautogui.locateCenterOnScreen(
                    image_path, confidence=0.75, minSearchTime=0.2, region=region
                )
                if button:
                    if click:
                        pyautogui.click(button)
                        self.main_window.log_message(f"Found and clicked {filename}")
                        return button
                    else:
                        return button
            except pyautogui.ImageNotFoundException:
                pass

            if attempt < max_attempts - 1 and log_attempts:
                time.sleep(delay_between)

        if log_attempts and max_attempts > 1:
            self.main_window.log_message(f"Failed to find {filename}")
        return None

    def team_trials_loop(self):
        """Main team trials loop"""
        try:
            if not self.navigate_to_team_trials():
                return

            while self.is_team_trials_running:
                if not self.execute_team_trial_cycle():
                    break

        except Exception as e:
            self.main_window.log_message(f"Team Trials error: {e}")
        finally:
            self.main_window.root.after(0, self.stop_team_trials)

    def navigate_to_team_trials(self):
        """Navigate to team trials section"""
        # Step 2: Check and click race tab
        race_tab_region = (200, 780, 680, 860)
        race_images = ["assets/buttons/home/team_trials/race_tab.png",
                       "assets/buttons/home/team_trials/race_tab_2.png"]

        race_clicked = False
        for race_image in race_images:
            if self.find_and_click(race_image, race_tab_region):
                self.main_window.log_message(f"Successfully clicked race tab")
                race_clicked = True
                time.sleep(1)
                break

        if not race_clicked:
            self.main_window.log_message("Race tab not found - Not on Home screen")
            return False

        # Step 2 continued: Click team trial button
        if not self.find_and_click("assets/buttons/home/team_trials/team_trial_btn.png",
                                   max_attempts=6, delay_between=3):
            return False

        # Step 3: Click team race button
        if not self.find_and_click("assets/buttons/home/team_trials/team_race_btn.png",
                                   max_attempts=6, delay_between=3):
            return False

        time.sleep(10)

        # Step 3 continued: Check for immediate next button (skip to race results)
        if self.find_and_click("assets/buttons/next_btn.png"):
            self.main_window.log_message("Next button found - proceeding directly to race")
            time.sleep(2)
            if self.find_and_click("assets/buttons/home/team_trials/race_btn.png"):
                time.sleep(2)
                return self.handle_race_results()

        return True

    def execute_team_trial_cycle(self):
        """Execute one complete team trial cycle"""
        if not self.is_team_trials_running:
            return False

            # Step 3 final: Check for refresh button
        if not self.find_and_click("assets/buttons/refresh_btn.png", max_attempts=6, delay_between=3, click=False):
            self.main_window.log_message("Neither refresh nor next button found")
            return False

        # Step 4: Check for PvP gift and opponent selection
        pvp_region = (200, 150, 700, 720)
        pvp_gift_pos = self.find_and_click("assets/buttons/home/team_trials/pvp_win_gift.png",
                                           pvp_region, log_attempts=False)

        if not pvp_gift_pos:
            # Select opponent if no PvP gift
            opponent_positions = {
                "Opponent 1": (500, 300),
                "Opponent 2": (500, 550),
                "Opponent 3": (500, 800)
            }

            opponent_choice = self.ui_tab.opponent_type.get()
            if opponent_choice in opponent_positions:
                pos = opponent_positions[opponent_choice]
                pyautogui.click(pos)
                self.main_window.log_message(f"Selected {opponent_choice}")
                time.sleep(2)

                # Click next button after opponent selection
                if not self.find_and_click("assets/buttons/next_btn.png", max_attempts=8, delay_between=3):
                    return False

        # Step 5: Handle parfait and race preparation
        # time.sleep(2)

        # Use parfait if PvP gift was clicked and option is enabled
        if pvp_gift_pos and self.ui_tab.use_parfait_gift_pvp.get():
            self.find_and_click("assets/buttons/home/team_trials/parfait.png", log_attempts=False)

        # Click race button to start race
        if not self.find_and_click("assets/buttons/home/team_trials/race_btn.png"):
            self.main_window.log_message("Failed to find race button")
            return False

        # Handle race results
        return self.handle_race_results()

    def handle_race_results(self):
        """Handle race results processing"""
        time.sleep(2)

        # Find and click see result button
        see_result_pos = self.find_and_click("assets/buttons/home/team_trials/see_result.png",
                                             max_attempts=8, delay_between=3)
        if not see_result_pos:
            return False

        # Click at see result position 40 times, checking for completion after 25 clicks
        for i in range(40):
            if not self.is_team_trials_running:
                return False

            # Check for completion buttons after 25 clicks
            if i >= 24:
                completion_buttons = [
                    "assets/buttons/cancel_btn.png",
                    "assets/buttons/next2_btn.png",
                    "assets/buttons/home/team_trials/race_again_btn.png"
                ]

                for button in completion_buttons:
                    if self.find_and_click(button, click=False, log_attempts=False):
                        self.main_window.log_message(f"Completion button found.")
                        return self.handle_shop_and_continue()
            else:
                time.sleep(0.5)

            pyautogui.click(see_result_pos)

        self.main_window.log_message("Completed 40 clicks - no completion buttons found, stopping bot")
        return False

    def handle_shop_and_continue(self):
        """Handle shop detection and race continuation - Step 7"""
        # Step 7: Handle shop if present
        if self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", click=False, log_attempts=False):
            self.main_window.log_message("Shop available")
            if self.ui_tab.stop_if_shop.get():
                self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", log_attempts=False)
                self.main_window.log_message("Shop detected - stopping as requested")
                return False
            else:
                self.find_and_click("assets/buttons/cancel_btn.png", log_attempts=False)
                self.main_window.log_message("Shop bypassed - clicked cancel")

        # Step 7 continued: Try race again button first
        if self.find_and_click("assets/buttons/home/team_trials/race_again_btn.png", log_attempts=False):
            if self.find_and_click("assets/buttons/restore_btn.png", click=False, log_attempts=False):
                self.main_window.log_message("No more turns available - stopping bot")
                return False
            return True

        # Step 7 alternate: Try next2 button sequence
        if self.find_and_click("assets/buttons/next2_btn.png", log_attempts=False):
            time.sleep(5)
            self.find_and_click("assets/buttons/next_btn.png", log_attempts=False)
            time.sleep(2)

        # Step 7 continued: Check shop again after next2 sequence
        time.sleep(5)
        if self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", click=False, log_attempts=False):
            if self.ui_tab.stop_if_shop.get():
                self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", log_attempts=False)
                self.main_window.log_message("Shop detected after next2 - stopping as requested")
                return False
            else:
                self.find_and_click("assets/buttons/cancel_btn.png", log_attempts=False)

        # Step 7 final: Final race again attempt
        if self.find_and_click("assets/buttons/home/team_trials/race_again_btn.png", log_attempts=False):
            if self.find_and_click("assets/buttons/restore_btn.png", click=False, log_attempts=False):
                self.main_window.log_message("No more turns available - stopping bot")
                return False
            return True

        # Step 8: Check for end condition
        if self.find_and_click("assets/buttons/no_btn.png", click=False, log_attempts=False):
            self.main_window.log_message("End condition detected - stopping team trials")
            return False

        return True

