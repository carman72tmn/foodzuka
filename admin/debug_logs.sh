#!/bin/bash
cd /root/foodzuka/foodtech
docker compose exec admin head -n 50 storage/logs/laravel.log | grep "local.ERROR" -A 1
docker compose exec admin tail -n 50 storage/logs/laravel.log | grep "local.ERROR" -A 1
