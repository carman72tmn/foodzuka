import asyncio
import uuid
import os
import sys
from datetime import datetime, timedelta
import httpx

# Setup for running from backend root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select, create_engine, SQLModel, Field
from typing import Optional

# --- MOCK MODELS ---
class Employee(SQLModel, table=True):
    __tablename__ = "test_employees_fb"
    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True)
    name: str = Field()
    phone: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Company(SQLModel, table=True):
    __tablename__ = "test_companies_fb"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    iiko_organization_id: str = Field()
    iiko_api_login: Optional[str] = Field(default=None)

class IikoSettings(SQLModel, table=True):
    __tablename__ = "test_iiko_settings_fb"
    id: Optional[int] = Field(default=None, primary_key=True)
    api_login: str = Field(default="test-login")
    organization_id: str = Field(default="test-org-id")

# --- MOCK SERVICES ---
from app.services.iiko_sync_service import IikoSyncService
from app.services.iiko_service import iiko_service
from unittest.mock import patch, MagicMock

# Use local SQLite for testing
sqlite_url = "sqlite:///test_emp_fb.db"
engine = create_engine(sqlite_url)

async def verify():
    print("Starting employee sync fallback verification...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    # Mock data for /api/1/employees/couriers (Step 2)
    mock_couriers_resp = {
        "employees": [
            {
                "organizationId": "test-org-id",
                "items": [
                    {
                        "id": "courier-uuid-1",
                        "displayName": "Fast Courier",
                        "firstName": "Fast",
                        "lastName": "Courier",
                        "isDeleted": False
                    }
                ]
            }
        ]
    }
    
    sync_service = IikoSyncService()

    # Define a custom mock for _request that raises 403 on first call
    call_count = 0
    async def mock_request_side_effect(method, endpoint, json_data, **kwargs):
        nonlocal call_count
        call_count += 1
        print(f"Mock request to: {endpoint} (Call #{call_count})")
        
        if endpoint == "/api/1/employees":
            # Simulate 403 Forbidden
            print(" -> Simulating 403 Forbidden")
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 403
            resp.text = "Forbidden"
            raise httpx.HTTPStatusError("Forbidden", request=MagicMock(), response=resp)
        
        if endpoint == "/api/1/employees/couriers":
            print(" -> Returning courier data")
            return mock_couriers_resp
        
        return {"shifts": [], "schedules": []}

    with patch("app.services.iiko_service.IikoService._request", side_effect=mock_request_side_effect):
        with Session(engine) as session:
            company = Company(name="Test Company", iiko_organization_id="test-org-id")
            settings = IikoSettings(api_login="test", organization_id="test-org-id")
            session.add(company)
            session.add(settings)
            session.commit()

            print("Running sync_employees_and_shifts...")
            with patch("app.services.iiko_sync_service.Company", Company), \
                 patch("app.services.iiko_sync_service.Employee", Employee), \
                 patch("app.services.iiko_sync_service.IikoSettings", IikoSettings):
                
                result = await sync_service.sync_employees_and_shifts(session, days=1)
                print(f"Sync Result: {result}")
            
            # Verify employees are in DB
            employees = session.exec(select(Employee)).all()
            print(f"Total employees in DB: {len(employees)}")
            for e in employees:
                print(f" - {e.name} (Role: {e.role}, Status: {e.status})")
                
            if len(employees) >= 1 and employees[0].role == "Courier":
                print("\nSUCCESS: Fallback mechanism worked correctly!")
            else:
                print("\nFAILED: Fallback mechanism failed to sync couriers.")

if __name__ == "__main__":
    asyncio.run(verify())
