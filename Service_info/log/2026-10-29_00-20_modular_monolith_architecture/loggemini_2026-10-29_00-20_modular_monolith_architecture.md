# Журнал работ: Переход на модульную архитектуру админ-панели (Modular Monolith + Dynamic UI Shell)

**Дата и время:** 29.10.2026 00:20 (UTC+5)  
**Сессия:** `modular_monolith_architecture`  
**Исполнитель:** AI-ассистент (Google DeepMind Antigravity)  
**Статус:** Выполнено успешно (100%)

---

## 1. Цель задачи
Реализация архитектурного перехода админ-панели на **Модульный монолит с динамическими плагинами (Modular Monolith + Dynamic UI Shell)**:
- Шаг 1. Предохранители на фронтенде (Error Boundaries): обертывание разделов админки в защитные компоненты Vue для предотвращения белого экрана при локальных сбоях.
- Шаг 2. Стандартизация структуры модуля на бэкенде: создание базового класса `BaseModule` и `ModuleManager` с автоматической регистрацией роутеров.
- Шаг 3. Реестр модулей в БД и интерфейсе: таблица `system_modules` и вкладка админки «Система -> Модули системы».
- Шаг 4. Пилотный модуль: разработка изолированного модуля «Хаб внешних интеграций» (`integrations_hub`) с живой диагностикой iiko, Т-Банка, Telegram, VK и PostgreSQL.

---

## 2. Создание резервной копии (Backup)
Перед началом любых изменений создан полный бэкап:
1. **Локальный бэкап:** `backups/adminka v2 (28_10_2026 V2)/`
2. **Удаленный бэкап на VPS:** `/root/foodzuka_backup_28_10_2026_v2/`

---

## 3. Выполненные изменения

### Бэкенд (FastAPI & SQLModel)
1. **Модель `SystemModule`**:
   - Файл: `backend/app/models/system_module.py`
   - Сопоставлена с таблицей `system_modules` в БД PostgreSQL (`foodtech-db`).
2. **Базовый класс модуля `BaseModule`**:
   - Файл: `backend/app/modules/base.py`
   - Атрибуты: `slug`, `name`, `description`, `version`, `author`, `icon`, `category`, `is_system`, `is_enabled`, `route_path`, `router`.
   - Методы: `get_router()`, `on_load(app)`, `on_unload(app)`, `get_info()`.
3. **Менеджер модулей `ModuleManager`**:
   - Файл: `backend/app/modules/manager.py`
   - Автообнаружение модулей в каталоге `backend/app/modules/`.
   - Синхронизация с БД (`sync_with_db`).
   - Динамическое монтирование роутеров (`mount_routes`) под префиксом `/api/v1/modules/{slug}`.
   - Управление состоянием (`toggle_module`).
4. **API системных модулей**:
   - Файл: `backend/app/api/system_modules.py`
   - `GET /api/v1/system/modules` — получение полного списка модулей с runtime-статусом.
   - `POST /api/v1/system/modules/{slug}/toggle` — переключение статуса модуля.
   - `POST /api/v1/system/modules/rescan` — пересканирование каталога модулей.
5. **Пилотный модуль `integrations_hub`**:
   - Каталог: `backend/app/modules/integrations_hub/__init__.py`
   - Эндпоинт: `GET /api/v1/modules/integrations-hub/status`
   - Диагностика связей: iiko Cloud, Т-Банк API, Telegram Bot, VK Bot, PostgreSQL.
6. **Подключение в ядро `backend/main.py`**:
   - Импортирован и инициализирован `module_manager.init_app(app)` в `startup_event`.
   - Подключен роутер `system_modules.router`.

### Фронтенд (Vue 3, Vuetify, Vite)
1. **Предохранитель `ModuleErrorBoundary.vue`**:
   - Файл: `admin/resources/js/components/ModuleErrorBoundary.vue`
   - Перехватывает ошибки через хук `onErrorCaptured`. Оборачивает `<RouterView />` в `admin/resources/js/layouts/default.vue`.
