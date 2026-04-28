import os
import sys
import json

# Добавляем путь к приложению
sys.path.append('/app')

try:
    from app.core.database import Session, engine
    from app.models.iiko_settings import IikoSettings
    from sqlmodel import select

    with Session(engine) as session:
        settings = session.exec(select(IikoSettings)).first()
        if settings:
            data = settings.model_dump()
            # Маскируем пароли
            if data.get('resto_password'):
                data['resto_password'] = '***'
            print(json.dumps(data, indent=2, default=str))
        else:
            print("No settings found in DB")
except Exception as e:
    print(f"Error: {e}")
