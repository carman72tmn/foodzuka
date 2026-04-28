#!/bin/bash
echo "=== TABLE COUNTS ==="
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -t -c "SELECT 'courier_orders: ' || COUNT(*) FROM courier_orders"
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -t -c "SELECT 'shifts: ' || COUNT(*) FROM shifts"
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -t -c "SELECT 'employees: ' || COUNT(*) FROM employees"
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -t -c "SELECT 'is_courier=true: ' || COUNT(*) FROM employees WHERE is_courier=true"
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -t -c "SELECT 'is_admin=true: ' || COUNT(*) FROM employees WHERE is_admin=true"

echo ""
echo "=== SHIFTS SAMPLE ==="
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c "SELECT e.name, s.date_open, s.date_close, s.status, s.revenue_at_close FROM shifts s JOIN employees e ON e.id=s.employee_id ORDER BY s.date_open DESC LIMIT 10"

echo ""
echo "=== iiko SETTINGS ==="
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -t -c "SELECT resto_url, resto_login, (CASE WHEN resto_password IS NOT NULL AND length(resto_password)>0 THEN 'SET' ELSE 'EMPTY' END) as pwd FROM iiko_settings LIMIT 1"
