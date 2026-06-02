import sys

def read_file_very_safe(path):
    encodings = ['utf-8', 'cp1251', 'latin-1']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                content = f.read()
                print(f"--- SUCCESS WITH {enc} ---")
                # Print only the part we care about
                lines = content.splitlines()
                start = max(0, 3420)
                end = min(len(lines), 3750)
                for i in range(start, end):
                    print(f"{i+1}: {lines[i]}")
                return
        except Exception as e:
            print(f"Failed with {enc}: {e}")

if __name__ == "__main__":
    read_file_very_safe(sys.argv[1])
