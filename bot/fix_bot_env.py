def fix_bot_env():
    file_path = r'c:\Users\v_kva\.gemini\antigravity\scratch\foodtech\bot\.env'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('BOT_TOKEN=7526269369:AAETk_qLTbbWYk26-U_ALC1heIRhmIhu1-k\n')
        f.write('API_URL=http://backend:8000/api/v1\n')
        f.write('DEBUG=False\n')
    print("✅ bot/.env fixed.")

if __name__ == "__main__":
    fix_bot_env()
