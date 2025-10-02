import pytesseract
from PIL import Image
import re

# Cấu hình đường dẫn Tesseract (uncomment và điều chỉnh nếu cần)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(pil_img: Image.Image) -> str:
  """
  Trích xuất text từ image sử dụng Tesseract
  """
  try:
    # Cấu hình Tesseract cho text recognition
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789%\ '
    text = pytesseract.image_to_string(pil_img, config=custom_config)
    return text.strip()
  except Exception as e:
    print(f"[WARNING] Tesseract text extraction failed: {e}")
    return ""

def extract_number(pil_img: Image.Image) -> str:
  """
  Trích xuất số từ image sử dụng Tesseract
  """
  try:
    # Cấu hình Tesseract chỉ cho phép số
    custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
    text = pytesseract.image_to_string(pil_img, config=custom_config)
    # Lọc chỉ lấy số
    numbers = re.findall(r'\d+', text)
    return ''.join(numbers)
  except Exception as e:
    print(f"[WARNING] Tesseract number extraction failed: {e}")
    return ""

def extract_text_advanced(pil_img: Image.Image, whitelist: str = None, psm: int = 6) -> str:
  """
  Trích xuất text với cấu hình tùy chỉnh

  Args:
      pil_img: PIL Image object
      whitelist: Chuỗi ký tự được phép (None = tất cả)
      psm: Page Segmentation Mode (6 = uniform block of text)
  """
  try:
    config_parts = [f'--oem 3 --psm {psm}']

    if whitelist:
      config_parts.append(f'-c tessedit_char_whitelist={whitelist}')

    custom_config = ' '.join(config_parts)
    text = pytesseract.image_to_string(pil_img, config=custom_config)
    return text.strip()
  except Exception as e:
    print(f"[WARNING] Tesseract advanced extraction failed: {e}")
    return ""

def extract_stat_number(pil_img: Image.Image) -> int:
  """
  Extract and validate stat number from image (0-9999) with improved accuracy

  Args:
      pil_img: PIL Image object containing stat number

  Returns:
      int: Validated stat number (0-9999)
  """
  try:
    # Extract number with custom configuration for digits only
    custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
    raw_text = pytesseract.image_to_string(pil_img, config=custom_config)

    print(f"[DEBUG OCR] Raw stat OCR output: '{raw_text}'")

    # Clean the extracted value
    cleaned_val = _clean_stat_number(raw_text)

    print(f"[DEBUG OCR] Cleaned stat value: {cleaned_val}")

    return cleaned_val

  except Exception as e:
    print(f"[WARNING] Stat number extraction failed: {e}")
    return 0


def _clean_stat_number(raw_text: str) -> int:
  """
  Clean and validate stat number from OCR output

  Args:
      raw_text: Raw OCR text output

  Returns:
      int: Validated stat number (0-9999)
  """
  if not raw_text:
    print(f"[DEBUG OCR] Empty raw text")
    return 0

  # Remove all non-digit characters and whitespace
  digits_only = ''.join(filter(str.isdigit, raw_text.strip()))

  print(f"[DEBUG OCR] Digits only: '{digits_only}'")

  # Handle empty result
  if not digits_only:
    print(f"[DEBUG OCR] No digits found after cleaning")
    return 0

  # If we have more than 4 digits, likely OCR error - need to find correct sequence
  if len(digits_only) > 4:
    print(f"[DEBUG OCR] More than 4 digits ({len(digits_only)}), finding best match")

    # Try to find a valid sequence (3 or 4 digits preferred)
    best_candidate = None
    best_score = -1

    # Check for 4-digit sequences first (most common for high stats)
    for i in range(len(digits_only) - 3):
      candidate = digits_only[i:i+4]
      val = int(candidate)

      # Valid stat range is 0-9999
      if val <= 9999:
        score = 0

        # Prefer 4-digit numbers in valid range (1000-9999)
        if 1000 <= val <= 9999:
          score += 20
        # Also consider 3-digit equivalents (100-999)
        elif 100 <= val <= 999:
          score += 15
        # Small numbers
        elif val < 100:
          score += 10

        # Prefer sequences at the beginning
        if i == 0:
          score += 5
        elif i == 1:
          score += 3

        # Avoid sequences starting with 0 (unless very small number)
        if candidate[0] == '0' and val >= 100:
          score -= 10

        print(f"[DEBUG OCR] 4-digit candidate '{candidate}' at position {i}, value={val}, score={score}")

        if score > best_score:
          best_score = score
          best_candidate = val

    # Also check 3-digit sequences
    for i in range(len(digits_only) - 2):
      candidate = digits_only[i:i+3]
      val = int(candidate)

      if val <= 999:
        score = 0

        # 3-digit numbers
        if 100 <= val <= 999:
          score += 12
        elif val < 100:
          score += 8

        # Position bonus
        if i == 0:
          score += 4
        elif i == 1:
          score += 2

        # Avoid leading zeros
        if candidate[0] == '0' and val >= 10:
          score -= 5

        print(f"[DEBUG OCR] 3-digit candidate '{candidate}' at position {i}, value={val}, score={score}")

        if score > best_score:
          best_score = score
          best_candidate = val

    if best_candidate is not None:
      print(f"[DEBUG OCR] Selected best candidate: {best_candidate}")
      return best_candidate

    # Fallback: take the last 4 digits
    print(f"[DEBUG OCR] No good candidate found, using last 4 digits")
    digits_only = digits_only[-4:]

  # Convert the digits to integer
  try:
    value = int(digits_only)
    # Clamp to valid range (0-9999)
    result = max(0, min(9999, value))

    if result != value:
      print(f"[DEBUG OCR] Clamped value from {value} to {result}")

    return result

  except ValueError:
    print(f"[WARNING] Could not convert '{digits_only}' to integer")
    return 0