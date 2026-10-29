# Лог сессии: 2026-09-02_login_error_investigation
Дата: 2026-09-02 20:35
Задача: Исправление ошибки входа в админку Unexpected token <, html... is not valid JSON

## 1. Исследование проблемы
- Пользователь получал ошибку: Unexpected token <, html... is not valid JSON при входе в админ-панель vezuroll.ru/admin.
- В логах Nginx: upstream prematurely closed connection / Connection reset by peer на запросы к /api/v1/auth/login и другим эндпоинтам.
- В логах бэкенда: OSError: [Errno 24] Too many open files.
- Проверка дескрипторов в foodtech-backend показала 1027 открытых FD, из которых 984 относились к SQLite базе сессий MAX /app/media/max_sessions/max_session_1858a14e.db.

## 2. Коренная причина
- В app/services/max_bridge_service.py методы работы с pymax.WebClient (sync_pymax_dialogs, fetch_chat_history, search_user_by_phone, send_bridge_message) не содержали блока finally для гарантированного вызова client.close() и client._app.store.close().
- Планировщик scheduler.py запускал задачу multichat_sync_max_user_task_wrapper каждые 20 секунд, создавая новые экземпляры клиентов и утечку дескрипторов SQLite при возникновении сетевых задержек/таймаутов.
- При достижении лимита 1024 FD FastAPI перестал принимать новые соединения, Nginx отдавал страницу 502 Bad Gateway в HTML, а фронтенд в auth.js пытался парсить HTML как JSON.

## 3. Выполненные исправления
- В max_bridge_service.py внедрен метод _close_pymax_client() с явным закрытием WebSocket и aiosqlite коннекта store.conn.
- Все методы обернуты в try...finally: await cls._close_pymax_client(client) с жесткими таймаутами на сетевые вызовы (asyncio.wait_for).
- В scheduler.py оптимизированы интервалы фоновой синхронизации мультичата VK и MAX до 60 секунд.
- В docker-compose.yml добавлен лимит ulimits: nofile: 65536 для контейнеров backend и worker.
- В admin/resources/js/utils/auth.js добавлен безопасный парсинг JSON ответов и человекочитаемые сообщения при ошибках сервера.
- Произведена пересборка фронтенда admin (npm run build) и перезапуск контейнеров на VPS.

## 4. Результаты проверки
- Количество открытых FD в foodtech-backend снизилось с 1027 до ~30 (норма).
- Запрос к /api/v1/auth/login возвращает корректный JSON токен (HTTP 200).
- Вход в админ-панель vezuroll.ru/admin полностью восстановлен и работает стабильно.
