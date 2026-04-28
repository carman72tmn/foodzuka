import os

def convert_to_utf8(file_path):
    try:
        # Пробуем прочитать как utf-8
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Если есть BOM или это UTF-16, chardet или ручная проверка помогут
        # Но мы просто попробуем декодировать как utf-8
        try:
            content.decode('utf-8')
            return # Уже utf-8
        except UnicodeDecodeError:
            pass

        # Пробуем прочитать как utf-16
        try:
            text = content.decode('utf-16')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Converted {file_path} from utf-16 to utf-8")
        except Exception as e:
            print(f"Failed to convert {file_path}: {e}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

dirs_to_fix = ['backend/app/models/', 'backend/app/services/', 'backend/app/api/', 'backend/app/core/']
for d in dirs_to_fix:
    if not os.path.exists(d): continue
    for root, dirs, files in os.walk(d):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                convert_to_utf8(file_path)
