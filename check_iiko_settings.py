from app.core.database import get_session
from app.models.vk_activity_settings import VkActivitySettings
from sqlmodel import select

db = next(get_session())
settings = db.exec(select(VkActivitySettings)).all()
print(f"Found {len(settings)} settings rows")
for s in settings:
    print(f"Settings ID: {s.id}, Bot ID: {s.vk_bot_connection_id}")
    print(f"  sync_with_iiko: {s.sync_with_iiko}")
    print(f"  iiko_conversion_rate: {s.iiko_conversion_rate}")
    print(f"  iiko_sync_mode: {getattr(s, 'iiko_sync_mode', 'N/A')}")
    print(f"  iiko_summing_logic: {getattr(s, 'iiko_summing_logic', 'N/A')}")
    print(f"  sync_on_verification: {getattr(s, 'sync_on_verification', 'N/A')}")
    print(f"  sync_on_balance_request: {getattr(s, 'sync_on_balance_request', 'N/A')}")
    print(f"  last_sync_at: {s.last_sync_at}")
