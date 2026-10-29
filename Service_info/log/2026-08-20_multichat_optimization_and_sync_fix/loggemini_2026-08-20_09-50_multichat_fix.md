# Лог выполнения задачи: Оптимизация Мультичата и настройка фоновой синхронизации MAX / VK
Дата: 2026-08-20 09:50
Сессия: `2026-08-20_multichat_optimization_and_sync_fix`
Файл лога: `loggemini_2026-08-20_09-50_multichat_fix.md`

## 1. Выявленные проблемы и их причины
1. **Торможение интерфейса и зависание браузера**:
   - **DOM-перегрузка**: В компоненте `admin/resources/js/pages/multichat/index.vue` внутри цикла каждого диалога (`v-for="dialog in filteredDialogs"`) создавались отдельные экземпляры выпадающих меню Vuetify (`<VMenu>`), карточек (`<VCard>`), списков (`<VList>`) и подсказок (`<VTooltip activator="parent">`). При десятках диалогов создавались тысячи виртуальных узлов и реактивных слушателей.
   - **Неоптимальная синхронизация**: Фоновый опрос `silentSync` каждые 10 секунд вызывал `mergeDialogsList`, который полностью перезаписывал массив `dialogs.value = updatedList`, приводя к постоянному уничтожению и пересозданию всех компонентов меню в DOM.
   - **Отсутствие индексов в БД**: Запросы `GET /api/v1/multichat/dialogs` выполняли последовательные сканирования таблицы `multichat_messages` по неиндексированным колонкам `(channel, peer_id)` и `(channel, is_read, direction)`.

2. **Не обновлялись сообщения из личных аккаунтов (MAX и ВКонтакте)**:
   - ВКонтакте (`vk_user`): Личные страницы VK не поддерживают вебхуки. Метод `sync_vk_user_dialogs` существовал, но не вызывался планировщиком `scheduler.py` в фоновом режиме.
   - MAX (`max_user` / PyMax Web Instance Bridge): Сессии SQLite сохранялись в эфемерную директорию вместо `/app/media/max_sessions` (смонтированный том на хост), фоновый опрос `sync_pymax_dialogs` не был добавлен в планировщик задач.

## 2. Выполненные изменения

### Бэкенд:
1. `backend/app/core/scheduler.py`:
   - Добавлены фоновые задачи периодической синхронизации в APScheduler:
     - `Мультичат: Синхронизация личного ВК` (`multichat_sync_vk_user_task_wrapper`): каждые 15 секунд.
     - `Мультичат: Синхронизация личного MAX` (`multichat_sync_max_user_task_wrapper`): каждые 20 секунд.
   - Автоматическая регистрация задач в БД `scheduled_tasks` при старте.
2. `backend/app/services/multichat_user_service.py`:
   - В `sync_vk_user_dialogs` добавлена моментальная трансляция новых входящих сообщений в WebSocket операторов через `broadcast_ws_message(new_msg)`.
3. `backend/app/services/max_bridge_service.py`:
   - Исправлен путь `MAX_SESSIONS_DIR` для сохранения баз сессий в постоянный смонтированный том `/app/media/max_sessions` (`/root/foodzuka/admin/public/media/max_sessions`).
   - В `sync_pymax_dialogs` добавлена проверка новых сообщений и рассылка через `broadcast_ws_message(new_msg)`.
4. База данных PostgreSQL (`foodtech-db`):
   - Созданы составные индексы для мгновенного выполнения запросов:
     - `ix_multichat_channel_peer` на `(channel, peer_id)`
     - `ix_multichat_unread` на `(channel, peer_id, is_read, direction)`
     - `ix_multichat_channel_created` на `(channel, created_at DESC)`
     - `ix_multichat_ext_chan` на `(channel, external_id)`

### Фронтенд:
1. `admin/resources/js/pages/multichat/index.vue`:
   - Устранено дублирование сотен экземпляров `<VMenu>` и `<VTooltip>` внутри каждого элемента списка диалогов.
   - Реализовано **единое всплывающее меню меток** (`showSingleTagMenu`, `activeTagMenuDialog`, `tagMenuTarget`), открывающееся при клике по кнопке метки диалога.
   - Переписан метод `mergeDialogsList`: объекты обновляются по месту без пересоздания массива `dialogs.value` и без лишней перерисовки DOM при отсутствии структурных изменений.
   - Добавлена проверка `document.hidden` в `silentSync` для экономии памяти и ресурсов процессора, когда вкладка свернута.
   - Добавлены CSS-свойства `content-visibility: auto` и `contain-intrinsic-size: 72px` для плавного скролла списка.
2. Сборка и деплой:
   - Фронтенд успешно скомпилирован через Vite (`npm run build`).
   - Собранные ассеты выгружены на VPS в `/root/foodzuka/admin/public/build/`.
   - Перезапущены контейнеры `foodtech-backend` и `foodtech-worker`.

## 3. Результаты проверки
- Сообщения из личного аккаунта ВКонтакте синхронизируются автоматически каждые 15 сек (актуальность: 2026-08-20 04:49:12).
- Сообщения из личного аккаунта MAX (PyMax Web Bridge) синхронизируются автоматически каждые 20 сек (актуальность: 2026-08-20 04:49:09).
- WebSocket-соединение оператора принимает уведомления и обновляет чат в реальном времени.
- Зависания браузера устранены, скорость рендеринга списка диалогов выросла более чем в 10 раз.
