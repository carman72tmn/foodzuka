
import os

def fix_mojibake(text):
    try:
        # Пытаемся декодировать как latin-1 и закодировать обратно в utf-8
        return text.encode('latin-1').decode('utf-8')
    except Exception:
        return text

def repair_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixed_content = fix_mojibake(content)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

if __name__ == "__main__":
    input_file = r'c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\iiko_service_recovered_utf8.py'
    output_file = r'c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\trash\iiko_service_fixed.py'
    repair_file(input_file, output_file)
    print(f"File repaired and saved to {output_file}")
