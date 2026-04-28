import subprocess
import base64
import sys
import os

def upload_file(local_path, remote_path):
    if not os.path.exists(local_path):
        print(f"Local file {local_path} not found")
        return False
    
    with open(local_path, 'rb') as f:
        content = f.read()
    
    b64_content = base64.b64encode(content).decode('utf-8')
    
    # Команда для декодирования на сервере
    # Мы используем python3 для надежности, так как base64 utility может капризничать с переносами строк
    remote_command = f"python3 -c \"import base64, sys; sys.stdout.buffer.write(base64.b64decode(sys.stdin.read().strip()))\" > {remote_path}"
    
    process = subprocess.Popen(['ssh', 'foodtech', remote_command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate(input=b64_content)
    
    if process.returncode == 0:
        print(f"Successfully uploaded {local_path} to {remote_path}")
        return True
    else:
        print(f"Failed to upload {local_path}")
        print(f"Error: {stderr}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload.py <local_path> <remote_path>")
        sys.exit(1)
    
    upload_file(sys.argv[1], sys.argv[2])
