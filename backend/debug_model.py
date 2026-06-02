from app.models.employee import CourierOrder
from sqlmodel import Session, select
from app.core.database import engine

def debug_model():
    print("CourierOrder columns in SQLModel metadata:")
    for col in CourierOrder.__table__.columns:
        print(f" - {col.name}")
    
    with Session(engine) as session:
        try:
            print("\nExecuting test query...")
            q = select(CourierOrder).limit(1)
            res = session.exec(q).first()
            print("Query executed successfully")
            if res:
                print(f"Result order_num: {res.order_num}")
        except Exception as e:
            print(f"Error during query: {e}")

if __name__ == "__main__":
    debug_model()
