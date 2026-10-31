# -*- coding: utf-8 -*-
import os
import sys
import django
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'QLVB'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from django.test import Client
from django.utils import timezone
from web.models import UserAccount, VanBanDi, PheDuyet, LichSuHoatDong, ThongBao, VaiTro

def run_tests():
    print("=== TESTING 4 CRITERIA CHECKLIST (BPMN COMPLIANCE) ===")
    
    # 1. Setup users
    admin_user = UserAccount.objects.filter(VaiTroID__ChucVu__icontains='Giám đốc').first() or UserAccount.objects.filter(is_superuser=True).first()
    specialist_user = UserAccount.get_operational_users().filter(VaiTroID__ChucVu__icontains='Nhân viên').first() or UserAccount.objects.exclude(pk=admin_user.pk).first()
    
    client = Client()
    client.force_login(admin_user)

    # 2. Test Approval with 4 criteria
    vb = VanBanDi.objects.create(
        SoKyHieu='TEST-BPMN-001',
        TrichYeu='Văn bản kiểm thử 4 tiêu chí BPMN',
        LoaiVanBan='Công văn',
        TrangThai=VanBanDi.TrangThaiChoices.CHO_PHE_DUYET,
        UserID=specialist_user,
        NguoiGui=specialist_user
    )

    payload_approve = {
        'action': 'dong_y',
        'chap_nhan': True,
        'ghi_chu': 'Đồng ý ban hành theo tờ trình.',
        'chu_ky_so': 'data:image/png;base64,TESTSIGNATUREDATA',
        'tieu_chi': {
            'the_thuc': True,
            'noi_dung': True,
            'tham_quyen': True,
            'can_cu': True,
            'so_luong_dat': 4
        }
    }

    resp = client.post(
        f'/api/van-ban-di/{vb.pk}/phe-duyet/',
        data=json.dumps(payload_approve),
        content_type='application/json'
    )
    print("Approval response status:", resp.status_code)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.content}"
    res_data = resp.json()
    assert res_data['status'] == 'success', f"Expected success: {res_data}"
    
    vb.refresh_from_db()
    assert vb.TrangThai == VanBanDi.TrangThaiChoices.DA_PHE_DUYET, f"Expected DA_PHE_DUYET, got {vb.TrangThai}"
    print("[PASS] Status updated to DA_PHE_DUYET")

    pd = PheDuyet.objects.filter(VanBanDiID=vb).order_by('-PheDuyetID').first()
    assert pd is not None
    assert pd.TrangThaiDuyet is True
    assert "Đồng ý ban hành" in pd.GhiChu
    print(f"[PASS] PheDuyet record recorded: {pd.GhiChu}")

    ls = LichSuHoatDong.objects.filter(DoiTuongID=vb.pk, LoaiDoiTuong='VanBanDi', HanhDong='PHE_DUYET').order_by('-LichSuID').first()
    assert ls is not None
    assert "Đã thẩm định đạt đủ 4/4 tiêu chí" in ls.NoiDungThayDoi
    print(f"[PASS] LichSuHoatDong recorded criteria log: {ls.NoiDungThayDoi}")

    # 3. Test Revision Request with failing criteria
    vb2 = VanBanDi.objects.create(
        SoKyHieu='TEST-BPMN-002',
        TrichYeu='Văn bản kiểm thử yêu cầu sửa tiêu chí',
        LoaiVanBan='Công văn',
        TrangThai=VanBanDi.TrangThaiChoices.CHO_PHE_DUYET,
        UserID=specialist_user,
        NguoiGui=specialist_user
    )

    payload_revise = {
        'action': 'yeu_cau_chinh_sua',
        'chap_nhan': False,
        'ghi_chu': 'Yêu cầu chỉnh sửa các tiêu chí chưa đạt:\n- 1. Thể thức & Kỹ thuật trình bày chưa đạt chuẩn Nghị định 30/2020/NĐ-CP',
        'tieu_chi': {
            'the_thuc': False,
            'noi_dung': True,
            'tham_quyen': True,
            'can_cu': True,
            'so_luong_dat': 3
        }
    }

    resp2 = client.post(
        f'/api/van-ban-di/{vb2.pk}/phe-duyet/',
        data=json.dumps(payload_revise),
        content_type='application/json'
    )
    print("Revision response status:", resp2.status_code)
    assert resp2.status_code == 200
    vb2.refresh_from_db()
    assert vb2.TrangThai == VanBanDi.TrangThaiChoices.CAN_SUA_DOI
    print("[PASS] Status updated to CAN_SUA_DOI for failed criteria")

    tb = ThongBao.objects.filter(UserID=specialist_user, VanBanDiID=vb2).order_by('-ThongBaoID').first()
    assert tb is not None
    assert "chỉnh sửa" in tb.TieuDe.lower()
    print(f"[PASS] Notification sent to author: {tb.TieuDe}")

    # 4. Verify templates contain all 4 criteria IDs and handlers
    for tmpl in ['QLVB/templates/xu_ly_van_ban/index.html', 'QLVB/templates/van_ban_di/index.html']:
        with open(tmpl, 'r', encoding='utf-8') as f:
            c = f.read()
        assert 'pd_chk_noi_dung' in c, f"Missing pd_chk_noi_dung in {tmpl}"
        assert 'pd_chk_can_cu' in c, f"Missing pd_chk_can_cu in {tmpl}"
        assert 'pd_chk_kha_thi' in c, f"Missing pd_chk_kha_thi in {tmpl}"
        assert 'pd_chk_ho_so' in c, f"Missing pd_chk_ho_so in {tmpl}"
        assert 'chonTatCaTieuChi' in c, f"Missing chonTatCaTieuChi in {tmpl}"
        print(f"[PASS] All 4 criteria and controls present in {tmpl}")

    # 5. Verify JS files contain functions
    for js_path in ['QLVB/static/js/pages/xu_ly_van_ban.js', 'QLVB/static/js/pages/van_ban_di.js']:
        with open(js_path, 'r', encoding='utf-8') as f:
            c = f.read()
        assert 'function resetTieuChiChecklist' in c
        assert 'function chonTatCaTieuChi' in c
        assert 'function capNhatTrangThaiTieuChi' in c
        assert 'countTieuChi < 4' in c
        print(f"[PASS] JS validation logic verified in {js_path}")

    # Clean up test objects
    vb.delete()
    vb2.delete()
    print("=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == '__main__':
    run_tests()
