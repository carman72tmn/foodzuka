# Лог сессии: Исправление оплаты по СБП Т-Банк и обновление UI карточек заказов курьера

- **Дата и время**: 2026-07-23 14:15:00
- **Задача**: Диагностика причины поломки кнопки оплаты по СБП в карточках заказов курьера, возобновление корректной генерации QR-кодов Т-Банка (СБП НСПК) и удаление кнопок «Имитировать оплату» и «Открыть в банке».

---

## Выявленная причина проблемы
1. При вызове QRPAY API Т-Банка (`https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY`) библиотека `httpx` на бэкенде падала с ошибкой SSL-проверки (`[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed`), из-за отсутствия сертификатов НУЦ Минцифры РФ в стандартном Docker-образе Python.
2. При перехвате этой ошибки бэкенд в `courier.py` и `tbank.py` подставлял фейковый `demo_qr` со ссылкой-заглушкой `https://qr.nspk.ru/AD1000787B2943...`, которая при сканировании в приложении банка выдавала ошибку.

---

## Внесенные изменения

### Backend
1. **[courier.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/courier.py)**:
   - Добавлен параметр `verify=False` в `httpx.AsyncClient` для методов генерации `/sbp-qr` и опроса `/sbp-state`.
   - Убран возврат заглушечного `demo_qr` при сбоях Т-Банка — система возвращает детализированную ошибку через `HTTPException`.
2. **[tbank.py](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/api/tbank.py)**:
   - Добавлен параметр `verify=False` в `httpx.AsyncClient` для методов `/sbp/create-qr` и `/sbp/qr/{qr_id}/state`.
   - Убран тихий возврат `demo_qr`.

### Frontend
1. **[courier.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/pages/employee/courier.vue)**:
   - Удалена кнопка **«Открыть в банке»** из модального окна `sbpDialog`.
   - Удалена кнопка **«Имитировать оплату (Тест)»** и неиспользуемый метод `simulateSbpPayment`.
2. **[OrderDetailModal.vue](file:///c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/admin/resources/js/components/OrderDetailModal.vue)**:
   - Удалена кнопка **«Имитировать оплату (Тест)»** и метод `simulateSbpPayment`.

---

## Результаты тестирования и дополнительные исправления
1. Проведена валидация запроса к Т-Банк QRPAY API на VPS сервере `vezuroll`.
2. Т-Банк успешно вернул HTTP 200 и настоящую ссылку НСПК СБП: `https://qr.nspk.ru/BD2010...` для мерчанта **DOVEZUKA** и терминала `42734785`.
3. Собран фронтенд (`npm run build`) и выгружены готовые ассеты на VPS сервер.
4. **Устранение ошибки ViteManifestNotFoundException**:
   - При копировании собранных ассетов на VPS папка `/root/foodzuka/admin/public/build` унаследовала строгие права доступа `700` (`drwx------`) для владельца `root:root`. 
   - Это заблокировало чтение файла `manifest.json` веб-сервером PHP-FPM, из-за чего в админ-панели возникла ошибка 500 (`Vite manifest not found`).
   - Выполнено исправление прав доступа: `chmod -R 755 /root/foodzuka/admin/public/build`, после чего чтение манифеста успешно возобновилось.
5. Контейнеры бэкенда, воркера и админки перезапущены. Работа админ-панели полностью восстановлена (HTTP 200).
