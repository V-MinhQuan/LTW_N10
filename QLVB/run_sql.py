import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

def run():
    with connection.cursor() as cursor:
        try:
            cursor.execute('ALTER TABLE web_vanbandi ALTER COLUMN "DonViNgoaiID_id" DROP NOT NULL')
            print("Dropped NOT NULL from DonViNgoaiID_id")
        except Exception as e:
            print(f"Error dropping NOT NULL from DonViNgoaiID_id: {e}")
            
        try:
            cursor.execute('ALTER TABLE web_vanbandi ALTER COLUMN "DonViTrongID_id" DROP NOT NULL')
            print("Dropped NOT NULL from DonViTrongID_id")
        except Exception as e:
            print(f"Error dropping NOT NULL from DonViTrongID_id: {e}")

if __name__ == "__main__":
    run()
