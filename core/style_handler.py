"""
Style Handler for Junior Style Selection at Debut

Handles detection of the style selection screen and automatic selection
of the preferred running style during debut.
"""

import pyautogui
import time
import cv2
import numpy as np
from PIL import ImageGrab
from typing import Dict, Optional, Callable, Any, List, Tuple

from core.click_handler import enhanced_click


STYLE_DISPLAY = {
    'none': 'None',
    'front': 'Front',
    'pace': 'Pace',
    'late': 'Late',
    'end': 'End',
}

# Assets folder for style buttons
STYLE_ASSETS_FOLDER = 'assets/buttons/style'


class StyleHandler:
    """Handler for Junior Style Selection at Debut"""

    def __init__(self, check_stop_func: Callable, check_window_func: Callable, log_func: Callable):
        """
        Initialize style handler

        Args:
            check_stop_func: Function to check if should stop
            check_window_func: Function to check if game window is active
            log_func: Function to log messages
        """
        self.check_stop = check_stop_func
        self.check_window = check_window_func
        self.log = log_func

        # Style button templates (will be loaded on demand)
        self.templates_loaded = False
        self.style_templates = {}

    def _load_templates(self) -> bool:
        """Load style selection templates"""
        if self.templates_loaded:
            return True

        import os

        # Template paths for style selection screen and buttons
        template_paths = {
            'screen': 'assets/scenario/style_selection.png',
            'front': f'{STYLE_ASSETS_FOLDER}/front.png',
            'pace': f'{STYLE_ASSETS_FOLDER}/pace.png',
            'late': f'{STYLE_ASSETS_FOLDER}/late.png',
            'end': f'{STYLE_ASSETS_FOLDER}/end.png',
            'confirm': f'{STYLE_ASSETS_FOLDER}/confirm.png',
        }

        for key, path in template_paths.items():
            if os.path.exists(path):
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is not None:
                    self.style_templates[key] = template

        self.templates_loaded = True
        return len(self.style_templates) > 0

    def is_style_selection_screen(self) -> bool:
        """Check if current screen is the style selection screen at debut"""
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        # Try template matching first if we have the template
        self._load_templates()

        if 'screen' in self.style_templates:
            try:
                screen = np.array(ImageGrab.grab())
                screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

                template = self.style_templates['screen']
                result = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)

                if max_val > 0.8:
                    return True
            except Exception as e:
                print(f"Error checking style screen with template: {e}")

        # Fallback: use pyautogui to check for style selection screen
        try:
            style_screen = pyautogui.locateCenterOnScreen(
                "assets/scenario/style_selection.png",
                confidence=0.8,
                minSearchTime=0.3
            )
            return style_screen is not None
        except Exception as e:
            print(f"Error checking style screen: {e}")
            return False

    def detect_style_buttons(self) -> List[Dict[str, Any]]:
        """
        Detect style option buttons on screen

        Returns:
            List of dictionaries containing button info:
            {'style': style_id, 'position': (x, y), 'confidence': float}
        """
        if self.check_stop():
            return []

        buttons = []

        # Try to find each style button
        style_buttons = {
            'front': f'{STYLE_ASSETS_FOLDER}/front.png',
            'pace': f'{STYLE_ASSETS_FOLDER}/pace.png',
            'late': f'{STYLE_ASSETS_FOLDER}/late.png',
            'end': f'{STYLE_ASSETS_FOLDER}/end.png',
        }

        for style_id, template_path in style_buttons.items():
            if self.check_stop():
                break

            try:
                import os
                if not os.path.exists(template_path):
                    continue

                pos = pyautogui.locateCenterOnScreen(
                    template_path,
                    confidence=0.8,
                    minSearchTime=0.2
                )

                if pos:
                    buttons.append({
                        'style': style_id,
                        'position': (pos.x, pos.y),
                        'confidence': 0.8
                    })
            except Exception as e:
                print(f"Error detecting {style_id} button: {e}")

        return buttons

    def select_style(self, target_style: str) -> bool:
        """
        Select the specified running style

        Args:
            target_style: Style to select ('front', 'pace', 'late', 'end')

        Returns:
            True if style was selected successfully
        """
        if self.check_stop():
            return False

        if not self.check_window():
            return False

        if target_style == 'none':
            return False

        # Try to click the style button
        template_path = f"{STYLE_ASSETS_FOLDER}/{target_style}.png"

        try:
            import os
            if os.path.exists(template_path):
                clicked = enhanced_click(
                    template_path,
                    text=f"Selecting style: {STYLE_DISPLAY.get(target_style, target_style)}",
                    check_stop_func=self.check_stop,
                    check_window_func=self.check_window,
                    log_func=self.log
                )

                if clicked:
                    time.sleep(0.5)

                    # Click confirm button
                    if self.check_stop():
                        return False

                    confirm_clicked = self._click_confirm_button()
                    if confirm_clicked:
                        self.log(f"Style selected successfully: {STYLE_DISPLAY.get(target_style, target_style)}")
                        return True
                    else:
                        self.log("[WARNING] Could not find confirm button after style selection")
                        return False

            else:
                self.log(f"[WARNING] Style template not found: {template_path}")
                # Fallback: try position-based selection
                return self._select_style_by_position(target_style)

        except Exception as e:
            self.log(f"[ERROR] Failed to select style: {e}")
            return False

        return False

    def _click_confirm_button(self) -> bool:
        """Click the confirm/OK button after selecting style"""
        if self.check_stop():
            return False

        # Try multiple possible confirm button templates
        confirm_templates = [
            f"{STYLE_ASSETS_FOLDER}/confirm.png",
            "assets/buttons/ok_btn.png",
            "assets/buttons/confirm_btn.png",
        ]

        for template in confirm_templates:
            if self.check_stop():
                return False

            try:
                import os
                if not os.path.exists(template):
                    continue

                clicked = enhanced_click(
                    template,
                    minSearch=0.5,
                    check_stop_func=self.check_stop,
                    check_window_func=self.check_window,
                    log_func=self.log
                )

                if clicked:
                    return True
            except Exception:
                continue

        return False

    def _select_style_by_position(self, style: str) -> bool:
        """
        Fallback: Select style by approximate screen position

        The style buttons are typically arranged vertically:
        1. Front - Top
        2. Pace - Second
        3. Late - Third
        4. End - Bottom
        """
        if self.check_stop():
            return False

        # Style positions are relative to screen center
        # These are approximate positions based on typical 1920x1080 resolution
        style_positions = {
            'front': (960, 400),     # Top button
            'pace': (960, 500),      # Second button
            'late': (960, 600),      # Third button
            'end': (960, 700),       # Bottom button
        }

        if style not in style_positions:
            self.log(f"[ERROR] Unknown style: {style}")
            return False

        x, y = style_positions[style]

        try:
            self.log(f"Using position-based style selection at ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(0.5)

            if self.check_stop():
                return False

            # Click confirm
            return self._click_confirm_button()

        except Exception as e:
            self.log(f"[ERROR] Position-based style selection failed: {e}")
            return False

    def handle_style_selection(self, style_settings: Dict[str, Any]) -> bool:
        """
        Handle the complete style selection flow

        Args:
            style_settings: Dictionary with style preferences:
                - style: str - Preferred style ('none', 'front', 'pace', 'late', 'end')

        Returns:
            True if style selection was handled
        """
        if self.check_stop():
            return False

        selected_style = style_settings.get('style', 'none')

        # If style is 'none', skip style selection
        if selected_style == 'none':
            return False

        # Check if we're on the style selection screen
        if not self.is_style_selection_screen():
            return False

        self.log("Style selection screen detected")

        # Try to select the style
        if self.select_style(selected_style):
            return True

        self.log("[WARNING] Style selection failed, manual intervention may be needed")
        return False


def get_style_options() -> List[Tuple[str, str]]:
    """
    Get list of available style options for UI dropdown

    Returns:
        List of tuples (style_id, display_name)
    """
    return [
        ('none', 'None'),
        ('front', 'Front'),
        ('pace', 'Pace'),
        ('late', 'Late'),
        ('end', 'End'),
    ]


def get_style_display_name(style_id: str) -> str:
    """Get display name for a style ID"""
    return STYLE_DISPLAY.get(style_id, style_id)


__all__ = [
    'StyleHandler',
    'STYLE_DISPLAY',
    'STYLE_ASSETS_FOLDER',
    'get_style_options',
    'get_style_display_name',
]
