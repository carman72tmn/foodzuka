#!/bin/bash
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c "SELECT id, name, role, is_courier FROM employees WHERE name ILIKE '%Эльнур%'"
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c "SELECT id, name, role, is_courier FROM employees WHERE is_courier=true LIMIT 10"
