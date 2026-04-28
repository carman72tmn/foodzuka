path = r'C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\iiko_sync_service.py'
for enc in ['utf-8', 'utf-16', 'utf-16le', 'utf-16be', 'cp1251']:
    try:
        with open(path, 'r', encoding=enc) as f:
            content = f.read(100)
            print(f"Success with {enc}: {content[:20]}...")
            break
    except Exception as e:
        print(f"Failed with {enc}: {e}")
