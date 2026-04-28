
from sqlmodel import Session, select
from app.core.database import engine
from app.models.bot_settings import BotSettings
from datetime import datetime

def update_bot_token():
    new_token = "7526269369:AAETk_qLTbbWYk26-U_ALC1heIRhmIhu1-k"
    
    with Session(engine) as session:
        # Check if settings exist
        statement = select(BotSettings)
        settings = session.exec(statement).first()
        
        if settings:
            print(f"Updating existing bot settings (current token placeholder: {settings.telegram_bot_token[:5]}...)")
            settings.telegram_bot_token = new_token
            settings.updated_at = datetime.utcnow()
        else:
            print("Creating new bot settings...")
            settings = BotSettings(
                telegram_bot_token=new_token,
                welcome_message="Р”РѕР±СЂРѕ РїРѕР¶Р°Р»РѕРІР°С‚СЊ РІ РЅР°С€РµРіРѕ Р±РѕС‚Р°!"
            )
            session.add(settings)
        
        session.commit()
        print("✅ Telegram Bot Token updated successfully in the database!")

if __name__ == "__main__":
    try:
        update_bot_token()
    except Exception as e:
        print(f"❌ Error updating bot token: {e}")
