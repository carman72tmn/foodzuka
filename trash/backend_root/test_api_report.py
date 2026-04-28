import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1" # This might not work if I don't have a tunnel, but I can try to use internal session if I had one.
# Since I'm on the machine, I can try to call the function directly using SQLModel if I want to be 100% sure.

from app.core.database import engine
from app.api.employees import get_courier_detail_report
from sqlmodel import Session
from datetime import date

def test_report():
    with Session(engine) as session:
        today = date.today().isoformat()
        # Test for today
        print(f"Testing report for {today}")
        result = get_courier_detail_report(date_from=today, date_to=today, session=session)
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_report()
