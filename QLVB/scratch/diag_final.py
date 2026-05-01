import os
import django
import sys

# Add current directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from web.models import DonViBenTrong, UserAccount, VanBanDi
from django.db.models import Q

def run():
    print("--- Departments ---")
    for d in DonViBenTrong.objects.all():
        print(f"ID: {d.pk}, Name: {d.TenDonVi}")

    print("\n--- Current User (vquyen) ---")
    try:
        u = UserAccount.objects.get(username='vquyen')
        print(f"User: {u.HoTen}, DeptID: {u.PhongBan_id}, DeptName: {u.PhongBan}")
        
        # Test the exact query used in views.py
        qs = VanBanDi.objects.filter(
            (Q(NguoiGui__isnull=False) & Q(NguoiGui__PhongBan=u.PhongBan)) |
            (Q(NguoiGui__isnull=True) & Q(UserID__PhongBan=u.PhongBan)) | 
            Q(DonViTrongID=u.PhongBan)
        ).distinct()
        
        print(f"\nVisible documents for {u.username} (Count: {qs.count()}):")
        for d in qs:
            print(f"- [{d.SoKyHieu}] {d.TrichYeu}")
            print(f"    NguoiGui_id: {d.NguoiGui_id}, Handler_id: {d.UserID_id}, Recipient_id: {d.DonViTrongID_id}")
            
    except UserAccount.DoesNotExist:
        print("User vquyen not found.")

if __name__ == "__main__":
    run()
