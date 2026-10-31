import os
import sys

base_dir = os.path.abspath('QLVB')
if base_dir not in sys.path: sys.path.insert(0, base_dir)
parent_dir = os.path.abspath('.')
if parent_dir not in sys.path: sys.path.insert(0, parent_dir)
os.chdir('QLVB')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
import django
django.setup()

from django.test import RequestFactory
from web.models import UserAccount
from web.views import van_ban_den_index, van_ban_di_index, quan_ly_tien_do_index, xu_ly_van_ban_index

user = UserAccount.objects.first()
rf = RequestFactory()

test_urls = [
    ('/van-ban-den/', van_ban_den_index),
    ('/van-ban-den/?trang_thai=DANG_XU_LY', van_ban_den_index),
    ('/van-ban-den/?trang_thai=HOAN_THANH', van_ban_den_index),
    ('/van-ban-di/', van_ban_di_index),
    ('/van-ban-di/?trang_thai=DU_THAO', van_ban_di_index),
    ('/van-ban-di/?trang_thai=CHO_PHE_DUYET', van_ban_di_index),
    ('/quan-ly-tien-do/', quan_ly_tien_do_index),
    ('/xu-ly-van-ban/', xu_ly_van_ban_index),
]

print("=" * 60)
print("TESTING TEMPLATE RENDERING ACROSS VIEWS & PARAMS")
print("=" * 60)

for path, func in test_urls:
    req = rf.get(path)
    req.user = user
    resp = func(req)
    assert resp.status_code == 200, f"{path} returned {resp.status_code}"
    print(f"  [PASS] {path} -> 200 OK (Bytes: {len(resp.content)})")

print("=" * 60)
print("ALL VIEWS AND TEMPLATES PASSED 100%!")
print("=" * 60)
