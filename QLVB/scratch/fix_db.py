from django.db import connection
def run():
    with connection.cursor() as cursor:
        cursor.execute('ALTER TABLE web_vanbandi ALTER COLUMN "DonViNgoaiID_id" DROP NOT NULL')
        cursor.execute('ALTER TABLE web_vanbandi ALTER COLUMN "DonViTrongID_id" DROP NOT NULL')
        print("Success")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
    django.setup()
    run()
