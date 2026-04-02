#!/bin/bash
cd /root/foodzuka/foodtech

# 1. Fix Frontend Host Blocking (Overwrite vite.config.js)
cat <<EOF > frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    allowedHosts: ['72roll.ru', 'www.72roll.ru'],
  }
})
EOF

# 2. Fix Frontend hardcoded IP addresses
# Replacing http://192.168.31.162:8000/api/v1 with https://72roll.ru/api/v1
sed -i "s|http://192.168.31.162:8000/api/v1|https://72roll.ru/api/v1|g" frontend/src/api/catalog.js
sed -i "s|http://192.168.31.162:8000/api/v1|https://72roll.ru/api/v1|g" frontend/src/api/order.js

# 3. Fix Admin .env for HTTPS
sed -i "s|APP_URL=.*|APP_URL=https://72roll.ru/admin|g" admin/.env
if ! grep -q "ASSET_URL" admin/.env; then
    echo "ASSET_URL=https://72roll.ru/" >> admin/.env
fi

# 4. Force HTTPS in Laravel (Add to boot method if not already there)
if ! grep -q "forceScheme('https')" admin/app/Providers/AppServiceProvider.php; then
    sed -i "/public function boot(): void/a \        \Illuminate\Support\Facades\URL::forceScheme('https');" admin/app/Providers/AppServiceProvider.php
fi

# 5. Restart containers to apply all changes
docker compose up -d
docker compose restart frontend admin nginx