2. **Страница реестра и хаба модулей**:
   - Файл: `admin/resources/js/pages/system/modules.vue`
   - Вкладка 1: Таблица реестра модулей (поиск, категории, версии, статус загрузки, переключатели активности).
   - Вкладка 2: Интерактивная панель пилотного модуля «Хаб интеграций» с кнопкой live-диагностики внешних сервисов.
   - Вкладка 3: Информационная справка по архитектуре Modular Monolith.
3. **Маршрутизация и навигация**:
   - Добавлен роут `system/modules` в `admin/resources/js/plugins/router/routes.js`.
   - Добавлен пункт меню «Модули системы» в `admin/resources/js/layouts/components/NavItems.vue` в блоке «Система».

---

## 4. Развертывание и верификация на VPS
- Все файлы загружены на удаленный сервер `vezuroll.ru` в `/root/foodzuka`.
- Контейнер `foodtech-backend` перезапущен, в логах:
  - `[ModuleManager] Scanning directory: /app/app/modules`
  - Регистрация и монтирование модуля `integrations_hub`.
  - Успешный запуск планировщиков и WebSocket.
- Сборка фронтенда `npm run build` выполнена успешно (768 модулей скомпилировано в чанки, включая `modules-BksvwZnK.js`).
- Очищен кэш представлений Laravel (`php artisan view:clear`).
- Проверены эндпоинты:
  - `GET https://vezuroll.ru/api/v1/system/modules` -> 200 OK
  - `GET https://vezuroll.ru/api/v1/modules/integrations-hub/status` -> 200 OK
  - `POST https://vezuroll.ru/api/v1/system/modules/integrations_hub/toggle` -> 200 OK

---

## 5. Документация
Обновлены файлы учета:
- `Service_info/system_faq.md` (добавлен Раздел 15 по Модульному монолиту).
- `Service_info/sql_faq.md` (добавлено описание таблицы `system_modules`).
- `Service_info/sitenav.md` (добавлено описание вкладки «Модули системы» в разделе «Система»).


---

## 6. Анализ и устранение ошибки ВКонтакте (Flood control) в Мультичате

### Диагностика
- **Текст ошибки:** `app.services.multichat_user_service VK getConversations error for account Довезука Ресторан-Доставки: {'error_code': 9, 'error_msg': 'Flood control'}`.
- **Причина возникновения:**
  1. Личный токен пользователя ВКонтакте («Довезука Ресторан-Доставки») используется для API-запросов к методам переписок (`messages.getConversations`) с IP-адреса хостинга/VPS (`178.212.13.48`).
  2. Антиспам и антифрод алгоритмы ВКонтакте временно блокируют доступ к методам сообщений для пользовательских токенов с IP датацентров при регулярном опросе (выдают `error_code: 9 ('Flood control')`). В ходе проверки было обнаружено, что даже базовый запрос `users.get` по данному токену отклоняется VK антиспамом с кодом 9.
  3. Ранее в коде стоял кулдаун всего на 10 минут (`600` сек), а планировщик запускался каждые 15 минут. ВКонтакте не успевал остыть и продлевал блокировку.
  4. При этом ответ VK логировался как `logger.warning`, из-за чего каждое срабатывание антифрода VK записывалось в таблицу `system_logs` базы данных и отображалось в админ-панели как ошибка.

### Решение
1. **Увеличен кулдаун до 2 часов (7200 сек)**:
   - В `backend/app/services/multichat_user_service.py` при получении `error_code in (9, 29)` в Redis устанавливается ключ `vk_flood_cooldown:{acc.id}` на 7200 сек.
   - Планировщик пропускает данный аккаунт, не отправляя повторных запросов, что дает ВКонтакте время снять ограничение.
2. **Оптимизирован уровень логирования**:
   - Ожидаемый ответ антифрода внешнего сервиса (`error_code: 9` или `29`) теперь логируется как `logger.info`, исключая засорение системных логов базы данных `system_logs`.
3. **Оптимизирован объем выборки**:
   - Параметр `count` в `messages.getConversations` уменьшен с 40 до 20 для снижения нагрузки и уменьшения вероятности триггера антифрода.
4. **Установлен первоначальный кулдаун в Redis**:
   - На VPS для аккаунта ID=11 («Довезука Ресторан-Доставки») активирован ключ `vk_flood_cooldown:11` на 7200 секунд.
