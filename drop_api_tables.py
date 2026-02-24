import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vinny_kj.settings')
django.setup()

def drop_api_tables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'api_%';")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            print(f"Dropping table {table_name}")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    print("All api_ tables dropped successfully.")

if __name__ == "__main__":
    drop_api_tables()
