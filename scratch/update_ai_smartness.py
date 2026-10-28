with open('QLVB/web/ai_services.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update candidate_models in _call_gemini_api
text = text.replace(
    'candidate_models = [model_name] if model_name else ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-3.8-flash"]',
    'candidate_models = [model_name] if model_name else ["gemini-3-flash-preview", "gemini-3.5-flash"]'
)

# 2. Update candidate_models in _call_gemini_multimodal_ocr
text = text.replace(
    'candidate_models = [model_name] if model_name else ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-3.8-flash"]',
    'candidate_models = [model_name] if model_name else ["gemini-3-flash-preview", "gemini-3.5-flash"]'
)

# 3. Update generate_smart_summary
old_gen = """def generate_smart_summary(text, trich_yeu="", loai_vb=""):
    \"\"\"
    AUTO-08: Nghiên cứu và tạo bản Tóm tắt thông minh bằng AI (Executive Smart Summary)
    Tích hợp Google Gemini AI tạo sinh mượt mà + Tự động Fallback sang Local Engine nếu mất mạng
    \"\"\"
    classification = classify_and_suggest_assignment(text, trich_yeu, loai_vb)

    ai_engine_used = "Local NLP Engine"
    summary_data = None

    # 1. Thử gọi Google Gemini AI nếu có API Key
    api_key = _get_gemini_api_key()
    if api_key:
        content_snippet = text[:4000] if text else trich_yeu
        prompt = f\"\"\"
Bạn là thư ký/trợ lý điều hành AI chuyên nghiệp cho Tổng Giám đốc Vietasia Travel.
Hãy đọc nội dung văn bản sau và tóm tắt thành định dạng JSON hợp lệ (không kèm markdown):
{{
  "muc_dich_cot_loi": "1 câu súc tích tóm lược mục đích văn bản và yêu cầu cốt lõi",
  "linh_vuc": "{classification['linh_vuc']}",
  "diem_chinh": [
    "Điểm chính 1: Nhiệm vụ hoặc thông tin quan trọng nhất",
    "Điểm chính 2: Yêu cầu hành động cụ thể",
    "Điểm chính 3: Mốc thời gian, số lượng hoặc chỉ đạo then chốt"
  ],
  "thoi_han_yeu_cau": "Thời hạn hoàn thành cụ thể (VD: Trước ngày 10/11/2026)",
  "muc_do_khan": "Tiêu chuẩn hoặc Khẩn / Cần lưu ý tiến độ"
}}

Loại văn bản: {loai_vb}
Trích yếu: {trich_yeu}
Nội dung văn bản:
{content_snippet}
\"\"\""""

new_gen = """def generate_smart_summary(text, trich_yeu="", loai_vb=""):
    \"\"\"
    AUTO-08: Nghiên cứu và tạo bản Tóm tắt thông minh bằng AI (Executive Smart Summary)
    Tích hợp Google Gemini AI tạo sinh mượt mà + Tự động Fallback sang Local Engine nếu mất mạng
    \"\"\"
    # Tự động trích xuất trích yếu thực tế từ văn bản nếu có V/v
    real_trich_yeu = trich_yeu
    if text:
        ty_m = re.search(r'(?:V/v|Về việc)\s*[:.]?\s*([^\\n\\r]+)', text, re.IGNORECASE)
        if ty_m and len(ty_m.group(1).strip(" .-_*")) > 5:
            real_trich_yeu = ty_m.group(1).strip(" .-_*")

    classification = classify_and_suggest_assignment(text, real_trich_yeu, loai_vb)

    ai_engine_used = "Local NLP Engine"
    summary_data = None

    # 1. Thử gọi Google Gemini AI nếu có API Key
    api_key = _get_gemini_api_key()
    if api_key:
        content_snippet = text[:4000] if text else real_trich_yeu
        prompt = f\"\"\"
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
\"\"\""""

text_norm = text.replace('\r\n', '\n')
old_gen_norm = old_gen.replace('\r\n', '\n')
new_gen_norm = new_gen.replace('\r\n', '\n')

assert old_gen_norm in text_norm, 'old_gen not found'
text_norm = text_norm.replace(old_gen_norm, new_gen_norm, 1)

with open('QLVB/web/ai_services.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_norm)
print("SUCCESS: Updated ai_services.py with smarter prompt and model priority!")

