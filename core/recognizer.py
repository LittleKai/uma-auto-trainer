import cv2
import numpy as np
from PIL import ImageGrab, ImageStat

from utils.screenshot import capture_region

def validate_region_coordinates(region):
  """Validate and fix region coordinates to prevent PyAutoGUI errors"""
  if not region:
    return None

  if len(region) == 4:
    left, top, width, height = region

    # Convert to integers and validate
    try:
      left, top, width, height = int(left), int(top), int(width), int(height)
    except (ValueError, TypeError):
      print(f"[ERROR] Invalid coordinate types in region: {region}")
      return None

    # Check for positive dimensions
    if width <= 0 or height <= 0:
      print(f"[ERROR] Invalid region dimensions - width: {width}, height: {height}")
      return None

    # Convert to (left, top, right, bottom) format for ImageGrab
    right = left + width
    bottom = top + height

    # Ensure right > left and bottom > top
    if right <= left or bottom <= top:
      print(f"[ERROR] Invalid region bounds - left: {left}, top: {top}, right: {right}, bottom: {bottom}")
      return None

    return (left, top, right, bottom)
  else:
    print(f"[ERROR] Invalid region format: {region}")
    return None

def match_template(template_path, region=None, threshold=0.85, debug=False):
  """Match template with improved region handling and error prevention"""
  try:
    # Validate and convert region if provided
    bbox_region = None
    if region:
      bbox_region = validate_region_coordinates(region)
      if bbox_region is None:
        print(f"[ERROR] Invalid region for template matching: {region}")
        return []

    # Get screenshot with error handling
    try:
      if bbox_region:
        screen = np.array(ImageGrab.grab(bbox=bbox_region))
      else:
        screen = np.array(ImageGrab.grab())
    except Exception as e:
      print(f"[ERROR] Failed to capture screen: {e}")
      return []

    # Convert color space
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    # Load template with error handling
    try:
      template = cv2.imread(template_path, cv2.IMREAD_COLOR)
      if template is None:
        print(f"[ERROR] Could not load template: {template_path}")
        return []
    except Exception as e:
      print(f"[ERROR] Failed to load template {template_path}: {e}")
      return []

    # Handle RGBA templates
    if len(template.shape) == 3 and template.shape[2] == 4:
      template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)

    # Perform template matching with error handling
    try:
      result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
      loc = np.where(result >= threshold)
    except Exception as e:
      print(f"[ERROR] Template matching failed: {e}")
      return []

    h, w = template.shape[:2]
    boxes = []

    # Convert matches to box format
    for pt in zip(*loc[::-1]):
      x, y = pt
      # Adjust coordinates if region was used
      if bbox_region:
        left, top = bbox_region[0], bbox_region[1]
        x += left
        y += top
      boxes.append((x, y, w, h))

    # Debug output
    if debug and boxes:
      for i, (x, y, w, h) in enumerate(boxes):
        # Calculate confidence for debug
        screen_y = y - (bbox_region[1] if bbox_region else 0)
        screen_x = x - (bbox_region[0] if bbox_region else 0)
        if 0 <= screen_y < result.shape[0] and 0 <= screen_x < result.shape[1]:
          confidence = result[screen_y, screen_x]
          print(f"  Match {i+1}: ({x}, {y}) - Confidence: {confidence:.3f}")

    return deduplicate_boxes(boxes)

  except Exception as e:
    print(f"[ERROR] Unexpected error in match_template: {e}")
    return []

def deduplicate_boxes(boxes, min_dist=5):
  """Remove duplicate detection boxes that are too close to each other"""
  if not boxes:
    return []

  filtered = []
  for x, y, w, h in boxes:
    cx, cy = x + w // 2, y + h // 2
    is_duplicate = False

    for fx, fy, fw, fh in filtered:
      fcx, fcy = fx + fw // 2, fy + fh // 2
      if abs(cx - fcx) <= min_dist and abs(cy - fcy) <= min_dist:
        is_duplicate = True
        break

    if not is_duplicate:
      filtered.append((x, y, w, h))

  return filtered

def is_infirmary_active(region):
  """Check if infirmary button is active based on brightness"""
  try:
    # Validate region coordinates
    validated_region = validate_region_coordinates(region)
    if validated_region is None:
      return False

    # Convert back to (left, top, width, height) for capture_region
    left, top, right, bottom = validated_region
    width = right - left
    height = bottom - top
    capture_region_format = (left, top, width, height)

    screenshot = capture_region(capture_region_format)
    grayscale = screenshot.convert("L")
    stat = ImageStat.Stat(grayscale)
    avg_brightness = stat.mean[0]

    # Threshold infirmary btn
    return avg_brightness > 150

  except Exception as e:
    print(f"[ERROR] Failed to check infirmary status: {e}")
    return False

