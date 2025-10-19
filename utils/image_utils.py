import time
import pyautogui
import cv2
import numpy as np
import os

def find_image(image_path, confidence=0.8, region=None):
    """
    Find the location of an image on the screen

    :param image_path: Path to the image to find
    :param confidence: Confidence threshold for image matching
    :param region: Optional region to search (left, top, width, height)
    :return: Location of the image or None if not found
    """
    # Ensure the image path exists
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return None

    # Locate the image on screen
    try:
        location = pyautogui.locateOnScreen(image_path, confidence=confidence, region=region)
        return location
    except pyautogui.ImageNotFoundException:
        return None

def click_image(image_path, attempts=1, confidence=0.8, wait_time=1, region=None):
    """
    Click on an image if found on screen

    :param image_path: Path to the image to find and click
    :param attempts: Number of attempts to find and click the image
    :param confidence: Confidence threshold for image matching
    :param wait_time: Wait time between attempts
    :param region: Optional region to search (left, top, width, height)
    :return: True if image was found and clicked, False otherwise
    """
    for _ in range(attempts):
        location = find_image(image_path, confidence, region)
        if location:
            # Calculate the center of the image
            center_x = location.left + location.width / 2
            center_y = location.top + location.height / 2

            # Click at the center of the image
            pyautogui.click(center_x, center_y)
            return True

        # Wait between attempts
        time.sleep(wait_time)

    print(f"Could not find image: {image_path}")
    return False

def wait_and_click(image_path, attempts=5, wait_time=2, confidence=0.8, region=None):
    """
    Wait and attempt to click an image multiple times

    :param image_path: Path to the image to find and click
    :param attempts: Number of attempts to find and click the image
    :param wait_time: Wait time between attempts
    :param confidence: Confidence threshold for image matching
    :param region: Optional region to search (left, top, width, height)
    :return: True if image was found and clicked, False otherwise
    """
    for _ in range(attempts):
        location = find_image(image_path, confidence, region)
        if location:
            # Calculate the center of the image
            center_x = location.left + location.width / 2
            center_y = location.top + location.height / 2

            # Click at the center of the image
            pyautogui.click(center_x, center_y)
            return True

        # Wait between attempts
        time.sleep(wait_time)

    print(f"Could not find and click image: {image_path}")
    return False

def check_image_exists(image_path, confidence=0.8, region=None):
    """
    Check if an image exists on the screen

    :param image_path: Path to the image to find
    :param confidence: Confidence threshold for image matching
    :param region: Optional region to search (left, top, width, height)
    :return: True if image exists, False otherwise
    """
    return find_image(image_path, confidence, region) is not None