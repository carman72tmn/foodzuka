import sys

def read_file_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            print(f.read())
    except UnicodeDecodeError:
        with open(path, 'r', encoding='utf-16') as f:
            print(f.read())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_file_safe(sys.argv[1])
