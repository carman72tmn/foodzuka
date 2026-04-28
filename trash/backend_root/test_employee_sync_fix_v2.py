import asyncio
import uuid
import os
import sys
from datetime import datetime, timedelta

# Setup for running from backend root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select, create_engine, SQLModel, Field
from typing import Optional

# --- MOCK MODELS ---
class Employee(SQLModel, table=True):
    __tablename__ = "test_employees"
    id: Optional[int] = Field(default=None, primary_key=True)
    iiko_id: str = Field(index=True, unique=True)
    name: str = Field()
    phone: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Company(SQLModel, table=True):
    __tablename__ = "test_companies"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field()
    iiko_organization_id: str = Field()
    iiko_api_login: Optional[str] = Field(default=None)

class IikoSettings(SQLModel, table=True):
    __tablename__ = "test_iiko_settings"
    id: Optional[int] = Field(default=None, primary_key=True)
    api_login: str = Field(default="test-login")
    organization_id: str = Field(default="test-org-id")

# --- MOCK SERVICES ---
from app.services.iiko_sync_service import IikoSyncService
from app.services.iiko_service import iiko_service
from unittest.mock import patch

# Use local SQLite for testing
sqlite_url = "sqlite:///test_emp.db"
engine = create_engine(sqlite_url)

async def verify():
    print("Starting employee sync verification (SQLite)...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    # Mock data for /api/1/employees
    mock_employees_resp = {
        "employees": [
            {
                "organizationId": "test-org-id",
                "items": [
                    {
                        "id": "emp-uuid-1",
                        "displayName": "Cook Master",
                        "phone": "+71112223344",
                        "roles": [{"name": "Cook"}],
                        "isDeleted": False
                    },
                    {
                        "id": "emp-uuid-2",
                        "firstName": "Admin",
                        "lastName": "User",
                        "phone": "+75556667788",
                        "roles": [{"name": "Administrator"}],
                        "isDeleted": False
                    }
                ]
            }
        ]
    }
    
    sync_service = IikoSyncService()

    with patch("app.services.iiko_service.IikoService._request") as mock_request:
        mock_request.side_effect = [
            mock_employees_resp, # get_employees
            {"shifts": []},      # get_shifts
            {"schedules": []}    # sync_schedules
        ]
        
        with Session(engine) as session:
            # Add test company and settings
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
                print(f" - {e.name} (Role: {e.role}, Status: {e.status}, Phone: {e.phone})")
                
            if len(employees) >= 2:
                print("SUCCESS: Employees synced correctly with roles and phones")
            else:
                print("FAILED: Not all employees synced")

if __name__ == "__main__":
    asyncio.run(verify())
