from app.core.database import engine
from sqlmodel import Session, select
from app.models.user import User
from app.models.role import Role

with Session(engine) as session:
    user = session.exec(select(User).where(User.username == "0001")).first()
    if user:
        print(f"User found: {user.username}, Role ID: {user.role_id}")
    else:
        print("User 0001 NOT FOUND")
