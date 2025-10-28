import pyautogui
import time
import threading
from core.execute import check_should_stop


class TeamTrialsLogic:
    """Optimized Team Trials logic handler with F3 stop support"""

    def __init__(self, main_window, ui_tab):
        self.main_window = main_window
        self.ui_tab = ui_tab
        self.is_team_trials_running = False
        self.team_trials_thread = None

    def check_stop_condition(self):
        """Check if bot should stop due to F3 press or team trials stop"""
        return not self.is_team_trials_running

    def start_team_trials(self):
        """Start team trials functionality"""
        return self.start_generic_activity(self.team_trials_loop, "Team Trials")

    def start_daily_races(self):
        """Start daily races functionality"""
        return self.start_generic_activity(self.daily_races_loop, "Daily Races")

    def start_legend_race(self):
        """Start legend race functionality"""
        self.main_window.log_message("Legend Race is currently under development. Bot stopped.")
        self.stop_team_trials()
        return False

    def start_generic_activity(self, loop_method, activity_name):
        """Generic method to start an activity"""
        if self.is_team_trials_running:
            return False

        self.is_team_trials_running = True
        self.main_window.status_section.set_bot_status(f"{activity_name} Running", "green")
        self.main_window.set_running_state(True)

        self.team_trials_thread = threading.Thread(target=loop_method, daemon=True)
        self.team_trials_thread.start()
        return True

    def stop_team_trials(self):
        """Stop team trials"""
        self.is_team_trials_running = False
        self.main_window.status_section.set_bot_status("Stopped", "red")
        self.main_window.set_running_state(False)
        self.main_window.is_running = False
        self.main_window.log_message("Team Trials stopped")

    def find_and_click(self, image_path, region=None, max_attempts=1, delay_between=1, click=True, log_attempts=True):
        """Universal function to find and optionally click images with stop checking"""
        time.sleep(1)

        # Check stop condition before starting
        if self.check_stop_condition():
            return None

        if not region:
            # Default to left half of screen
            screen_width, screen_height = pyautogui.size()
            region = (0, 0, screen_width // 2, screen_height)

        filename = image_path.split('/')[-1].replace('.png', '')

        for attempt in range(max_attempts):
            # Check stop condition before each attempt
            if self.check_stop_condition():
                return None

            try:
                button = pyautogui.locateCenterOnScreen(
                    image_path, confidence=0.75, minSearchTime=0.2, region=region
                )
                if button:
                    if click:
                        # Check stop condition before clicking
                        if self.check_stop_condition():
                            return None
                        pyautogui.click(button)
                        self.main_window.log_message(f"Clicked {filename}")
                        if image_path == "assets/buttons/home/team_trials/pvp_win_gift.png":
                            time.sleep(10)
                        return button
                    else:
                        return button
            except pyautogui.ImageNotFoundException:
                pass

            if attempt < max_attempts - 1 and log_attempts:
                # Check stop condition before delay
                if self.check_stop_condition():
                    return None
                time.sleep(delay_between)

        if log_attempts and max_attempts > 1:
            self.main_window.log_message(f"Failed to find {filename}")
        return None

    def navigate_to_daily_races(self):
        """Navigate to daily races section"""
        # Check stop condition
        if self.check_stop_condition():
            return False

        # Home screen race tab selection
        race_tab_region = (200, 780, 680, 860)
        race_images = ["assets/buttons/home/team_trials/race_tab.png", "assets/buttons/home/team_trials/race_tab_2.png"]
        race_clicked = False
        for race_image in race_images:
            if self.check_stop_condition():
                return False

            if self.find_and_click(race_image, race_tab_region):
                race_clicked = True
                time.sleep(1)
                break

        if not race_clicked:
            self.main_window.log_message("Race tab not found - Not on Home screen")
            return False

        # Daily race button
        if not self.find_and_click("assets/buttons/home/daily_race/daily_race_btn.png", max_attempts=5, delay_between=5):
            return False

        # Handle next button if it appears
        if self.find_and_click("assets/buttons/next_btn.png", click=False, max_attempts=2, delay_between=5):
            return True

        # # Handle resume button if it appears
        # if self.find_and_click("assets/buttons/resume_btn.png"):
        #     time.sleep(2)

        # Race selection (Moonlight Sho or Jupiter Cup)
        race_selection = {
            "Moonlight Sho": "assets/buttons/home/daily_race/moonlight_sho.png",
            "Jupiter Cup": "assets/buttons/home/daily_race/jupiter_cup.png"
        }

        race_btn_path = race_selection.get(self.ui_tab.default_race.get())
        if not self.find_and_click(race_btn_path, max_attempts=5, delay_between=3):
            return False

        # Check no more turns
        if self.find_and_click("assets/buttons/ok_btn.png", click=False):
            self.main_window.log_message("No more turns available - stopping bot")
            return False

        # Hard difficulty
        if not self.find_and_click("assets/buttons/home/daily_race/hard_btn.png", max_attempts=5, delay_between=3):
            return False

        # Race button
        if not self.find_and_click("assets/buttons/home/daily_race/race!_btn.png", max_attempts=5, delay_between=2):
            return False

        # Confirm button
        if not self.find_and_click("assets/buttons/confirm_btn.png", max_attempts=5, delay_between=3):
            return False

        return True

    def execute_daily_race_cycle(self):
        """Execute one complete daily race cycle"""
        # Next button
        if not self.find_and_click("assets/buttons/next_btn.png", max_attempts=5, delay_between=3):
            return False

        # Race button home
        if not self.find_and_click("assets/buttons/home/team_trials/race_btn.png", max_attempts=5, delay_between=3):
            return False

        # View results processing
        if not self.process_daily_race_results():
            return False

        if not self.find_and_click("assets/buttons/next_btn.png", max_attempts=3, delay_between=5):
            return False
        time.sleep(1)

        # Handle shop option
        if self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", click=False):
            if self.ui_tab.daily_race_stop_if_shop.get():
                self.find_and_click("assets/buttons/home/team_trials/shop_btn.png")
                self.main_window.log_message("Shop detected - stopping as requested")
                return False
            else:
                # Check stop condition before cancel click
                if self.check_stop_condition():
                    return False
                self.find_and_click("assets/buttons/cancel_btn.png", log_attempts=False)

        # Race again button
        if not self.find_and_click("assets/buttons/home/team_trials/race_again_btn.png", max_attempts=5, delay_between=5):
            return False

        # Check no more turns
        if self.find_and_click("assets/buttons/ok_btn.png", click=False):
            self.main_window.log_message("No more turns available - stopping bot")
            return False

        return True

    def process_daily_race_results(self):
        """Process daily race results"""
        # View results
        see_result_pos = self.find_and_click("assets/buttons/view_results.png", max_attempts=5, delay_between=5)
        if not see_result_pos:
            return False

        # Click result multiple times
        for i in range(2):
            pyautogui.click(see_result_pos)
            time.sleep(4)

        return True

    def daily_races_loop(self):
        """Main daily races loop"""
        try:
            if self.check_stop_condition():
                self.main_window.log_message("Daily Races stopped before navigation")
                return

            if not self.navigate_to_daily_races():
                return

            while self.is_team_trials_running:
                if self.check_stop_condition():
                    self.main_window.log_message("Daily Races stopped during execution")
                    break

                if not self.execute_daily_race_cycle():
                    break

        except Exception as e:
            self.main_window.log_message(f"Daily Races error: {e}")
        finally:
            self.main_window.root.after(0, self.stop_team_trials)

    def navigate_to_team_trials(self):
        """Navigate to team trials section with stop checking"""
        # Check stop condition before starting navigation
        if self.check_stop_condition():
            return False

        # Step 2: Check and click race tab
        race_tab_region = (200, 780, 680, 860)
        race_images = ["assets/buttons/home/team_trials/race_tab.png",
                       "assets/buttons/home/team_trials/race_tab_2.png"]

        race_clicked = False
        for race_image in race_images:
            # Check stop condition before each race image attempt
            if self.check_stop_condition():
                return False

            if self.find_and_click(race_image, race_tab_region):
                self.main_window.log_message(f"Successfully clicked race tab")
                race_clicked = True
                time.sleep(1)
                break

        if not race_clicked:
            self.main_window.log_message("Race tab not found - Not on Home screen")
            return False

        # Check stop condition before team trial button
        if self.check_stop_condition():
            return False

        # Step 2 continued: Click team trial button
        if not self.find_and_click("assets/buttons/home/team_trials/team_trial_btn.png",
                                   max_attempts=6, delay_between=3):
            return False

        # Check stop condition before team race button
        if self.check_stop_condition():
            return False

        # Step 3: Click team race button
        if not self.find_and_click("assets/buttons/home/team_trials/team_race_btn.png",
                                   max_attempts=6, delay_between=3):
            return False
        elif self.find_and_click("assets/buttons/restore_btn.png", click=False, log_attempts=False):
            self.main_window.log_message("No more turns available - stopping bot")
            return False

        time.sleep(10)

        # Check stop condition before next button check
        if self.check_stop_condition():
            return False

        # Step 3 continued: Check for immediate next button (skip to race results)
        if self.find_and_click("assets/buttons/next_btn.png"):
            self.main_window.log_message("Next button found - proceeding directly to race")
            time.sleep(2)

            # Check stop condition before race button
            if self.check_stop_condition():
                return False

            if self.find_and_click("assets/buttons/home/team_trials/race_btn.png"):
                time.sleep(2)
                return self.handle_race_results()

        return True

    def execute_team_trial_cycle(self):
        """Execute one complete team trial cycle with stop checking"""
        # Check stop condition at start of cycle
        if self.check_stop_condition():
            return False

        # Step 3 final: Check for refresh button
        if not self.find_and_click("assets/buttons/refresh_btn.png", max_attempts=8, delay_between=3, click=False, log_attempts=False):
            self.main_window.log_message("Neither refresh nor next button found")
            return False

        # Check PvP gift
        pvp_gift_pos = self.find_and_click("assets/buttons/home/team_trials/pvp_win_gift.png", log_attempts="Found Pvp gift")

        # Select opponent if no PvP gift
        if not pvp_gift_pos:
            # Select opponent if no PvP gift
            opponent_positions = {
                "Opponent 1": (500, 300),
                "Opponent 2": (500, 550),
                "Opponent 3": (500, 800)
            }

            opponent_choice = self.ui_tab.opponent_type.get()
            if opponent_choice in opponent_positions:
                # Check stop condition before clicking opponent
                if self.check_stop_condition():
                    return False

                pos = opponent_positions[opponent_choice]
                pyautogui.click(pos)
                self.main_window.log_message(f"Selected {opponent_choice}")
                time.sleep(2)

                # Check stop condition before next button
                if self.check_stop_condition():
                    return False

        # Click next button after opponent selection
        if not self.find_and_click("assets/buttons/next_btn.png", max_attempts=8, delay_between=3):
            return False

        # Check stop condition before parfait handling
        if self.check_stop_condition():
            return False

        # Step 5: Handle parfait and race preparation
        # Use parfait if PvP gift was clicked and option is enabled
        if pvp_gift_pos and self.ui_tab.use_parfait_gift_pvp.get():
            if self.check_stop_condition():
                return False
            self.find_and_click("assets/buttons/home/team_trials/parfait.png", log_attempts=False)

        # Check stop condition before race button
        if self.check_stop_condition():
            return False

        # Click race button to start race
        if not self.find_and_click("assets/buttons/home/team_trials/race_btn.png"):
            self.main_window.log_message("Failed to find race button")
            return False

        # Handle race results
        return self.handle_race_results()

    def team_trials_loop(self):
        """Main team trials loop with stop checking"""
        try:
            # Check stop condition before navigation
            if self.check_stop_condition():
                self.main_window.log_message("Team Trials stopped before navigation")
                return

            if not self.navigate_to_team_trials():
                return

            while self.is_team_trials_running:
                # Check stop condition at start of each cycle
                if self.check_stop_condition():
                    self.main_window.log_message("Team Trials stopped during execution")
                    break

                if not self.execute_team_trial_cycle():
                    break

        except Exception as e:
            self.main_window.log_message(f"Team Trials error: {e}")
        finally:
            self.main_window.root.after(0, self.stop_team_trials)

    def handle_race_results(self):
        """Handle race results processing with stop checking"""
        time.sleep(2)

        # Check stop condition before handling results
        if self.check_stop_condition():
            return False

        # Find and click see result button
        see_result_pos = self.find_and_click("assets/buttons/home/team_trials/see_result.png",
                                             max_attempts=8, delay_between=3)
        if not see_result_pos:
            return False

        # Click at see result position 40 times, checking for completion after 25 clicks
        for i in range(40):
            # Check stop condition at each iteration
            if self.check_stop_condition():
                self.main_window.log_message("Team Trials stopped during race results processing")
                return False

            # Check for completion buttons after 25 clicks
            if i >= 24:
                completion_buttons = [
                    "assets/buttons/cancel_btn.png",
                    "assets/buttons/next2_btn.png",
                    "assets/buttons/home/team_trials/race_again_btn.png"
                ]

                for button in completion_buttons:
                    # Check stop condition before each button check
                    if self.check_stop_condition():
                        return False

                    if self.find_and_click(button, click=False, log_attempts=False):
                        self.main_window.log_message(f"Completion button found.")
                        return self.handle_shop_and_continue()
            else:
                time.sleep(0.5)

            # Check stop condition before clicking
            if self.check_stop_condition():
                return False

            pyautogui.click(see_result_pos)

        self.main_window.log_message("Completed 40 clicks - no completion buttons found, stopping bot")
        return False

    def handle_shop_and_continue(self):
        """Handle shop detection and race continuation with stop checking"""
        # Check stop condition before shop handling
        if self.check_stop_condition():
            return False

        # Step 7: Check Story Unlocked
        if self.find_and_click("assets/buttons/close_btn.png", log_attempts=False):
            time.sleep(2)

        # Step 7: Handle shop if present
        if self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", click=False, log_attempts=False):
            self.main_window.log_message("Shop available")

            if self.ui_tab.stop_if_shop.get():
                # Check stop condition before shop click
                if self.check_stop_condition():
                    return False

                self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", log_attempts=False)
                self.main_window.log_message("Shop detected - stopping as requested")
                return False
            else:
                # Check stop condition before cancel click
                if self.check_stop_condition():
                    return False

                self.find_and_click("assets/buttons/cancel_btn.png", log_attempts=False)
                self.main_window.log_message("Shop bypassed - clicked cancel")

        # Check stop condition before race again button
        if self.check_stop_condition():
            return False

        # Step 7 continued: Try race again button first
        if self.find_and_click("assets/buttons/home/team_trials/race_again_btn.png", log_attempts=False):
            if self.find_and_click("assets/buttons/restore_btn.png", click=False, log_attempts=False):
                self.main_window.log_message("No more turns available - stopping bot")
                return False
            return True

        # Check stop condition before next2 button
        if self.check_stop_condition():
            return False

        # Step 7 alternate: Try next2 button sequence
        if self.find_and_click("assets/buttons/next2_btn.png", log_attempts=False):
            time.sleep(2)

            # Check stop condition before next button
            if self.check_stop_condition():
                return False

            self.find_and_click("assets/buttons/next_btn.png", log_attempts=False)

        # Step 7 continued: Check shop again after next2 sequence
        time.sleep(2)

        # Check stop condition before shop check again
        if self.check_stop_condition():
            return False

        if self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", click=False, log_attempts=False):
            if self.ui_tab.stop_if_shop.get():
                # Check stop condition before shop click
                if self.check_stop_condition():
                    return False

                self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", log_attempts=False)
                self.main_window.log_message("Shop detected after next2 - stopping as requested")
                return False
            else:
                # Check stop condition before cancel click
                if self.check_stop_condition():
                    return False

                self.find_and_click("assets/buttons/cancel_btn.png", log_attempts=False)

        # Check stop condition before final race again attempt
        if self.check_stop_condition():
            return False

        # Step 7 final: Final race again attempt
        if self.find_and_click("assets/buttons/home/team_trials/race_again_btn.png", log_attempts=False):
            if self.find_and_click("assets/buttons/restore_btn.png", click=False, log_attempts=False):
                self.main_window.log_message("No more turns available - stopping bot")
                return False
            return True

        # Check stop condition before end condition check
        if self.check_stop_condition():
            return False

        # Step 8: Check for end condition
        if self.find_and_click("assets/buttons/no_btn.png", click=False, log_attempts=False):
            self.main_window.log_message("End condition detected - stopping team trials")
            return False

        return True