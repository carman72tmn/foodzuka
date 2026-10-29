path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\vk_token_manager.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace async db calls with sync or inspect db.exec
old_1 = "res_settings = await db.exec(stmt_settings)"
new_1 = "res_settings = db.exec(stmt_settings) if not hasattr(db.exec(stmt_settings), '__await__') else await db.exec(stmt_settings)"

old_2 = "res_mc = await db.exec(stmt_mc)"
new_2 = "res_mc = db.exec(stmt_mc) if not hasattr(db.exec(stmt_mc), '__await__') else await db.exec(stmt_mc)"

text = text.replace(old_1, "res_settings = db.exec(stmt_settings)")
text = text.replace(old_2, "res_mc = db.exec(stmt_mc)")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_token_manager.py session queries made sync-compatible")
