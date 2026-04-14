import os
import sys
import django
from django.db import connection

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'QLVB.settings')
django.setup()

def fix_column():
    table_name = 'web_vanbanden'
    column_name = 'NgayHoanThanh'
    
    with connection.cursor() as cursor:
        # Check if the column exists
        cursor.execute(f"""
            SELECT count(*) 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND column_name = '{column_name}'
        """)
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            print(f"Adding column '{column_name}' to table '{table_name}'...")
            try:
                # Adding as timestamp with time zone (DateTimeField equivalent in Postgres)
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN \"{column_name}\" timestamp with time zone NULL;")
                print("Column added successfully!")
            except Exception as e:
                print(f"Error adding column: {e}")
        else:
            print(f"Column '{column_name}' already exists in table '{table_name}'.")

if __name__ == "__main__":
    fix_column()
