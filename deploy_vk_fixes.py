import subprocess
import os
import base64

# Files to sync
files_to_sync = [
    ('backend/app/models/vk_webhook_log.py', '/root/foodzuka/backend/app/models/vk_webhook_log.py'),
    ('backend/app/models/__init__.py', '/root/foodzuka/backend/app/models/__init__.py'),
    ('backend/app/api/vk.py', '/root/foodzuka/backend/app/api/vk.py'),
    ('admin/resources/js/pages/settings/vk.vue', '/root/foodzuka/admin/resources/js/pages/settings/vk.vue'),
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

# 2. Build admin frontend on VPS
print("Building admin frontend on VPS (this might take a while)...")
build_cmd = "cd /root/foodzuka/admin && npm run build"
try:
    # Use -t for interactive if needed, or just run it
    subprocess.run(["ssh", "foodtech", build_cmd], check=True)
    print("Admin frontend built successfully!")
except Exception as e:
    print(f"Error building admin frontend: {e}")

# 3. Restart backend on VPS
print("Restarting backend on VPS...")
restart_cmd = "cd /root/foodzuka && docker-compose restart backend"
try:
    subprocess.run(["ssh", "foodtech", restart_cmd], check=True)
    print("Backend restarted successfully!")
except Exception as e:
    print(f"Error restarting backend: {e}")

print("Deployment of VK fixes finished!")
