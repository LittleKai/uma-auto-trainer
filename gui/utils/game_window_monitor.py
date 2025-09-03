import threading
import time
import pygetwindow as gw


class GameWindowMonitor:
    """Monitors game window status and provides window management functions"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.monitoring = False
        self.monitor_thread = None

    def start(self):
        """Start game window monitoring in background thread"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """Stop game window monitoring"""
        self.monitoring = False

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self.check_game_window()
                time.sleep(2)
            except Exception as e:
                # Silently continue on errors to avoid spam
                pass

    def check_game_window(self):
        """Check game window status and update GUI"""
        try:
            window_titles = ["Umamusume", "ウマ娘", "Uma Musume", "DMM GAME PLAYER"]

            found_window = None
            window_title_found = ""

            # Search for game window
            for title in window_titles:
                try:
                    windows = gw.getWindowsWithTitle(title)
                    if windows:
                        found_window = windows[0]
                        window_title_found = title
                        break
                except Exception:
                    continue

            if found_window:
                self._handle_found_window(found_window, window_title_found)
            else:
                self._handle_missing_window()

        except Exception as e:
            self.main_window.root.after(0, self.main_window.update_game_status,
                                        f"Error: {str(e)[:30]}", "red")

    def _handle_found_window(self, window, title):
        """Handle when game window is found"""
        try:
            is_active = window.isActive
            window_info = f"Found ({title})"

            if is_active:
                self.main_window.root.after(0, self.main_window.update_game_status,
                                            f"{window_info} - Active", "green")
            else:
                self.main_window.root.after(0, self.main_window.update_game_status,
                                            f"{window_info} - Inactive", "orange")
        except Exception:
            self.main_window.root.after(0, self.main_window.update_game_status,
                                        f"Found ({title}) - Error", "red")

    def _handle_missing_window(self):
        """Handle when game window is not found"""
        try:
            all_windows = gw.getAllWindows()
            game_related = [w for w in all_windows
                            if any(keyword in w.title.lower()
                                   for keyword in ['uma', 'ウマ', 'dmm', 'game'])
                            and w.title.strip()]

            if game_related:
                titles = [w.title[:30] + "..." if len(w.title) > 30 else w.title
                          for w in game_related[:3]]
                hint = f"Similar: {', '.join(titles)}"
                self.main_window.root.after(0, self.main_window.update_game_status,
                                            f"Not Found - {hint}", "red")
            else:
                self.main_window.root.after(0, self.main_window.update_game_status,
                                            "Not Found - Please start game", "red")
        except Exception:
            self.main_window.root.after(0, self.main_window.update_game_status,
                                        "Not Found - Detection Error", "red")

    def focus_game_window(self):
        """Focus and activate game window"""
        try:
            window_titles = ["Umamusume", "ウマ娘", "Uma Musume", "DMM GAME PLAYER"]

            found_window = None
            for title in window_titles:
                try:
                    windows = gw.getWindowsWithTitle(title)
                    if windows:
                        found_window = windows[0]
                        break
                except Exception:
                    continue

            # Fallback search
            if not found_window:
                all_windows = gw.getAllWindows()
                game_windows = [w for w in all_windows
                                if any(keyword in w.title.lower()
                                       for keyword in ['uma', 'ウマ', 'dmm'])
                                and w.title.strip()]
                if game_windows:
                    found_window = game_windows[0]

            if not found_window:
                self.main_window.log_message("Error: No game window found with any recognized title")
                self.main_window.log_message("Please ensure the game is running and window title contains 'Umamusume', 'ウマ娘', 'Uma Musume', or 'DMM GAME PLAYER'")
                return False

            # Focus the window
            if found_window.isMinimized:
                found_window.restore()
            found_window.activate()

            try:
                found_window.maximize()
            except:
                pass

            time.sleep(0.5)
            return True

        except Exception as e:
            self.main_window.log_message(f"Error focusing game window: {e}")
            return False