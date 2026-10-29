# Лог расследования: Белый экран в админ-панели vezuroll.ru/admin
Дата: 2026-09-03 18:50 - 19:25
Задача: Выяснить, почему админка не загружается и показывает белый экран, устранить первопричины, протестировать на VPS и восстановить работоспособность.

---

## 1. Симптомы и первичная диагностика
- При переходе на `https://vezuroll.ru/admin/` пользователь видел белый экран.
- В браузере (Chrome DevTools MCP):
  - DOM-контейнер `#app` содержал пустой `<router-view>` (комментарий `<!---->`).
  - Состояние Vue Router: `path: "/"`, `matched: []`, хук `router.beforeEach` зависал при вызове `await fetchMe()`.
  - Запрос к `/api/v1/auth/me` ожидал ровно 60 секунд и возвращал `504 Gateway Time-out` от Nginx (`upstream timed out (110: Connection timed out)`).
  - На время ожидания промиса `fetchMe()` Vue Router блокировал вызов `next()`, оставляя страницу пустой.

---

## 2. Обнаруженные первопричины сбоя бэкенда

### Причина 1: Утечка соединений пула БД в WebSocket-эндпоинте (`chat.py`)
- В `backend/app/api/chat.py` эндпоинт `@router.websocket("/ws")` содержал зависимость `db: Session = Depends(deps.get_db)`.
- Поскольку WebSocket-соединение непрерывно и удерживается часами (`while True: await websocket.receive_text()`), генератор зависимости `deps.get_db` не завершался.
- В результате соединение с PostgreSQL удерживалось в статусе `idle in transaction`.
- Лимит пула SQLAlchemy составлял `pool_size=10, max_overflow=20` (всего 30 соединений).
- При открытии нескольких вкладок/клиентов (администраторы, курьеры) пул соединений полностью исчерпывался. Все новые HTTP-запросы блокировались на `pool_timeout=60` и обрывались сервером Nginx по 504.

### Причина 2: Блокировка основного цикла событий (AsyncIO Event Loop) Uvicorn в APScheduler
- В `backend/app/core/scheduler.py` задача `multichat_sync_vk_user_task_wrapper` была объявлена как `async def`.
- В APScheduler с `AsyncIOExecutor` корутины выполняются непосредственно в основном потоке Uvicorn.
- Внутри вызывался `multichat_user_service.sync_vk_user_dialogs(session)`, содержащий:
  - Синхронные вызовы `httpx.get` к VK API (`messages.getConversations` и поочередные вызовы `messages.getConversationsById` для бесед в цикле из 40 элементов с таймаутами по 5-10 секунд).
  - Цикл обработки бесед с непрерывным потоком сообщений и десятками синхронных SQL-запросов.
- Интервал выполнения задачи в таблице `scheduled_tasks` (id=39) составлял всего 15 секунд. Из-за этого процесс синхронизации занимал 10-14 секунд из каждых 15 секунд, парализуя event loop Uvicorn на 90% времени.
- Аналогично `multichat_sync_max_user_task_wrapper` удерживал общую сессию БД в течение всех асинхронных операций клиента pymax.

### Причина 3: Переполнение буферов I/O из-за SQL echo в режиме DEBUG
- В `backend/app/core/database.py` было установлено `echo=settings.DEBUG` (где `DEBUG=True`).
- При постоянной обработке спам-сообщений ВК в stdout каждую минуту выводилось более 12 000 строк SQL, вызывая задержки ввода-вывода (I/O saturation).

### Причина 4: Недостаточная отказоустойчивость роутера фронтенда при сбоях бэкенда
- В `admin/resources/js/utils/auth.js` в функции `fetchMe()` отсутствовал клиентский таймаут через `AbortController`.
- В `admin/resources/js/plugins/router/index.js` условие проверяло `if (!authState.token && authRequired)`. При сетевой ошибке 504 токен оставался в localStorage, `authState.user` был `null`, роутер не перенаправлял на `/login`, а пытался перейти в `/dashboard`, где дочерние компоненты падали.

---

## 3. Внесенные исправления

