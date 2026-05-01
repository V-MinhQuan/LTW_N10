import os
import django
import sys

# Add current directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from web.models import UserAccount, VanBanDi
from django.db.models import Q

def run():
    u = UserAccount.objects.filter(HoTen='Vương Văn Quyền').first()
    if not u:
        print("User Vương Văn Quyền not found.")
        return
        
    print(f"Name: {u.HoTen}, Username: {u.username}")
    print(f"Role: {u.VaiTroID.ChucVu if u.VaiTroID else 'None'}")
    print(f"Dept: {u.PhongBan}")
    
    is_truong_phong = u.VaiTroID and 'Trưởng phòng' in u.VaiTroID.ChucVu
    print(f"Is TP: {is_truong_phong}")

    # The doc in question: 3/VBD
    doc = VanBanDi.objects.filter(SoKyHieu='3/VBD').first()
    if doc:
        print(f"\nDocument 3/VBD:")
        print(f"  Trich Yeu: {doc.TrichYeu}")
        print(f"  Creator (NguoiGui): {doc.NguoiGui}")
        print(f"  Handler (UserID): {doc.UserID}")
        print(f"  Handler Dept: {doc.UserID.PhongBan if doc.UserID else 'None'}")
        print(f"  Recipient Dept (DonViTrongID): {doc.DonViTrongID}")
        
        # Check why it's visible to u
        match_handler = doc.UserID and doc.UserID.PhongBan == u.PhongBan
        match_recipient = doc.DonViTrongID == u.PhongBan
        print(f"  Matches Handler Dept? {match_handler}")
        print(f"  Matches Recipient Dept? {match_recipient}")

if __name__ == "__main__":
    run()
