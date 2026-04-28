import os

def fix_env_bom():
    file_path = r'c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\.env'
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Remove BOM if exists
        if content.startswith(b'\xef\xbb\xbf'):
            print("Found BOM, removing...")
            new_content = content[3:]
            with open(file_path, 'wb') as f:
                f.write(new_content)
        else:
            print("BOM not found, rewriting as clean UTF-8...")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('DATABASE_URL=postgresql://foodtech_user:postgres@db:5432/foodtech_db\n')
                f.write('SECRET_KEY=5aVqE4Buca_n1QaBuYxyncZ5SbiZ3obsSuXDVxi46Ik\n')
                f.write('IIKO_API_LOGIN=86dfd64bd15c42199b789edf6adcb289\n')
                f.write('IIKO_ORGANIZATION_ID=2704eeae-dc5f-4c9f-9b81-375c454dd5bd\n')
                f.write('API_RELOAD=True\n')
                f.write('DEBUG=True\n')
                f.write('APP_PUBLIC_URL=https://72roll.ru\n')

    print("✅ .env file fixed.")

if __name__ == "__main__":
    fix_env_bom()
