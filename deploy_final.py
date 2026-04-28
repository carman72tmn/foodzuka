import base64
import os
import subprocess

files_to_deploy = [
    {
        "local": "backend/app/services/iiko_sync_service.py",
        "remote": "/root/foodzuka/backend/app/services/iiko_sync_service.py"
    },
    {
        "local": "admin/resources/js/pages/clients/index.vue",
        "remote": "/root/foodzuka/admin/resources/js/pages/clients/index.vue"
    },
    {
        "local": "system_faq.md",
        "remote": "/root/foodzuka/system_faq.md"
    },
    {
        "local": "sql_faq.md",
        "remote": "/root/foodzuka/sql_faq.md"
    },
    {
        "local": "sitenav.md",
        "remote": "/root/foodzuka/sitenav.md"
    }
]

def deploy():
    for f in files_to_deploy:
        if not os.path.exists(f["local"]):
            print(f"File {f['local']} not found locally!")
            continue
            
        print(f"Deploying {f['local']} to {f['remote']}...")
        
        with open(f["local"], "rb") as file:
            content = file.read()
            
        # Используем SSH с передачей данных через stdin
        ssh_cmd = ["ssh", "foodtech", f"cat > '{f['remote']}'"]
        
        try:
            subprocess.run(ssh_cmd, input=content, check=True)
            print(f"Successfully deployed {f['local']}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to deploy {f['local']}: {e}")

if __name__ == "__main__":
    deploy()
