import threading
import keyboard
from tkinter import messagebox

from core.execute import set_stop_flag, career_lobby


class BotController:
    """Handles bot control operations, keyboard shortcuts, and bot logic"""

    def __init__(self, main_window):
        self.main_window = main_window

    def setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts"""
        try:
            keyboard.add_hotkey('f1', self.main_window.start_bot)
            keyboard.add_hotkey('f3', self.enhanced_stop_bot)
            keyboard.add_hotkey('f5', self.main_window.force_exit_program)
        except Exception as e:
            self.main_window.log_message(f"Warning: Could not setup keyboard shortcuts: {e}")

    def start_bot(self):
        """Start the bot and save support card counts from current preset"""
        if self.main_window.is_running:
            return

        if not self.main_window.initial_key_validation_done:
            self.main_window.log_message("Waiting for key validation to complete...")
            return

        if not self.main_window.key_valid:
            messagebox.showerror("Key Validation Failed", "Invalid key. Cannot start bot.")
            self.main_window.log_message("Bot start failed: Invalid key")
            return

        if not self.main_window.game_monitor.focus_game_window():
            self.main_window.log_message("Cannot start bot: Game window not found or cannot be focused")
            return

        # Check if Team Trials tab is active
        if hasattr(self.main_window, 'team_trials_tab') and self.main_window.team_trials_tab.is_active_tab():
            # Start Team Trials
            if self.main_window.team_trials_tab.start_team_trials():
                self.main_window.is_running = True
                self.main_window.set_running_state(True)
                return
            else:
                self.main_window.log_message("Failed to start Team Trials")
                return

        # Start normal bot
        # Save support card counts from current preset to state
        self.save_support_card_state()

        set_stop_flag(False)
        self.main_window.is_running = True

        # Update UI
        self.main_window.set_running_state(True)
        self.main_window.status_section.set_bot_status("Running", "green")

        # Start bot thread
        self.main_window.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.main_window.bot_thread.start()

        self.main_window.log_message("Bot started successfully!")

    def save_support_card_state(self):
        """Save support card counts from current preset when F1 is pressed"""
        try:
            # Get current support cards from event choice tab
            current_settings = self.main_window.get_event_choice_settings()
            support_cards = current_settings.get('support_cards', [])

            # Count each support card type
            support_card_counts = {
                'spd': 0,
                'sta': 0,
                'pwr': 0,
                'guts': 0,
                'wit': 0,
                'friend': 0
            }

            for card in support_cards:
                if card == "None" or not card:
                    continue

                # Extract card type from card name (format: "type: Card Name" or "type/Card Name")
                card_lower = card.lower()
                if 'spd' in card_lower or 'speed' in card_lower:
                    support_card_counts['spd'] += 1
                elif 'sta' in card_lower or 'stamina' in card_lower:
                    support_card_counts['sta'] += 1
                elif 'pow' in card_lower or 'power' in card_lower:
                    support_card_counts['pwr'] += 1
                elif 'gut' in card_lower:
                    support_card_counts['guts'] += 1
                elif 'wit' in card_lower or 'wisdom' in card_lower:
                    support_card_counts['wit'] += 1
                elif 'frd' in card_lower or 'friend' in card_lower:
                    support_card_counts['friend'] += 1

            # Save to global state for use in training calculations
            from core.state import set_support_card_state
            set_support_card_state(support_card_counts)

            # Log the saved counts
            self.main_window.log_message(f"Support cards: {support_card_counts}")

        except Exception as e:
            self.main_window.log_message(f"Error saving support card state: {e}")

    def stop_bot(self):
        """Stop the bot"""
        if not self.main_window.is_running:
            return

        # Stop team trials if running
        if hasattr(self.main_window, 'team_trials_tab') and self.main_window.team_trials_tab.is_team_trials_running:
            self.main_window.team_trials_tab.stop_team_trials()

        # Stop main bot
        set_stop_flag(True)
        self.main_window.is_running = False

        # Update UI
        self.main_window.set_running_state(False)
        self.main_window.status_section.set_bot_status("Stopped", "red")

        self.main_window.log_message("Bot stopped")

    def enhanced_stop_bot(self):
        """Enhanced F3 stop functionality - handles both main bot and team trials"""
        set_stop_flag(True)
        self.stop_bot()

        # Also stop team trials if running
        if hasattr(self.main_window, 'team_trials_tab'):
            team_trials_tab = self.main_window.team_trials_tab
            if hasattr(team_trials_tab, 'is_team_trials_running') and team_trials_tab.is_team_trials_running:
                team_trials_tab.stop_team_trials()

    def force_exit_program(self):
        """Force exit program - F5 key handler"""
        self.main_window.log_message("F5 pressed - Force exiting program...")
        self.stop_bot()

        # Also stop team trials if running
        if hasattr(self.main_window, 'team_trials_tab'):
            team_trials_tab = self.main_window.team_trials_tab
            if hasattr(team_trials_tab, 'is_team_trials_running') and team_trials_tab.is_team_trials_running:
                team_trials_tab.stop_team_trials()

        try:
            keyboard.unhook_all()
        except:
            pass
        import os
        os._exit(0)

    def bot_loop(self):
        """Main bot loop running in separate thread"""
        try:
            career_lobby(self.main_window)
        except Exception as e:
            self.main_window.log_message(f"Bot error: {e}")
        finally:
            self.main_window.root.after(0, self.stop_bot)

    def should_stop_for_conditions(self, game_state):
        """
        Check all stop conditions and return True if any condition is met
        This function should be added to the main GUI window class
        """
        try:
            # Get current settings
            settings = self.main_window.get_current_settings()

            # Return False if stop conditions are disabled
            if not settings.get('enable_stop_conditions', False):
                return False

            current_date = game_state.get('current_date', {})
            absolute_day = current_date.get('absolute_day', 0)

            # Most conditions only apply after day 24
            day_24_passed = absolute_day > 24

            # 1. Stop when race day (works immediately, no day restriction)
            if (settings.get('stop_on_race_day', False) and
                    game_state.get('turn') == "Race Day" and
                    game_state.get('year') != "Finale Season"):
                self.main_window.log_message("Stop condition triggered: Race Day detected")
                return True

            # Skip other conditions if before day 24
            if not day_24_passed:
                return False

            # 2. Stop when infirmary needed (check debuff status)
            if settings.get('stop_on_infirmary', False):
                debuff_status = game_state.get('debuff_status', {})
                has_serious_debuff = any([
                    debuff_status.get('headache', False),
                    debuff_status.get('stomach_ache', False),
                    debuff_status.get('cold', False),
                    debuff_status.get('overweight', False),
                    debuff_status.get('injury', False)
                ])
                if has_serious_debuff:
                    self.main_window.log_message("Stop condition triggered: Infirmary needed (serious debuff detected)")
                    return True

            # 3. Stop when need rest (check energy level)
            if settings.get('stop_on_need_rest', False):
                energy_percentage = game_state.get('energy_percentage', 100)
                # Consider need rest when energy is very low (below 30%)
                if energy_percentage < 42:
                    self.main_window.log_message(f"Stop condition triggered: Need rest (Energy: {energy_percentage}%)")
                    return True

            # 4. Stop when mood below threshold
            if settings.get('stop_on_low_mood', False):
                current_mood = game_state.get('mood', 'NORMAL')
                threshold_mood = settings.get('stop_mood_threshold', 'BAD')

                mood_levels = ['AWFUL', 'BAD', 'NORMAL', 'GOOD', 'GREAT']
                current_mood_index = mood_levels.index(current_mood) if current_mood in mood_levels else 2
                threshold_mood_index = mood_levels.index(threshold_mood) if threshold_mood in mood_levels else 1
                if not current_mood == "UNKNOWN":
                    if current_mood_index < threshold_mood_index:
                        self.main_window.log_message(f"Stop condition triggered: Mood ({current_mood}) below threshold ({threshold_mood})")
                        return True

            # 5. Stop before summer (June - month 6)
            if settings.get('stop_before_summer', False):
                month_num = current_date.get('month_num', 0)
                if month_num == 6:  # June
                    self.main_window.log_message("Stop condition triggered: Summer period reached (June)")
                    return True

            # 6. Stop at specific month
            if settings.get('stop_at_month', False):
                target_month = settings.get('target_month', 'June')
                current_month = current_date.get('month', '')

                # Convert month names to compare
                month_mapping = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4,
                    'May': 5, 'June': 6, 'July': 7, 'August': 8,
                    'September': 9, 'October': 10, 'November': 11, 'December': 12
                }

                target_month_num = month_mapping.get(target_month, 0)
                current_month_num = current_date.get('month_num', 0)

                if current_month_num == target_month_num:
                    self.main_window.log_message(f"Stop condition triggered: Target month reached ({target_month})")
                    return True

            return False

        except Exception as e:
            self.main_window.log_message(f"Error checking stop conditions: {e}")
            return False