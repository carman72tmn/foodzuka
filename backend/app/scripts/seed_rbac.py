import sys
import os
from datetime import datetime, timezone

# Добавляем путь к backend, чтобы можно было импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.role import Role, Permission
from app.models.user import User

PERMISSIONS = [
    # Старые базовые права (для обратной совместимости)
    {"name": "Просмотр заказов (Базовый)", "code": "orders_view", "category": "Заказы (Базовые)", "description": "Доступ к списку заказов"},
    {"name": "Редактирование заказов (Базовый)", "code": "orders_edit", "category": "Заказы (Базовые)", "description": "Изменение статусов, состава и данных заказа"},
    {"name": "Удаление заказов (Базовый)", "code": "orders_delete", "category": "Заказы (Базовые)", "description": "Возможность удалять заказы"},
    {"name": "Экспорт заказов (Базовый)", "code": "orders_export", "category": "Заказы (Базовые)", "description": "Выгрузка заказов в Excel/CSV"},
    {"name": "Просмотр меню (Базовый)", "code": "menu_view", "category": "Каталог (Базовые)", "description": "Просмотр товаров и категорий"},
    {"name": "Управление меню (Базовый)", "code": "menu_edit", "category": "Каталог (Базовые)", "description": "Создание, редактирование и удаление товаров"},
    {"name": "Синхронизация меню (Базовый)", "code": "menu_sync", "category": "Каталог (Базовые)", "description": "Запуск синхронизации с iiko"},
    {"name": "Просмотр пользователей (Базовый)", "code": "users_view", "category": "Пользователи (Базовые)", "description": "Доступ к списку сотрудников в админке"},
    {"name": "Управление пользователями (Базовый)", "code": "users_edit", "category": "Пользователи (Базовые)", "description": "Создание и редактирование учетных записей"},
    {"name": "Управление ролями (Базовый)", "code": "roles_manage", "category": "Пользователи (Базовые)", "description": "Настройка прав доступа и создание ролей"},
    {"name": "Просмотр клиентов (Базовый)", "code": "customers_view", "category": "Клиенты (Базовые)", "description": "Просмотр базы гостей"},
    {"name": "Редактирование клиентов (Базовый)", "code": "customers_edit", "category": "Клиенты (Базовые)", "description": "Изменение данных гостей и баланса бонусов"},
    {"name": "Просмотр отчетов (Базовый)", "code": "reports_view", "category": "Отчеты (Базовые)", "description": "Общие финансовые отчеты"},
    {"name": "Отчеты курьеров (Базовый)", "code": "courier_reports_view", "category": "Отчеты (Базовые)", "description": "Просмотр логов и статистики курьеров"},
    {"name": "Просмотр настроек (Базовый)", "code": "settings_view", "category": "Настройки (Базовые)", "description": "Доступ к настройкам системы"},
    {"name": "Изменение настроек (Базовый)", "code": "settings_edit", "category": "Настройки (Базовые)", "description": "Редактирование интеграций и параметров сайта"},
    {"name": "Закуп Просмотр (Базовый)", "code": "purchase_view", "category": "Закуп (Базовые)", "description": "Доступ к разделу закупа"},
    {"name": "Закуп Управление (Базовый)", "code": "purchase_manage", "category": "Закуп (Базовые)", "description": "Создание и управление закупками"},
    {"name": "Управление пользователями (Базовый)", "code": "users_manage", "category": "Пользователи (Базовые)", "description": "Глобальное управление пользователями"},

    # --- Новые детальные права ---
    
    # Рабочий стол
    {"name": "Рабочий стол (Просмотр)", "code": "dashboard_view", "category": "Рабочий стол", "description": "Доступ к просмотру рабочего стола"},
    {"name": "Рабочий стол (Редактирование)", "code": "dashboard_edit", "category": "Рабочий стол", "description": "Настройка виджетов рабочего стола"},
    
    # Компании и Филиалы
    {"name": "Мои компании (Просмотр)", "code": "companies_view", "category": "Компании и филиалы", "description": "Просмотр информации о компаниях"},
    {"name": "Мои компании (Редактирование)", "code": "companies_edit", "category": "Компании и филиалы", "description": "Редактирование информации о компаниях"},
    {"name": "Все филиалы (Просмотр)", "code": "branches_view", "category": "Компании и филиалы", "description": "Просмотр списка филиалов"},
    {"name": "Все филиалы (Редактирование)", "code": "branches_edit", "category": "Компании и филиалы", "description": "Редактирование и создание филиалов"},
    {"name": "Зоны доставки (Просмотр)", "code": "zones_view", "category": "Компании и филиалы", "description": "Просмотр зон доставки на карте"},
    {"name": "Зоны доставки (Редактирование)", "code": "zones_edit", "category": "Компании и филиалы", "description": "Управление геозонами доставки"},
    
    # Каталог
    {"name": "Разделы меню (Просмотр)", "code": "menu_categories_view", "category": "Каталог", "description": "Просмотр разделов меню"},
    {"name": "Разделы меню (Редактирование)", "code": "menu_categories_edit", "category": "Каталог", "description": "Создание, изменение и удаление разделов"},
    {"name": "Товары (Просмотр)", "code": "menu_products_view", "category": "Каталог", "description": "Просмотр товаров"},
    {"name": "Товары (Редактирование)", "code": "menu_products_edit", "category": "Каталог", "description": "Создание, изменение и удаление товаров"},
    {"name": "Опции и Модификаторы (Просмотр)", "code": "menu_options_view", "category": "Каталог", "description": "Просмотр опций и групп модификаторов"},
    {"name": "Опции и Модификаторы (Редактирование)", "code": "menu_options_edit", "category": "Каталог", "description": "Редактирование опций и модификаторов"},
    {"name": "Импорт iiko (Просмотр)", "code": "menu_import_view", "category": "Каталог", "description": "Доступ к разделу импорта меню из iiko"},
    {"name": "Импорт iiko (Запуск)", "code": "menu_import_edit", "category": "Каталог", "description": "Запуск принудительного импорта данных из iiko"},
    
    # Курьеры
    {"name": "Мониторинг курьеров (Просмотр)", "code": "courier_view", "category": "Курьеры", "description": "Просмотр карты и статусов курьеров"},
    {"name": "Мониторинг курьеров (Управление)", "code": "courier_edit", "category": "Курьеры", "description": "Назначение курьеров на заказы и управление сменами"},
    {"name": "Отображать неназначенные доставки", "code": "courier_view_unassigned", "category": "Курьеры", "description": "Показывать заказы без назначенного курьера"},
    {"name": "Отображать только свои доставки", "code": "courier_view_assigned_self", "category": "Курьеры", "description": "Показывать доставки, назначенные на текущего курьера"},
    {"name": "Отображать все доставки всех курьеров", "code": "courier_view_assigned_all", "category": "Курьеры", "description": "Показывать все доставки всех курьеров"},
    
    # Клиенты
    {"name": "База гостей (Просмотр)", "code": "clients_view", "category": "Клиенты", "description": "Просмотр списка клиентов"},
    {"name": "База гостей (Редактирование)", "code": "clients_edit", "category": "Клиенты", "description": "Редактирование анкеты клиентов и управление метками"},
    {"name": "Карточка: Анкета (Просмотр)", "code": "customer_tab_profile_view", "category": "Карточка клиента", "description": "Просмотр вкладки Анкета в карточке гостя"},
    {"name": "Карточка: Анкета (Редактирование)", "code": "customer_tab_profile_edit", "category": "Карточка клиента", "description": "Изменение ФИО, телефона и категорий гостя"},
    {"name": "Карточка: Бонусы (Просмотр)", "code": "customer_tab_bonuses_view", "category": "Карточка клиента", "description": "Просмотр бонусного баланса и истории начислений"},
    {"name": "Карточка: Бонусы (Начисление/Списание)", "code": "customer_tab_bonuses_edit", "category": "Карточка клиента", "description": "Ручное начисление и списание бонусов гостю"},
    {"name": "Карточка: Заказы (Просмотр)", "code": "customer_tab_orders_view", "category": "Карточка клиента", "description": "Просмотр истории заказов гостя"},
    {"name": "Карточка: Аналитика (Просмотр)", "code": "customer_tab_analytics_view", "category": "Карточка клиента", "description": "Просмотр аналитики LTV и среднего чека гостя"},
    {"name": "Карточка: Риски (Просмотр)", "code": "customer_tab_risks_view", "category": "Карточка клиента", "description": "Просмотр группы риска гостя"},
    {"name": "Карточка: Риски (Редактирование)", "code": "customer_tab_risks_edit", "category": "Карточка клиента", "description": "Изменение группы риска и указание причины"},
    {"name": "Карточка: Адреса (Просмотр)", "code": "customer_tab_addresses_view", "category": "Карточка клиента", "description": "Просмотр адресов доставки гостя"},
    {"name": "Карточка: Адреса (Редактирование)", "code": "customer_tab_addresses_edit", "category": "Карточка клиента", "description": "Редактирование, удаление и добавление адресов гостя"},
    {"name": "Карточка: Инфо/Рассылки (Просмотр)", "code": "customer_tab_notifications_view", "category": "Карточка клиента", "description": "Просмотр маркетинговых согласий гостя"},
    {"name": "Карточка: Инфо/Рассылки (Редактирование)", "code": "customer_tab_notifications_edit", "category": "Карточка клиента", "description": "Изменение маркетинговых согласий гостя"},
    {"name": "Карточка: Локальные заказы (Просмотр)", "code": "customer_tab_local_orders_view", "category": "Карточка клиента", "description": "Просмотр локальных заказов гостя"},
    {"name": "Карточка: Социальные сети (Просмотр)", "code": "customer_tab_socials_view", "category": "Карточка клиента", "description": "Просмотр привязанных соцсетей гостя"},
    {"name": "Карточка: Социальные сети (Управление)", "code": "customer_tab_socials_edit", "category": "Карточка клиента", "description": "Отвязка и блокировка рассылок в соцсетях гостя"},
    {"name": "Карточка: Лог (Просмотр)", "code": "customer_tab_extra_view", "category": "Карточка клиента", "description": "Просмотр лога изменений гостя"},
    
    # Закуп
    {"name": "Списки закупа (Просмотр)", "code": "purchase_lists_view", "category": "Закуп", "description": "Просмотр списков закупленных товаров"},
    {"name": "Списки закупа (Редактирование)", "code": "purchase_lists_edit", "category": "Закуп", "description": "Создание, изменение, отправка и удаление списков закупа"},
    {"name": "Справочники закупа (Просмотр)", "code": "purchase_positions_view", "category": "Закуп", "description": "Просмотр справочников товаров и поставщиков"},
    {"name": "Справочники закупа (Редактирование)", "code": "purchase_positions_edit", "category": "Закуп", "description": "Редактирование справочников позиций, поставщиков и подкатегорий"},
    {"name": "Закуп: Вкладка Магазин (Просмотр)", "code": "purchase_tab_shop_view", "category": "Закуп (Вкладки)", "description": "Доступ к закупам направления Магазин"},
    {"name": "Закуп: Вкладка Магазин (Редактирование)", "code": "purchase_tab_shop_edit", "category": "Закуп (Вкладки)", "description": "Редактирование закупов направления Магазин"},
    {"name": "Закуп: Вкладка Хозка (Просмотр)", "code": "purchase_tab_household_view", "category": "Закуп (Вкладки)", "description": "Доступ к закупам направления Хозка"},
    {"name": "Закуп: Вкладка Хозка (Редактирование)", "code": "purchase_tab_household_edit", "category": "Закуп (Вкладки)", "description": "Редактирование закупов направления Хозка"},
    {"name": "Закуп: Вкладка Поставки (Просмотр)", "code": "purchase_tab_supply_view", "category": "Закуп (Вкладки)", "description": "Доступ к закупам направления Поставки"},
    {"name": "Закуп: Вкладка Поставки (Редактирование)", "code": "purchase_tab_supply_edit", "category": "Закуп (Вкладки)", "description": "Редактирование закупов направления Поставки"},
    {"name": "Справочники: Позиции (Просмотр)", "code": "purchase_positions_tab_positions_view", "category": "Закуп (Справочники)", "description": "Просмотр позиций закупа в справочниках"},
    {"name": "Справочники: Позиции (Редактирование)", "code": "purchase_positions_tab_positions_edit", "category": "Закуп (Справочники)", "description": "Управление позициями закупа"},
    {"name": "Справочники: Поставщики (Просмотр)", "code": "purchase_positions_tab_suppliers_view", "category": "Закуп (Справочники)", "description": "Просмотр поставщиков в справочниках"},
    {"name": "Справочники: Поставщики (Редактирование)", "code": "purchase_positions_tab_suppliers_edit", "category": "Закуп (Справочники)", "description": "Управление поставщиками"},
    {"name": "Справочники: Подкатегории (Просмотр)", "code": "purchase_positions_tab_subcategories_view", "category": "Закуп (Справочники)", "description": "Просмотр подкатегорий закупа"},
    {"name": "Справочники: Подкатегории (Редактирование)", "code": "purchase_positions_tab_subcategories_edit", "category": "Закуп (Справочники)", "description": "Управление подкатегориями закупа"},
    
    # Отзывы и NPS
    {"name": "Отзывы клиентов (Просмотр)", "code": "nps_reviews_view", "category": "Отзывы и NPS", "description": "Просмотр отзывов гостей"},
    {"name": "Отзывы клиентов (Редактирование)", "code": "nps_reviews_edit", "category": "Отзывы и NPS", "description": "Ответы на отзывы и удаление отзывов"},
    {"name": "Оценка блюд (Просмотр)", "code": "nps_dishes_view", "category": "Отзывы и NPS", "description": "Просмотр оценок по блюдам"},
    {"name": "Оценка блюд (Редактирование)", "code": "nps_dishes_edit", "category": "Отзывы и NPS", "description": "Управление оценками блюд"},
    {"name": "Аналитика NPS (Просмотр)", "code": "nps_analytics_view", "category": "Отзывы и NPS", "description": "Просмотр аналитики NPS"},
    {"name": "Аналитика NPS (Редактирование)", "code": "nps_analytics_edit", "category": "Отзывы и NPS", "description": "Сброс или пересчет аналитики NPS"},
    
    # Акции и Лояльность
    {"name": "Контентная информация (Просмотр)", "code": "promotions_content_view", "category": "Акции и Лояльность", "description": "Просмотр баннеров и промо-страниц"},
    {"name": "Контентная информация (Редактирование)", "code": "promotions_content_edit", "category": "Акции и Лояльность", "description": "Редактирование баннеров и промо-акций"},
    {"name": "Шкала подарков (Просмотр)", "code": "promotions_scale_view", "category": "Акции и Лояльность", "description": "Просмотр уровней подарков в корзине"},
    {"name": "Шкала подарков (Редактирование)", "code": "promotions_scale_edit", "category": "Акции и Лояльность", "description": "Редактирование уровней и условий выдачи подарков"},
    {"name": "Истории (Просмотр)", "code": "marketing_stories_view", "category": "Акции и Лояльность", "description": "Просмотр историй (Stories) в приложении"},
    {"name": "Истории (Редактирование)", "code": "marketing_stories_edit", "category": "Акции и Лояльность", "description": "Создание, редактирование и удаление историй"},
    {"name": "Промокоды (Просмотр)", "code": "promo_codes_view", "category": "Акции и Лояльность", "description": "Просмотр списка промокодов"},
    {"name": "Промокоды (Редактирование)", "code": "promo_codes_edit", "category": "Акции и Лояльность", "description": "Создание, удаление и активация промокодов"},
    {"name": "Воронки (Просмотр)", "code": "marketing_funnels_view", "category": "Акции и Лояльность", "description": "Просмотр воронок вовлеченности"},
    {"name": "Воронки (Редактирование)", "code": "marketing_funnels_edit", "category": "Акции и Лояльность", "description": "Управление шагами воронок вовлеченности"},
    {"name": "Программа лояльности (Просмотр)", "code": "loyalty_view", "category": "Акции и Лояльность", "description": "Просмотр настроек лояльности"},
    {"name": "Программа лояльности (Редактирование)", "code": "loyalty_edit", "category": "Акции и Лояльность", "description": "Изменение правил начисления бонусов"},
    {"name": "Боты ВКонтакте (Просмотр)", "code": "marketing_vk_bots_view", "category": "Акции и Лояльность", "description": "Просмотр настроек ботов ВКонтакте (Именинники)"},
    {"name": "Боты ВКонтакте (Редактирование)", "code": "marketing_vk_bots_edit", "category": "Акции и Лояльность", "description": "Управление и изменение настроек ботов ВКонтакте"},
    
    # Рассылки
    {"name": "Общие рассылки (Просмотр)", "code": "mailings_general_view", "category": "Рассылки", "description": "Просмотр истории рассылок гостям"},
    {"name": "Общие рассылки (Создание)", "code": "mailings_general_edit", "category": "Рассылки", "description": "Создание и запуск массовых рассылок гостям"},
    {"name": "Настройки Telegram Бота (Просмотр)", "code": "settings_bot_view", "category": "Рассылки", "description": "Просмотр токена и настроек Telegram бота"},
    {"name": "Настройки Telegram Бота (Редактирование)", "code": "settings_bot_edit", "category": "Рассылки", "description": "Изменение токена и параметров Telegram бота"},
    {"name": "Настройки VK Бота (Просмотр)", "code": "settings_vk_view", "category": "Рассылки", "description": "Просмотр настроек подключений VK-ботов"},
    {"name": "Настройки VK Бота (Редактирование)", "code": "settings_vk_edit", "category": "Рассылки", "description": "Управление подключениями VK-ботов и запуск сканирования"},
    {"name": "Системные рассылки (Просмотр)", "code": "settings_vk_notifications_view", "category": "Рассылки", "description": "Просмотр получателей и настроек системных рассылок"},
    {"name": "Системные рассылки (Редактирование)", "code": "settings_vk_notifications_edit", "category": "Рассылки", "description": "Управление получателями, подписками и шаблонами рассылок"},
    {"name": "Парсер ВК (Просмотр)", "code": "settings_vk_parser_view", "category": "Рассылки", "description": "Просмотр настроек парсера ВК и мониторинга"},
    {"name": "Парсер ВК (Редактирование)", "code": "settings_vk_parser_edit", "category": "Рассылки", "description": "Редактирование фразы парсинга, маски, отвязка аккаунтов"},
    {"name": "Настройка MAX (Просмотр)", "code": "settings_max_view", "category": "Рассылки", "description": "Просмотр API-ключей и настроек ботов MAX"},
    {"name": "Настройка MAX (Редактирование)", "code": "settings_max_edit", "category": "Рассылки", "description": "Изменение API-ключей и создание ботов в MAX"},
    {"name": "Уведомления и рассылки - Каскады (Просмотр)", "code": "mailings_cascades_view", "category": "Рассылки", "description": "Просмотр каскадов рассылок"},
    {"name": "Уведомления и рассылки - Каскады (Редактирование)", "code": "mailings_cascades_edit", "category": "Рассылки", "description": "Создание, изменение и удаление шагов каскада"},
    {"name": "Команды ботов (Просмотр)", "code": "settings_bot_commands_view", "category": "Рассылки", "description": "Просмотр списка команд ботов"},
    {"name": "Команды ботов (Редактирование)", "code": "settings_bot_commands_edit", "category": "Рассылки", "description": "Редактирование текстов ответов команд ботов"},
    {"name": "Интеграция Senler (Просмотр)", "code": "settings_senler_view", "category": "Рассылки", "description": "Просмотр настроек, подписчиков и статистики Senler"},
    {"name": "Интеграция Senler (Редактирование)", "code": "settings_senler_edit", "category": "Рассылки", "description": "Изменение токена Senler, принудительный импорт и создание рассылок"},
    {"name": "Парсер ВК: Таб Настройки (Просмотр)", "code": "vk_parser_tab_settings_view", "category": "Рассылки (Парсер)", "description": "Вкладка Настройки и статистика"},
    {"name": "Парсер ВК: Таб Настройки (Редактирование)", "code": "vk_parser_tab_settings_edit", "category": "Рассылки (Парсер)", "description": "Изменение фразы и маски заказа"},
    {"name": "Парсер ВК: Таб Уведомления (Просмотр)", "code": "vk_parser_tab_notifications_view", "category": "Рассылки (Парсер)", "description": "Вкладка Настройка уведомлений ВК"},
    {"name": "Парсер ВК: Таб Уведомления (Редактирование)", "code": "vk_parser_tab_notifications_edit", "category": "Рассылки (Парсер)", "description": "Изменение шаблонов по статусам заказа"},
    {"name": "Парсер ВК: Таб Мониторинг (Просмотр)", "code": "vk_parser_tab_monitoring_view", "category": "Рассылки (Парсер)", "description": "Вкладка Мониторинг сообщений"},
    {"name": "Парсер ВК: Таб Мониторинг (Управление)", "code": "vk_parser_tab_monitoring_edit", "category": "Рассылки (Парсер)", "description": "Очистка сообщений и сканирование"},
    {"name": "Парсер ВК: Таб Связанные (Просмотр)", "code": "vk_parser_tab_accounts_view", "category": "Рассылки (Парсер)", "description": "Вкладка Связанные аккаунты ВК"},
    {"name": "Парсер ВК: Таб Связанные (Управление)", "code": "vk_parser_tab_accounts_edit", "category": "Рассылки (Парсер)", "description": "Удаление привязки и блокировка рассылок"},
    
    # Операции банка
    {"name": "Входящие платежи (Просмотр)", "code": "bank_payments_view", "category": "Операции банка", "description": "Просмотр списка входящих банковских оплат"},
    {"name": "Входящие платежи (Редактирование)", "code": "bank_payments_edit", "category": "Операции банка", "description": "Ручное сопоставление платежей с заказами"},
    {"name": "Монитор Т-Банк (Просмотр)", "code": "bank_tbank_payments_view", "category": "Операции банка", "description": "Просмотр LIVE монитора Т-Банка"},
    {"name": "Монитор Т-Банк (Редактирование)", "code": "bank_tbank_payments_edit", "category": "Операции банка", "description": "Запуск ручной синхронизации выписок"},
    
    # Система
    {"name": "Мониторинг сервера (Просмотр)", "code": "system_server_view", "category": "Система", "description": "Просмотр метрик CPU, RAM и диска"},
    {"name": "Метки клиентов (Просмотр)", "code": "system_tags_view", "category": "Система", "description": "Просмотр справочника меток клиентов"},
    {"name": "Метки клиентов (Редактирование)", "code": "system_tags_edit", "category": "Система", "description": "Управление метками клиентов (создание, удаление)"},
    {"name": "Настройки iiko (Просмотр)", "code": "settings_iiko_view", "category": "Система", "description": "Просмотр API ключей и настроек организации iiko"},
    {"name": "Настройки iiko (Редактирование)", "code": "settings_iiko_edit", "category": "Система", "description": "Изменение настроек интеграции с iiko"},
    {"name": "Логи синхронизации (Просмотр)", "code": "settings_sync_logs_view", "category": "Система", "description": "Просмотр истории синхронизации гостей"},
    {"name": "Настройки Яндекс (Просмотр)", "code": "settings_yandex_view", "category": "Система", "description": "Просмотр настроек интеграции с Яндекс Картами"},
    {"name": "Настройки Яндекс (Редактирование)", "code": "settings_yandex_edit", "category": "Система", "description": "Изменение API ключей Яндекс"},
    {"name": "Настройки T-API (Просмотр)", "code": "settings_tbank_view", "category": "Система", "description": "Просмотр настроек интеграции с Т-Банк API"},
    {"name": "Настройки T-API (Редактирование)", "code": "settings_tbank_edit", "category": "Система", "description": "Изменение настроек терминалов Т-Банка"},
    {"name": "Интеграция с Mango (Просмотр)", "code": "settings_mango_view", "category": "Система", "description": "Просмотр настроек Mango Office и журнала звонков"},
    {"name": "Интеграция с Mango (Редактирование)", "code": "settings_mango_edit", "category": "Система", "description": "Изменение настроек Mango, звонки из CRM и записи разговоров"},
    {"name": "Настройки уведомлений (Просмотр)", "code": "settings_notifications_view", "category": "Система", "description": "Просмотр настроек звуков и Web Push"},
    {"name": "Настройки уведомлений (Редактирование)", "code": "settings_notifications_edit", "category": "Система", "description": "Изменение звуков, ключей VAPID и подписка на Web Push"},
    {"name": "Фоновые процессы (Просмотр)", "code": "system_tasks_view", "category": "Система", "description": "Просмотр списка фоновых задач Celery"},
    {"name": "Фоновые процессы (Управление)", "code": "system_tasks_edit", "category": "Система", "description": "Пауза, запуск и отмена задач Celery"},
    {"name": "Логи системы (Просмотр)", "code": "system_logs_view", "category": "Система", "description": "Просмотр технических логов ошибок бэкенда"},
    {"name": "Настройки валидации (Просмотр)", "code": "settings_validation_view", "category": "Система", "description": "Просмотр настроек валидации телефонов"},
    {"name": "Настройки валидации (Редактирование)", "code": "settings_validation_edit", "category": "Система", "description": "Изменение настроек валидации и тестирование отправки"},
    
    # Кухня
    {"name": "Кухня: Техкарты (Просмотр)", "code": "kitchen_recipes_view", "category": "Кухня", "description": "Просмотр каталога техкарт и печать"},
    {"name": "Кухня: Техкарты (Редактирование)", "code": "kitchen_recipes_edit", "category": "Кухня", "description": "Создание, редактирование и синхронизация техкарт"},
    {"name": "Кухня: Экран повара (Просмотр)", "code": "kitchen_screen_view", "category": "Кухня", "description": "Просмотр экрана повара и распределение заказов"},
    {"name": "Кухня: Экран повара (Управление)", "code": "kitchen_screen_edit", "category": "Кухня", "description": "Изменение статусов приготовления блюд (начать готовить, приготовлено)"},
    {"name": "Кухня: Управление зонами", "code": "kitchen_zones_manage", "category": "Кухня", "description": "Создание, изменение и удаление зон приготовления блюд"},

    # Администрирование
    {"name": "Список сотрудников (Просмотр)", "code": "employees_view", "category": "Администрирование", "description": "Просмотр списка сотрудников организации"},
    {"name": "Список сотрудников (Редактирование)", "code": "employees_edit", "category": "Администрирование", "description": "Редактирование данных сотрудников"},
    {"name": "Список пользователей (Просмотр)", "code": "users_view", "category": "Администрирование", "description": "Просмотр списка пользователей админки"},
    {"name": "Список пользователей (Редактирование)", "code": "users_edit", "category": "Администрирование", "description": "Создание, удаление и редактирование пользователей"},
    {"name": "Управление ролями (Просмотр)", "code": "roles_view", "category": "Администрирование", "description": "Просмотр списка ролей доступа"},
    {"name": "Управление ролями (Редактирование)", "code": "roles_edit", "category": "Администрирование", "description": "Создание ролей, изменение и привязка прав доступа"},
    {"name": "Мультичат (Просмотр)", "code": "multichat_view", "category": "Мультичат", "description": "Просмотр всех чатов и переписки"},
    {"name": "Мультичат (Отправка)", "code": "multichat_edit", "category": "Мультичат", "description": "Отправка сообщений в чаты"},
    {"name": "Мультичат (Управление аккаунтами)", "code": "multichat_accounts_manage", "category": "Мультичат", "description": "Добавление, подключение и удаление личных аккаунтов ВКонтакте, Telegram, MAX"},
]

