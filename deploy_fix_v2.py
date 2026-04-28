import subprocess
import os
import base64

# Files to sync
files_to_sync = [
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('admin/resources/js/components/CustomerDetailModal.vue', '/root/foodzuka/admin/resources/js/components/CustomerDetailModal.vue'),
]

def sync_file(local_path, remote_path):
    print(f"Syncing {local_path} -> {remote_path}")
    if not os.path.exists(local_path):
        print(f"File {local_path} not found!")
        return False

    with open(local_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')
    
    # Write file via SSH
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

# 2. Restart backend and worker services
print("Restarting backend and worker on VPS...")
restart_cmd = "cd /root/foodzuka && docker-compose restart backend worker"
subprocess.run(["ssh", "foodtech", restart_cmd], check=True)

# 3. Rebuild Admin Frontend
print("Rebuilding admin frontend on VPS...")
# We run npm run build inside the admin directory on the host to update the public/build directory
build_cmd = "cd /root/foodzuka/admin && npm install && npm run build"
subprocess.run(["ssh", "foodtech", build_cmd], check=True)

# 4. Restart admin container just in case
print("Restarting admin container...")
restart_admin_cmd = "cd /root/foodzuka && docker-compose restart admin"
subprocess.run(["ssh", "foodtech", restart_admin_cmd], check=True)

print("Full deployment finished!")
