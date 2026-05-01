import os
import django
import sys

# Add current directory to path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

from web.models import VaiTro, DonViBenTrong

def run():
    print("--- Auto-linking Roles to Departments ---")
    roles = VaiTro.objects.all()
    depts = DonViBenTrong.objects.all()
    
    for v in roles:
        found = False
        for d in depts:
            # Check if department name is in the Role name (case insensitive)
            if d.TenDonVi.lower() in v.ChucVu.lower() or v.ChucVu.lower().endswith(d.TenDonVi.lower().replace("Phòng ", "")):
                v.PhongBan = d
                v.save()
                print(f"Linked: '{v.ChucVu}' -> '{d.TenDonVi}'")
                found = True
                break
        if not found:
            print(f"Could not find department for: '{v.ChucVu}'")

if __name__ == "__main__":
    run()
