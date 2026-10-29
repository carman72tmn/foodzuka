# Лог исправления ошибки сохранения профиля анкеты аккаунта

**Дата:** 16.06.2026 16:20 (UTC+5)  
**Задача:** Выявить и устранить причину, по которой не сохраняются настройки анкеты аккаунта.

---

### Описание проблемы
При сохранении анкеты на странице `https://vezuroll.ru/admin/account-settings` пользователь получал ошибку (красный Snackbar), хотя в системных логах Nginx HTTP-запросы `PATCH /api/v1/users/me` регистрировались со статусом `200` (успешно).

### Исследование и диагностика
1. С помощью `chrome-devtools-mcp` была открыта страница настроек аккаунта в браузере, и нажата кнопка "Сохранить Изменения".
2. В консоли браузера была зафиксирована ошибка:
   `DataCloneError: Failed to execute 'structuredClone' on 'Window': #<Object> could not be cloned.`
3. **Причина ошибки:**
   В Vue 3 реактивные переменные (объявленные через `ref()`) оборачиваются в Proxy. В компоненте `AccountSettingsAccount.vue` вызов `structuredClone(accountDataLocal.value)` приводил к падению, так как `structuredClone` не умеет напрямую клонировать Proxy-объекты во Vue 3. Это прерывало выполнение скрипта прямо в месте обновления локального кэша и перенаправляло управление в блок `catch (e)`. Из-за отсутствия у этой ошибки свойства `response` в Snackbar выводилось общее сообщение об ошибке.

### Проделанные изменения
1. **Фронтенд:**
   - В [AccountSettingsAccount.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/views/pages/account-settings/AccountSettingsAccount.vue) все 6 вызовов `structuredClone` заменены на глубокое клонирование через `JSON.parse(JSON.stringify(...))`. Это надежно работает с реактивными Vue Proxy объектами, содержащими простые примитивы.
2. **Деплой и Сборка:**
   - Измененный файл отправлен на VPS в `/root/foodzuka/admin/resources/js/views/pages/account-settings/AccountSettingsAccount.vue`.
   - Запущена инкрементальная сборка ассетов через `npm run build` непосредственно в директории `admin` на VPS (без пересборки Docker-контейнера).

### Верификация
1. Страница `/admin/account-settings` была обновлена в тестовом сеансе Chromium.
2. При нажатии кнопки "Сохранить Изменения" данные успешно записались в бэкенд FastAPI (статус 200), а на фронтенде корректно отобразился зеленый Snackbar "Изменения успешно сохранены".
3. Ошибка `DataCloneError` в консоли браузера полностью устранена.
