import sys
import os
from sqlmodel import Session, select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import engine
from app.models.tbank_settings import TBankSettings

def run():
    with Session(engine) as session:
        settings = session.exec(select(TBankSettings)).first()
        if not settings:
            print("Settings not found, creating new.")
            settings = TBankSettings()
            session.add(settings)
            
        settings.terminal_key = "42734785"
        settings.terminal_pickup = "42734785"
        settings.terminal_delivery = "42734785"
        settings.token = "LYqV0t7V3FBffuphkOs7oR7Le9Cr994xRjmaGxoVJKY="
        settings.certificate_content = None
        settings.is_active = True
        
        session.add(settings)
        session.commit()
        print("Successfully updated T-Bank settings to new credentials!")

if __name__ == "__main__":
    run()
