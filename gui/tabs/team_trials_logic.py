import pyautogui
import time
import threading


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

    def start_champion_meets(self):
        """Start Champion Meeting functionality"""
        return self.start_generic_activity(self.champion_meet_loop, "Champion Meeting")

    def start_legend_race(self):
        """Start Legend Race with specified parameters"""
        return self.start_generic_activity(self.legend_race_loop, "Legend Races")

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
        self.main_window.log_message("Daily Activities stopped")

    def find_and_click(self, image_path, full_screen=False, region=None, max_attempts=1, delay_between=1, click=True,
                       log_attempts=True, click_count=1, confidence=0.8, click_count_delay=0.3):
        """Universal function to find and optionally click images with stop checking"""
        time.sleep(1)

        # Check stop condition before starting
        if self.check_stop_condition():
            return None
        if full_screen:
            screen_width, screen_height = pyautogui.size()
            region = (0, 0, screen_width, screen_height)
        else:
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
                    image_path, confidence=confidence, minSearchTime=0.2, region=region
                )
                if button:
                    if click:
                        # Check stop condition before clicking
                        if self.check_stop_condition():
                            return None
                        for i in range(click_count):
                            pyautogui.click(button)
                            time.sleep(click_count_delay)
                        if log_attempts:
                            self.main_window.log_message(f"Clicked {filename}")
                        if image_path == "assets/buttons/home/team_trials/pvp_win_gift.png":
                            time.sleep(8)
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

    def navigate_to_champion_meet(self):
        """Navigate to Champion Meeting section"""
        # Check stop condition
        if self.check_stop_condition():
            return False

        # Home screen race tab selection
        race_tab_region = (200, 600, 680, 800)
        race_images = ["assets/buttons/home/champion_meeting/find_race_btn.png"]
        race_clicked = False
        for race_image in race_images:
            if self.check_stop_condition():
                return False

            if self.find_and_click(race_image, race_tab_region, click=None):
                race_clicked = True
                time.sleep(1)
                break

        if not race_clicked:
            self.main_window.log_message("Race button not found - Not in Champion Meeting")
            return False

        return True

    def execute_champion_meet_cycle(self):
        """Execute one complete daily race cycle"""
        # Race button home
        if not self.find_and_click("assets/buttons/home/champion_meeting/find_race_btn.png", max_attempts=5,
                                   delay_between=2):
            return False
        print("execute_champion_meet_cycle")
        if not self.find_and_click("assets/buttons/next_btn.png", max_attempts=18, delay_between=5):
            return False

        if not self.find_and_click("assets/buttons/home/champion_meeting/race_brn.png", max_attempts=5, delay_between=3,
                                   click_count=3):
            return False
        time.sleep(3)

        # # RECHECK if race_brn was clicked
        # if self.find_and_click("assets/buttons/home/champion_meeting/race_brn.png", max_attempts=1, delay_between=1, log_attempts=""):
        #     time.sleep(2)

        if not self.find_and_click("assets/buttons/home/daily_race/race!_btn.png", max_attempts=5, delay_between=5):
            return False
        time.sleep(2)

        for i in range(4):
            self.find_and_click("assets/buttons/skip_btn.png", max_attempts=3, delay_between=2, click_count=2,
                                log_attempts=False)

        time.sleep(2)
        for i in range(4):
            next_btn_pos = self.find_and_click("assets/buttons/next_btn.png", max_attempts=1, delay_between=1,
                                               click_count=2)
            if not next_btn_pos:
                pyautogui.click(400, 400)
                time.sleep(3)
                if i == 4:
                    return False
            else:
                time.sleep(3)
                if self.find_and_click("assets/buttons/next_btn.png", max_attempts=1, delay_between=1,
                                       click_count=3):
                    time.sleep(5)
                else:
                    time.sleep(2)
                break

        # # RECHECK if race_brn was clicked
        # if self.find_and_click("assets/buttons/home/champion_meeting/race_brn.png", max_attempts=1, delay_between=1, log_attempts=""):
        #     time.sleep(5)

        # Check no more turns
        if self.find_and_click("assets/buttons/home/champion_meeting/claim_btn.png", click=False):
            self.main_window.log_message("No more turns available - stopping bot")
            return False

        return True

    def champion_meet_loop(self):
        """Main Champion Meeting loop"""
        try:
            if self.check_stop_condition():
                self.main_window.log_message("Champion Meeting stopped before navigation")
                return

            if not self.navigate_to_champion_meet():
                return

            while self.is_team_trials_running:
                if self.check_stop_condition():
                    self.main_window.log_message("Champion Meeting stopped during execution")
                    break

                if not self.execute_champion_meet_cycle():
                    break

        except Exception as e:
            self.main_window.log_message(f"Champion Meeting error: {e}")
        finally:
            self.main_window.root.after(0, self.stop_team_trials)

    def legend_race_loop(self):
        """Main legend race loop with stop checking"""
        try:
            # Check stop condition before navigation
            if self.check_stop_condition():
                self.main_window.log_message("Legend Races stopped before navigation")
                return

            if not self.navigate_to_legend_race():
                return

        except Exception as e:
            self.main_window.log_message(f"Legend Races error: {e}")
        finally:
            self.main_window.root.after(0, self.stop_team_trials)

    def navigate_to_legend_race(self):
        # Check active tab and ensure no ongoing processes
        # if not self.ui_tab.is_active_tab() or self.is_team_trials_running:
        #     return False
        #
        # # Set running flag
        # self.is_team_trials_running = True

        try:
            # 1. Check race images
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
            # 2. Click Race Event button
            if not self.find_and_click("assets/buttons/home/race_event/race_event_btn.png", click=True, max_attempts=3,
                                       delay_between=5):
                return False
                # Click Legend Race button
            if not self.find_and_click("assets/buttons/home/race_event/legend_race_btn.png", click=True, max_attempts=3,
                                       delay_between=3):
                return False

            time.sleep(5)

            while True:
                # 3. Check EX unavailability
                if not self.find_and_click("assets/buttons/next_btn.png", click=False, log_attempts=False):

                    # if self.find_and_click("assets/buttons/home/race_event/ex-unavailable_btn.png", click=False, log_attempts=False):
                    #         self.main_window.log_message("No more Legend Race attempts available.")
                    #         break

                    # 4. Click EX button
                    if not self.find_and_click("assets/buttons/home/race_event/ex_btn.png", click=True, max_attempts=3,
                                               delay_between=3):
                        return False

                    # 5. Click Race button
                    if not self.find_and_click("assets/buttons/home/team_trials/race_btn.png", click=True,
                                               max_attempts=3, delay_between=2):
                        return False

                    self.find_and_click("assets/buttons/home/daily_race/race!_btn.png", confidence=0.9,
                                        click=True, log_attempts=False, max_attempts=2, delay_between=3)

                    # 6. Confirm
                    if not self.find_and_click("assets/buttons/confirm_btn.png", click=True, max_attempts=3,
                                               delay_between=3):
                        return False

                # 7. Next button
                if not self.find_and_click("assets/buttons/next_btn.png", click=True, max_attempts=5, delay_between=3):
                    return False

                # 8. Use Parfait if enabled
                if self.ui_tab.legend_race_use_parfait.get():
                    self.find_and_click("assets/buttons/home/team_trials/parfait.png", click=True, max_attempts=3,
                                        delay_between=1)

                # 9. Race button
                if not self.find_and_click("assets/buttons/home/team_trials/race_btn.png", click=True, max_attempts=5,
                                           delay_between=2):
                    return False

                # 10. View results and click
                see_result_pos = self.find_and_click("assets/buttons/view_results.png", max_attempts=5, delay_between=3)
                if not see_result_pos:
                    return False

                # Click result multiple times
                for i in range(2):
                    pyautogui.click(see_result_pos)
                    time.sleep(4)

                    # 11 & 12. Next buttons
                if not self.find_and_click("assets/buttons/next_btn.png", click=True, max_attempts=3, delay_between=3):
                    return False

                if not self.find_and_click("assets/buttons/next_btn.png", click=True, max_attempts=3, delay_between=2):
                    return False

                    # 13. Handle shop if present
                if self.find_and_click("assets/buttons/home/team_trials/shop_btn.png", click=False, log_attempts=False):
                    self.main_window.log_message("Shop available")

                    if self.ui_tab.legend_race_stop_if_shop.get():
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

                    # 14. Continue to next iteration
                    if not self.find_and_click("assets/buttons/next_btn.png", click=True, max_attempts=3,
                                               delay_between=2):
                        return False

        except Exception as e:
            print(f"Error in Legend Race: {e}")
            return False
        finally:
            self.is_team_trials_running = False

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
        if not self.find_and_click("assets/buttons/refresh_btn.png", click=False, log_attempts=False, max_attempts=2,
                                   delay_between=2):
            time.sleep(4)

        # Check stop condition before next button check
        if self.check_stop_condition():
            return False

        # Step 3 continued: Check for immediate next button (skip to race results)
        if self.find_and_click("assets/buttons/quick_mode_on.png", click=False, confidence=0.7, max_attempts=3,
                               delay_between=1, log_attempts=False) or self.find_and_click("assets/buttons/quick_mode_off.png",
                                                                       click=False, log_attempts=False):
            self.main_window.log_message("Proceeding directly to race")

            # Check stop condition before race button
            if self.check_stop_condition():
                return False

            return self.handle_race_results()

        return True

    def execute_team_trial_cycle(self):
        """Execute one complete team trial cycle with stop checking"""
        # Check stop condition at start of cycle
        if self.check_stop_condition():
            return False

        # Step 3 final: Check for refresh button
        if not self.find_and_click("assets/buttons/refresh_btn.png", max_attempts=8, delay_between=3, click=False,
                                   log_attempts=False):
            self.main_window.log_message("Neither refresh nor next button found")
            return False

        # Check PvP gift
        pvp_gift_pos = self.find_and_click("assets/buttons/home/team_trials/pvp_win_gift.png",
                                           log_attempts="Found Pvp gift")

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

        time.sleep(2)

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
        print('handle_race_results')
        # Check stop condition before handling results
        if self.check_stop_condition():
            return False

        if not self.find_and_click("assets/buttons/home/team_trials/see_all_race_results.png", max_attempts=5, delay_between=2, click_count=2):
            self.main_window.log_message("Failed to find see_all_race_results button")
            return False

        if self.check_stop_condition():
            return False

        if not self.find_and_click("assets/buttons/skip_btn.png", max_attempts=5, delay_between=1, click_count=3):
            return False

        if self.check_stop_condition():
            return False

        if not self.find_and_click("assets/buttons/next_btn.png", max_attempts=5, delay_between=1):
            return False

        time.sleep(1)

        if not self.handle_shop_and_continue():
            return False

        return True

    def handle_shop_and_continue(self):
        """Handle shop detection and race continuation with stop checking"""
        # Check stop condition before shop handling
        time.sleep(2)
        if self.check_stop_condition():
            return False

        # Step 7: Check Story Unlocked
        if self.find_and_click("assets/buttons/close_btn.png", log_attempts=False):
            time.sleep(2)

        # Check for completion buttons after 10 clicks
        should_break = False
        completion_buttons = [
            "assets/buttons/cancel_btn.png", "assets/buttons/next2_btn.png",
            # "assets/buttons/next_btn.png",
            "assets/buttons/home/team_trials/race_again_btn.png"
        ]
        for i in range(10):

            if self.check_stop_condition():
                self.main_window.log_message("Team Trials stopped during race results processing")
                return False

            for button in completion_buttons:
                # Check stop condition before each button check
                if self.check_stop_condition():
                    return False

                if self.find_and_click(button, click=False, log_attempts=False):
                    self.main_window.log_message(f"Completion button found.")
                    should_break = True
                    break
            if should_break:
                break
            pyautogui.click(400, 400)
            time.sleep(1)
        else:
            time.sleep(0.5)

        # Check stop condition before race again button
        if self.check_stop_condition():
            return False

            # Step 7 final: Final race again attempt
        if self.find_and_click("assets/buttons/home/team_trials/race_again_btn.png", log_attempts=False):
            if self.find_and_click("assets/buttons/restore_btn.png", click=False, log_attempts=False):
                self.main_window.log_message("No more turns available - stopping bot")
                return False
            return True
        else:
            # Step 7 alternate: Try next2 button sequence
            if self.find_and_click("assets/buttons/next2_btn.png", log_attempts=False):
                # Check stop condition before next button
                if self.check_stop_condition():
                    return False

                self.find_and_click("assets/buttons/next_btn.png", log_attempts=False, max_attempts=5, delay_between=1)

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
