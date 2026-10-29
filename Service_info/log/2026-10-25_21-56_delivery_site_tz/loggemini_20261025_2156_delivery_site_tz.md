# Лог сессии: Разработка полного Технического Задания (ТЗ) на клиентский сайт доставки еды и Mini Apps (VK + MAX) с полной интеграцией iiko / iikoCard

- **Дата и время**: 2026-10-25 21:56 (Asia/Yekaterinburg)
- **Сессия**: `26bef29c-6749-48df-bd22-82ca171cb5bb`
- **Задача**: `delivery_site_iiko_vk_max_tz`
- **Статус**: Выполнено

## 1. Изученные файлы документации и кодовой базы
1. `Service_info/system_faq.md` — архитектура проекта, версии компонентов, логика работы iiko Cloud / iiko Server API, KDS, T-Bank, ботов ВК/MAX/TG.
2. `Service_info/sql_faq.md` — полная схема всех таблиц PostgreSQL (`products`, `product_sizes`, `product_modifier_groups`, `product_modifiers`, `kitchen_zones`, `product_recipes`, `orders`, `order_items`, `loyalty_statuses`, `loyalty_rules`, `loyalty_transactions`, `iiko_loyalty_items`, `actions`, `promo_codes`, `iiko_settings`, `vk_users`, `max_bots`, `mailing_cascades` и др.).
3. `Service_info/sitenav.md` — структура навигации `/admin` и `/pers`.
4. Бэкенд (`backend/app/`):
   - Модели: `models/product.py`, `models/category.py`, `models/order.py`, `models/loyalty.py`, `models/iiko_loyalty.py`, `models/action.py`, `models/promo_code.py`, `models/iiko_settings.py`.
   - Роутеры: `api/products.py`, `api/categories.py`, `api/kitchen.py`, `api/loyalty.py`, `api/actions.py`, `api/promo_codes.py`, `api/orders.py`, `api/iiko.py`, `api/stories.py`, `api/branches.py`, `api/bank.py`, `api/validation.py`, `api/yandex.py`.
   - Сервисы: `services/iiko_service.py`, `services/iiko_sync_service.py`.
5. Клиентский фронтенд (`frontend/src/`):
   - `views/Home.vue`, `views/Cart.vue`, `store/cart.js`.

## 2. Выявленные критические точки, зафиксированные в ТЗ
1. **Размеры и модификаторы блюд (iiko External Menu v2 -> Order -> iiko Cloud API)**:
   - В `backend/app/api/orders.py` при формировании `iiko_items` для размерного блюда нельзя подменять `productId` (`products.iiko_id`) на `size.iiko_id`. Необходимо передавать `"productId": product.iiko_id` и отдельно `"sizeId": size.iiko_id` (если `size.iiko_id` не равен `product.iiko_id` и не равен `"default"`).
   - Для модификаторов необходимо передавать `"productId": modifier.iiko_id`, `"productGroupId": group.iiko_id` (для групповых модификаторов), `"amount": modifier_amount`, `"price": modifier.price`.
   - На фронтенде (`frontend/src/`) необходим полноценный конфигуратор размеров (`product_sizes`) и групповых/одиночных модификаторов (`product_modifier_groups` + `product_modifiers`) с контролем `min_amount`, `max_amount`, `is_required`, `default_amount` и фильтрацией `is_visible == true`.
2. **Интеграция iikoCard, бонусов, статусов, акций и промокодов**:
   - Единый эндпоинт предрасчета корзины `POST /api/v1/orders/calculate` с вызовом `POST /api/1/loyalty/iiko/calculate` (Checkin) и сверкой с локальными таблицами `actions`, `promo_codes`, `iiko_loyalty_items`, `loyalty_statuses`, `loyalty_rules`.
   - Передача купонов в `order.loyaltyInfo`, скидок в `order.discountsInfo`, бонусов iikoCard и онлайн-оплаты Т-Банк в `order.payments`.
3. **Защита логов и иммутабельность данных заказов (`Zero Data Loss`)**:
   - Append-only логика для `orders.status_history`, сохранение слепка `customer_info_details`, `discounts_details` (`ui_info`), `payments_details`, `order_items_details` без затирания при приходе неполных вебхуков от iiko.
4. **Единое приложение для Web + VK Mini App + MAX WebApp**:
   - Слой `platformAdapter.js` для работы одного фронтенда в браузере, внутри ВКонтакте (`@vkontakte/vk-bridge`) и внутри мессенджера MAX (`WebApp SDK`), бесшовная авторизация и связка с 6 маркетинговыми ботами ВК/MAX и каскадами рассылок.

## 3. Созданные артефакты
- Полное техническое задание сохранено в артефакт сессии `tz_delivery_site_iiko_vk_max.md` и в рабочую папку проекта `Service_info/TZ_DELIVERY_SITE_IIKO_VK_MAX.md`.
