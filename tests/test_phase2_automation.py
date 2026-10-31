import os
import sys
import json
import base64
from unittest.mock import patch, MagicMock

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
sys.path.insert(0, 'QLVB')
django.setup()

from django.test import RequestFactory
from django.utils import timezone
from web.models import VanBanDi, DonViBenNgoai, UserAccount, VaiTro, ThongBao, NgoaiLeHeThong
from web.views import (
    api_vbdi_tao_bieu_mau,
    api_vbdi_phat_hanh,
    api_ngoai_le_danh_sach,
    api_ngoai_le_thu_lai,
    api_ngoai_le_thu_lai_tat_ca,
    api_ngoai_le_huy,
    thuc_hien_thu_lai_ngoai_le
)

factory = RequestFactory()
user = UserAccount.objects.first()
if not user:
    user = UserAccount.objects.create(username='test_user', HoTen='Nguyen Van Test')

print("=" * 70)
print("BẮT ĐẦU KIỂM THỬ GIAI ĐOẠN 2 (PHASE 2 AUTOMATION TESTS)")
print("=" * 70)

# ==============================================================================
# TEST 1: AUTO-03 - TỰ ĐỘNG SINH VĂN BẢN TỪ BIỂU MẪU CHUẨN (.DOCX)
# ==============================================================================
print("\n>>> [TEST 1] AUTO-03: Tự động sinh văn bản từ Biểu mẫu chuẩn (.docx)")

# 1.1 Tải trực tiếp file .docx
req = factory.get('/api/van-ban-di/tao-bieu-mau/', {
    'loai_vb': 'Công văn',
    'so_ky_hieu': '099/CV-VAT-2026',
    'trich_yeu': 'V/v kiểm thử tự động sinh mẫu văn bản Vietasia Travel',
    'don_vi': 'Sở Du lịch Thành phố Hà Nội',
    'ngay_ban_hanh': '2026-10-28',
    'nguoi_ky': 'Đỗ Ngọc Hà'
})
req.user = user
resp = api_vbdi_tao_bieu_mau(req)
assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
file_content = b"".join(resp.streaming_content)
assert len(file_content) > 10000, f"File size too small: {len(file_content)} bytes"
print(f"  [PASS] 1.1 Sinh và tải file docx Công văn thành công: {len(file_content)} bytes, header: {resp.get('Content-Disposition')}")

# 1.2 Xuất dạng Base64 để client tự động đính kèm
req_b64 = factory.get('/api/van-ban-di/tao-bieu-mau/', {
    'loai_vb': 'Quyết định',
    'so_ky_hieu': '010/QĐ-VAT-2026',
    'trich_yeu': 'Về việc bổ nhiệm cán bộ quản trị hệ thống',
    'format': 'base64'
})
req_b64.user = user
resp_b64 = api_vbdi_tao_bieu_mau(req_b64)
assert resp_b64.status_code == 200
data_b64 = json.loads(resp_b64.content.decode('utf-8'))
assert data_b64['status'] == 'success'
assert 'base64' in data_b64 and len(data_b64['base64']) > 5000
decoded = base64.b64decode(data_b64['base64'])
assert len(decoded) == data_b64['size']
print(f"  [PASS] 1.2 Sinh dạng Base64 phục vụ tự động đính kèm thành công: filename={data_b64['filename']}, size={data_b64['size']} bytes")

# 1.3 Kiểm thử đa dạng biểu mẫu: Quyết định, Tờ trình, Thông báo, Báo cáo, Hợp đồng
for loai in ['Tờ trình', 'Thông báo', 'Báo cáo', 'Hợp đồng']:
    r = factory.get('/api/van-ban-di/tao-bieu-mau/', {'loai_vb': loai, 'trich_yeu': f'Mẫu thử nghiệm {loai}'})
    r.user = user
    res = api_vbdi_tao_bieu_mau(r)
    assert res.status_code == 200
    cnt = b"".join(res.streaming_content)
    assert len(cnt) > 10000
    print(f"  [PASS] 1.3 Mẫu '{loai}' sinh hợp lệ: {len(cnt)} bytes")


# ==============================================================================
# TEST 2: AUTO-06 - XỬ LÝ SỰ CỐ KẾT NỐI & NGOẠI LỆ HỆ THỐNG
# ==============================================================================
print("\n>>> [TEST 2] AUTO-06: Xử lý sự cố kết nối & ngoại lệ hệ thống")

# 2.1 Tạo dữ liệu mẫu: Đơn vị bên ngoài và Văn bản đi đã phê duyệt
dv_ngoai, _ = DonViBenNgoai.objects.get_or_create(
    TenDonVi='Công ty Lữ hành Quốc tế Fictional',
    defaults={'Email': 'fictional_partner@example.com', 'NguoiLienHe': 'Nguyen Van Partner'}
)

vb_test = VanBanDi.objects.create(
    SoKyHieu='888/CV-VAT-2026',
    TrichYeu='Thử nghiệm xử lý ngoại lệ mất mạng khi phát hành',
    LoaiVanBan='Công văn',
    TrangThai=VanBanDi.TrangThaiChoices.DA_PHE_DUYET,
    UserID=user,
    NgayBanHanh=timezone.now().date()
)

