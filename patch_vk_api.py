path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\api\vk.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Add diagnostics endpoint if not present
if "get_connection_diagnostics" not in text:
    extra_code = """

@router.get("/connections/{connection_id}/diagnostics")
async def get_connection_diagnostics(
    connection_id: int,
    db: AsyncSession = Depends(get_db)
):
    \"\"\"Диагностика токенов и прав VK API для подключения\"\"\"
    from app.services.vk_token_manager import get_vk_token_permissions_diagnostic, get_valid_user_token
    from app.models.vk_bot_connection import VkBotConnection
    from sqlmodel import select
    
    stmt = select(VkBotConnection).where(VkBotConnection.id == connection_id)
    res = await db.exec(stmt)
    conn = res.first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
        
    diag = await get_vk_token_permissions_diagnostic(conn.vk_bot_token, conn.vk_user_token)
    active_user_token = await get_valid_user_token(db, conn)
    diag["has_working_user_token"] = bool(active_user_token)
    diag["active_user_token_source"] = "auto_fallback" if active_user_token and active_user_token != conn.vk_user_token else ("direct" if active_user_token else "none")
    return diag
"""
    text += extra_code
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("vk.py updated with diagnostics endpoint")
else:
    print("Diagnostics already present")
