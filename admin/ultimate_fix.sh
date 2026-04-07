#!/bin/bash
# Скрипт для финальной настройки и исправления путей в продакшене.
# Запускайте из корня проекта: bash admin/ultimate_fix.sh

cd /root/foodzuka/foodtech

echo "🚀 Запуск исправления конфигураций для 72roll.ru..."

# 1. Исправление блокировки хоста фронтендом (Vite)
echo "📦 Настройка vite.config.js..."
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

# 2. Замена хардкодных локальных IP во фронтенде
echo "🔗 Обновление API URL во фронтенде..."
sed -i "s|http://192.168.31.162:8000/api/v1|https://72roll.ru/api/v1|g" frontend/src/api/catalog.js
sed -i "s|http://192.168.31.162:8000/api/v1|https://72roll.ru/api/v1|g" frontend/src/api/order.js

# 3. Настройка .env админки для HTTPS
echo "⚙️ Настройка окружения админ-панели..."
sed -i "s|APP_URL=.*|APP_URL=https://72roll.ru/admin|g" admin/.env
if ! grep -q "ASSET_URL" admin/.env; then
    echo "ASSET_URL=https://72roll.ru/" >> admin/.env
fi

# 4. Принудительное использование HTTPS в Laravel
# (Файл AppServiceProvider.php уже исправлен вручную, здесь только проверка)
echo "🔒 Проверка принудительного HTTPS в Laravel..."
if ! grep -q "forceScheme('https')" admin/app/Providers/AppServiceProvider.php; then
    echo "⚠️ ВНИМАНИЕ: forceScheme('https') не найден в AppServiceProvider.php. Проверьте файл вручную."
fi

# 5. Перезапуск контейнеров для применения изменений
echo "🔄 Перезапуск контейнеров..."
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml restart frontend admin nginx

echo "✅ Все исправления применены! Проверьте https://72roll.ru/admin"