# 2.2 Giả lập sự cố mất kết nối mạng khi gửi email trong api_vbdi_phat_hanh
payload_phat_hanh = {
    'ph_scope': 'external',
    'don_vi_ngoai_id': dv_ngoai.DonViNgoaiID,
    'trich_yeu': vb_test.TrichYeu
}

req_ph = factory.post(
    f'/api/van-ban-di/{vb_test.VanBanDiID}/phat-hanh/',
    data=json.dumps(payload_phat_hanh),
    content_type='application/json'
)
req_ph.user = user

# Mock email.send để ném ngoại lệ mất mạng (ConnectionError)
with patch('django.core.mail.EmailMessage.send', side_effect=ConnectionError("[Errno 10051] Network unreachable / Mất kết nối đường truyền")):
    resp_ph = api_vbdi_phat_hanh(req_ph, pk=vb_test.VanBanDiID)
    assert resp_ph.status_code == 200, f"Expected 200, got {resp_ph.status_code}"
    res_json = json.loads(resp_ph.content.decode('utf-8'))
    assert res_json['status'] == 'success'
    print(f"  [PASS] 2.1 Phát hành không bị sập khi mất mạng. Phản hồi: {res_json['message']}")

# Kiểm tra trạng thái văn bản đã chuyển sang DA_PHAT_HANH
vb_test.refresh_from_db()
assert vb_test.TrangThai == VanBanDi.TrangThaiChoices.DA_PHAT_HANH
print("  [PASS] 2.2 Trạng thái văn bản được bảo toàn an toàn: DA_PHAT_HANH")

# Kiểm tra bản ghi NgoaiLeHeThong được tự động tạo trong hàng đợi thử lại
ngoai_le = NgoaiLeHeThong.objects.filter(VanBanDiID=vb_test, LoaiNgoaiLe=NgoaiLeHeThong.LoaiNgoaiLeChoices.GUI_EMAIL).first()
assert ngoai_le is not None, "NgoaiLeHeThong record was not created"
assert ngoai_le.TrangThai == NgoaiLeHeThong.TrangThaiChoices.CHO_XU_LY
assert ngoai_le.SoLanThuLai == 0
assert 'fictional_partner@example.com' in ngoai_le.DuLieuPayload['to_email']
print(f"  [PASS] 2.3 Bản ghi NgoaiLeHeThong #{ngoai_le.NgoaiLeID} được tạo tự động với trạng thái CHO_XU_LY và đầy đủ payload")

# Kiểm tra thông báo cảnh báo gửi tới Admin
tb_admin = ThongBao.objects.filter(VanBanDiID=vb_test, TieuDe__icontains='Cảnh báo mất kết nối').first()
assert tb_admin is not None, "Admin notification not created"
print(f"  [PASS] 2.4 Thông báo hệ thống cảnh báo admin được tạo: '{tb_admin.TieuDe}'")

# 2.3 Thử nghiệm cơ chế Thử lại (Retry):
# Lần thử lại 1: Tiếp tục giả lập mạng chập chờn -> Tăng số lần thử lại, trạng thái vẫn là CHO_XU_LY
with patch('django.core.mail.EmailMessage.send', side_effect=TimeoutError("Connection timed out")):
    retry_res1 = thuc_hien_thu_lai_ngoai_le(ngoai_le)
    ngoai_le.refresh_from_db()
    assert ngoai_le.SoLanThuLai == 1
    assert ngoai_le.TrangThai == NgoaiLeHeThong.TrangThaiChoices.CHO_XU_LY
    print(f"  [PASS] 2.5 Thử lại lần 1 khi mạng chưa phục hồi: SoLanThuLai = {ngoai_le.SoLanThuLai}/3, TrangThai = {ngoai_le.TrangThai}")

# Lần thử lại 2: Mạng đã phục hồi -> Thành công!
with patch('django.core.mail.EmailMessage.send', return_value=1):
    retry_res2 = thuc_hien_thu_lai_ngoai_le(ngoai_le)
    ngoai_le.refresh_from_db()
    assert retry_res2['status'] == 'success'
    assert ngoai_le.TrangThai == NgoaiLeHeThong.TrangThaiChoices.THANH_CONG
    assert ngoai_le.NgayThuLaiCuoi is not None
    print(f"  [PASS] 2.6 Thử lại lần 2 khi mạng phục hồi: {retry_res2['message']} -> TrangThai = {ngoai_le.TrangThai}")

# 2.4 Kiểm tra các API quản lý hàng đợi ngoại lệ
req_list = factory.get('/api/ngoai-le/danh-sach/')
req_list.user = user
resp_list = api_ngoai_le_danh_sach(req_list)
assert resp_list.status_code == 200
list_data = json.loads(resp_list.content.decode('utf-8'))
assert 'items' in list_data and 'pending_count' in list_data
print(f"  [PASS] 2.7 API lấy danh sách ngoại lệ hoạt động chuẩn: tổng {len(list_data['items'])} bản ghi, pending_count={list_data['pending_count']}")

# Cleanup
vb_test.delete()
dv_ngoai.delete()

print("\n" + "=" * 70)
print("TẤT CẢ CÁC BÀI TEST GIAI ĐOẠN 2 ĐÃ ĐẠT 100% THÀNH CÔNG!")
print("=" * 70)

