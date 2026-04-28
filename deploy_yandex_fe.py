import os
import subprocess

def run_command(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(f"Output: {result.stdout}")
    return result.returncode == 0

files_to_sync = [
    "admin/resources/js/pages/settings/yandex.vue",
    "admin/resources/js/pages/settings/iiko.vue",
    "admin/resources/js/plugins/router/routes.js",
    "admin/resources/js/components/YandexDeliveryMap.vue"
]

for file_path in files_to_sync:
    local_path = file_path.replace("/", "\\")
    remote_path = f"/root/foodzuka/{file_path}"
    
    # Ensure remote directory exists
    remote_dir = os.path.dirname(remote_path).replace("\\", "/")
    run_command(f"ssh foodtech 'mkdir -p {remote_dir}'")
    
    print(f"Syncing {local_path} to {remote_path}...")
    run_command(f"scp {local_path} foodtech:{remote_path}")

print("Building admin frontend on VPS...")
run_command("ssh foodtech 'cd /root/foodzuka/admin && npm run build'")
