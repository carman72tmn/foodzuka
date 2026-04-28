import os

def convert_to_utf8(file_path):
    try:
        # Пробуем прочитать как utf-8
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return # Уже utf-8
    except UnicodeDecodeError:
        pass

    # Пробуем прочитать как utf-16
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        text = content.decode('utf-16')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Converted {file_path} from utf-16 to utf-8")
    except Exception as e:
        print(f"Failed to convert {file_path}: {e}")

models_dir = 'backend/app/models/'
for root, dirs, files in os.walk(models_dir):
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            convert_to_utf8(file_path)
