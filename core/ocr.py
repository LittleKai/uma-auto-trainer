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
  Làm sạch và trích xuất số stat từ OCR text

  Xử lý:
  - OCR nhầm ký tự thành số với bảng mapping mở rộng
  - Stat luôn có ít nhất 2 chữ số
  - Nếu có 4 chữ số mà chữ số đầu giống chữ số thứ 2 → loại bỏ chữ số đầu
  - Giới hạn trong khoảng [0, 2400]
  """
  if not raw_text:
    return 0

  # Bảng chuyển đổi các lỗi OCR phổ biến (mở rộng)
  OCR_CORRECTIONS = {
    # Số 0
    'O': '0', 'o': '0',           # Chữ O
    'D': '0',                      # Chữ D
    'Q': '0',                      # Chữ Q (đôi khi)

    # Số 1
    'I': '1', 'i': '1',           # Chữ I (hoa/thường)
    'l': '1',                      # Chữ l (lowercase L)
    '|': '1',                      # Ký tự pipe
    '!': '1',                      # Dấu chấm than
    'j': '1',                      # Chữ j (đôi khi)
    '/': '1',                      # Dấu gạch chéo
    '\\': '1',                     # Dấu gạch chéo ngược

    # Số 2
    'Z': '2', 'z': '2',           # Chữ Z

    # Số 3

    # Số 4
    'A': '4',                      # Chữ A (đôi khi)

    # Số 5
    'S': '5', 's': '5',           # Chữ S

    # Số 6
    'G': '6',                      # Chữ G (có thể là 6 hoặc 9)
    'b': '6',                      # Chữ b thường (đôi khi)

    # Số 7
    'T': '7',                      # Chữ T (đôi khi)

    # Số 8
    'B': '8',                      # Chữ B
    '&': '8',                      # Ký tự &

    # Số 9
    'g': '9',                      # Chữ g thường
    'q': '9',                      # Chữ q
    'y': '9',                      # Chữ y (đôi khi)

    # Ký tự đặc biệt cần loại bỏ
    ' ': '',                       # Khoảng trắng
    ',': '',                       # Dấu phấy
    '.': '',                       # Dấu chấm
    '-': '',                       # Dấu gạch ngang
    '_': '',                       # Dấu gạch dưới
    ':': '',                       # Dấu hai chấm
    ';': '',                       # Dấu chấm phẩy
    '+': '',                       # Dấu cộng
    '=': '',                       # Dấu bằng
    '~': '',                       # Dấu ngã
    '`': '',                       # Dấu backtick
    "'": '',                       # Dấu nháy đơn
    '"': '',                       # Dấu nháy kép
    '(': '',                       # Ngoặc mở
    ')': '',                       # Ngoặc đóng
    '[': '',                       # Ngoặc vuông mở
    ']': '',                       # Ngoặc vuông đóng
    '{': '',                       # Ngoặc nhọn mở
    '}': '',                       # Ngoặc nhọn đóng
    '<': '',                       # Dấu nhỏ hơn
    '>': '',                       # Dấu lớn hơn
    '#': '',                       # Dấu thăng
    '$': '',                       # Dấu dollar
    '%': '',                       # Dấu phần trăm
    '*': '',                       # Dấu sao
  }

  # Áp dụng corrections
  corrected_text = raw_text.strip()
  for wrong_char, correct_char in OCR_CORRECTIONS.items():
    corrected_text = corrected_text.replace(wrong_char, correct_char)

  # Lọc chỉ lấy chữ số
  digits_only = ''.join(filter(str.isdigit, corrected_text))

  if not digits_only:
    return 0

  # Xử lý trường hợp quá dài (>4 chữ số)
  if len(digits_only) > 4:
    digits_only = digits_only[-4:]

  # Xử lý trường hợp 4 chữ số với chữ số đầu trùng chữ số thứ 2
  # Ví dụ: 8886 → 886, 1123 → 123
  if len(digits_only) == 4 and digits_only[0] == digits_only[1]:
    candidate = int(digits_only[1:])
    if candidate <= 2400:
      return candidate

  # Trường hợp bình thường
  try:
    value = int(digits_only)
    return max(0, min(2400, value))
  except ValueError:
    return 0