def seed_rbac():
    with Session(engine) as session:
        print("Starting RBAC seeding with granular permissions...")
        
        # 1. Добавление прав
        db_permissions = []
        for p_data in PERMISSIONS:
            existing = session.exec(select(Permission).where(Permission.code == p_data["code"])).first()
            if not existing:
                p = Permission(**p_data)
                session.add(p)
                db_permissions.append(p)
                print(f"Created permission: {p.code}")
            else:
                existing.name = p_data["name"]
                existing.category = p_data["category"]
                existing.description = p_data["description"]
                session.add(existing)
                db_permissions.append(existing)
        
        session.commit()
        for p in db_permissions:
            session.refresh(p)
            
        # 2. Создание системных ролей
        admin_role = session.exec(select(Role).where(Role.code == "SUPER_ADMIN")).first()
        if not admin_role:
            admin_role = Role(
                name="Администратор",
                code="SUPER_ADMIN",
                description="Полный доступ ко всем функциям системы",
                is_system=True
            )
            session.add(admin_role)
            print("Created SUPER_ADMIN role")
        else:
            admin_role.is_system = True
            session.add(admin_role)
            
        session.commit()
        session.refresh(admin_role)
        
        # Привязка всех прав к администратору
        admin_role.permissions = db_permissions
        session.add(admin_role)
        session.commit()
        print(f"Assigned {len(db_permissions)} permissions to SUPER_ADMIN")
        
        # 3. Привязка дефолтного пользователя к роли
        default_user = session.exec(select(User).where(User.username == "0001")).first()
        if default_user:
            default_user.role_id = admin_role.id
            default_user.is_superuser = True
            session.add(default_user)
            session.commit()
            print("Assigned user '0001' to SUPER_ADMIN role")
        
        print("RBAC seeding completed successfully!")

if __name__ == "__main__":
    seed_rbac()
