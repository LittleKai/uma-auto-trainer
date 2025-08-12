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