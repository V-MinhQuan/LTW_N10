import os
import sys
import django
from django.db import connection

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

def check_columns():
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'web_vanbanden'")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Columns in web_vanbanden: {columns}")
        
        if 'NgayHoanThanh' not in columns:
            print("NgayHoanThanh is MISSING!")
        else:
            print("NgayHoanThanh EXISTS.")

if __name__ == "__main__":
    check_columns()
