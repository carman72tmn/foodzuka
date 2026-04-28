# Log Gemini - 2026-04-23 14:30 - Session 1 - Switch to Polling

## Task: Resolve Iiko Cloud Sync Issues
Critical failure: `Passed revision is too old` and `TOO_MANY_DATA_REQUESTED`.

## Changes Made:
1.  **Backend Logic (`app/services/iiko_service.py`)**:
    *   Enhanced `get_orders_by_date` to support multiple JSON response structures from Iiko Cloud (`items` vs `orders` inside `ordersByOrganizations`).
    *   Added detailed logging for debugging empty responses.
2.  **Sync Service (`app/services/iiko_sync_service.py`)**:
    *   **Completely disabled revision-based sync** (`sync_orders_by_revision`) in the main loop.
    *   Implemented robust date-based polling using 2-hour chunks.
    *   Set the range to +/- 24 hours from current local time (48 hours total).
    *   Added specific error handling for 429 (Rate Limit) and 422 (Too Many Data).
3.  **Server Maintenance**:
    *   Cleaned up Docker images and old archives (>48h).
    *   Recovered ~5GB disk space.
4.  **Verification**:
    *   Manual sync runs without revision errors.
    *   Identified that Iiko Cloud API currently returns empty lists for the organization, suggesting external configuration issues on Iiko's side.

## Files Updated:
- `backend/app/services/iiko_service.py`
- `backend/app/services/iiko_sync_service.py`
- `sync_trigger.py` (for manual testing)
- `system_faq.md` (updated documentation)
- `sql_faq.md` (updated fields)

## Next Steps:
- Monitor incoming webhooks (if they start arriving).
- User needs to check Iiko Cloud "Cloud API" settings for organization `2704eeae-dc5f-4c9f-9b81-375c454dd5bd`.
