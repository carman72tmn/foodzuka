path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\vk_service.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. TTL 30 minutes for FSM states
fsm_check_target = "async def get_user_state("
fsm_replacement = """async def get_user_state(peer_id: int, db: Session) -> Optional[BotUserState]:
    # TTL Check 30 minutes: auto-clear expired states
    from datetime import datetime, timedelta
    stmt = select(BotUserState).where(BotUserState.peer_id == peer_id)
    state = db.exec(stmt).first()
    if state and state.updated_at:
        # If older than 30 mins, reset state
        try:
            diff = datetime.utcnow() - state.updated_at.replace(tzinfo=None)
            if diff.total_seconds() > 1800:
                logger.info(f"FSM state {state.state} for peer_id {peer_id} expired (>30m), auto-clearing")
                db.delete(state)
                db.commit()
                return None
        except Exception:
            pass
    return state

async def _old_get_user_state("""

if "TTL Check 30 minutes" not in text and fsm_check_target in text:
    text = text.replace(fsm_check_target, fsm_replacement, 1)

# 2. Universal exit commands for FSM
exit_cmd_target = "text_clean = message_text.strip().lower()"
exit_replacement = """text_clean = message_text.strip().lower()
    # Universal FSM exit commands
    if text_clean in ["отмена", "отменить", "выход", "стоп", "меню", "в главное меню", "оператор", "назад", "❌ отмена", "❌ отмена (в главное меню)"]:
        await clear_user_state(peer_id, db)
        logger.info(f"User {peer_id} triggered FSM exit via '{text_clean}'")
"""
if "Universal FSM exit commands" not in text and exit_cmd_target in text:
    text = text.replace(exit_cmd_target, exit_replacement, 1)

# 3. Handle Error 901
err_901_target = 'if "error" in data:'
err_901_replacement = """if "error" in data:
            error_data = data.get("error", {})
            if error_data.get("error_code") == 901:
                # User blocked group messages
                logger.warning(f"Error 901: User {peer_id} denied messages from group. Marking is_subscribed = False")
                try:
                    stmt_u = select(VkUser).where(VkUser.vk_id == peer_id)
                    u = db.exec(stmt_u).first() if 'db' in locals() and db else None
                    if u:
                        u.is_subscribed = False
                        db.add(u)
                        db.commit()
                except Exception:
                    pass
"""
if "error_code\") == 901" not in text and err_901_target in text:
    text = text.replace(err_901_target, err_901_replacement, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_service.py successfully enhanced with FSM TTL, Exit Commands and Error 901 handling")
