import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from app.core.database import engine
from sqlalchemy import text

def run_migration():
    queries = [
        "ALTER TABLE ai_site_assistants ADD COLUMN IF NOT EXISTS allow_external_queries BOOLEAN DEFAULT TRUE;",
        "ALTER TABLE ai_site_assistants ADD COLUMN IF NOT EXISTS allow_iiko_api_queries BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE ai_site_assistants ADD COLUMN IF NOT EXISTS allow_iiko_export BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE ai_site_assistants ADD COLUMN IF NOT EXISTS allowed_external_tools JSONB DEFAULT '[\"weather\", \"general_search\", \"consulting\"]'::jsonb;",
        "ALTER TABLE ai_site_assistants ADD COLUMN IF NOT EXISTS iiko_allowed_actions JSONB DEFAULT '[\"read_orders\", \"read_menu\", \"read_stop_list\"]'::jsonb;",
        "ALTER TABLE ai_site_assistants ADD COLUMN IF NOT EXISTS enable_analytics_learning BOOLEAN DEFAULT TRUE;"
    ]
    with engine.connect() as conn:
        for q in queries:
            conn.execute(text(q))
        conn.commit()
    print("Migration executed successfully!")

if __name__ == "__main__":
    run_migration()
