import os
import subprocess

def run_db_query(query):
    cmd = f"ssh foodtech \"docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c \\\"{query}\\\"\""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr

# Fetch 5 sample phone numbers
stdout, stderr = run_db_query("SELECT id, phone FROM customers LIMIT 5;")
print("Query result:")
print(stdout)
if stderr:
    print("Error:")
    print(stderr)
