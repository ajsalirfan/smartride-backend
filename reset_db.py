import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartride_backend.settings')
django.setup()

try:
    with connection.cursor() as cursor:
        print("Dropping database smartride_db...")
        cursor.execute("DROP DATABASE IF EXISTS smartride_db")
        print("Creating database smartride_db...")
        cursor.execute("CREATE DATABASE smartride_db")
        print("Database reset successfully!")
except Exception as e:
    print(f"Error: {e}")
