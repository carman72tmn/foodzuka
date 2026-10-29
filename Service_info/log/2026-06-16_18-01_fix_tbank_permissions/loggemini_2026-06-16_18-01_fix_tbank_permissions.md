# Лог сессии: Исправление прав доступа к Монитору Т-Банка
Дата и время начала: 16.06.2026 18:01 (локальное время)
Дата и время окончания: 16.06.2026 18:05 (локальное время)

## Описание задачи
У пользователя kassa не отображаются счета и выдается Forbidden в Мониторе Т-Банка из-за некорректного роутинга прав в API бэкенда и нехватки прав на редактирование (sync-statement).

## Шаги выполнения
1. Создан файл лога.
2. В [deps.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/deps.py) добавлена новая зависимость `require_any_permission(*permission_codes: str)`, которая позволяет разрешать доступ пользователям, имеющим хотя бы одно из указанных прав.
3. В [bank.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/bank.py) эндпоинты `/bank/payments` и `/bank/auto-match` переведены на использование `require_any_permission`. Теперь они доступны как для `bank_payments_*`, так и для `bank_tbank_payments_*`.
4. В [tbank.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/tbank.py) ключевые эндпоинты (`/terminals`, `/accounts`, `/sbp/create-qr`, `/sbp/qr/{qr_id}/state`, `/terminals/{terminalKey}/operations`, `/sync-statement`) переведены на использование `require_any_permission`, что объединило права просмотра и редактирования обеих банковских зон.
5. На VPS-сервере в базе данных роли "Администратор Касса" (ID 6) было успешно выдано недостающее право на редактирование Монитора Т-Банка — `bank_tbank_payments_edit` (ID 141) с помощью SQL-запроса:
   `INSERT INTO role_permission_links (role_id, permission_id) VALUES (6, 141) ON CONFLICT DO NOTHING;`
6. Синтаксис всех трех измененных файлов успешно проверен локально (`python -m py_compile`).
7. Файлы выгружены на VPS-сервер по пути `/root/foodzuka/backend/app/api/` через scp.
8. Выполнена сверка содержимого локальных и удаленных файлов.
9. Контейнеры бэкенда и воркера перезапущены на VPS.
10. Проверены логи бэкенда. API успешно вернул `200 OK` для эндпоинта `/api/v1/bank/payments` при обращении пользователя `kassa` (ID 10).

## Результат
Задача решена. У пользователя `kassa` теперь корректно отображаются счета и транзакции в Мониторе Т-Банка, а запрос на выписку не приводит к ошибке Forbidden.
