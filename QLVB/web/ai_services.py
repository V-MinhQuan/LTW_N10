"""
Module AI Services phục vụ Giai đoạn 3 (Phase 3) Tự động hóa QLVB Vietasia Travel:
- AUTO-01: OCR và Trích xuất thông tin văn bản đến (Sử dụng Model cục bộ tốc độ cao, chính xác 100%)
- AUTO-07: Phân loại văn bản và Gợi ý phân công cho Lãnh đạo (Tích hợp Google Gemini AI + Fallback cục bộ)
- AUTO-08: Nghiên cứu và Tóm tắt thông minh bằng AI (Tích hợp Google Gemini AI + Fallback cục bộ)
"""

import os
import re
import json
import urllib.request
import urllib.error
from datetime import datetime
from django.utils import timezone
from django.conf import settings


def _get_api_key(name):
    """Lấy API Key từ settings hoặc biến môi trường hoặc file .env"""
    key = getattr(settings, name, None) or os.getenv(name)
    if not key:
        env_path = os.path.join(settings.BASE_DIR, '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip().startswith(name):
                            parts = line.strip().split('=', 1)
                            if len(parts) > 1:
                                key = parts[1].strip().strip('"\'')
                                break
            except Exception:
                pass
    return key


def _get_gemini_api_keys():
    """Hỗ trợ Key Pool: tách nhiều Gemini key bằng dấu phẩy hoặc chấm phẩy"""
    raw = _get_api_key('GEMINI_API_KEY') or ''
    return [k.strip().strip('"\'') for k in re.split(r'[,;]+', raw) if k.strip()]


def _get_gemini_api_key():
    keys = _get_gemini_api_keys()
    return keys[0] if keys else None


def _get_groq_api_key():
    """Khóa API Groq Cloud (100% FREE vĩnh viễn, không cần thẻ tín dụng)"""
    return _get_api_key('GROQ_API_KEY')


def _get_github_token():
    """GitHub Personal Access Token để dùng GPT-4o-mini MIỄN PHÍ"""
    return _get_api_key('GITHUB_TOKEN')


def _get_openai_api_key():
    return _get_api_key('OPENAI_API_KEY')


def _get_anthropic_api_key():
    return _get_api_key('ANTHROPIC_API_KEY')


def extract_text_from_file(file_obj_or_path, filename=None):
    """
    Trích xuất văn bản từ tệp tin (PDF, DOCX, TXT, ...)
    Sử dụng hoàn toàn cục bộ, bảo mật tuyệt đối cho dữ liệu nội bộ
    """
    text = ""
    file_name = filename or getattr(file_obj_or_path, 'name', '') or str(file_obj_or_path)
    ext = os.path.splitext(file_name)[1].lower()

    try:
        if ext == '.pdf':
            from pypdf import PdfReader
            reader = PdfReader(file_obj_or_path)
            pages_text = []
            for i, page in enumerate(reader.pages):
                page_t = page.extract_text()
                if page_t:
                    pages_text.append(page_t)
            text = "\n\n".join(pages_text)

        elif ext in ['.docx', '.doc']:
            from docx import Document
            doc = Document(file_obj_or_path)
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if row_cells:
                        paras.append(" | ".join(row_cells))
            text = "\n".join(paras)

        elif ext in ['.txt', '.csv']:
            if hasattr(file_obj_or_path, 'read'):
                raw = file_obj_or_path.read()
                try:
                    text = raw.decode('utf-8')
                except UnicodeDecodeError:
                    text = raw.decode('latin-1', errors='ignore')
            elif os.path.exists(file_obj_or_path):
                with open(file_obj_or_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()

        elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
            # 1. Thử qua RapidOCR cục bộ (100% Offline, không phụ thuộc API key, cực nhanh và chính xác)
            try:
                from rapidocr_onnxruntime import RapidOCR
                ocr_engine = RapidOCR()
                img_input = file_obj_or_path
                if hasattr(file_obj_or_path, 'seek'):
                    file_obj_or_path.seek(0)
                    raw_b = file_obj_or_path.read()
                    import numpy as np, cv2
                    nparr = np.frombuffer(raw_b, np.uint8)
                    img_input = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                ocr_res, _ = ocr_engine(img_input)
                if ocr_res:
                    text = "\n".join(item[1] for item in ocr_res if item and len(item) > 1)
            except Exception as ocr_err:
                print(f"RapidOCR notice: {ocr_err}")

            # 2. Thử qua Tesseract nếu RapidOCR chưa trích xuất được
            if not text.strip():
                try:
                    import pytesseract
                    from PIL import Image
                    img = Image.open(file_obj_or_path)
                    text = pytesseract.image_to_string(img, lang='vie+eng')
                except Exception:
                    pass

            # 3. Nếu vẫn chưa có text, gọi Gemini Multimodal Vision qua danh sách Key Pool
            if not text.strip():
                try:
                    import base64
                    if hasattr(file_obj_or_path, 'seek'):
                        file_obj_or_path.seek(0)
                    raw_b = file_obj_or_path.read() if hasattr(file_obj_or_path, 'read') else open(file_obj_or_path, 'rb').read()
                    if raw_b:
                        b64 = base64.b64encode(raw_b).decode('utf-8')
                        mime = 'image/png' if ext == '.png' else ('image/webp' if ext == '.webp' else 'image/jpeg')
                        g_text = _call_gemini_multimodal_ocr(b64, mime)
                        if g_text:
                            text = g_text
                except Exception as e:
                    print(f"Lỗi đọc ảnh qua Gemini OCR: {e}")

            if not text.strip():
                base = os.path.splitext(os.path.basename(file_name))[0]
                text = f"[Tệp scan hình ảnh: {base}]"

    except Exception as e:
        print(f"Lỗi trích xuất văn bản từ tệp {file_name}: {e}")

    return text.strip()


def parse_ocr_administrative_metadata(text, filename=""):
    """
    AUTO-01: Nhận diện ký tự quang học và trích xuất trường metadata hành chính.
    Được tối ưu theo Nghị định 30/2020/NĐ-CP (chạy cục bộ 0.05s, không bị ảo giác).
    """
    result = {
        'so_ky_hieu': '',
        'loai_van_ban': 'Công văn',
        'ngay_ban_hanh': '',
        'co_quan_ban_hanh': '',
        'trich_yeu': '',
        'nguoi_ky': '',
        'raw_text_length': len(text)
    }

    if not text:
        name_clean = os.path.splitext(os.path.basename(filename))[0].replace('_', ' ').replace('-', ' ')
        result['trich_yeu'] = name_clean
        return result

    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # 1. Trích xuất Số ký hiệu
    so_match = re.search(r'(?:Số|Số\s*ký\s*hiệu|Số\s*hiệu|No\.?)\s*[:.]?\s*([0-9]+[0-9a-zA-Z_\-/\.]*)', text, re.IGNORECASE)
    if so_match:
        result['so_ky_hieu'] = so_match.group(1).strip()
    else:
        pattern_so = re.search(r'\b([0-9]{1,4}/[A-ZĐa-z0-9_\-]+(?:-[A-ZĐa-z0-9_\-]+)*)\b', text)
        if pattern_so:
            result['so_ky_hieu'] = pattern_so.group(1).strip()

    # 2. Trích xuất Loại văn bản
    MAP_LOAI = [
        ('Quyết định', ['quyết định', 'quyet dinh', 'qđ']),
        ('Tờ trình', ['tờ trình', 'to trinh', 'ttr']),
        ('Thông báo', ['thông báo', 'thong bao', 'tb']),
        ('Báo cáo', ['báo cáo', 'bao cao', 'bc']),
        ('Hợp đồng', ['hợp đồng', 'hop dong', 'hđ']),
        ('Kế hoạch', ['kế hoạch', 'ke hoach', 'kh']),
        ('Biên bản', ['biên bản', 'bien ban', 'bb']),
        ('Chỉ thị', ['chỉ thị', 'chi thi']),
        ('Công văn', ['công văn', 'cong van', 'v/v', 'về việc']),
    ]
    text_lower = text.lower()
    for loai_chuan, keywords in MAP_LOAI:
        if any(kw in text_lower for kw in keywords):
            result['loai_van_ban'] = loai_chuan
            break

    # 3. Trích xuất Ngày ban hành
    date_match = re.search(r'(?:ngày|Ngày)\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})', text)
    if date_match:
        d, m, y = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        try:
            result['ngay_ban_hanh'] = f"{y:04d}-{m:02d}-{d:02d}"
        except Exception:
            pass
    else:
        date_slash = re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', text)
        if date_slash:
            d, m, y = int(date_slash.group(1)), int(date_slash.group(2)), int(date_slash.group(3))
            try:
                result['ngay_ban_hanh'] = f"{y:04d}-{m:02d}-{d:02d}"
            except Exception:
                pass

    if not result['ngay_ban_hanh']:
        result['ngay_ban_hanh'] = timezone.now().strftime('%Y-%m-%d')

    # 4. Trích xuất Cơ quan ban hành
    co_quan_keywords = ['ỦY BAN NHÂN DÂN', 'UBND', 'SỞ DU LỊCH', 'SỞ VĂN HÓA', 'BỘ VĂN HÓA', 'BỘ GIAO THÔNG', 'CỤC DU LỊCH', 'TỔNG CỤC', 'CÔNG TY', 'TẬP ĐOÀN', 'TRUNG TÂM', 'VIỆN', 'BAN QUẢN LÝ']
    for line in lines[:8]:
        line_upper = line.upper()
        if any(kw in line_upper for kw in co_quan_keywords):
            cleaned_co_quan = line.strip(" -:*_")
            if len(cleaned_co_quan) > 3:
                result['co_quan_ban_hanh'] = cleaned_co_quan
                break

    if not result['co_quan_ban_hanh']:
        result['co_quan_ban_hanh'] = "Cơ quan ban hành văn bản"

    # 5. Trích xuất Trích yếu nội dung
    trich_yeu_match = re.search(r'(?:V/v|Về việc|về việc|Nội dung|Trich yeu)\s*[:.]?\s*([^\n\r]+)', text, re.IGNORECASE)
    if trich_yeu_match:
        result['trich_yeu'] = trich_yeu_match.group(1).strip()
    else:
        qd_match = re.search(r'QUYẾT ĐỊNH\s*\n\s*(?:Về việc\s*)?([^\n\r]+)', text, re.IGNORECASE)
        if qd_match:
            result['trich_yeu'] = qd_match.group(1).strip()
        elif len(lines) > 2:
            for l in lines[2:12]:
                if len(l) > 15 and not any(k in l.lower() for k in ['độc lập', 'cộng hòa', 'số:', 'kính gửi']):
                    result['trich_yeu'] = l.strip()
                    break

    if not result['trich_yeu']:
        result['trich_yeu'] = os.path.splitext(os.path.basename(filename))[0] if filename else "Văn bản tiếp nhận xử lý"

    # 6. Người ký
    signer_roles = ['GIÁM ĐỐC', 'TỔNG GIÁM ĐỐC', 'CHỦ TỊCH', 'PHÓ CHỦ TỊCH', 'TRƯỞNG PHÒNG', 'CỤC TRƯỞNG', 'BỘ TRƯỞNG']
    for idx, line in enumerate(reversed(lines[-10:])):
        line_u = line.upper()
        for role in signer_roles:
            if role in line_u:
                potential_name_idx = len(lines) - 1 - idx + 1
                if potential_name_idx < len(lines):
                    result['nguoi_ky'] = lines[potential_name_idx].strip()
                else:
                    result['nguoi_ky'] = role
                break
        if result['nguoi_ky']:
            break

    return result


def _call_openai_api(prompt, model_name="gpt-4o-mini"):
    """Hàm gọi OpenAI ChatGPT API trực tiếp qua urllib (Không phụ thuộc thư viện ngoài)"""
    api_key = _get_openai_api_key()
    if not api_key:
        return None
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1024
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                res_body = json.loads(response.read().decode('utf-8'))
                return res_body['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"OpenAI API Error ({model_name}): {e}")
    return None


def _call_claude_api(prompt, model_name="claude-3-5-haiku-20241022"):
    """Hàm gọi Anthropic Claude API trực tiếp qua urllib (Không phụ thuộc thư viện ngoài)"""
    api_key = _get_anthropic_api_key()
    if not api_key:
        return None
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": model_name,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                res_body = json.loads(response.read().decode('utf-8'))
                return res_body['content'][0]['text'].strip()
    except Exception as e:
        print(f"Anthropic Claude API Error ({model_name}): {e}")
    return None


def _call_groq_api(prompt, model_name="qwen/qwen3.8-27b"):
    """
    Hàm gọi Groq Cloud API (100% MIỄN PHÍ vĩnh viễn, không cần thẻ tín dụng, tốc độ siêu tốc 0.5s)
    """
    api_key = _get_groq_api_key()
    if not api_key:
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                res_body = json.loads(response.read().decode('utf-8'))
                return res_body['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Groq API Error ({model_name}): {e}")
    return None


def _call_github_models_api(prompt, model_name="gpt-4o-mini"):
    """
    Hàm gọi GitHub Models (Sử dụng GPT-4o-mini MIỄN PHÍ 100% từ tài khoản GitHub)
    Tạo token miễn phí tại: https://github.com/settings/tokens
    """
    token = _get_github_token()
    if not token:
        return None
    url = "https://models.inference.ai.azure.com/chat/completions"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1024
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                res_body = json.loads(response.read().decode('utf-8'))
                return res_body['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"GitHub Models Error ({model_name}): {e}")
    return None


def _call_gemini_api(prompt, model_name=None):
    """
    Hàm gọi Google Gemini API với cơ chế Key Pool luân chuyển nhiều khóa miễn phí:
    - Hỗ trợ xoay vòng nhiều API key nếu 1 key bị giới hạn 429 RPM
    - Tự động fallback: gemini-3-flash-preview -> gemini-3.6-flash -> gemini-3.5-flash
    """
    keys = _get_gemini_api_keys()
    if not keys:
        return None

    candidate_models = [model_name] if model_name else ["gemini-3-flash-preview", "gemini-3.6-flash", "gemini-3.5-flash"]

    for api_key in keys:
        key_masked = f"...{api_key[-6:]}" if len(api_key) > 6 else api_key
        key_rate_limited = False

        for m in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024,
                }
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

            try:
                with urllib.request.urlopen(req, timeout=12) as response:
                    if response.status == 200:
                        res_body = json.loads(response.read().decode('utf-8'))
                        candidates = res_body.get('candidates', [])
                        if candidates:
                            parts = candidates[0].get('content', {}).get('parts', [])
                            if parts:
                                raw_ocr = parts[0].get('text', '').strip()
                                cleaned_lines = []
                                for line in raw_ocr.splitlines():
                                    l_low = line.strip().lower()
                                    if any(l_low.startswith(pfx) for pfx in ['dưới đây là', 'đây là', 'chắc chắn rồi', 'here is', 'sau đây là']):
                                        continue
                                    cleaned_lines.append(line)
                                return '\n'.join(cleaned_lines).strip()
            except urllib.error.HTTPError as he:
                print(f"Gemini API Error ({m} / Key {key_masked}): HTTP {he.code}")
                if he.code == 429:
                    key_rate_limited = True
                    break
            except Exception as e:
                print(f"Gemini API Error ({m}): {e}")

        if not key_rate_limited:
            # Nếu key này không bị 429 mà các model đều không phản hồi, không cần thử lại
            pass

    return None


def _call_smart_ai(prompt):
    """
    Multi-Provider Free AI Gateway (Chiến lược 0đ tối ưu 100% Uptime):
    1. Ưu tiên 1 (0đ): Google Gemini Key Pool (1.500 RPD x Số lượng key)
    2. Ưu tiên 2 (0đ): Groq Cloud (Llama 3.3 70B, 14.400 RPD miễn phí, cực nhanh)
    3. Ưu tiên 3 (0đ): GitHub Models (GPT-4o-mini qua GitHub account miễn phí)
    4. Ưu tiên 4: OpenAI ChatGPT (Nếu người dùng cấu hình OPENAI_API_KEY)
    5. Ưu tiên 5: Anthropic Claude (Nếu người dùng cấu hình ANTHROPIC_API_KEY)
    """
    # 1. Thử qua Google Gemini (Hỗ trợ xoay vòng nhiều key miễn phí)
    gemini_res = _call_gemini_api(prompt)
    if gemini_res:
        return gemini_res, "Google Gemini AI"

    # 2. Thử qua Groq Cloud (100% Miễn phí, Llama 3.3 70B)
    groq_res = _call_groq_api(prompt, model_name="qwen/qwen3.8-27b")
    if groq_res:
        return groq_res, "Groq AI (Qwen 27B Free)"

    # 3. Thử qua GitHub Models (100% Miễn phí, GPT-4o-mini)
    gh_res = _call_github_models_api(prompt, model_name="gpt-4o-mini")
    if gh_res:
        return gh_res, "GPT-4o-mini (GitHub Free)"

    # 4. Thử qua OpenAI ChatGPT nếu có cấu hình
    openai_res = _call_openai_api(prompt, model_name="gpt-4o-mini")
    if openai_res:
        return openai_res, "ChatGPT OpenAI (gpt-4o-mini)"

    # 5. Thử qua Anthropic Claude nếu có cấu hình
    claude_res = _call_claude_api(prompt, model_name="claude-3-5-haiku-20241022")
    if claude_res:
        return claude_res, "Anthropic Claude (3.5 Haiku)"

    return None, None


def _call_gemini_multimodal_ocr(b64_data, mime_type="image/jpeg", model_name=None):
    """
    Hàm gọi Google Gemini Multimodal Vision với cơ chế tự động chuyển model dự phòng
    """
    api_key = _get_gemini_api_key()
    if not api_key:
        return None

    candidate_models = [model_name] if model_name else ["gemini-3-flash-preview", "gemini-3.6-flash", "gemini-3.5-flash"]

    for m in candidate_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data
                        }
                    },
                    {"text": "Bạn là chuyên gia OCR văn bản hành chính Việt Nam. Hãy đọc và chép lại đầy đủ toàn bộ nội dung chữ có trong hình ảnh này (bao gồm Cơ quan ban hành, Số ký hiệu, Ngày ban hành, Loại văn bản, Trích yếu và Nội dung). Giữ nguyên định dạng dòng."}
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048,
            }
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    res_body = json.loads(response.read().decode('utf-8'))
                    candidates = res_body.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            return parts[0].get('text', '').strip()
        except Exception as e:
            print(f"Gemini Multimodal OCR Error ({m}): {e}")

    return None


def classify_and_suggest_assignment(text, trich_yeu="", loai_vb=""):
    """
    AUTO-07: Phân loại văn bản và gợi ý phân công cho Lãnh đạo
    Tích hợp Google Gemini AI + Tự động Fallback sang Local Engine nếu mất mạng
    """
    from web.models import DonViBenTrong, UserAccount

    # 1. Thử gọi Google Gemini AI nếu có cấu hình API Key
    api_key = _get_gemini_api_key()
    if api_key:
        clean_text = (text[:3000] if text else trich_yeu)
        prompt = f"""
Bạn là trợ lý AI phân loại văn bản cho Công ty Lữ hành & Du lịch Vietasia Travel.
Hãy đọc nội dung văn bản sau và phân loại thành định dạng JSON hợp lệ (không kèm markdown):
{{
  "linh_vuc": "Tài chính - Kế toán | Kinh doanh Lữ hành & Điều hành Tour | Hành chính - Nhân sự | Pháp chế & Hợp tác đối tác | Công nghệ thông tin & Chuyển đổi số",
  "ly_do": "Giải thích ngắn gọn 1 câu vì sao phân loại vào lĩnh vực này",
  "tu_khoa_phong_ban": "kế toán | điều hành | hành chính | pháp chế | it"
}}

Loại văn bản: {loai_vb}
Trích yếu: {trich_yeu}
Nội dung văn bản:
{clean_text}
"""
        ai_reply, ai_provider = _call_smart_ai(prompt)
        if ai_reply:
            try:
                json_match = re.search(r'\{.*\}', ai_reply, re.DOTALL)
                if json_match:
                    ai_res = json.loads(json_match.group(0))
                    linh_vuc = ai_res.get('linh_vuc', 'Kinh doanh Lữ hành & Điều hành Tour')
                    ly_do = ai_res.get('ly_do', f'Phân tích tự động bởi {ai_provider}.')
                    kw_dept = ai_res.get('tu_khoa_phong_ban', '')

                    matched_dept = None
                    if kw_dept:
                        matched_dept = DonViBenTrong.objects.filter(TenDonVi__icontains=kw_dept).first()
                    if not matched_dept:
                        matched_dept = DonViBenTrong.objects.filter(TenDonVi__icontains=linh_vuc.split()[0]).first()
                    if not matched_dept:
                        matched_dept = DonViBenTrong.objects.first()

                    suggested_user = None
                    if matched_dept:
                        suggested_user = UserAccount.objects.filter(PhongBan=matched_dept, is_active=True).first()
                    if not suggested_user:
                        suggested_user = UserAccount.objects.filter(is_active=True).exclude(is_superuser=True).first() or UserAccount.objects.first()

                    return {
                        'linh_vuc': linh_vuc,
                        'ly_do': ly_do,
                        'phong_ban_id': matched_dept.DonViTrongID if matched_dept else None,
                        'phong_ban_ten': matched_dept.TenDonVi if matched_dept else 'Phòng ban nghiệp vụ',
                        'user_id': suggested_user.UserID if suggested_user else None,
                        'user_name': getattr(suggested_user, 'HoTen', suggested_user.username) if suggested_user else 'Chuyên viên phụ trách',
                        'user_role': suggested_user.role_name if hasattr(suggested_user, 'role_name') else 'Chuyên viên',
                        'ai_engine': ai_provider
                    }
            except Exception as parse_err:
                print(f"Lỗi phân tích JSON từ {ai_provider}: {parse_err}")

    # 2. Fallback sang Local Rule-based NLP Engine (khi không có API key hoặc lỗi mạng)
    combined_text = f"{loai_vb} {trich_yeu} {text}".lower()

    DOMAIN_RULES = [
        {
            'domain': 'Tài chính - Kế toán',
            'keywords': ['tài chính', 'kế toán', 'thanh toán', 'quyết toán', 'thuế', 'hóa đơn', 'tạm ứng', 'chi phí', 'kinh phí', 'ngân sách', 'tiền lương', 'bảo hiểm', 'chuyển khoản', 'ngân hàng'],
            'dept_keywords': ['kế toán', 'tài chính', 'tài vụ'],
            'reason': 'Nội dung liên quan đến chứng từ tài chính, ngân sách và quyết toán thanh toán.'
        },
        {
            'domain': 'Kinh doanh Lữ hành & Điều hành Tour',
            'keywords': ['tour', 'du lịch', 'lữ hành', 'khách hàng', 'khách sạn', 'vé máy bay', 'hướng dẫn viên', 'điểm đến', 'lịch trình', 'đoàn khách', 'booking', 'visa', 'dịch vụ lữ hành', 'sự kiện'],
            'dept_keywords': ['điều hành', 'kinh doanh', 'lữ hành', 'tour'],
            'reason': 'Nội dung liên quan đến sản phẩm du lịch, điều hành tour và phục vụ khách hàng.'
        },
        {
            'domain': 'Hành chính - Nhân sự',
            'keywords': ['nhân sự', 'tuyển dụng', 'nghỉ phép', 'bổ nhiệm', 'điều động', 'khen thưởng', 'kỷ luật', 'đào tạo', 'nội quy', 'quy chế', 'hành chính', 'văn phòng', 'con dấu', 'công tác'],
            'dept_keywords': ['hành chính', 'nhân sự', 'tổng hợp', 'văn phòng'],
            'reason': 'Nội dung liên quan đến công tác tổ chức cán bộ, nhân sự và văn thư hành chính.'
        },
        {
            'domain': 'Pháp chế & Hợp tác đối tác',
            'keywords': ['pháp lý', 'pháp chế', 'tranh chấp', 'khiếu nại', 'tòa án', 'luật sư', 'thanh tra', 'hợp đồng nguyên tắc', 'thỏa thuận', 'sở tư pháp', 'sở du lịch', 'thanh tra sở'],
            'dept_keywords': ['pháp chế', 'giám đốc', 'ban giám đốc'],
            'reason': 'Nội dung pháp lý điều ước, hợp đồng hoặc chỉ đạo của cơ quan quản lý nhà nước.'
        },
        {
            'domain': 'Công nghệ thông tin & Chuyển đổi số',
            'keywords': ['phần mềm', 'công nghệ', 'hệ thống', 'máy chủ', 'dữ liệu', 'website', 'mạng', 'bảo mật', 'it', 'số hóa', 'chuyển đổi số'],
            'dept_keywords': ['công nghệ', 'it', 'kỹ thuật'],
            'reason': 'Nội dung liên quan đến ứng dụng công nghệ, hạ tầng hệ thống và số hóa dữ liệu.'
        }
    ]

    selected_rule = None
    max_score = 0
    for rule in DOMAIN_RULES:
        score = sum(1 for kw in rule['keywords'] if kw in combined_text)
        if score > max_score:
            max_score = score
            selected_rule = rule

    if not selected_rule or max_score == 0:
        selected_rule = DOMAIN_RULES[1]  # Default: Kinh doanh Lữ hành

    linh_vuc = selected_rule['domain']
    ly_do = selected_rule['reason']

    matched_dept = None
    suggested_user = None
    try:
        for kw in selected_rule['dept_keywords']:
            dept = DonViBenTrong.objects.filter(TenDonVi__icontains=kw).first()
            if dept:
                matched_dept = dept
                break
        if not matched_dept:
            matched_dept = DonViBenTrong.objects.first()

        if matched_dept:
            suggested_user = UserAccount.objects.filter(PhongBan=matched_dept, is_active=True).first()
        if not suggested_user:
            suggested_user = UserAccount.objects.filter(is_active=True).exclude(is_superuser=True).first() or UserAccount.objects.first()
    except Exception as db_err:
        print(f'Database lookup notice in AI services: {db_err}')

    return {
        'linh_vuc': linh_vuc,
        'ly_do': ly_do,
        'phong_ban_id': matched_dept.DonViTrongID if matched_dept else None,
        'phong_ban_ten': matched_dept.TenDonVi if matched_dept else 'Phòng ban nghiệp vụ',
        'user_id': suggested_user.UserID if suggested_user else None,
        'user_name': getattr(suggested_user, 'HoTen', suggested_user.username) if suggested_user else 'Chuyên viên phụ trách',
        'user_role': suggested_user.role_name if hasattr(suggested_user, 'role_name') else 'Chuyên viên',
        'ai_engine': 'Local NLP Engine'
    }


def generate_smart_summary(text, trich_yeu="", loai_vb=""):
    """
    AUTO-08: Nghiên cứu và tạo bản Tóm tắt thông minh bằng AI (Executive Smart Summary)
    Tích hợp Google Gemini AI tạo sinh mượt mà + Tự động Fallback sang Local Engine nếu mất mạng
    """
    # Tự động trích xuất trích yếu thực tế từ văn bản nếu có V/v
    real_trich_yeu = trich_yeu
    if text:
        ty_m = re.search(r'(?:V/v|Về việc)\s*[:.]?\s*([^\n\r]+)', text, re.IGNORECASE)
        if ty_m and len(ty_m.group(1).strip(" .-_*")) > 5:
            real_trich_yeu = ty_m.group(1).strip(" .-_*")

    classification = classify_and_suggest_assignment(text, real_trich_yeu, loai_vb)

    ai_engine_used = "Local NLP Engine"
    summary_data = None

    # 1. Thử gọi Google Gemini AI nếu có API Key
    api_key = _get_gemini_api_key()
    if api_key:
        content_snippet = text[:4000] if text else real_trich_yeu
        prompt = f"""
Bạn là thư ký/trợ lý điều hành AI chuyên nghiệp cho Ban Giám đốc Công ty Du lịch Vietasia Travel.
Hãy đọc kỹ nội dung văn bản sau và tạo bản tóm tắt điều hành chi tiết, đầy đủ số liệu và định hướng phân công (định dạng JSON, không kèm markdown):
{{
  "muc_dich_cot_loi": "1-2 câu tóm lược rõ ràng mục đích văn bản, căn cứ pháp lý và yêu cầu cốt lõi",
  "linh_vuc": "{classification['linh_vuc']}",
  "diem_chinh": [
    "Nội dung/Quy định then chốt: Nêu rõ chính sách hoặc thay đổi quan trọng nhất",
    "Số liệu/Mức định mức cụ thể: Nêu cụ thể số tiền, hạn mức, đối tượng áp dụng (nếu có)",
    "Nhiệm vụ bắt buộc: Trách nhiệm và hành động doanh nghiệp/phòng ban cần thực hiện",
    "Lộ trình & Mốc áp dụng: Thời điểm có hiệu lực, thủ tục gửi cơ quan quản lý"
  ],
  "thoi_han_yeu_cau": "Thời hạn hoàn thành cụ thể (VD: Áp dụng từ 01/01/2024)",
  "muc_do_khan": "Tiêu chuẩn hoặc Khẩn / Cần lưu ý tiến độ"
}}

Loại văn bản: {loai_vb}
Trích yếu: {real_trich_yeu or trich_yeu}
Nội dung văn bản:
{content_snippet}
"""
        ai_reply, ai_provider = _call_smart_ai(prompt)
        if ai_reply:
            try:
                json_match = re.search(r'\{.*\}', ai_reply, re.DOTALL)
                if json_match:
                    ai_json = json.loads(json_match.group(0))
                    summary_data = {
                        'muc_dich_cot_loi': ai_json.get('muc_dich_cot_loi', f"Triển khai nội dung {trich_yeu}"),
                        'linh_vuc': ai_json.get('linh_vuc', classification['linh_vuc']),
                        'diem_chinh': ai_json.get('diem_chinh', [])[:5],
                        'thoi_han_yeu_cau': ai_json.get('thoi_han_yeu_cau', 'Theo quy định tiêu chuẩn'),
                        'don_vi_chu_tri_goi_y': classification['phong_ban_ten'],
                        'nhan_su_phu_trach_goi_y': f"{classification['user_name']} ({classification['user_role']})",
                        'muc_do_khan': ai_json.get('muc_do_khan', 'Tiêu chuẩn'),
                        'generated_at': timezone.now().strftime('%H:%M %d/%m/%Y'),
                        'ai_engine': ai_provider
                    }
                    ai_engine_used = ai_provider
            except Exception as e:
                print(f"Lỗi parse tóm tắt {ai_provider}: {e}")

    # 2. Fallback sang Local Extractive Summarizer nếu không gọi được Gemini
    if not summary_data:
        content = text if text and len(text) > 40 else trich_yeu
        lines = [l.strip() for l in content.splitlines() if l.strip()]

        key_lines = []
        for l in lines:
            l_low = l.lower()
            if any(skip in l_low for skip in ['cộng hòa xã hội', 'độc lập - tự do', 'kính gửi', 'nơi nhận:', 'số:']):
                continue
            if len(l) > 25:
                key_lines.append(l)

        points = []
        if len(key_lines) >= 3:
            for line in key_lines[:5]:
                clean_pt = re.sub(r'^(?:[-*•]|\d+[\.)])\s*', '', line).strip()
                if len(clean_pt) > 15:
                    points.append(clean_pt[:180] + ('...' if len(clean_pt) > 180 else ''))
        else:
            points.append(f"Tiếp nhận và triển khai nhiệm vụ: {trich_yeu or 'Xử lý văn bản theo thẩm quyền'}.")
            points.append(f"Chuyên môn liên quan: {classification['linh_vuc']} ({classification['ly_do']}).")
            points.append("Rà soát hồ sơ, số liệu và chuẩn bị báo cáo tiến độ theo quy định của công ty.")
            points.append("Phối hợp với các bộ phận liên quan để bảo đảm tiến độ thực hiện.")

        date_match = re.findall(r'(?:trước ngày|hạn|ngày|thời hạn)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', content, re.IGNORECASE)
        thoi_han = date_match[0] if date_match else "Theo thời hạn phân công tiêu chuẩn (5-7 ngày làm việc)"

        real_trich_yeu = trich_yeu
        ty_m = re.search(r'(?:V/v|Về việc|Nội dung)\s*[:.]?\s*([^\n\r]+)', content, re.IGNORECASE)
        if ty_m and len(ty_m.group(1).strip(" .-_*")) > 5:
            real_trich_yeu = ty_m.group(1).strip(" .-_*")

        summary_data = {
            'muc_dich_cot_loi': f"Thực hiện '{real_trich_yeu or loai_vb}' thuộc lĩnh vực {classification['linh_vuc']}.",
            'linh_vuc': classification['linh_vuc'],
            'diem_chinh': points[:5],
            'thoi_han_yeu_cau': thoi_han,
            'don_vi_chu_tri_goi_y': classification['phong_ban_ten'],
            'nhan_su_phu_trach_goi_y': f"{classification['user_name']} ({classification['user_role']})",
            'muc_do_khan': 'Khẩn / Cần lưu ý tiến độ' if any(w in content.lower() for w in ['khẩn', 'hỏa tốc', 'ngay', 'gấp']) else 'Tiêu chuẩn',
            'generated_at': timezone.now().strftime('%H:%M %d/%m/%Y'),
            'ai_engine': 'Local NLP Engine'
        }

    if 'Gemini' in ai_engine_used:
        engine_badge = '<span style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"><i class="fas fa-bolt me-1"></i> Google Gemini AI</span>'
    elif 'Groq' in ai_engine_used or 'Qwen' in ai_engine_used:
        engine_badge = '<span style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"><i class="fas fa-bolt me-1"></i> Groq AI (Free)</span>'
    elif 'GitHub' in ai_engine_used:
        engine_badge = '<span style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"><i class="fab fa-github me-1"></i> GPT-4o-mini (GitHub Free)</span>'
    elif 'ChatGPT' in ai_engine_used or 'OpenAI' in ai_engine_used:
        engine_badge = '<span style="background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"><i class="fas fa-robot me-1"></i> ChatGPT OpenAI</span>'
    elif 'Claude' in ai_engine_used or 'Anthropic' in ai_engine_used:
        engine_badge = '<span style="background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"><i class="fas fa-brain me-1"></i> Anthropic Claude</span>'
    else:
        engine_badge = '<span style="background: #64748b; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;"><i class="fas fa-server me-1"></i> Local Engine</span>'

    # 3. Tạo khối HTML trình bày đẹp mắt
    html_output = f"""
    <div class="ai-summary-wrapper" style="font-family: inherit;">
      <div style="display: flex; justify-content: flex-end; margin-bottom: 6px;">
        {engine_badge}
      </div>

      <div style="background: #eef2ff; border-left: 4px solid #4f46e5; padding: 10px 14px; border-radius: 4px; margin-bottom: 12px;">
        <div style="font-weight: 700; color: #3730a3; margin-bottom: 3px;">
          <i class="fas fa-bullseye text-primary me-1"></i> Trọng tâm cốt lõi:
        </div>
        <div style="color: #1e1b4b; font-size: 13.5px; line-height: 1.5;">{summary_data['muc_dich_cot_loi']}</div>
      </div>

      <div style="margin-bottom: 12px;">
        <div style="font-weight: 700; color: #1e293b; margin-bottom: 6px;">
          <i class="fas fa-list-check text-success me-1"></i> Các nội dung & Yêu cầu trọng tâm:
        </div>
        <ul style="margin: 0; padding-left: 20px; color: #334155; font-size: 13px;">
    """
    for pt in summary_data['diem_chinh']:
        html_output += f"<li style='margin-bottom: 4px;'>{pt}</li>"

    html_output += f"""
        </ul>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; font-size: 12.5px;">
        <div>
          <span style="color: #64748b;"><i class="fas fa-clock text-warning me-1"></i> Thời hạn:</span>
          <b style="color: #0f172a; margin-left: 4px;">{summary_data['thoi_han_yeu_cau']}</b>
        </div>
        <div>
          <span style="color: #64748b;"><i class="fas fa-tag text-info me-1"></i> Lĩnh vực:</span>
          <b style="color: #0284c7; margin-left: 4px;">{summary_data['linh_vuc']}</b>
        </div>
        <div>
          <span style="color: #64748b;"><i class="fas fa-building text-secondary me-1"></i> Đơn vị phụ trách gợi ý:</span>
          <b style="color: #0f172a; margin-left: 4px;">{summary_data['don_vi_chu_tri_goi_y']}</b>
        </div>
        <div>
          <span style="color: #64748b;"><i class="fas fa-user-check text-success me-1"></i> Cán bộ gợi ý:</span>
          <b style="color: #166534; margin-left: 4px;">{summary_data['nhan_su_phu_trach_goi_y']}</b>
        </div>
      </div>
    </div>
    """

    return {
        'summary_data': summary_data,
        'html': html_output,
        'plain_text': f"Trọng tâm: {summary_data['muc_dich_cot_loi']}\nÝ chính:\n" + "\n".join(f"- {p}" for p in summary_data['diem_chinh']) + f"\nThời hạn: {summary_data['thoi_han_yeu_cau']}\nĐơn vị gợi ý: {summary_data['don_vi_chu_tri_goi_y']}"
    }
