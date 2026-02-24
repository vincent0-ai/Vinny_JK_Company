import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vinny_kj.settings')
django.setup()

def clear_migration_history():
    with connection.cursor() as cursor:
        print("Clearing migration history for 'api'...")
        cursor.execute("DELETE FROM django_migrations WHERE app='api';")
    print("Migration history for 'api' cleared.")

if __name__ == "__main__":
    clear_migration_history()
