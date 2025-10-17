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

# def extract_number(pil_img: Image.Image) -> str:
#   """
#   Trích xuất số từ image sử dụng Tesseract
#   """
#   try:
#     # Cấu hình Tesseract chỉ cho phép số
#     custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
#     text = pytesseract.image_to_string(pil_img, config=custom_config)
#     # Lọc chỉ lấy số
#     numbers = re.findall(r'\d+', text)
#     return ''.join(numbers)
#   except Exception as e:
#     print(f"[WARNING] Tesseract number extraction failed: {e}")
#     return ""

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
  try:
    custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
    raw_text = pytesseract.image_to_string(pil_img, config=custom_config)

    cleaned_val = _clean_stat_number(raw_text)
    return cleaned_val

  except Exception as e:
    print(f"[WARNING] Stat number extraction failed: {e}")
    return 0

def _clean_stat_number(raw_text: str) -> int:
  """
  Advanced stat number cleaning with intelligent OCR error correction

  Limit stat values between 0 and 1200
  """
  if not raw_text:
    return 0

  # Mở rộng bảng ánh xạ lỗi OCR với ưu tiên chuyển đổi
  OCR_CORRECTIONS = {
    # Chuyển chữ cái/ký hiệu thành số
    'O': '0', 'o': '0', 'D': '0', 'Q': '0',  # O → 0
    'I': '1', 'i': '1', 'l': '1', '|': '1', '!': '1',
    'j': '1', '/': '1', '\\': '1',            # I/l → 1
    'Z': '2', 'z': '2',                       # Z → 2
    'A': '4',                                 # A → 4
    'S': '5', 's': '5',                       # S → 5
    'G': '6', 'b': '6',                       # G → 6
    'T': '7',                                 # T → 7
    'B': '8', '&': '8',                       # B → 8
    'g': '9', 'q': '9', 'y': '9'              # g → 9
  }

  def intelligent_conversion(text):
    converted = []
    for char in text:
      converted.append(OCR_CORRECTIONS.get(char, char))
    return ''.join(converted)

  # Lọc và chuyển đổi
  converted_text = intelligent_conversion(raw_text)

  # Chỉ giữ lại các ký tự số
  digits_only = ''.join(char for char in converted_text if char.isdigit())

  def process_stat_number(number_str):
    # Nếu có 3-4 chữ số
    if len(number_str) >= 3 and len(number_str) <= 4:
      # Ưu tiên 4 chữ số cuối
      if len(number_str) > 4:
        number_str = number_str[-4:]

      # Chuyển sang số nguyên
      number = int(number_str)

      # Giới hạn trong khoảng 0-1200
      return max(0, min(number, 1200))

    return 0

  # Thực hiện xử lý
  result = process_stat_number(digits_only)

  # Debug log để theo dõi quá trình chuyển đổi
  print(f"[OCR DEBUG] Raw input: {raw_text}")
  print(f"[OCR DEBUG] Converted: {converted_text}")
  print(f"[OCR DEBUG] Digits only: {digits_only}")
  print(f"[OCR DEBUG] Final result: {result}")

  return result