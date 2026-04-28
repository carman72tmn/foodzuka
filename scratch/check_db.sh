#!/bin/bash
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c "SELECT count(*) FROM courier_orders WHERE actual_delivery_time >= '2026-04-23 19:00:00'"
docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c "SELECT actual_delivery_time FROM courier_orders ORDER BY actual_delivery_time DESC LIMIT 5"