1. **`backend/app/api/chat.py`**:
   - Удалена зависимость `db: Session = Depends(deps.get_db)` из параметров эндпоинта `@router.websocket("/ws")`.
   - Аутентификация и валидация токена переведены на кратковременную сессию `with Session(engine) as db:`, соединение возвращается в пул немедленно.
   - Сохранение сообщений в блоке `action == "send"` переведено на локальную кратковременную сессию `with Session(engine) as db:`. Соединение закрывается сразу после коммита, ДО рассылки WebSocket и пушей.
   - Исправлена ошибка `UnboundLocalError`: при отключении и обработке исключений вызывается `manager.disconnect(user_id, websocket)`.

2. **`backend/app/core/scheduler.py`**:
   - Задача `multichat_sync_vk_user_task_wrapper` обернута в `await asyncio.to_thread(_sync)`, что полностью исключает блокировку основного потока Uvicorn.
   - В `multichat_sync_max_user_task_wrapper` вызов `max_bridge_service.sync_pymax_dialogs()` освобожден от внешнего удержания сессии БД.

3. **`backend/app/services/max_bridge_service.py`**:
   - Аргумент `db` в методе `sync_pymax_dialogs` сделан опциональным. При отсутствии внешней сессии метод использует изолированные кратковременные сессии для выборки аккаунтов и для сохранения результатов. Транзакции БД больше не висят во время сетевых вызовов MAX.

4. **`backend/app/services/multichat_user_service.py`**:
   - Устранена проблема N последовательных синхронных HTTP-запросов в цикле: добавлен предварительный пакетный запрос `messages.getConversationsById` для всех групповых бесед без `chat_settings` одним обращением к VK API.

5. **`backend/app/core/database.py`**:
   - Установлено `echo=False` для исключения переполнения stdout и логов.
   - Настройки пула оптимизированы: `pool_size=15`, `max_overflow=25`, `pool_timeout=30`, `pool_recycle=1800`.

6. **База данных PostgreSQL (`scheduled_tasks`)**:
   - Интервалы выполнения фоновых задач мультичата (id=39 - ВК, id=40 - MAX) увеличены с 15/20 секунд до 60 секунд.

7. **`admin/resources/js/utils/auth.js`**:
   - В функцию `fetchMe()` добавлен таймаут 7000 мс через `AbortController`, чтобы фронтенд гарантированно сбрасывал ожидание и не висел минуту.

8. **`admin/resources/js/plugins/router/index.js`**:
   - Исправлена проверка в хуке `beforeEach`: если `!authState.user && authRequired`, роутер безопасно перенаправляет пользователя на `/login`, предотвращая зависание на белом экране.

---

## 4. Верификация и тестирование

1. **Сверка контрольных сумм локальных и удаленных файлов**:
   - MD5 всех 7 обновленных файлов на VPS полностью совпали с локальными копиями.
2. **Сборка фронтенда**:
   - Выполнена успешная сборка Vite (`npm run build`) в директории `admin` на сервере (exit code 0).
3. **Перезапуск служб**:
   - Перезапущены контейнеры `foodtech-backend`, `foodtech-worker`, `foodtech-nginx`.
4. **Проверка эндпоинтов и скорости ответа**:
   - Запрос `/health` через контейнер nginx отвечает мгновенно (менее 50 мс): `{"статус":"здоров","база_данных":"подключено"}`.
   - Запрос `/api/v1/auth/me` без токена мгновенно возвращает `401 Unauthorized` (вместо 504).
   - В PostgreSQL (`pg_stat_activity`) отсутствуют зависшие запросы и `idle in transaction`.
5. **Тестирование UI в браузере (Chrome DevTools MCP)**:
   - Страница `https://vezuroll.ru/admin/` успешно открылась и отрендерила форму авторизации.
   - Произведен вход под учетной записью `0001` / `121212`.
   - Успешный переход в `https://vezuroll.ru/admin/dashboard`.
   - Отобразились все пункты меню, заголовок "Поздравляем, Админ! 🎉", виджеты "Прибыль: 12,628 ₽", статистика и графики.
   - Консоль браузера чистая, без ошибок.
