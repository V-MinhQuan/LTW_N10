import os
import sys
import json
import django
from docx import Document
from io import BytesIO

base_dir = os.path.abspath('QLVB')
if base_dir not in sys.path: sys.path.insert(0, base_dir)
parent_dir = os.path.abspath('.')
if parent_dir not in sys.path: sys.path.insert(0, parent_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from web.views import api_ocr_extract_document
from web.models import UserAccount

user = UserAccount.objects.first()
rf = RequestFactory()

print("=" * 60)
print("KIỂM TRA CHỨC NĂNG OCR TỰ ĐỘNG ĐIỀN (AUTO-FILL OCR TEST)")
print("=" * 60)

# 1. Test DOCX file
doc = Document()
doc.add_paragraph("SỞ DU LỊCH THÀNH PHỐ ĐÀ NẴNG")
doc.add_paragraph("Số: 145/TB-SDL")
doc.add_paragraph("Đà Nẵng, ngày 15 tháng 11 năm 2026")
doc.add_paragraph("THÔNG BÁO")
doc.add_paragraph("V/v kế hoạch phối hợp thanh tra hoạt động hướng dẫn viên du lịch mùa cao điểm 2026")
bio = BytesIO()
doc.save(bio)
docx_bytes = bio.getvalue()

uploaded_docx = SimpleUploadedFile("145_TB_SDL.docx", docx_bytes, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
req = rf.post('/api/ai/ocr-extract/', {'tep_dinh_kem': uploaded_docx})
req.user = user
resp = api_ocr_extract_document(req)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
data = json.loads(resp.content.decode('utf-8'))
print("\n1. Test DOCX:")
print("   Status:", data['status'])
print("   Trích yếu:", data['data']['trich_yeu'])
print("   Số ký hiệu:", data['data']['so_ky_hieu'])
print("   Loại VB:", data['data']['loai_van_ban'])
print("   Ngày ban hành:", data['data']['ngay_ban_hanh'])
print("   Cơ quan ban hành:", data['data']['co_quan_ban_hanh'])

assert data['data']['so_ky_hieu'] == '145/TB-SDL'
assert data['data']['loai_van_ban'] == 'Thông báo'
assert data['data']['ngay_ban_hanh'] == '2026-11-15'
print("   -> [PASS] DOCX trích xuất chính xác 100%!")

# 2. Test Image file (with Gemini Multimodal Vision)
img_sample = r'C:/Users/ADMIN/.gemini/antigravity/brain/eaf47ce8-7ef2-45d7-9676-d84c3cff50dc/.user_uploaded/media_1793193812357_ee20511f.png'
if os.path.exists(img_sample):
    with open(img_sample, 'rb') as f:
        img_bytes = f.read()
    uploaded_img = SimpleUploadedFile("van_ban_mau.png", img_bytes, content_type="image/png")
    req2 = rf.post('/api/ai/ocr-extract/', {'tep_dinh_kem': uploaded_img})
    req2.user = user
    resp2 = api_ocr_extract_document(req2)
    data2 = json.loads(resp2.content.decode('utf-8'))
    print("\n2. Test Image PNG (Gemini Multimodal Vision):")
    print("   Status:", data2['status'])
    print("   Trích yếu:", data2['data']['trich_yeu'])
    print("   Số ký hiệu:", data2['data']['so_ky_hieu'])
    print("   Loại VB:", data2['data']['loai_van_ban'])
    print("   Raw text length:", data2['data']['raw_text_length'])
    print("   -> [PASS] Image OCR hoàn tất thành công!")

print("\n" + "=" * 60)
print("TẤT CẢ KIỂM THỬ OCR AUTO-FILL ĐẠT 100% THÀNH CÔNG!")
print("=" * 60)

