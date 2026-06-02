import sys

def fix_encoding(path):
    try:
        # Read as latin-1 to avoid decode errors, but then we need to be careful
        # Actually, let's try reading as bytes and decode with errors='ignore' for a cleaner UTF-8
        with open(path, 'rb') as f:
            data = f.read()
        
        # Try to decode as utf-8 first, then fallback to something else
        try:
            content = data.decode('utf-8')
            print("Already UTF-8")
        except UnicodeDecodeError:
            print("Fixing encoding...")
            content = data.decode('utf-8', errors='replace')
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_encoding(sys.argv[1])
