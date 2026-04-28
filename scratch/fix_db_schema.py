import subprocess

# SQL to fix multiple columns in the customers table
columns_to_fix = [
    'orders_history',
    'iiko_categories',
    'additional_phones',
    'marketing_consents'
]

def fix_db():
    print("Fixing customers table schema on VPS...")
    
    for col in columns_to_fix:
        print(f"Ensuring {col} is JSONB...")
        fix_sql = f"ALTER TABLE customers ALTER COLUMN {col} TYPE JSONB USING {col}::JSONB;"
        # Escape single quotes and newlines
        escaped_sql = fix_sql.replace("'", "'\\''").replace("\n", " ")
        cmd = f"ssh foodtech \"docker exec -t foodtech-db psql -U foodtech_user -d foodtech_db -c '{escaped_sql}'\""
        
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode == 0:
            print(f"  Successfully ensured {col} is JSONB.")
        else:
            if "already of type jsonb" in process.stderr.lower():
                print(f"  {col} is already JSONB.")
            else:
                print(f"  Error updating {col}: {process.stderr}")

if __name__ == "__main__":
    fix_db()
