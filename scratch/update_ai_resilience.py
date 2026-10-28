import os

# 1. Update views.py
with open('QLVB/web/views.py', 'r', encoding='utf-8') as f:
    views_code = f.read()

target_views = """    raw_text = ""
    if doc.TepDinhKem:
        try:
            if doc.TepDinhKem.storage.exists(doc.TepDinhKem.name):
                raw_text = extract_text_from_file(doc.TepDinhKem)
        except Exception as err:
            print(f"Lỗi đọc file tóm tắt AI: {err}")"""

replacement_views = """    raw_text = ""
    if doc.TepDinhKem:
        try:
            if hasattr(doc.TepDinhKem, 'path') and os.path.exists(doc.TepDinhKem.path):
                raw_text = extract_text_from_file(doc.TepDinhKem.path, filename=doc.TepDinhKem.name)
            elif doc.TepDinhKem.storage.exists(doc.TepDinhKem.name):
                raw_text = extract_text_from_file(doc.TepDinhKem, filename=doc.TepDinhKem.name)
        except Exception as err:
            print(f"Lỗi đọc file tóm tắt AI: {err}")"""

views_norm = views_code.replace('\r\n', '\n')
target_views_norm = target_views.replace('\r\n', '\n')
replacement_views_norm = replacement_views.replace('\r\n', '\n')

if target_views_norm in views_norm:
    views_norm = views_norm.replace(target_views_norm, replacement_views_norm, 1)
    with open('QLVB/web/views.py', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(views_norm)
    print("SUCCESS: Updated views.py")
else:
    print("FAILED: target_views not found in views.py")

# 2. Update ai_services.py
with open('QLVB/web/ai_services.py', 'r', encoding='utf-8') as f:
    ai_code = f.read()

target_ai_model = """def _call_gemini_api(prompt, model_name="gemini-3-flash-preview"):
    \"\"\"
    Hàm gọi Google Gemini API trực tiếp với timeout và quản lý ngoại lệ an toàn
    \"\"\"
    api_key = _get_gemini_api_key()
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
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
                        return parts[0].get('text', '').strip()
    except Exception as e:
        print(f"Gemini API Error ({model_name}): {e}")

    return None


def _call_gemini_multimodal_ocr(b64_data, mime_type="image/jpeg", model_name="gemini-3-flash-preview"):
    \"\"\"
    Hàm gọi Google Gemini Multimodal Vision để đọc nội dung chữ từ hình ảnh / tài liệu scan
    \"\"\"
    api_key = _get_gemini_api_key()
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
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
        print(f"Gemini Multimodal OCR Error ({model_name}): {e}")

    return None"""

replacement_ai_model = """def _call_gemini_api(prompt, model_name=None):
    \"\"\"
    Hàm gọi Google Gemini API với cơ chế tự động chuyển model dự phòng (gemini-3.5-flash -> gemini-3-flash-preview)
    \"\"\"
    api_key = _get_gemini_api_key()
    if not api_key:
        return None

    candidate_models = [model_name] if model_name else ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-3.8-flash"]

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
                            return parts[0].get('text', '').strip()
        except Exception as e:
            print(f"Gemini API Error ({m}): {e}")

    return None


def _call_gemini_multimodal_ocr(b64_data, mime_type="image/jpeg", model_name=None):
    \"\"\"
    Hàm gọi Google Gemini Multimodal Vision với cơ chế tự động chuyển model dự phòng
    \"\"\"
    api_key = _get_gemini_api_key()
    if not api_key:
        return None

    candidate_models = [model_name] if model_name else ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-3.8-flash"]

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

    return None"""

ai_norm = ai_code.replace('\r\n', '\n')
target_ai_norm = target_ai_model.replace('\r\n', '\n')
replacement_ai_norm = replacement_ai_model.replace('\r\n', '\n')

if target_ai_norm in ai_norm:
    ai_norm = ai_norm.replace(target_ai_norm, replacement_ai_norm, 1)
    with open('QLVB/web/ai_services.py', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(ai_norm)
    print("SUCCESS: Updated ai_services.py")
else:
    print("FAILED: target_ai_model not found in ai_services.py")

