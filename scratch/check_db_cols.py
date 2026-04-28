import subprocess

def check_columns():
    print("Checking customers table columns on VPS...")
    sql = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'customers';"
    escaped_sql = sql.replace("'", "'\\''")
    cmd = f"ssh foodtech \"docker exec -t foodtech-db psql -U foodtech_user -d foodtech_db -c '{escaped_sql}'\""
    
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(process.stdout)

if __name__ == "__main__":
    check_columns()
