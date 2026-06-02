# Log: Address & OLAP Stabilization
Date: 2026-04-30 20:45
Session: Address Stabilization

## Changes:
1. **Schemas**: Added `AddressHistoryResponse` and updated `CustomerResponse` to support a list of detailed address objects instead of a single string.
2. **API**: Updated `get_customer` in `backend/app/api/customers.py` to populate the `addresses` field with data from `ClientAddressHistory`, including city, street, house, entrance, floor, apartment, and doorphone.
3. **Iiko Service**: Fixed `AttributeError: 'coroutine' object has no attribute 'resto_url'` by correctly awaiting `_get_settings_by_org_id` in `_resto_request`.
4. **Frontend**: Updated `CustomerDetailModal.vue` to display the "Returned Guest" indicator (7+ months) and "New Guest" indicator (<= 1 order). Added structured address display with chips for all components.

## Verification:
- Backend API now returns `addresses` as `[{"id": 1, "city": "Тюмень", "street": "Ленина", ...}, ...]`.
- Frontend maps these objects to UI chips.
- OLAP requests should no longer crash with coroutine errors.

## Next Steps:
- Push to VPS and restart containers.
- Rebuild frontend (`npm run build`).
