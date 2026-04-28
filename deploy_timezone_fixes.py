import subprocess
import os
import base64

# Files to sync
files_to_sync = [
    ('backend/app/core/datetime_utils.py', '/root/foodzuka/backend/app/core/datetime_utils.py'),
    ('backend/app/api/employees.py', '/root/foodzuka/backend/app/api/employees.py'),
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('backend/app/services/iiko_sync_service.py', '/root/foodzuka/backend/app/services/iiko_sync_service.py'),
    ('backend/app/models/order.py', '/root/foodzuka/backend/app/models/order.py'),
    ('backend/app/schemas/__init__.py', '/root/foodzuka/backend/app/schemas/__init__.py'),
    ('admin/resources/js/utils/date.js', '/root/foodzuka/admin/resources/js/utils/date.js'),
    ('admin/resources/js/App.vue', '/root/foodzuka/admin/resources/js/App.vue'),
    ('admin/resources/js/pages/orders/index.vue', '/root/foodzuka/admin/resources/js/pages/orders/index.vue'),
    ('admin/resources/js/components/OrderDetailModal.vue', '/root/foodzuka/admin/resources/js/components/OrderDetailModal.vue'),
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

# 2. Build admin on VPS
print("Building admin frontend on VPS...")
# Используем npm run build. Предполагаем что зависимости уже установлены.
build_cmd = "cd /root/foodzuka/admin && npm run build"
subprocess.run(["ssh", "foodtech", build_cmd], check=True)

# 3. Restart services
print("Restarting services on VPS...")
restart_cmd = "cd /root/foodzuka && docker-compose restart backend admin"
subprocess.run(["ssh", "foodtech", restart_cmd], check=True)

print("Deployment finished!")
