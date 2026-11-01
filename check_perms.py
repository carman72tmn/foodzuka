from app.core.database import get_session
from app.models.user import User
from app.models.role import Role
from sqlmodel import select

with next(get_session()) as session:
    # Use session.scalars to get the actual User instance
    user = session.scalars(select(User).where(User.username == "0001")).first()
    print(f"Type of user: {type(user)}")
    print(f"User 0001: {user.username if user else 'None'}, Role ID: {user.role_id if user else 'None'}")
    if user and user.role_id:
        role = session.exec(select(Role).where(Role.id == user.role_id)).first()
        print(f"Role: {role.name if role else 'None'}, {role.code if role else 'None'}")
        if role:
            print(f"Number of permissions: {len(role.permissions)}")
            for p in sorted([p.code for p in role.permissions]):
                if "vk" in p:
                    print(f" - {p}")
