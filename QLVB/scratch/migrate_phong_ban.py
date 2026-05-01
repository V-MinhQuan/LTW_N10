import sys
import os
import django

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from web.models import UserAccount, DonViBenTrong

def run():
    units = {u.TenDonVi: u.DonViTrongID for u in DonViBenTrong.objects.all()}
    count = 0
    for user in UserAccount.objects.all():
        if user.PhongBan:
            # Nếu đã là ID (số), bỏ qua
            if str(user.PhongBan).isdigit():
                continue
            
            # Thử map tên sang ID
            unit_id = units.get(user.PhongBan)
            old_val = user.PhongBan
            user.PhongBan = str(unit_id) if unit_id else None
            user.save()
            count += 1
            print(f"Updated {user.username}: '{old_val}' -> {user.PhongBan}")
    print(f"Total updated: {count} users")

if __name__ == "__main__":
    run()
