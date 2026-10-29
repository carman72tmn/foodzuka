import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import Session, engine
from sqlmodel import select
from app.models.user import User

def check_rbac():
    with Session(engine) as session:
        u = session.exec(select(User).where(User.username == '0001')).first()
        if not u:
            print("User 0001 not found!")
            return
            
        print("User:", u.username)
        print("Superuser:", u.is_superuser)
        print("Role name:", u.role.name if u.role else "None")
        print("Role code:", u.role.code if u.role else "None")
        
        if u.role:
            print("Permissions count:", len(u.role.permissions))
            has_view = any(p.code == 'multichat_view' for p in u.role.permissions)
            has_edit = any(p.code == 'multichat_edit' for p in u.role.permissions)
            print("Has multichat_view:", has_view)
            print("Has multichat_edit:", has_edit)
        else:
            print("No role assigned!")

if __name__ == "__main__":
    check_rbac()