def find_template_position(template_path, region=None, threshold=0.85, return_center=True, region_format='xywh'):
  """Find a single template position on screen and return its location with improved error handling"""
  try:
    # Handle different region formats and validate
    bbox_region = None
    if region:
      if region_format == 'xywh':
        # Convert (x, y, width, height) to (left, top, right, bottom)
        bbox_region = validate_region_coordinates(region)
      else:  # 'ltrb'
        left, top, right, bottom = region
        # Validate ltrb format
        if right <= left or bottom <= top:
          print(f"[ERROR] Invalid ltrb region: {region}")
          return None
        bbox_region = (left, top, right, bottom)

      if bbox_region is None:
        print(f"[ERROR] Invalid region for template position: {region}")
        return None

    # Capture screenshot with error handling
    try:
      if bbox_region:
        screen = np.array(ImageGrab.grab(bbox=bbox_region))
        region_left, region_top = bbox_region[0], bbox_region[1]
      else:
        screen = np.array(ImageGrab.grab())
        region_left, region_top = 0, 0
    except Exception as e:
      print(f"[ERROR] Failed to capture screenshot: {e}")
      return None

    # Convert RGB to BGR for OpenCV
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    # Load template image with error handling
    try:
      template = cv2.imread(template_path, cv2.IMREAD_COLOR)
      if template is None:
        print(f"[ERROR] Template image not found: {template_path}")
        return None
    except Exception as e:
      print(f"[ERROR] Failed to load template: {e}")
      return None

    # Handle RGBA templates by converting to BGR
    if len(template.shape) == 3 and template.shape[2] == 4:
      template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)

    # Perform template matching with error handling
    try:
      result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    except Exception as e:
      print(f"[ERROR] Template matching failed: {e}")
      return None

    # Find the best match location
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if match meets threshold
    if max_val < threshold:
      return None

    # Get template dimensions
    h, w = template.shape[:2]

    # Calculate position based on return_center flag
    if return_center:
      # Return center coordinates
      center_x = max_loc[0] + w // 2
      center_y = max_loc[1] + h // 2
      position = (center_x, center_y)
    else:
      # Return top-left coordinates
      position = max_loc

    # Adjust coordinates if region was specified
    adjusted_x = position[0] + region_left
    adjusted_y = position[1] + region_top
    return (adjusted_x, adjusted_y)

  except Exception as e:
    print(f"[ERROR] Unexpected error in find_template_position: {e}")
    return None

# Add these functions to your existing core/recognizer.py file

import pyautogui
import time
import cv2
import numpy as np

def click_position(x, y):
  """Click at specific coordinates"""
  try:
    pyautogui.click(x, y)
    return True
  except Exception as e:
    print(f"Error clicking position ({x}, {y}): {e}")
    return False

def recognize_image(image_path, region=None, confidence=0.7):
  """
  Check if image exists in screen or specified region

  Args:
      image_path (str): Path to the image file
      region (tuple): Region to search in (x, y, width, height) or None for full screen
      confidence (float): Matching confidence threshold

  Returns:
      bool: True if image is found, False otherwise
  """
  try:
    if region:
      # Convert region format from (x1, y1, x2, y2) to (x, y, width, height)
      if len(region) == 4:
        x1, y1, x2, y2 = region
        if x2 > x1 and y2 > y1:  # (x1, y1, x2, y2) format
          region = (x1, y1, x2 - x1, y2 - y1)

    location = pyautogui.locateOnScreen(image_path, region=region, confidence=confidence)
    return location is not None
  except Exception as e:
    print(f"Error recognizing image {image_path}: {e}")
    return False

def click_image_if_found(image_path, region=None, confidence=0.7):
  """
  Click on image if found in screen or specified region

  Args:
      image_path (str): Path to the image file
      region (tuple): Region to search in (x, y, width, height) or None for full screen
      confidence (float): Matching confidence threshold

  Returns:
      bool: True if image was found and clicked, False otherwise
  """
  try:
    if region:
      # Convert region format from (x1, y1, x2, y2) to (x, y, width, height)
      if len(region) == 4:
        x1, y1, x2, y2 = region
        if x2 > x1 and y2 > y1:  # (x1, y1, x2, y2) format
          region = (x1, y1, x2 - x1, y2 - y1)

    location = pyautogui.locateOnScreen(image_path, region=region, confidence=confidence)
    if location:
      center = pyautogui.center(location)
      pyautogui.click(center)
      return True
    else:
      return False
  except Exception as e:
    print(f"Error clicking image {image_path}: {e}")
    return False

def get_left_half_screen_region():
  """Get the left half of the screen region"""
  try:
    screen_width, screen_height = pyautogui.size()
    return (0, 0, screen_width // 2, screen_height)
  except Exception as e:
    print(f"Error getting screen region: {e}")
    return None