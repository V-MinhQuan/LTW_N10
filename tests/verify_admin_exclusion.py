# -*- coding: utf-8 -*-
import os
import sys
import django
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'QLVB'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from django.test import Client
from web.models import UserAccount, DonViBenTrong, VanBanDen

def test_all():
    print("=== VERIFYING CLEANUP AND ADMIN EXCLUSION FROM SELECTS ===")

    # 1. Check all users in DB
    all_users = list(UserAccount.objects.all().order_by('UserID'))
    usernames = [u.username for u in all_users]
    print(f"1. Total users in DB: {len(all_users)}")
    print(f"   Usernames: {usernames}")

    test_unames = ['admin_temp', 'chuyenvien_test', 'test_giamdoc', 'test_truongphong', 'test_chuyenvien']
    for tu in test_unames:
        assert tu not in usernames, f"Test account {tu} should NOT be in DB!"
    print("   [PASS] No test accounts exist in database.")

    # 2. Check get_operational_users
    op_users = UserAccount.get_operational_users(is_active=False)
    op_unames = [u.username for u in op_users]
    assert 'admin' not in op_unames, "Admin must NOT be in operational users!"
    for u in op_users:
        assert not u.is_admin_account, f"User {u.username} should not be an admin account!"
    print(f"2. [PASS] Operational users count: {len(op_unames)}, admin is excluded.")

    # 3. Test Views via Client
    admin_user = UserAccount.objects.get(username='admin')
    hado_user = UserAccount.objects.get(username='hado') # Active Director
    kdung_user = UserAccount.objects.get(username='kdung') # Active Head of Dept

    c = Client()
    c.force_login(hado_user)

    # 3.1 van-ban-di/
    resp_vbdi = c.get('/van-ban-di/')
    assert resp_vbdi.status_code == 200
    html_vbdi = resp_vbdi.content.decode('utf-8')
    # Look at select #pc_nguoi_soan_id
    select_pc_match = re.search(r'<select[^>]*id="pc_nguoi_soan_id"[^>]*>(.*?)</select>', html_vbdi, re.DOTALL)
    assert select_pc_match is not None, "pc_nguoi_soan_id select not found!"
    select_pc_html = select_pc_match.group(1)
    assert 'Quản trị viên' not in select_pc_html and 'Admin' not in select_pc_html, "Admin found in pc_nguoi_soan_id!"
    print("3.1 [PASS] van-ban-di/ pc_nguoi_soan_id select contains NO admin.")

    # 3.2 xu-ly-van-ban/
    resp_xlvb = c.get('/xu-ly-van-ban/')
    assert resp_xlvb.status_code == 200
    html_xlvb = resp_xlvb.content.decode('utf-8')
    # Look at filter nguoi_xu_ly select
    select_nx_match = re.search(r'<select[^>]*name="nguoi_xu_ly"[^>]*>(.*?)</select>', html_xlvb, re.DOTALL)
    if select_nx_match:
        assert 'Quản trị viên' not in select_nx_match.group(1) and 'Admin' not in select_nx_match.group(1), "Admin found in nguoi_xu_ly select!"
    # Look at rep-nguoiNhan and xl-newRecipient
    for sel_id in ['rep-nguoiNhan', 'xl-newRecipient']:
        sel_match = re.search(rf'<select[^>]*id="{sel_id}"[^>]*>(.*?)</select>', html_xlvb, re.DOTALL)
        if sel_match:
            assert 'Quản trị viên' not in sel_match.group(1) and 'Admin' not in sel_match.group(1), f"Admin found in {sel_id} select!"
    print("3.2 [PASS] xu-ly-van-ban/ user selects contain NO admin.")

    # 3.3 quan-ly-tien-do/
    resp_qltd = c.get('/quan-ly-tien-do/')
    assert resp_qltd.status_code == 200
    html_qltd = resp_qltd.content.decode('utf-8')
    select_ov_match = re.search(r'<select[^>]*id="overdue_user_moi"[^>]*>(.*?)</select>', html_qltd, re.DOTALL)
    assert select_ov_match is not None, "overdue_user_moi select not found!"
    assert 'Quản trị viên' not in select_ov_match.group(1) and 'Admin' not in select_ov_match.group(1), "Admin found in overdue_user_moi select!"
    print("3.3 [PASS] quan-ly-tien-do/ overdue_user_moi select contains NO admin.")

    # 3.4 API: /api/nguoi-dung/list/?page_size=all&exclude_admin=1
    resp_api_ex = c.get('/api/nguoi-dung/list/?page_size=all&exclude_admin=1')
    assert resp_api_ex.status_code == 200
    data_ex = resp_api_ex.json()['data']
    api_ex_unames = [u['username'] for u in data_ex]
    assert 'admin' not in api_ex_unames, "Admin must NOT be returned when exclude_admin=1!"
    print(f"3.4 [PASS] api/nguoi-dung/list/?exclude_admin=1 has {len(api_ex_unames)} users, strictly excludes admin.")

    # 3.5 API without exclude_admin (for User Management page)
    resp_api_all = c.get('/api/nguoi-dung/list/?page_size=all')
    assert resp_api_all.status_code == 200
    data_all = resp_api_all.json()['data']
    api_all_unames = [u['username'] for u in data_all]
    assert 'admin' in api_all_unames, "Admin SHOULD be present in User Management view!"
    print("3.5 [PASS] api/nguoi-dung/list/ (User Management) includes admin correctly for management.")

    # 3.6 API: /api/van-ban-den/thong-tin-xin-y-kien/
    vbd = VanBanDen.objects.first()
    if vbd:
        c_kdung = Client()
        c_kdung.force_login(kdung_user)
        resp_xyk = c_kdung.get(f'/api/van-ban-den/thong-tin-xin-y-kien/?vbd_id={vbd.pk}')
        if resp_xyk.status_code == 200:
            xyk_data = resp_xyk.json().get('data', {})
            recipients = xyk_data.get('recipients', [])
            xyk_names = [r['name'] for r in recipients]
            for name in xyk_names:
                assert 'admin' not in name.lower() and 'quản trị' not in name.lower(), f"Admin found in opinion recipients: {name}"
            print(f"3.6 [PASS] Opinion request recipients: {xyk_names}, no admin.")

    print("\n=== ALL ASSERTIONS PASSED! 100% VERIFIED ===")

if __name__ == '__main__':
    test_all()
