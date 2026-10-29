# Лог сессии: Восстановление загрузки сообщений и синхронизации каналов в Мультичате

**Дата**: 04.09.2026  
**Сессия**: loggemini_2026-09-04_20-55_multichat_fix_channels_sync_and_auth  
**Статус**: Успешно завершено (DONE)  

## 1. Постановка задачи
Пользователь обратился с проблемой:
«! И в мультичат - перестали загружаться все уведомления и сообщения из каналов Вк личный аккаунт, группы, MAX и т д!!!!»

## 2. Диагностика на VPS сервере и анализ корневых причин
1. **Фатальная ошибка JavaScript (TDZ ReferenceError)**:
   - В `admin/resources/js/pages/multichat/index.vue` функции `isVkChannel`, `isMaxChannel`, `isBotChannel` были объявлены внизу файла через стрелочные константы `const isVkChannel = (channel) => ...`.
   - При этом вверху функция `isDialogHidden`, вычисляемые свойства `totalUnreadCount` и восстановление кэша в `onMounted` вызывали `isVkChannel` до инициализации.
   - В рантайме браузера это приводило к исключению `ReferenceError: Cannot access 'isVkChannel' before initialization`, полностью прерывая инициализацию Vue-компонента Мультичата, блокируя рендеринг и вызовы `fetchDialogs()`, `fetchAccounts()`, `fetchTags()`, `fetchHiddenKeys()` и `initWebSocket()`.
2. **Ошибки 401 Unauthorized при обращении к API Мультичата**:
   - В `admin/resources/js/employee_main.js` (точка входа для `/pers`) отсутствовал глобальный перехватчик `axios.interceptors.request.use`. Все вызовы `axios.get('/api/v1/multichat/*')` отправлялись без заголовка `Authorization: Bearer <token>`, приводя к 401 Unauthorized `{"detail": "Not authenticated"}`.
   - В `index.vue` методы не передавали заголовки авторизации `getAuthHeaders()` явно.
3. **Логика скрытия в `isDialogHidden`**:
   - Поиск `dialogs.value.find` внутри `isDialogHidden` приводил к квадратичной задержке $O(N^2)$ и ошибочному скрытию диалогов из общего списка.
4. **Потокобезопасность WebSocket в `broadcast_ws_message`**:
   - При вызове из воркеров фоновой синхронизации (`multichat_sync_vk_user_task_wrapper`) задача бросалась во временный цикл событий потока и уничтожалась до выполнения. Необходима отправка через `asyncio.run_coroutine_threadsafe(manager.broadcast(payload_ws), main_loop)`.

## 3. Внесенные изменения
1. **`admin/resources/js/employee_main.js`**:
   - Добавлен глобальный Axios request interceptor (`axios.interceptors.request.use`), внедряющий `Authorization: Bearer ${token}` и `X-Device-Id` во все HTTP-запросы из панели сотрудников (`/pers`).
2. **`admin/resources/js/pages/multichat/index.vue`**:
   - Функции `isVkChannel`, `isMaxChannel`, `isBotChannel` перенесены в самый верх скрипта как стандартные функции (function declaration), исключая Temporal Dead Zone.
   - Устранены дубликаты функций каналов в теле файла.
   - Оптимизирована функция `isDialogHidden` (убран тяжелый `find`, проверка идет строго по `hiddenDialogsKeys.value.has(key)` или флагу `dialog.is_hidden`).
   - Функция `getRequestHeaders` внедрена во все 35 вызовов Axios (`fetchDialogs`, `fetchHistory`, `fetchAccounts`, `initTelegramQr`, `initWhatsAppQr`, `initMaxQr`, `initVkQr`, `searchGlobalMessages`, `searchByPhone` и т.д.).
3. **`backend/app/api/chat.py`**:
   - В класс `ConnectionManager` добавлена фиксация главного цикла событий `self.loop = asyncio.get_running_loop()`.
   - Реализован потокобезопасный метод `broadcast_sync(message)`, транслирующий сообщения через `asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)`.
4. **`backend/app/api/multichat.py`**:
   - В `broadcast_ws_message` добавлена корректная маршрутизация: если корутина выполняется в главном loop — вызывается `loop.create_task(manager.broadcast(payload_ws))`, если в фоновом потоке — `manager.broadcast_sync(payload_ws)` с потокобезопасной инвалидацией кэша.

## 4. Контрольные суммы SHA-256 (Сверка Local / VPS)
- `admin/resources/js/employee_main.js`: `031f665b7f836a6a5e8a48d49cd73676e8db40b69d88f8a773f02e1113c9fe1a` (Совпадает 100%)
- `admin/resources/js/pages/multichat/index.vue`: `f9fe0bc440f4b7ae47d8428ea1d19ff8882c3a0f3d2770ce15a587f3bbad908f` (Совпадает 100%)
- `backend/app/api/chat.py`: `743e7b03772e82bcdfa1faf881c32efb68929d7df995e42d9f647be7852332e2` (Совпадает 100%)
- `backend/app/api/multichat.py`: `e0e2cd1df598f34678e5ead5e111a21c524e7c25432fa479aaeb2633b36f8aae` (Совпадает 100%)

## 5. Сборка и перезапуск на VPS
1. Фронтенд: `cd /root/foodzuka/admin && npm run build` (Успешно собран за 1м 11с).
2. Бэкенд и воркер: `cd /root/foodzuka && docker compose restart backend worker` (Оба контейнера запущены).
3. Веб-сервер: `cd /root/foodzuka && docker compose restart nginx` (Успешно перезапущен).

## 6. Результаты верификации и тестирования
1. **Проверка API на VPS (`test_multichat.py`)**:
   - `GET /dialogs`: 200 OK, загружен 351 диалог (каналы: `vk_user`: 40, `vk`: 250, `max_user`: 61).
   - `GET /history (vk_user)`: 200 OK, все сообщения и история заказов возвращаются корректно.
   - `GET /accounts`: 200 OK, подключенные аккаунты активны (MAX Пользователь, Довезука Ресторан-Доставки).
   - `GET /tags`: 200 OK, метки загружены.
2. **Проверка в браузере (Chrome DevTools)**:
   - `/admin/multichat`: 0 ошибок в консоли, WebSocket соединение активно (`Multichat WS Connected (Real-time active)`), список диалогов отображается с аватарами, бейджами, временем, метками и счетчиками непрочитанных. История сообщений при клике на диалог открывается мгновенно.
   - `/pers/multichat`: 0 ошибок 401 Unauthorized, перехватчик токенов работает штатно, WebSocket подключен, входящие сообщения поступают в реальном времени.
