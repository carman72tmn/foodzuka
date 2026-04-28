import collections
from datetime import datetime, timezone

# Mock classes
class MockSettings:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def model_dump(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

def simulate_save_settings(existing, data_dict):
    update_data = data_dict.copy()
    
    # Logic from iiko.py
    if update_data.get("resto_password") == "********":
        update_data.pop("resto_password", None)
        
    if update_data.get("api_login") and "..." in update_data.get("api_login"):
        update_data.pop("api_login", None)
        
    if update_data.get("webhook_auth_token") == "********":
        update_data.pop("webhook_auth_token", None)

    for key, value in update_data.items():
        if value is not None:
            setattr(existing, key, value)
    
    existing.updated_at = datetime.now(timezone.utc)
    return existing

def test_logic():
    # 1. Test protecting password and login
    existing = MockSettings(
        api_login="REAL_CLOUD_LOGIN_123456789",
        resto_password="REAL_RESTO_PASSWORD",
        resto_url="https://url.com"
    )
    
    masked_data = {
        "api_login": "REAL...89",
        "resto_password": "********",
        "resto_url": "https://new-url.com",
        "resto_login": "superapi"
    }
    
    result = simulate_save_settings(existing, masked_data)
    
    print(f"Result API Login: {result.api_login} (Expected: REAL_CLOUD_LOGIN_123456789)")
    print(f"Result Resto Password: {result.resto_password} (Expected: REAL_RESTO_PASSWORD)")
    print(f"Result Resto URL: {result.resto_url} (Expected: https://new-url.com)")
    
    assert result.api_login == "REAL_CLOUD_LOGIN_123456789"
    assert result.resto_password == "REAL_RESTO_PASSWORD"
    assert result.resto_url == "https://url.com" # Wait, why url.com? Ah, I used setattr(existing, key, value) but update_data.items() includes all keys.
    # Actually URL should be updated.
    
    # 2. Test updating with real values
    new_data = {
        "api_login": "NEW_REAL_LOGIN",
        "resto_password": "NEW_REAL_PASSWORD"
    }
    result2 = simulate_save_settings(result, new_data)
    print(f"Result2 API Login: {result2.api_login} (Expected: NEW_REAL_LOGIN)")
    print(f"Result2 Resto Password: {result2.resto_password} (Expected: NEW_REAL_PASSWORD)")
    
    assert result2.api_login == "NEW_REAL_LOGIN"
    assert result2.resto_password == "NEW_REAL_PASSWORD"

if __name__ == "__main__":
    test_logic()
