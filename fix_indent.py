path = r"C:\Users\v_kva\.gemini\antigravity\scratch\foodtech\backend\app\services\vk_service.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

bad_block = """                if "error" in data:
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
                    pass"""

good_block = """                if "error" in data:
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
                            pass"""

text = text.replace(bad_block, good_block)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

print("vk_service.py indentation fixed")
