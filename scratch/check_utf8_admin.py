import glob

files = glob.glob('c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/**/*.vue', recursive=True)
question_files = []
for f in files:
    try:
        content = open(f, 'r', encoding='utf-8').read()
        if '????' in content:
            question_files.append(f)
    except Exception as e:
        print(f"ERROR reading {f}: {e}")

print(f"Checked {len(files)} vue files in admin.")
if question_files:
    print("Files with ???? found:")
    for qf in question_files:
        print(" -", qf)
else:
    print("No files with ???? found.")
