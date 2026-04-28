import subprocess
import json

def check_data():
    print("Checking for string data in orders_history...")
    sql = "SELECT id, phone, orders_history FROM customers WHERE orders_history IS NOT NULL LIMIT 20;"
    escaped_sql = sql.replace("'", "'\\''")
    cmd = f"ssh foodtech \"docker exec -t foodtech-db psql -U foodtech_user -d foodtech_db -c '{escaped_sql}'\""
    
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(process.stdout)

if __name__ == "__main__":
    check_data()
