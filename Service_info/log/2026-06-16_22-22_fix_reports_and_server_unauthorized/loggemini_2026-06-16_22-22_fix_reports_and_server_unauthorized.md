# Лог сессии Gemini: Исправление ошибок 401 Unauthorized в Отчетах и Системе

**Дата/Время:** 16.06.2026 22:22 (UTC+5)
**Название сессии:** `fix_reports_and_server_unauthorized`
**Описание задачи:** Исправить ошибки `401 Unauthorized` при попытке загрузить отчеты OLAP (выручка, продажи и т.д.) и при загрузке данных о ресурсах сервера в разделе «Система -> Сервер».

---

## 1. Исследование проблемы

- В ходе анализа логов бэкенда на VPS обнаружены регулярные ошибки:
  ```
  GET /api/v1/system/server-status HTTP/1.1 401 Unauthorized
  GET /api/v1/reports/olap/revenue?... HTTP/1.1 401 Unauthorized
  ```
- **Причина 1 (Серверный статус)**:
  В компоненте `server.vue` запрос `axios.get('/api/v1/system/server-status')` выполнялся без передачи заголовков авторизации, поэтому бэкенд возвращал 401. Фронтенд ловил исключение и выводил заглушку о том, что `psutil` не установлен, хотя на самом деле библиотека `psutil` была установлена (версия `5.9.8`).
- **Причина 2 (Отчеты OLAP)**:
  В файлах отчетов (`reports/*.vue`) использовался `fetch` для отправки запросов с ручной сборкой заголовков `'Authorization': Bearer ...`, но без передачи заголовка `X-Device-Id`. Бэкенд в проверке сессии (`get_current_user` в `deps.py`) проверяет соответствие `device_id` (`fp` из токена и заголовок `X-Device-Id`). При отсутствии заголовка бэкенд отклонял запросы с кодом `401 Unauthorized`.
- **Причина 3 (Сотрудники)**:
  В компоненте `employees.vue` fetch-запросы также собирались вручную без `X-Device-Id`.

---

## 2. Реализованные изменения

Все изменения были внесены локально в файлы проекта, успешно прошли тестовую сборку Vite (`npm run build`) и затем были выгружены на VPS.

### 2.1. Frontend изменения (Внедрение `getAuthHeaders`)

Во всех измененных файлах был импортирован хелпер `getAuthHeaders` из `@/utils/auth` и подставлен в заголовки запросов:

1. **[server.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/system/server.vue)**:
   - Добавлен импорт `getAuthHeaders`.
   - Запрос изменен на:
     ```javascript
     const { data } = await axios.get('/api/v1/system/server-status', {
       headers: getAuthHeaders()
     })
     ```
2. **Файлы отчетов (OLAP)**:
   - **[revenue.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/reports/revenue.vue)**
   - **[sales.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/reports/sales.vue)**
   - **[products.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/reports/products.vue)**
   - **[days.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/reports/days.vue)**
   - **[clients.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/reports/clients.vue)**
   - **[orders.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/reports/orders.vue)**
   - **[payment_types.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/reports/payment_types.vue)**
   Во всех этих файлах ручная сборка заголовков заменена на стандартный хелпер:
   ```javascript
   const resp = await fetch(`/api/v1/reports/olap/...`, {
     headers: getAuthHeaders()
   })
   ```
3. **[employees.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/employees.vue)**:
   - Внедрен импорт `getAuthHeaders`.
   - Во всех 6 fetch-запросах (`loadEmployees`, `syncEmployees`, `loadEmployeeShifts`, `loadStats`, `loadCourierReport`, `syncCourierReports`) ручные заголовки заменены на `headers: getAuthHeaders()`.

### 2.2. Деплой-скрипт изменения

1. **[sync_to_vps.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/sync_to_vps.py)**:
   - Все 8 новых Vue/JS страниц добавлены в список синхронизации `files_to_sync` для гарантированного обновления на стороне VPS.

---

## 3. Деплой и перезапуск на VPS

1. Скрипт `sync_to_vps.py` успешно запущен на Windows.
2. Все файлы синхронизированы с VPS-сервером `vezuroll`.
3. На VPS успешно выполнена полная пересборка фронтенда (`npm run build`).
4. Контейнеры `backend`, `worker` и `nginx` на VPS успешно перезапущены.
5. Uvicorn-процесс бэкенда перезапущен и готов принимать запросы.

---

## 4. Результаты

- Запросы отчетов и статуса сервера в админке теперь выполняются с корректными заголовками `Authorization` и `X-Device-Id`.
- Бэкенд успешно пропускает данные запросы без возникновения `401 Unauthorized` и отдает корректную статистику.
- Исключены сбои в разделах "Отчеты", "Система -> Сервер" и "Сотрудники".
