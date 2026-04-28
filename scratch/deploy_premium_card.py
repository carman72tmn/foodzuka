import subprocess
import os
import base64

# Files to sync for the Premium Guest Card reconstruction
files_to_sync = [
    ('backend/app/schemas/__init__.py', '/root/foodzuka/backend/app/schemas/__init__.py'),
    ('backend/app/api/customers.py', '/root/foodzuka/backend/app/api/customers.py'),
    ('backend/app/services/iiko_service.py', '/root/foodzuka/backend/app/services/iiko_service.py'),
    ('admin/resources/js/components/CustomerDetailModal.vue', '/root/foodzuka/admin/resources/js/components/CustomerDetailModal.vue'),
    ('admin/resources/styles/customer-card-premium.css', '/root/foodzuka/admin/resources/styles/customer-card-premium.css'),
    ('admin/package.json', '/root/foodzuka/admin/package.json'),
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

    # Write file using base64 to avoid encoding issues
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
# We use npm install to pick up axios and vue-toastification
build_cmd = "cd /root/foodzuka/admin && npm install && npm run build"
subprocess.run(["ssh", "foodtech", build_cmd], check=True)

# 3. Restart services
print("Restarting services on VPS...")
# Restarting backend to pick up new schemas and API endpoints
# Restarting worker to pick up changes in iiko_service
# Admin container usually serves static files, but restart ensures everything is clean
restart_cmd = "cd /root/foodzuka && docker-compose restart backend worker admin"
subprocess.run(["ssh", "foodtech", restart_cmd], check=True)

print("Premium Guest Card Deployment finished!")
