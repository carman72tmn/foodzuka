import json
from decimal import Decimal

# Mock data
iiko_data_missing_risk = {
    "phone": "79220079019",
    "categories": [{"name": "VIP"}],
    "comment": "Test comment"
}

iiko_data_with_risk_false = {
    "phone": "79220079019",
    "shouldBeCheckedForRisk": False
}

iiko_data_with_risk_true = {
    "phone": "79220079019",
    "shouldBeCheckedForRisk": True
}

class MockCustomer:
    def __init__(self):
        self.is_high_risk = True
        self.iiko_categories = []
        self.iiko_comment = ""

def test_sync_logic(customer, iiko_data):
    print(f"Before sync: is_high_risk = {customer.is_high_risk}")
    
    # Logic from iiko_sync_service.py (modified)
    risk_keys = ["shouldBeCheckedForRisk", "isHighRisk", "checkedForRisk"]
    risk_found = False
    for rk in risk_keys:
        if rk in iiko_data:
            customer.is_high_risk = bool(iiko_data.get(rk))
            risk_found = True
            print(f"Risk found in field '{rk}': {customer.is_high_risk}")
            break
    
    if not risk_found:
        risk_in_categories = any("риск" in str(cat).lower() or "risk" in str(cat).lower() for cat in (customer.iiko_categories or []))
        if risk_in_categories:
            customer.is_high_risk = True
            print("Risk found in categories")
        else:
            print(f"Risk not found in iiko data, keeping local: {customer.is_high_risk}")

    print(f"After sync: is_high_risk = {customer.is_high_risk}")
    print("-" * 20)

# Run tests
print("Case 1: iiko data missing risk field (local is True)")
c1 = MockCustomer()
test_sync_logic(c1, iiko_data_missing_risk)

print("Case 2: iiko data has risk=False (local is True)")
c2 = MockCustomer()
test_sync_logic(c2, iiko_data_with_risk_false)

print("Case 3: iiko data has risk=True (local is False)")
c3 = MockCustomer()
c3.is_high_risk = False
test_sync_logic(c3, iiko_data_with_risk_true)
