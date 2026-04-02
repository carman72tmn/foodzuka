#!/bin/bash
cd /root/foodzuka/foodtech
# Update Admin .env for HTTPS
sed -i "s|APP_URL=.*|APP_URL=https://72roll.ru/admin/|g" admin/.env
if ! grep -q "ASSET_URL" admin/.env; then
    echo "ASSET_URL=https://72roll.ru/" >> admin/.env
fi
# Restart services to apply changes
docker compose restart frontend admin
