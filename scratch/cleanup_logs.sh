docker exec foodtech-db psql -U foodtech_user -d foodtech_db -c "DELETE FROM system_logs WHERE message LIKE '%?%';"
