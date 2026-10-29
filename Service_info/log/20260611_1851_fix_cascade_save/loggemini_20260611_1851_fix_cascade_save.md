# Лог Gemini: Исправление ошибки при сохранении каскада рассылок
**Дата/Время:** 11.06.2026, 18:51 (местное время, UTC+5)  
**Сессия:** `fix_cascade_save`

## Описание задачи
Пользователь сообщил об ошибке при попытке создания/сохранения нового каскада уведомлений в подразделе «Уведомления и рассылки» админ-панели (сообщение «Ошибка при сохранении каскада»).

## Исследование и обнаружение баги
1. Проведен анализ логов бэкенда на VPS. Обнаружена ошибка `psycopg2.errors.ForeignKeyViolation: update or delete on table "mailing_cascades" violates foreign key constraint "customer_reminders_cascade_id_fkey"`.
2. В процессе детального анализа механизма сохранения выяснилось:
   - При редактировании каскада через PUT-запрос бэкенд в методе `update_cascade` полностью пересоздает шаги каскада (удаляет старые и записывает новые).
   - В БД таблица `customer_message_logs` (журнал отправленных сообщений) содержит внешний ключ `cascade_step_id`, ссылающийся на `mailing_cascade_steps.id`.
   - Если по редактируемому каскаду ранее отправлялись сообщения, СУБД PostgreSQL блокировала удаление старых шагов из-за отсутствия правила `ON DELETE SET NULL`, что приводило к ошибке 500.

## Реализация решения
1. **База данных на VPS**:
   Выполнена SQL миграция для изменения поведения внешнего ключа в таблице логов сообщений:
   ```sql
   ALTER TABLE customer_message_logs 
   DROP CONSTRAINT customer_message_logs_cascade_step_id_fkey, 
   ADD CONSTRAINT customer_message_logs_cascade_step_id_fkey 
   FOREIGN KEY (cascade_step_id) REFERENCES mailing_cascade_steps(id) 
   ON DELETE SET NULL;
   ```
2. **Модели бэкенда**:
   В файле [message_log.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/models/message_log.py) изменено описание поля `cascade_step_id` в классе `CustomerMessageLog` с использованием `sa_column=Column(...)`, чтобы при будущих генерациях БД constraint создавался с `ondelete="SET NULL"`.
3. **Выгрузка и перезапуск**:
   - Файл `message_log.py` скопирован на VPS через SCP в `/root/foodzuka/backend/app/models/message_log.py`.
   - Контейнеры бэкенда и воркера перезапущены: `docker restart foodtech-backend foodtech-worker`.

## Результаты тестирования
1. Был написан и запущен тестовый скрипт `test_cascade_foreign_key.py` внутри докер-контейнера на VPS. Скрипт успешно создал каскад, шаг и лог, затем удалил шаг. Тест подтвердил, что:
   - Шаг удалился без ошибок.
   - Ссылка `cascade_step_id` в логе приняла значение `NULL`.
   - Все временные данные удалены.
2. Проведено ручное тестирование через интерфейс админ-панели (с помощью DevTools-клиента). Создан новый каскад, добавлен шаг, каскад сохранен. Затем этот же каскад отредактирован и сохранен еще раз. Все запросы прошли со статусом `200 OK`.

## Выводы
Проблема ForeignKey-блокировок при обновлении шагов каскада полностью устранена. История сообщений теперь сохраняется корректно с занулением удаленных шагов.
