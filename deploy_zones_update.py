import os
import subprocess
import sys

def run_ssh(cmd):
    print(f"Running: {cmd}")
    try:
        # Use subprocess.run for better control and avoid encoding issues in print
        process = subprocess.Popen(f'ssh foodtech "{cmd}"', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = process.stdout.readline()
            if not line:
                break
            try:
                # Try to decode as utf-8, ignore errors for printing
                decoded_line = line.decode('utf-8', errors='replace').strip()
                print(decoded_line)
            except Exception:
                pass
        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"Execution error: {e}")
        return False

def upload_file(local_path, remote_path):
    print(f"Uploading {local_path} to {remote_path}")
    os.system(f'scp "{local_path}" foodtech:"{remote_path}"')

# Paths
REMOTE_BASE = "/root/foodzuka"
LOCAL_BASE = "c:/Users/v_kva/.gemini/antigravity/scratch/foodtech"

# Files to upload
files = [
    "backend/app/models/company.py",
    "backend/app/schemas/__init__.py",
    "backend/app/api/branches.py",
    "backend/app/utils/geo_utils.py",
    "backend/app/services/yandex_service.py",
    "admin/resources/js/pages/branches/zones.vue",
    "admin/resources/js/components/YandexDeliveryMap.vue"
]

# Ensure directory exists for geo_utils
run_ssh(f"mkdir -p {REMOTE_BASE}/backend/app/utils")

for f in files:
    upload_file(os.path.join(LOCAL_BASE, f), os.path.join(REMOTE_BASE, f))

# Database migration inside Docker
print("Running migrations...")
run_ssh(f"docker exec foodtech-backend alembic upgrade head")

# Restart backend container
print("Restarting backend...")
run_ssh("docker restart foodtech-backend")

# Build frontend
print("Building admin frontend...")
run_ssh(f"cd {REMOTE_BASE}/admin && npm run build")

print("Deployment finished!")
