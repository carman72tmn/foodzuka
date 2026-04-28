
import sys
import os
from sqlmodel import Session, create_engine, select
from datetime import datetime, timedelta
import requests
import json

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.models.iiko import IikoSettings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

def get_olap_columns():
    with Session(engine) as session:
        settings_db = session.exec(select(IikoSettings)).first()
        if not settings_db or not settings_db.resto_url:
            print("Settings not found")
            return
            
        url = settings_db.resto_url
        login = settings_db.resto_login
        password = settings_db.resto_password
        
        print(f"URL: {url}, Login: {login}")
        
        auth_url = f"{url}/resto/api/auth?login={login}&pass={password}"
        resp = requests.get(auth_url)
        if resp.status_code != 200:
            print(f"Auth failed: {resp.status_code}")
            return
        
        token = resp.text.strip('"')
        
        cols_url = f"{url}/resto/api/v2/reports/olap/columns?key={token}&reportType=DELIVERIES"
        resp = requests.get(cols_url)
        if resp.status_code != 200:
            print(f"Get columns failed: {resp.status_code}")
            print(resp.text)
            return
        
        cols = resp.json()
        print(json.dumps(cols, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    get_olap_columns()
