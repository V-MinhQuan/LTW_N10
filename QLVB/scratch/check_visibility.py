import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from web.models import UserAccount, VanBanDi

def run():
    # Find all department heads
    heads = UserAccount.objects.filter(VaiTroID__ChucVu__icontains='Trưởng phòng')
    for u in heads:
        print(f"User: {u.username} ({u.HoTen}), Dept: {u.PhongBan}")
        # Count documents they can see
        # Logic from get_filtered_documents
        docs = VanBanDi.objects.filter(
            django.db.models.Q(UserID__PhongBan=u.PhongBan) | 
            django.db.models.Q(DonViTrongID=u.PhongBan)
        ).distinct()
        print(f"  Can see {docs.count()} outgoing docs")
        for d in docs[:3]:
            creator_dept = d.UserID.PhongBan if d.UserID else "N/A"
            recipient_dept = d.DonViTrongID
            print(f"    - {d.SoKyHieu}: {d.TrichYeu} (From: {creator_dept}, To: {recipient_dept})")

if __name__ == "__main__":
    run()
