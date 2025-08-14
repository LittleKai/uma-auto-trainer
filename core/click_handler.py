import pyautogui
import random
import time
from typing import Tuple, Optional

def random_click_in_region(left: int, top: int, width: int, height: int, duration: float = 0.175) -> bool:
    """
    Click at a random position within the specified region

    Args:
        left, top, width, height: Region boundaries
        duration: Mouse movement duration

    Returns:
        bool: True if click was successful
    """
    try:
        # Generate random coordinates within the region
        # Add some padding to avoid clicking too close to edges
        padding = min(width, height) * 0.1  # 10% padding

        random_x = left + padding + random.random() * (width - 2 * padding)
        random_y = top + padding + random.random() * (height - 2 * padding)

        # Ensure coordinates are within bounds
        random_x = max(left, min(left + width, random_x))
        random_y = max(top, min(top + height, random_y))

        pyautogui.moveTo(random_x, random_y, duration=duration)
        pyautogui.click()

        return True
    except Exception as e:
        print(f"[WARNING] Random click failed: {e}")
        return False

def enhanced_click(img: str, confidence: float = 0.8, minSearch: float = 2,
                   click_count: int = 1, text: str = "", use_random: bool = True,
                   check_stop_func=None, check_window_func=None, log_func=None) -> bool:
    """
    Enhanced click function with random clicking and stop check

    Args:
        img: Image path to find and click
        confidence: Template matching confidence
        minSearch: Minimum search time
        click_count: Number of clicks to perform
        text: Optional text to log
        use_random: Whether to use random clicking
        check_stop_func: Function to check if should stop
        check_window_func: Function to check if game window is active
        log_func: Function to log messages

    Returns:
        bool: True if click was successful
    """
    if check_stop_func and check_stop_func():
        return False

    if check_window_func and not check_window_func():
        return False

    btn = pyautogui.locateCenterOnScreen(img, confidence=confidence, minSearchTime=minSearch)
    if btn:
        if text and log_func:
            log_func(text)

        if check_stop_func and check_stop_func():
            return False

        if use_random:
            # Get the full button region for random clicking
            btn_region = pyautogui.locateOnScreen(img, confidence=confidence, minSearchTime=0.1)
            if btn_region:
                # Click randomly within the button region
                for _ in range(click_count):
                    if check_stop_func and check_stop_func():
                        return False
                    random_click_in_region(btn_region.left, btn_region.top,
                                           btn_region.width, btn_region.height)
                    if click_count > 1:
                        time.sleep(0.1)  # Small delay between multiple clicks
            else:
                # Fallback to center click if region detection fails
                pyautogui.moveTo(btn, duration=0.175)
                pyautogui.click(clicks=click_count)
        else:
            # Traditional center click
            pyautogui.moveTo(btn, duration=0.175)
            pyautogui.click(clicks=click_count)

        return True

    return False

def random_screen_click(offset_range: int = 100) -> None:
    """
    Click at a random position near screen center

    Args:
        offset_range: Maximum offset from center in pixels
    """
    try:
        screen_width, screen_height = pyautogui.size()
        center_x = screen_width // 2 + random.randint(-offset_range, offset_range)
        center_y = screen_height // 2 + random.randint(-offset_range, offset_range)
        pyautogui.click(center_x, center_y)
    except Exception as e:
        print(f"[WARNING] Random screen click failed: {e}")

def triple_click_random(region: Tuple[int, int, int, int], interval: float = 0.1) -> None:
    """
    Perform triple click with random positions within region

    Args:
        region: (left, top, width, height) region to click in
        interval: Interval between clicks
    """
    left, top, width, height = region

    for i in range(3):
        random_click_in_region(left, top, width, height, duration=0.1)
        if i < 2:  # Don't sleep after the last click
            time.sleep(interval)

def move_to_random_position(base_x: int, base_y: int, offset_range: int = 10) -> None:
    """
    Move mouse to a random position near the base coordinates

    Args:
        base_x, base_y: Base coordinates
        offset_range: Maximum offset in pixels
    """
    try:
        random_x = base_x + random.randint(-offset_range, offset_range)
        random_y = base_y + random.randint(-offset_range, offset_range)
        pyautogui.moveTo(x=random_x, y=random_y)
    except Exception as e:
        print(f"[WARNING] Random move failed: {e}")
        pyautogui.moveTo(x=base_x, y=base_y)  # Fallback to original position