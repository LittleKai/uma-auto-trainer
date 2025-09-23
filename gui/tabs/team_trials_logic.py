import pyautogui
import time
import threading


class TeamTrialsLogic:
    """Team Trials logic handler - separated from UI"""

    def __init__(self, main_window, ui_tab):
        self.main_window = main_window
        self.ui_tab = ui_tab

        # Team trials state
        self.is_team_trials_running = False
        self.team_trials_thread = None

    def start_team_trials(self):
        """Start team trials functionality"""
        if self.is_team_trials_running:
            return False

        self.is_team_trials_running = True

        # Update status
        self.main_window.status_section.set_bot_status("Team Trials Running", "green")

        # Start team trials in separate thread
        self.team_trials_thread = threading.Thread(target=self.team_trials_loop, daemon=True)
        self.team_trials_thread.start()

        return True

    def stop_team_trials(self):
        """Stop team trials"""
        self.is_team_trials_running = False

        # Update status
        self.main_window.status_section.set_bot_status("Stopped", "red")
        self.main_window.log_message("Team Trials stopped")

    def check_and_repeat(self, image_path, region=None, max_attempts=5, delay_between=1, action="click"):
        """General function to check for image with repeat and delay

        Args:
            image_path: Path to image file
            region: Screen region to search in (optional)
            max_attempts: Maximum number of attempts
            delay_between: Delay between attempts in seconds
            action: 'click' to click if found, 'check' to only check existence

        Returns:
            bool: True if found (and clicked if action='click'), False otherwise
        """
        for attempt in range(max_attempts):
            try:
                if region:
                    button = pyautogui.locateCenterOnScreen(
                        image_path,
                        confidence=0.75,
                        minSearchTime=0.2,
                        region=region
                    )
                else:
                    # Check left half of screen by default
                    screen_width = pyautogui.size().width
                    screen_height = pyautogui.size().height
                    left_half_region = (0, 0, screen_width // 2, screen_height)
                    button = pyautogui.locateCenterOnScreen(
                        image_path,
                        confidence=0.75,
                        minSearchTime=0.2,
                        region=left_half_region
                    )

                if button:
                    if action == "click":
                        pyautogui.click(button)
                        self.main_window.log_message(f"Successfully found and clicked {image_path} on attempt {attempt + 1}")
                    else:
                        self.main_window.log_message(f"Successfully found {image_path} on attempt {attempt + 1}")
                    return True

            except pyautogui.ImageNotFoundException:
                pass

            # Log attempt if not the last one
            if attempt < max_attempts - 1:
                self.main_window.log_message(f"{image_path} not found - attempt {attempt + 1}/{max_attempts}")
                time.sleep(delay_between)

        self.main_window.log_message(f"Failed to find {image_path} after {max_attempts} attempts")
        return False

    def click_button_with_check(self, image_path, region=None, max_attempts=1, delay_after=0):
        """Click button with image detection and check"""
        for attempt in range(max_attempts):
            try:
                if region:
                    button = pyautogui.locateCenterOnScreen(
                        image_path,
                        confidence=0.75,
                        minSearchTime=0.2,
                        region=region
                    )
                else:
                    # Check left half of screen by default
                    screen_width = pyautogui.size().width
                    screen_height = pyautogui.size().height
                    left_half_region = (0, 0, screen_width // 2, screen_height)
                    button = pyautogui.locateCenterOnScreen(
                        image_path,
                        confidence=0.75,
                        minSearchTime=0.2,
                        region=left_half_region
                    )

                if button:
                    pyautogui.click(button)
                    if delay_after > 0:
                        time.sleep(delay_after)
                    return True
            except pyautogui.ImageNotFoundException:
                pass

            time.sleep(1)

        return False

    def check_button_exists(self, image_path, region=None):
        """Check if button exists without clicking"""
        try:
            if region:
                button = pyautogui.locateCenterOnScreen(
                    image_path,
                    confidence=0.75,
                    minSearchTime=0.2,
                    region=region
                )
            else:
                # Check left half of screen by default
                screen_width = pyautogui.size().width
                screen_height = pyautogui.size().height
                left_half_region = (0, 0, screen_width // 2, screen_height)
                button = pyautogui.locateCenterOnScreen(
                    image_path,
                    confidence=0.75,
                    minSearchTime=0.2,
                    region=left_half_region
                )
            return button is not None
        except pyautogui.ImageNotFoundException:
            return False

    def team_trials_loop(self):
        """Main team trials loop"""
        try:
            # Step 2: Check for race tab and navigate to team trials
            if not self.navigate_to_team_trials():
                return

            while self.is_team_trials_running:
                # Step 4: Main team trials loop
                if not self.execute_team_trial_cycle():
                    break

        except Exception as e:
            self.main_window.log_message(f"Team Trials error: {e}")
        finally:
            self.main_window.root.after(0, self.stop_team_trials)

    def navigate_to_team_trials(self):
        """Navigate to team trials section"""
        # Step 2: Check race tab in home (try both versions)
        race_tab_region = (200, 780, 680, 860)
        race_tab_found = False
        race_tab_image = ""

        # Try first race tab image
        if self.check_button_exists("assets/buttons/home/team_trials/race_tab.png", race_tab_region):
            race_tab_found = True
            race_tab_image = "assets/buttons/home/team_trials/race_tab.png"
            self.main_window.log_message("Found race_tab.png")
        # Try second race tab image if first not found
        elif self.check_button_exists("assets/buttons/home/team_trials/race_tab_2.png", race_tab_region):
            race_tab_found = True
            race_tab_image = "assets/buttons/home/team_trials/race_tab_2.png"
            self.main_window.log_message("Found race_tab_2.png")

        if not race_tab_found:
            self.main_window.log_message("Race tab not found - Không phải Home")
            return False

        # Click race tab using the found image
        if not self.click_button_with_check(race_tab_image, race_tab_region, delay_after=1):
            self.main_window.log_message("Failed to click race tab")
            return False

        self.main_window.log_message("Clicked race tab successfully")
        time.sleep(3)

        # Click team trial button - sử dụng hàm check_and_repeat
        if not self.check_and_repeat("assets/buttons/home/team_trials/team_trial_btn.png", max_attempts=5, delay_between=3):
            self.main_window.log_message("Failed to find team trial button after multiple attempts")
            return False

        self.main_window.log_message("Team trial button found and clicked successfully")

        # Step 3: Check and click team race button with 5 attempts, 4s delay each
        time.sleep(5)
        team_race_clicked = False
        for attempt in range(5):
            if self.click_button_with_check("assets/buttons/home/team_trials/team_race_btn.png", delay_after=3):
                team_race_clicked = True
                self.main_window.log_message(f"Clicked team race button successfully on attempt {attempt + 1}")
                break
            self.main_window.log_message(f"Team race button not found - attempt {attempt + 1}/5")
            time.sleep(4)

        if not team_race_clicked:
            self.main_window.log_message("Failed to click team race button after 5 attempts")
            return False

        # Wait for refresh button to appear and check for next button
        refresh_found = False

        for attempt in range(5):
            # First check for next button - if found, click and go to step 6
            if self.click_button_with_check("assets/buttons/next_btn.png", delay_after=1):
                self.main_window.log_message("Next button found and clicked during refresh check - proceeding to step 6")
                # Click race button
                if not self.click_button_with_check("assets/buttons/home/team_trials/race_btn.png"):
                    self.main_window.log_message("Failed to find race button")
                    return False

                self.main_window.log_message("Clicked race button")

                self.main_window.log_message("Proceeding to step 6")
                # Skip to step 6 - race results handling
                return self.handle_race_results()

            # If no next button, check for refresh button
            if self.check_button_exists("assets/buttons/refresh_btn.png"):
                refresh_found = True
                self.main_window.log_message("Refresh button found")
                break

            self.main_window.log_message(f"Neither refresh nor next button found - attempt {attempt + 1}/5")
            time.sleep(3)

        if not refresh_found:
            self.main_window.log_message("Refresh button not found after 5 attempts")
            return False

        return True

    def handle_race_results(self):
        """Handle race results (Step 6 logic)"""
        # Step 6: Handle race results
        time.sleep(10)

        # Store mouse position after clicking see result
        see_result_pos = None

        # Try to find and click see result button with 5 attempts, 5s delay each
        see_result_found = False
        for attempt in range(5):
            try:
                button = pyautogui.locateCenterOnScreen(
                    "assets/buttons/home/team_trials/see_result.png",
                    confidence=0.75,
                    minSearchTime=0.2
                )
                if button:
                    pyautogui.click(button)
                    see_result_pos = button  # Store the position
                    see_result_found = True
                    time.sleep(1)
                    self.main_window.log_message(f"Found and clicked see result button on attempt {attempt + 1} - storing position")
                    break
                else:
                    self.main_window.log_message(f"See result button not found - attempt {attempt + 1}/5")
            except pyautogui.ImageNotFoundException:
                self.main_window.log_message(f"See result button not found - attempt {attempt + 1}/5")

            if attempt < 4:  # Don't delay after the last attempt
                time.sleep(5)

        if not see_result_found:
            self.main_window.log_message("See result button not found after 5 attempts")
            return False

        # Click at the stored position 40 times total
        if see_result_pos:
            for i in range(40):
                if not self.is_team_trials_running:
                    return False

                # After the 25th click, start checking for step 7 buttons
                if i >= 24:  # After 25 clicks (0-indexed, so >= 24)
                    # Check for cancel button (shop available)
                    if self.check_button_exists("assets/buttons/cancel_btn.png"):
                        self.main_window.log_message(f"Cancel button found on click {i + 1} - proceeding to step 7")
                        return self.handle_shop_and_continue()

                    # Check for next2 button
                    if self.check_button_exists("assets/buttons/next2_btn.png"):
                        self.main_window.log_message(f"Next2 button found on click {i + 1} - proceeding to step 7")
                        return self.handle_shop_and_continue()

                    # Check for race again button
                    if self.check_button_exists("assets/buttons/home/team_trials/race_again_btn.png"):
                        self.main_window.log_message(f"Race again button found on click {i + 1} - proceeding to step 7")
                        return self.handle_shop_and_continue()

                pyautogui.click(see_result_pos)
                time.sleep(0.5)
                self.main_window.log_message(f"Clicked at see result position {i + 1}/40")

        # If completed all 40 clicks without finding step 7 buttons, continue to step 7
        self.main_window.log_message("After Clicks, Buttons not found - Stop Bot")
        return False

    def handle_shop_and_continue(self):
        """Handle shop detection and continue (Step 7 logic)"""
        # Step 7: Handle shop and continue

        # Try to continue with next2 button
        if self.click_button_with_check("assets/buttons/next2_btn.png", delay_after=5):
            self.main_window.log_message("Clicked next2 button")
            if not self.click_button_with_check("assets/buttons/next_btn.png", delay_after=2):
                self.main_window.log_message("Failed to find next button after next2")
                return False
            self.main_window.log_message("Clicked next button after next2")
        else:
            self.main_window.log_message("Next2 button not found - continuing without it")

        time.sleep(5)
        # Check for cancel button (shop available)
        if self.check_button_exists("assets/buttons/cancel_btn.png"):
            self.main_window.log_message("Cancel button found - shop available")
            if self.ui_tab.stop_if_shop.get():
                # Stop if shop and option is enabled
                if self.click_button_with_check("assets/buttons/home/team_trials/shop_btn.png"):
                    self.main_window.log_message("Shop detected - stopping as requested")
                    return False
                else:
                    self.main_window.log_message("Failed to find shop button")
            else:
                # Continue - click cancel
                if not self.click_button_with_check("assets/buttons/cancel_btn.png", delay_after=1):
                    self.main_window.log_message("Failed to click cancel button")
                    return False
                self.main_window.log_message("Clicked cancel button")
        else:
            self.main_window.log_message("No cancel button found - no shop")


        # Click race again button
        if not self.click_button_with_check("assets/buttons/home/team_trials/race_again_btn.png"):
            self.main_window.log_message("Failed to find race again button")
            return False

        self.main_window.log_message("Clicked race again button")

        # Step 8: Check for no button (end condition)
        time.sleep(1)
        if self.check_button_exists("assets/buttons/no_btn.png"):
            self.main_window.log_message("No button detected - stopping team trials")
            return False

        self.main_window.log_message("No button not found - continuing team trials cycle")
        return True

    def execute_team_trial_cycle(self):
        """Execute one complete team trial cycle"""
        if not self.is_team_trials_running:
            return False

        for attempt in range(5):
            # If no next button, check for refresh button
            if self.check_button_exists("assets/buttons/refresh_btn.png"):
                refresh_found = True
                self.main_window.log_message("Refresh button found")
                break

            self.main_window.log_message(f"Refresh button not found - attempt {attempt + 1}/5")
            time.sleep(3)

        # Step 4: Check for PvP gift and opponent selection
        pvp_region = (200, 150, 700, 720)
        clicked_pvp_gift = False

        # Check for PvP gift and click on its exact position
        try:
            pvp_gift_button = pyautogui.locateCenterOnScreen(
                "assets/buttons/home/team_trials/pvp_win_gift.png",
                confidence=0.75,
                minSearchTime=0.2,
                region=pvp_region
            )

            if pvp_gift_button:
                pyautogui.click(pvp_gift_button)
                clicked_pvp_gift = True
                self.main_window.log_message("Found and clicked PvP gift")
            else:
                self.main_window.log_message("PvP gift not found - selecting opponent")
        except pyautogui.ImageNotFoundException:
            self.main_window.log_message("PvP gift not found - selecting opponent")

        if not clicked_pvp_gift:
            # Select opponent based on dropdown choice
            opponent_positions = {
                "Opponent 1": (500, 300),
                "Opponent 2": (500, 550),
                "Opponent 3": (500, 800)
            }

            opponent_choice = self.ui_tab.opponent_type.get()
            if opponent_choice in opponent_positions:
                pos = opponent_positions[opponent_choice]
                pyautogui.click(pos)
                self.main_window.log_message(f"Selected {opponent_choice} at position {pos}")
                time.sleep(10)

                # Click next button with 5 attempts, 4s delay each
                next_clicked = False
                for attempt in range(5):
                    if self.click_button_with_check("assets/buttons/next_btn.png"):
                        next_clicked = True
                        self.main_window.log_message(f"Clicked next button after opponent selection on attempt {attempt + 1}")
                        break
                    self.main_window.log_message(f"Next button not found after opponent selection - attempt {attempt + 1}/5")
                    if attempt < 4:  # Don't delay after the last attempt
                        time.sleep(4)

                if not next_clicked:
                    self.main_window.log_message("Failed to find next button after opponent selection after 5 attempts")
                    return False

        # Step 5: Handle parfait and race preparation
        # Wait for next button to appear (check 5 times, 3s delay each)
        time.sleep(5)
        next_found = False
        for attempt in range(5):
            if self.click_button_with_check("assets/buttons/next_btn.png", delay_after=1):
                next_found = True
                self.main_window.log_message(f"Next button clicked successfully on attempt {attempt + 1}")
                break
            self.main_window.log_message(f"Next button not found/clicked - attempt {attempt + 1}/5")
            time.sleep(3)

        if not next_found:
            self.main_window.log_message("Failed to click next button after 5 attempts")
            return False

        self.main_window.log_message("Clicked next button in step 5")

        time.sleep(5)

        if not self.check_button_exists(self,"assets/buttons/home/team_trials/race_btn.png"):
            self.click_button_with_check("assets/buttons/next_btn.png", delay_after=2)

        # If clicked PvP gift, handle parfait option
        if clicked_pvp_gift and self.ui_tab.use_parfait_gift_pvp.get():
            if not self.click_button_with_check("assets/buttons/home/team_trials/parfait.png"):
                self.main_window.log_message("Failed to find parfait button")
            else:
                self.main_window.log_message("Clicked parfait button")

        # Click race button
        if not self.click_button_with_check("assets/buttons/home/team_trials/race_btn.png"):
            self.main_window.log_message("Failed to find race button")
            return False

        self.main_window.log_message("Clicked race button")

        # Now handle race results using the separated method
        return self.handle_race_results()