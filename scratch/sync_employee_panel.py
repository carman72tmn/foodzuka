import base64
import subprocess
import os

# Files to sync: (local_path, remote_path)
files_to_sync = [
    ('configs/nginx/default.conf', '/root/foodzuka/configs/nginx/default.conf'),
    ('admin/routes/web.php', '/root/foodzuka/admin/routes/web.php'),
    ('admin/vite.config.js', '/root/foodzuka/admin/vite.config.js'),
    ('admin/resources/views/employee_application.blade.php', '/root/foodzuka/admin/resources/views/employee_application.blade.php'),
    ('admin/resources/js/employee_main.js', '/root/foodzuka/admin/resources/js/employee_main.js'),
    ('admin/resources/js/EmployeeApp.vue', '/root/foodzuka/admin/resources/js/EmployeeApp.vue'),
    ('admin/resources/js/plugins/router/index.js', '/root/foodzuka/admin/resources/js/plugins/router/index.js'),
    ('admin/resources/js/plugins/router/employee_routes.js', '/root/foodzuka/admin/resources/js/plugins/router/employee_routes.js'),
    ('admin/resources/js/pages/employee/dashboard.vue', '/root/foodzuka/admin/resources/js/pages/employee/dashboard.vue'),
]

def sync_file(local_path, remote_path):
    if not os.path.exists(local_path):
        print(f"File {local_path} not found!")
        return False

    with open(local_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')
    
    remote_dir = os.path.dirname(remote_path)
    subprocess.run(["ssh", "vezuroll", f"mkdir -p {remote_dir}"], check=True)

    python_code = f"import sys, base64; open('{remote_path}', 'wb').write(base64.b64decode(sys.stdin.read()))"
    cmd = ["ssh", "vezuroll", f"python3 -c \"{python_code}\""]
    
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=content_b64)
    
    if process.returncode == 0:
        print(f"Successfully synced {local_path}")
        return True
    else:
        print(f"Error syncing {local_path}: {stderr}")
        return False

if __name__ == "__main__":
    success_count = 0
    for lp, rp in files_to_sync:
        if sync_file(lp, rp):
            success_count += 1
    
    print(f"\nSynced {success_count}/{len(files_to_sync)} files.")
