from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_bot import VkTemplate, VkBotAccount
from app.models.vk_bot_connection import VkBotConnection

with Session(engine) as db:
    print("=== ШАБЛОНЫ VK_TEMPLATES ===")
    templates = db.exec(select(VkTemplate)).all()
    for t in templates:
        print(f"ID={t.id} | event={t.event_type} | active={t.is_active} | target={t.target_mode} | name={t.name}")
        print(f"    chain_config={t.chain_config}")
    
    print("\n=== БОТЫ VK_BOT_CONNECTIONS ===")
    bots = db.exec(select(VkBotConnection)).all()
    for b in bots:
        print(f"ID={b.id} | name={b.name} | group_id={b.vk_group_id} | active={b.is_active} | is_main={b.is_main}")

    print("\n=== ПОЛУЧАТЕЛИ КУРЬЕРЫ В VK_BOT_ACCOUNTS ===")
    couriers = db.exec(select(VkBotAccount).where(VkBotAccount.is_courier == True)).all()
    for c in couriers:
        print(f"ID={c.id} | name={c.name} | is_active={c.is_active} | emp_id={c.employee_id} | vk_id={c.vk_user_id} | tg_id={c.tg_user_id} | max_id={c.max_user_id} | use_vk={c.use_vk} | use_tg={c.use_tg} | use_max={c.use_max} | use_sms={c.use_sms}")
