import asyncio
import os
import sys

# Setup for running from backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.iiko_service import iiko_service
from app.core.database import get_session
from app.models.company import Company
from sqlmodel import select

async def main():
    db = next(get_session())
    try:
        companies = db.exec(select(Company).where(Company.iiko_organization_id != None)).all()
        if not companies:
            print("No companies found")
            return
            
        for company in companies:
            print(f"Company: {company.name}, Org ID: {company.iiko_organization_id}")
            
            # Test variations directly using internal _request
            endpoints = [
                ("POST", "/api/1/employees/info", {"organizationIds": [company.iiko_organization_id]}),
                ("POST", "/api/1/employees", {"organizationIds": [company.iiko_organization_id]}),
                ("GET", "/api/1/employees", None),
                ("GET", f"/api/1/employees?organizationId={company.iiko_organization_id}", None),
                ("POST", "/api/1/employees/shift", {
                    "organizationIds": [company.iiko_organization_id],
                    "dateFrom": "2026-02-01 00:00:00.000",
                    "dateTo": "2026-03-01 00:00:00.000"
                })
            ]
            
            for method, endpoint, payload in endpoints:
                print(f"\\n--- Testing {method} {endpoint} with payload {payload}")
                try:
                    res = await iiko_service._request(method, endpoint, payload)
                    print(f"SUCCESS: {res}")
                except Exception as e:
                    print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
