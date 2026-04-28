#!/bin/bash
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c "SELECT id, iiko_id, name FROM employees WHERE id = 369"
