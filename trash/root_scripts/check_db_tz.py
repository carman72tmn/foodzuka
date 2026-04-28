import sqlite3
import os

db_path = '/root/foodzuka/backend/foodzuka.db'
if not os.path.exists(db_path):
    # Try alternative path
    db_path = '/root/foodzuka/backend/app.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT timezone_name, manual_timezone FROM iikosettings')
        print(f"Timezone settings: {cursor.fetchone()}")
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
else:
    print(f"DB not found at {db_path}")
