import cv2
import numpy as np
import pytesseract
from PIL import Image

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

def enhance_ocr_image(image, aggressive=False):
  """
  Cường hóa ảnh với nhiều kỹ thuật xử lý

  Args:
      image: Ảnh đầu vào
      aggressive: Bật chế độ xử lý mạnh mẽ hơn
  """
  # Kiểm tra và chuyển đổi ảnh sang numpy array
  if not isinstance(image, np.ndarray):
    image = np.array(image)

  # Đảm bảo ảnh là grayscale
  if len(image.shape) > 2:
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  # Khử nhiễu
  denoised = cv2.fastNlMeansDenoising(image, None, 3, 7, 21)

  # Nếu ở chế độ mạnh, thực hiện thêm các bước xử lý
  if aggressive:
    # Tăng độ tương phản
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    denoised = clahe.apply(denoised)

    # Làm mờ nhẹ để loại bỏ nhiễu nhỏ
    denoised = cv2.GaussianBlur(denoised, (3, 3), 0)

  # Nhị phân hóa Otsu
  _, binary = cv2.threshold(denoised, 0, 255,
                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)

  return binary

def _clean_stat_number(raw_text: str, max_stat: int = 1200) -> int:
  """
  Trích xuất và làm sạch số stat với nhiều chiến lược

  Args:
      raw_text: Văn bản đầu vào từ OCR
      max_stat: Giá trị stat tối đa (mặc định là 1200)
  """
  if not raw_text:
    return 0

  # Bảng chuyển đổi mở rộng
  OCR_CORRECTIONS = {
    'O': '0', 'o': '0', 'D': '0', 'Q': '0',
    'I': '1', 'i': '1', 'l': '1', '|': '1',
    '!': '1', 'j': '1', '/': '1', '\\': '1',
    'Z': '2', 'z': '2',
    'A': '4',
    'S': '5', 's': '5',
    'G': '6', 'b': '6',
    'T': '7',
    'B': '8',
    'g': '9', 'q': '9'
  }

  # Kiểm tra nếu là MAX hoặc biến thể, với nhiều biến thể hơn
  max_variants = [
    'MAX', 'max', 'Max',  # Uppercase, lowercase, title case
    'MA', 'ma',           # Chữ hoa và chữ thường
    'MX', 'mx',           # Chữ hoa và chữ thường
    'AX', 'ax'            # Thêm biến thể AX
  ]

  # Tìm kiếm MAX với điều kiện chặt chẽ
  max_match = None
  for variant in max_variants:
    if variant in raw_text:
      max_match = variant
      print(f"[LOG] MAX variant detected: '{max_match}' in text '{raw_text}'")
      return max_stat

  # Chuyển đổi và lọc
  digits_only = ''.join(
    OCR_CORRECTIONS.get(char, char)
    for char in raw_text
    if char.isdigit() or char in OCR_CORRECTIONS
  )

  # Xử lý số với nhiều chiến lược
  if 3 <= len(digits_only) <= 4:
    # Ưu tiên các cách đọc
    candidates = []

    # 4 chữ số: thử 2 số cuối và 2 số đầu
    if len(digits_only) == 4:
      candidates.extend([
        int(digits_only[-2:]),   # 2 số cuối
        int(digits_only[:2]),    # 2 số đầu
        int(digits_only)         # cả 4 số
      ])
    else:
      # 3 chữ số: thử đọc trực tiếp
      candidates.append(int(digits_only))

    # Lọc và chọn giá trị phù hợp
    valid_candidates = [c for c in candidates if 0 < c <= max_stat]
    return max(valid_candidates) if valid_candidates else 0

  return 0

def extract_stat_number(pil_img, max_stat: int = 1200):
  """
  Trích xuất số stat với nhiều phương pháp

  Args:
      pil_img: Ảnh đầu vào
      max_stat: Giá trị stat tối đa (mặc định là 1200)
  """
  # Danh sách các cấu hình OCR
  ocr_configs = [
    # Cấu hình cơ bản
    r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789MAXmax',
    # Cấu hình cho từng ký tự
    r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789MAXmax',
    # Cấu hình linh hoạt
    r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789MAXmax'
  ]

  # Thử các phương pháp cường hóa ảnh
  enhancing_methods = [
    lambda img: enhance_ocr_image(img, aggressive=False),
    lambda img: enhance_ocr_image(img, aggressive=True)
  ]

  # Thử nhiều phương pháp
  for enhance_method in enhancing_methods:
    try:
      # Cường hóa ảnh
      enhanced_img = enhance_method(pil_img)

      # Thử các cấu hình OCR
      for config in ocr_configs:
        # Thực hiện OCR
        raw_text = pytesseract.image_to_string(enhanced_img, config=config)

        # Làm sạch và trích xuất số
        result = _clean_stat_number(raw_text, max_stat)

        # Nếu kết quả hợp lệ, trả về
        if result > 0:
          return result

    except Exception as e:
      print(f"[WARNING] Stat OCR attempt failed: {e}")

  # Nếu không đọc được
  return 0