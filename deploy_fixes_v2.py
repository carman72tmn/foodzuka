import subprocess
import os
import base64

# Files to sync
files_to_sync = [
    ('backend/app/models/__init__.py', '/root/foodzuka/backend/app/models/__init__.py'),
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
]

def sync_file(local_path, remote_path):
    print(f"Syncing {local_path} -> {remote_path}")
    if not os.path.exists(local_path):
        print(f"File {local_path} not found!")
        return False

    with open(local_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')
    
    # Ensure directory exists
    remote_dir = os.path.dirname(remote_path)
    try:
        subprocess.run(["ssh", "foodtech", f"mkdir -p {remote_dir}"], check=True)
    except Exception as e:
        print(f"Error creating directory {remote_dir}: {e}")
        return False

    # Write file
    python_code = f"import sys, base64; open('''{remote_path}''', 'wb').write(base64.b64decode(sys.stdin.read()))"
    cmd = ["ssh", "foodtech", f"python3 -c \"{python_code}\""]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=content_b64)
    
    if process.returncode == 0:
        print(f"Successfully synced {local_path}")
        return True
    else:
        print(f"Error syncing {local_path}: {stderr}")
        return False

# 1. Sync files
for lp, rp in files_to_sync:
    sync_file(lp, rp)

# 2. Restart and Rebuild backend
print("Rebuilding and restarting backend on VPS...")
build_cmd = "cd /root/foodzuka && docker-compose up -d --build backend"
try:
    subprocess.run(["ssh", "foodtech", build_cmd], check=True)
    print("Backend rebuilt and restarted successfully!")
except Exception as e:
    print(f"Error during rebuild/restart: {e}")

print("Deployment of fixes finished!")
