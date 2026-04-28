import subprocess
import os
import base64

# Files to sync
files_to_sync = [
    ('backend/app/api/orders.py', '/root/foodzuka/backend/app/api/orders.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
]

def sync_file(local_path, remote_path):
    print(f"Syncing {local_path} -> {remote_path}")
    if not os.path.exists(local_path):
        print(f"File {local_path} not found!")
        return False

    with open(local_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')
    
    # Write file on VPS
    python_code = f"import sys, base64; open('{remote_path}', 'wb').write(base64.b64decode(sys.stdin.read()))"
    cmd = ["ssh", "foodtech", f"python3 -c \"{python_code}\""]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=content_b64)
    
    if process.returncode == 0:
        print(f"Successfully synced to VPS: {remote_path}")
        # Now copy into docker
        docker_path = remote_path.replace('/root/foodzuka/backend/', '/app/')
        copy_cmd = f"docker cp {remote_path} foodtech-backend:{docker_path}"
        subprocess.run(["ssh", "foodtech", copy_cmd], check=True)
        print(f"Successfully copied to container: {docker_path}")
        return True
    else:
        print(f"Error syncing {local_path}: {stderr}")
        return False

# 1. Sync files
for lp, rp in files_to_sync:
    sync_file(lp, rp)

# 2. Restart services
print("Restarting backend service on VPS...")
restart_cmd = "docker restart foodtech-backend"
subprocess.run(["ssh", "foodtech", restart_cmd], check=True)

print("Deployment finished!")
