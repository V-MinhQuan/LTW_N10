import os
import django
import sys

# Add current directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from web.models import UserAccount, VanBanDi, DonViBenTrong
from django.db.models import Q

def run():
    # Find a department head (e.g., Marketing)
    # Let's list all first
    print("--- Department Heads ---")
    heads = UserAccount.objects.filter(VaiTroID__ChucVu__icontains='Trưởng phòng')
    for u in heads:
        print(f"ID: {u.pk}, User: {u.username}, Role: {u.VaiTroID.ChucVu}, Dept: {u.PhongBan}")

    # Pick one for testing (e.g. the first one that is not IT Head)
    test_user = None
    for u in heads:
        if "IT" not in u.VaiTroID.ChucVu:
            test_user = u
            break
    
    if not test_user:
        print("No non-IT department head found.")
        return

    print(f"\n--- Testing for User: {test_user.username} (Dept: {test_user.PhongBan}) ---")
    
    # Logic from get_filtered_documents
    qs = VanBanDi.objects.filter(
        Q(UserID__PhongBan=test_user.PhongBan) | 
        Q(DonViTrongID=test_user.PhongBan)
    ).distinct()
    
    print(f"Total documents visible: {qs.count()}")
    for d in qs:
        creator_dept = d.NguoiGui.PhongBan if hasattr(d, 'NguoiGui') and d.NguoiGui else (d.UserID.PhongBan if d.UserID else "Unknown")
        handler_dept = d.UserID.PhongBan if d.UserID else "Unknown"
        recipient_dept = d.DonViTrongID
        print(f"- [{d.SoKyHieu}] {d.TrichYeu}")
        print(f"    Creator Dept: {creator_dept}")
        print(f"    Handler Dept: {handler_dept}")
        print(f"    Recipient Dept: {recipient_dept}")
        if creator_dept != test_user.PhongBan and recipient_dept != test_user.PhongBan:
            print("    *** LEAK? Visible despite neither creator nor recipient matching dept. ***")

if __name__ == "__main__":
    run()
