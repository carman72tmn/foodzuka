# Лог сессии: Персональные Push- и браузерные уведомления (всплывающее окно) для курьеров

**Дата и время**: 2026-09-03 22:30  
**Сессия**: loggemini_2026-09-03_22-30_courier_browser_notifications  
**Задача**:
1. Для курьеров в админке сделать отдельные пуши и уведомления в браузере (всплывающее окно).
2. Скрыть для курьеров все существующие общие уведомления (базовые заказы, оплаты, чужие отмены и смены).
3. Сделать для курьеров 10 выделенных событий:
   1. Назначен заказ на доставку (`courier_order_assigned`)
   2. Установление времени приготовления заказа (`courier_cooking_time_set`)
   3. Изменение времени приготовления заказа (`courier_cooking_time_changed`)
   4. Изменение статуса заказа (только на готов и отменен) (`courier_status_changed`)
   5. Изменение суммы заказа (`courier_amount_changed`)
   6. Изменение адреса доставки (`courier_address_changed`)
   7. Изменение способа доставки заказа (изменили на самовывоз) (`courier_changed_to_pickup`)
   8. Заказ убран из доставки (`courier_removed_from_delivery`)
   9. Заказ убран из списка доставок выбранного курьера (`courier_unassigned`)
   10. Изменение времени доставки заказа (`courier_delivery_time_changed`)
4. Возможность настройки каждого уведомления, смены звука с предпрослушиванием.
5. По умолчанию все 10 уведомлений активны!

---

## План действий
1. Расширение модели `AdminNotificationSettings` в `backend/app/models/admin_notification_settings.py`.
2. Создание скрипта миграции `backend/app/scripts/migrate_courier_notification_settings.py`.
3. Обновление Pydantic схемы `UserRead` в `backend/app/schemas/user.py` с флагом `is_courier`.
4. Обновление эндпоинтов `/auth/me` и `/users/me` для передачи `is_courier`.
5. Обновление `backend/app/api/notifications.py` для чтения и сохранения 10 курьерских настроек.
6. Внедрение генерации и отправки 10 событий в `backend/app/services/iiko_sync_service.py` и `backend/app/api/orders.py`.
7. Обновление `admin/resources/js/stores/chatStore.js` (фильтрация общих уведомлений для курьеров, обработка 10 событий, всплывающее окно, звуки, пуши).
8. Обновление `admin/resources/js/layouts/components/DefaultLayoutWithVerticalNav.vue` (всплывающее окно для курьера, иконки и цвета в колокольчике).
9. Обновление страницы настроек `admin/resources/js/pages/settings/notifications.vue` (сокрытие общих настроек для курьеров, блок управления 10 событиями курьера).
10. Сборка фронтенда, выгрузка на VPS, миграция БД, перезапуск контейнеров, тестирование на боевом сервере.
11. Обновление `system_faq.md`, `sql_faq.md`, `sitenav.md`.

---

## Выполненные работы

1. **Модель настроек и база данных**:
   - В модель `AdminNotificationSettings` добавлены 30 полей для 10 курьерских событий (`*_sound_enabled`, `*_sound_file`, `*_push_enabled`) со значениями по умолчанию `True`.
   - Создан скрипт `migrate_courier_notification_settings.py`.
   - Миграция успешно выполнена на сервере VPS через `docker exec foodtech-backend python /app/app/scripts/migrate_courier_notification_settings.py`.

2. **Определение роли курьера**:
   - В `backend/app/api/deps.py` реализована функция `check_is_courier(user, db)`.
   - В схемах `UserRead` и `EmployeeShort` добавлено поле `is_courier: bool = False`.
   - В эндпоинтах `/api/v1/auth/me` и `/api/v1/users/me` возвращается вычисленный флаг `is_courier`.
   - Во фронтенде `admin/resources/js/utils/auth.js` добавлена функция `isCourierUser()`.

3. **Бэкенд-диспетчеризация 10 курьерских событий**:
   - В `iiko_sync_service.py` реализованы методы `find_courier_user` и `send_courier_notification` (с поддержкой WebSocket `target_user_id`, Web Push и VAPID).
   - В методе `sync_single_order` реализована детекция всех 10 событий с фиксацией старых параметров.
   - В `backend/app/api/orders.py` привязаны события при установке/изменении времени кухни и назначении курьера.

4. **Фронтенд и Pinia Store (`chatStore.js`)**:
   - Реализовано хранилище `courierAlert`.
   - Настроена изоляция: если текущий пользователь является курьером (`isCourier.value`), все базовые общие уведомления админки (`new_bank_payment`, `new_order`, `delivery_unassigned`, `order_cancelled` и др.) полностью подавляются.
   - Обрабатываются все 10 курьерских событий: показ всплывающего окна, звуковой сигнал с учетом настроек, системный Web Push, лог в колокольчике.

5. **Интерфейс всплывающего окна (`DefaultLayoutWithVerticalNav.vue`)**:
   - Внедрен интерактивный `VSnackbar` всплывающего окна `courierAlert` с кнопкой «СМОТРЕТЬ ЗАКАЗ», деталями заказа и динамической расцветкой.
   - В историю колокольчика добавлены иконки и цвета для всех 10 курьерских типов.

6. **Страница настроек (`notifications.vue`)**:
   - Для курьеров скрыты общие карточки админки, выведен блок персональной настройки 10 курьерских событий с тумблерами звука, выбора аудиофайла, кнопкой предпрослушивания и тумблерами Push.
   - Для администраторов добавлен блок шаблонов курьерских уведомлений.

7. **Сборка, синхронизация и верификация на VPS**:
   - Фронтенд успешно собран локально через `npm run build` без ошибок (0 warnings/errors).
   - Все измененные файлы бэкенда, фронтенда и скомпилированные бандлы выгружены на VPS `vezuroll.ru`.
   - Контейнеры `foodtech-backend`, `foodtech-worker` перезапущены, кэш `foodtech-admin` очищен.
   - Проверено состояние БД на VPS: все 30 колонок присутствуют и имеют корректные дефолтные значения `True` (`ALL 30 COURIER NOTIFICATION SETTINGS VERIFIED SUCCESSFULLY!`).
   - Сервер Uvicorn и воркер Celery работают штатно, WebSocket соединения принимаются.
   - Документация `system_faq.md`, `sql_faq.md`, `sitenav.md` обновлена и выгружена на сервер.

