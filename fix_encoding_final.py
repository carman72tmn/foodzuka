import os

files = [
    'backend/app/services/iiko_service.py',
    'backend/app/services/iiko_sync_service.py'
]

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Try to decode as utf-8, if fails, it might be something else
        try:
            content.decode('utf-8')
            print(f"{file_path}: Already UTF-8")
        except UnicodeDecodeError:
            print(f"{file_path}: NOT UTF-8, attempting fix...")
            # Try to decode as utf-16 or cp1251 and convert
            for enc in ['utf-16', 'cp1251', 'latin1']:
                try:
                    text = content.decode(enc)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"{file_path}: Converted from {enc} to UTF-8")
                    break
                except:
                    continue
    else:
        print(f"{file_path}: File not found")
