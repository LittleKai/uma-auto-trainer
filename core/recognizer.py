import cv2
import numpy as np
from PIL import ImageGrab, ImageStat

from utils.screenshot import capture_region

def match_template(template_path, region=None, threshold=0.85, debug = False):
  # Get screenshot
  if region:
    screen = np.array(ImageGrab.grab(bbox=region))  # (left, top, right, bottom)
  else:
    screen = np.array(ImageGrab.grab())
  screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

  # Load template
  template = cv2.imread(template_path, cv2.IMREAD_COLOR)  # safe default
  if template.shape[2] == 4:
    template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
  result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
  loc = np.where(result >= threshold)

  h, w = template.shape[:2]
  boxes = [(x, y, w, h) for (x, y) in zip(*loc[::-1])]

  # print confidence
  if debug:
    for i, (x, y, w, h) in enumerate(boxes):
      confidence = result[y, x]
      print(f"  Match {i+1}: ({x}, {y}) - Confidence: {confidence:.3f}")

  return deduplicate_boxes(boxes)


def deduplicate_boxes(boxes, min_dist=5):
  filtered = []
  for x, y, w, h in boxes:
    cx, cy = x + w // 2, y + h // 2
    if all(abs(cx - (fx + fw // 2)) > min_dist or abs(cy - (fy + fh // 2)) > min_dist
        for fx, fy, fw, fh in filtered):
      filtered.append((x, y, w, h))
  return filtered

def is_infirmary_active(REGION):
  screenshot = capture_region(REGION)
  grayscale = screenshot.convert("L")
  stat = ImageStat.Stat(grayscale)
  avg_brightness = stat.mean[0]

  # Treshold infirmary btn
  return avg_brightness > 150

def find_template_position(template_path, region=None, threshold=0.85, return_center=True, region_format='xywh'):
  """
  Find a single template position on screen and return its location.

  Args:
      template_path (str): Path to the template image file
      region (tuple, optional): Search region. Format depends on region_format parameter
      threshold (float): Confidence threshold for template matching (0.0-1.0)
      return_center (bool): If True, returns center point; if False, returns top-left corner
      region_format (str): Format of region parameter
                         - 'xywh': (x, y, width, height)
                         - 'ltrb': (left, top, right, bottom)

  Returns:
      tuple or None: (x, y) position of the template, or None if not found
                    - If return_center=True: returns center coordinates
                    - If return_center=False: returns top-left coordinates
                    - Coordinates are absolute screen positions
  """
  try:
    # Handle different region formats
    if region:
      if region_format == 'xywh':
        # Convert (x, y, width, height) to (left, top, right, bottom)
        x, y, w, h = region
        left, top, right, bottom = x, y, x + w, y + h
      else:  # 'ltrb'
        left, top, right, bottom = region

      # Capture screenshot from specified region
      screen = np.array(ImageGrab.grab(bbox=(left, top, right, bottom)))
    else:
      screen = np.array(ImageGrab.grab())
      left, top = 0, 0  # For coordinate adjustment

    # Convert RGB to BGR for OpenCV
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    # Load template image
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
      raise FileNotFoundError(f"Template image not found: {template_path}")

    # Handle RGBA templates by converting to BGR
    if template.shape[2] == 4:
      template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)

    # Perform template matching
    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)

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
    if region:
      adjusted_x = position[0] + left
      adjusted_y = position[1] + top
      return (adjusted_x, adjusted_y)

    return position

  except Exception as e:
    print(f"Error in find_template_position: {e}")
    return None
