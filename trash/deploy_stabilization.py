
import subprocess
import os
import base64

# Files to sync
files_to_sync = [
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
    ('Service_info/system_faq.md', '/root/foodzuka/Service_info/system_faq.md'),
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
    subprocess.run(["ssh", "foodtech", f"mkdir -p {remote_dir}"], check=True)

    # Write file using python3 to avoid shell expansion issues
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
success = True
for lp, rp in files_to_sync:
    if not sync_file(lp, rp):
        success = False

if success:
    # 2. Restart services
    print("Restarting backend and worker on VPS...")
    # We use -d to not block
    restart_cmd = "cd /root/foodzuka && docker-compose restart backend worker"
    subprocess.run(["ssh", "foodtech", restart_cmd], check=True)
    print("Deployment and restart finished successfully!")
else:
    print("Deployment failed during file sync.")
