import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.user import User
from app.api.multichat import get_dialogs

def test():
    with Session(engine) as db:
        user = db.exec(select(User)).first()
        try:
            res = get_dialogs(db=db, current_user=user)
            print(f"SUCCESS! Found {len(res)} dialogs:")
            for d in res[:5]:
                print("Dialog:", d)
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test()
