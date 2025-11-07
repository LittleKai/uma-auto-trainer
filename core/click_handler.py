import pyautogui
import random
import time
from typing import Tuple, Optional

def random_click_in_region(left: int, top: int, width: int, height: int, duration: float = 0.175) -> bool:
    """
    Click at a random position within the specified region
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

    try:
        screen_width, screen_height = pyautogui.size()
        center_x = screen_width // 3  + random.randint(-offset_range, offset_range)
        center_y = screen_height // 2 + random.randint(-offset_range, offset_range)
        pyautogui.click(center_x, center_y)
    except Exception as e:
        print(f"[WARNING] Random screen click failed: {e}")

def triple_click_random(region: Tuple[int, int, int, int], interval: float = 0.1) -> None:
    """
    Perform triple click with random positions within region

    """
    left, top, width, height = region

    for i in range(3):
        random_click_in_region(left, top, width, height, duration=0.1)
        if i < 2:  # Don't sleep after the last click
            time.sleep(interval)

def move_to_random_position(base_x: int, base_y: int, offset_range: int = 10) -> None:
    """
    Move mouse to a random position near the base coordinates
    """
    try:
        random_x = base_x + random.randint(-offset_range, offset_range)
        random_y = base_y + random.randint(-offset_range, offset_range)
        pyautogui.moveTo(x=random_x, y=random_y)
    except Exception as e:
        print(f"[WARNING] Random move failed: {e}")
        pyautogui.moveTo(x=base_x, y=base_y)  # Fallback to original position

def find_and_click_with_random(img_path: str, region: Optional[Tuple[int, int, int, int]] = None,
                               max_attempts: int = 1, delay_between: float = 1.0,
                               click: bool = True, use_random: bool = True,
                               confidence: float = 0.8, log_attempts: bool = True,
                               check_stop_func=None, log_func=None) -> Optional[Tuple[int, int]]:
    """
    Find and optionally click an image on screen with random clicking support

    Args:
        img_path: Path to the image to find
        region: Optional (left, top, width, height) region to search in
        max_attempts: Number of attempts to find the image
        delay_between: Delay between attempts in seconds
        click: Whether to click when found
        use_random: Whether to use random clicking within the found region
        confidence: Template matching confidence (0-1)
        log_attempts: Whether to log attempt failures
        check_stop_func: Function to check if should stop
        log_func: Function to log messages

    Returns:
        Tuple of (x, y) coordinates if found, None otherwise
    """
    time.sleep(1)

    # Check stop condition before starting
    if check_stop_func and check_stop_func():
        return None

    # Set default region to left half of screen if not provided
    if not region:
        screen_width, screen_height = pyautogui.size()
        region = (0, 0, screen_width // 2, screen_height)

    # Extract filename for logging
    filename = img_path.split('/')[-1].replace('.png', '')

    for attempt in range(max_attempts):
        # Check stop condition before each attempt
        if check_stop_func and check_stop_func():
            return None

        try:
            # Try to locate the image center
            button = pyautogui.locateCenterOnScreen(
                img_path, confidence=confidence, minSearchTime=0.2, region=region
            )

            if button:
                if click:
                    # Check stop condition before clicking
                    if check_stop_func and check_stop_func():
                        return None

                    if use_random:
                        # Get the full button region for random clicking
                        btn_region = pyautogui.locateOnScreen(
                            img_path, confidence=confidence, minSearchTime=0.1, region=region
                        )
                        if btn_region:
                            # Click randomly within the button region
                            random_click_in_region(btn_region.left, btn_region.top,
                                                   btn_region.width, btn_region.height)
                            if log_func:
                                log_func(f"Random clicked {filename}")
                        else:
                            # Fallback to center click
                            pyautogui.moveTo(button, duration=0.175)
                            pyautogui.click()
                            if log_func:
                                log_func(f"Clicked {filename}")
                    else:
                        # Traditional center click
                        pyautogui.moveTo(button, duration=0.175)
                        pyautogui.click()
                        if log_func:
                            log_func(f"Clicked {filename}")

                    return button
                else:
                    # Just return the position without clicking
                    return button

        except pyautogui.ImageNotFoundException:
            pass

        # Delay between attempts if not the last attempt
        if attempt < max_attempts - 1:
            if check_stop_func and check_stop_func():
                return None
            time.sleep(delay_between)

    # Log failure if enabled and multiple attempts were made
    if log_attempts and max_attempts > 1:
        if log_func:
            log_func(f"Failed to find {filename}")

    return None