from app.core.database import engine
from sqlalchemy import text

def migrate():
    columns = [
        ("post_max_age_days", "INTEGER DEFAULT 7"),
        ("override_keywords", "VARCHAR DEFAULT ''"),
        ("msg_points_like", "TEXT DEFAULT NULL"),
        ("msg_points_comment", "TEXT DEFAULT NULL"),
        ("msg_points_repost", "TEXT DEFAULT NULL"),
        ("msg_points_poll", "TEXT DEFAULT NULL"),
        ("msg_points_join", "TEXT DEFAULT NULL"),
        ("msg_balance_info", "TEXT DEFAULT NULL"),
        ("msg_unlinked_notice", "TEXT DEFAULT NULL")
    ]
    
    with engine.begin() as conn:
        for col_name, col_type in columns:
            try:
                conn.execute(text(f"ALTER TABLE vk_activity_settings ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                print(f"Column {col_name} checked/added.")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")

if __name__ == "__main__":
    migrate()
