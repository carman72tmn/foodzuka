<script setup>
import { ref, onMounted, computed } from 'vue'
import { authState, getAuthHeaders } from '@/utils/auth.js'

const roles = ref([])
const permissions = ref([])
const loading = ref(true)
const isDialogVisible = ref(false)
const isPermissionDialogVisible = ref(false)
const isViewPermissionsDialogVisible = ref(false)
const isDeleting = ref(false)
const deleteDialog = ref(false)
const roleToDelete = ref(null)

// Фильтры и поиск в диалоге настройки прав
const permSearchQuery = ref('')
const permFilterMode = ref('all') // 'all' | 'active' | 'inactive'
const expandedPanels = ref([])

// Поиск в диалоге просмотра действующих прав
const viewPermSearchQuery = ref('')

const headers = [
  { title: 'Название', key: 'name' },
  { title: 'Код', key: 'code' },
  { title: 'Системная', key: 'is_system' },
  { title: 'Главная страница', key: 'default_page' },
  { title: 'Действующие права', key: 'permissions_count' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' },
]

const editedItem = ref({
  id: null,
  name: '',
  code: '',
  description: '',
  default_page: null,
})

const defaultItem = {
  id: null,
  name: '',
  code: '',
  description: '',
  default_page: null,
}

const defaultPageOptions = [
  { title: 'Рабочий стол', value: '/dashboard' },
  { title: 'Уведомления (Центр событий)', value: '/notifications-feed' },
  { title: 'Заказы', value: '/orders' },
  { title: 'Мультичат', value: '/multichat' },
  { title: 'Курьеры', value: '/courier' },
  { title: 'Все клиенты', value: '/clients' },
  { title: 'Списки закупа', value: '/purchase' },
  { title: 'Позиции закупа', value: '/purchase/positions' },
  { title: 'Мои компании', value: '/companies' },
  { title: 'Все филиалы', value: '/branches' },
  { title: 'Зоны доставки', value: '/branches/zones' },
  { title: 'Разделы меню', value: '/menu/categories' },
  { title: 'Товары', value: '/menu/products' },
  { title: 'Опции и Модификаторы', value: '/menu/options' },
  { title: 'Импорт из iiko', value: '/menu/import' },
  { title: 'Отзывы клиентов', value: '/nps/reviews' },
  { title: 'Оценка блюд', value: '/nps/dishes' },
  { title: 'Аналитика NPS', value: '/nps/analytics' },
  { title: 'Контентная информация акций', value: '/promotions/content' },
  { title: 'Шкала подарков', value: '/promotions/scale' },
  { title: 'Истории (Stories)', value: '/marketing/stories' },
  { title: 'Промокоды', value: '/promo' },
  { title: 'Воронки вовлеченности', value: '/marketing/funnels' },
  { title: 'Программа лояльности', value: '/loyalty' },
  { title: 'Боты ВКонтакте и MAX', value: '/marketing/vk-bots' },
  { title: 'Автопостинг ВКонтакте', value: '/marketing/group-posting' },
  { title: 'Планировщик постов ВК', value: '/marketing/vk-scheduler' },
  { title: 'Общие рассылки', value: '/marketing/mailings' },
  { title: 'Настройки Telegram Бота', value: '/settings/bot' },
  { title: 'Настройки VK Бота', value: '/settings/vk' },
  { title: 'Системные рассылки', value: '/settings/vk-notifications' },
  { title: 'Парсер ВК', value: '/settings/vk-parser' },
  { title: 'Интеграция Senler', value: '/settings/senler' },
  { title: 'Настройка MAX', value: '/settings/max' },
  { title: 'Уведомления и рассылки (каскады)', value: '/mailings/cascades' },
  { title: 'Команды ботов', value: '/settings/bot-commands' },
  { title: 'Входящие платежи', value: '/bank/payments' },
  { title: 'Монитор Т-Банка', value: '/bank/tbank-payments' },
  { title: 'Агенты ИИ', value: '/settings/ai-agents' },
  { title: 'Мониторинг сервера', value: '/system/server' },
  { title: 'Метки клиентов', value: '/system/tags' },
  { title: 'Настройки iiko', value: '/settings/iiko' },
  { title: 'Логи синхронизации', value: '/settings/sync-logs' },
  { title: 'Настройки Яндекс', value: '/settings/yandex' },
  { title: 'Настройки T-API', value: '/settings/tbank' },
  { title: 'Интеграция с Mango', value: '/settings/mango' },
  { title: 'Настройки уведомлений', value: '/settings/notifications' },
  { title: 'Фоновые процессы (Celery)', value: '/system/tasks' },
  { title: 'Логи системы', value: '/system/logs' },
  { title: 'Отчет: Выручка', value: '/reports/revenue' },
  { title: 'Отчет: Продажи', value: '/reports/sales' },
  { title: 'Отчет: Продажи (по товарам)', value: '/reports/products' },
  { title: 'Отчет: Продажи (по дням)', value: '/reports/days' },
  { title: 'Отчет: Клиенты', value: '/reports/clients' },
  { title: 'Отчет: Заказы', value: '/reports/orders' },
  { title: 'Отчет: Типы оплат', value: '/reports/payments' },
  { title: 'Список сотрудников', value: '/employees' },
  { title: 'Список пользователей', value: '/users' },
  { title: 'Настройки аккаунта', value: '/account-settings' },
  { title: 'Кухня: Техкарты', value: '/kitchen/recipes' },
  { title: 'Кухня: Экран повара', value: '/kitchen/screen' }
]

const selectedRole = ref(null)
const selectedPermissions = ref([])

const formTitle = computed(() => editedItem.value.id ? 'Редактировать роль' : 'Новая роль')

// Структурированная схема группировки прав по пунктам меню, вкладкам и сущностям
const permissionGroups = [
  {
    title: 'Рабочий стол',
    icon: 'ri-dashboard-line',
    items: [
      { title: 'Рабочий стол', viewCode: 'dashboard_view', editCode: 'dashboard_edit', description: 'Отображение сводной статистики, виджетов и графиков на главном экране' }
    ]
  },
  {
    title: 'Центр уведомлений',
    icon: 'ri-notification-3-line',
    items: [
      { 
        title: 'Живая лента событий', 
        viewCode: 'notifications_feed_view', 
        editCode: 'notifications_feed_edit', 
        description: 'Доступ к интерактивной ленте заказов, смены статусов, оплат Т-Банка и сообщений ВК/MAX (Просмотр) / Управление и отметка прочитанными (Редактирование)' 
      }
    ]
  },
  {
    title: 'Заказы',
    icon: 'ri-shopping-cart-2-line',
    items: [
      { title: 'Управление заказами', viewCode: 'orders_view', editCode: 'orders_edit', description: 'Просмотр списка входящих заказов, изменение статусов, состава и адреса доставки' },
      { title: 'Удаление заказов', viewCode: 'orders_delete', description: 'Право на полное удаление или отмену заказов в системе' },
      { title: 'Экспорт заказов', viewCode: 'orders_export', description: 'Возможность выгрузки списка заказов в форматы Excel и CSV' }
    ]
  },
  {
    title: 'Курьеры',
    icon: 'ri-e-bike-2-line',
    items: [
      { title: 'Мониторинг курьеров', viewCode: 'courier_view', editCode: 'courier_edit', description: 'Карта курьеров, управление сменами, назначение курьеров на заказы' },
      { title: 'Отображать неназначенные доставки', viewCode: 'courier_view_unassigned', description: 'Разрешить курьерам видеть и брать свободные заказы без назначенного курьера' },
      { title: 'Отображать только свои доставки', viewCode: 'courier_view_assigned_self', description: 'Показывать только те доставки, которые назначены на текущего курьера' },
      { title: 'Отображать все доставки всех курьеров', viewCode: 'courier_view_assigned_all', description: 'Показывать общую картину по всем активным курьерам и доставкам' }
    ]
  },
  {
    title: 'Клиенты (База гостей)',
    icon: 'ri-group-line',
    items: [
      { title: 'Список клиентов', viewCode: 'clients_view', editCode: 'clients_edit', description: 'Просмотр реестра зарегистрированных гостей, добавление меток и фильтрация' },
      { title: 'Карточка: Анкета', viewCode: 'customer_tab_profile_view', editCode: 'customer_tab_profile_edit', description: 'Просмотр и изменение личных данных гостя (ФИО, телефон, дата рождения)' },
      { title: 'Карточка: Бонусы', viewCode: 'customer_tab_bonuses_view', editCode: 'customer_tab_bonuses_edit', description: 'Просмотр баланса бонусов и ручное начисление/списание баллов' },
      { title: 'Карточка: История заказов', viewCode: 'customer_tab_orders_view', description: 'Просмотр истории всех заказов гостя через сайт и приложение' },
      { title: 'Карточка: Аналитика LTV', viewCode: 'customer_tab_analytics_view', description: 'Просмотр финансовых показателей гостя, среднего чека и LTV' },
      { title: 'Карточка: Группы риска', viewCode: 'customer_tab_risks_view', editCode: 'customer_tab_risks_edit', description: 'Просмотр и изменение группы лояльности/риска гостя' },
      { title: 'Карточка: Адреса доставки', viewCode: 'customer_tab_addresses_view', editCode: 'customer_tab_addresses_edit', description: 'Просмотр, добавление и удаление адресов доставки клиента' },
      { title: 'Карточка: Инфо и Рассылки', viewCode: 'customer_tab_notifications_view', editCode: 'customer_tab_notifications_edit', description: 'Просмотр и изменение согласий на получение уведомлений' },
      { title: 'Карточка: Локальные заказы', viewCode: 'customer_tab_local_orders_view', description: 'Просмотр локальных покупок клиента в ресторанах' },
      { title: 'Карточка: Социальные сети', viewCode: 'customer_tab_socials_view', editCode: 'customer_tab_socials_edit', description: 'Просмотр привязанных профилей VK/Telegram, отвязка аккаунтов' },
      { title: 'Карточка: Системный лог', viewCode: 'customer_tab_extra_view', description: 'Просмотр истории изменений анкеты гостя администраторами' }
    ]
  },
  {
    title: 'Мультичат',
    icon: 'ri-chat-3-line',
    items: [
      { 
        title: 'Мультичат (Диалоги и Сообщения)', 
        viewCode: 'multichat_view', 
        editCode: 'multichat_edit', 
        description: 'Доступ и чтение переписки в Мультичате (Просмотр) / Отправка сообщений и управление метками (Редактирование)' 
      },
      { 
        title: 'Подключение личных аккаунтов', 
        viewCode: 'multichat_accounts_manage', 
        description: 'Подключение, сопряжение по QR-коду и удаление личных аккаунтов WhatsApp, Telegram, ВКонтакте, MAX' 
      }
    ]
  },
  {
    title: 'Акции и Маркетинговые боты',
    icon: 'ri-gift-line',
    items: [
      { 
        title: 'Боты ВКонтакте и MAX', 
        viewCode: 'marketing_vk_bots_view', 
        editCode: 'marketing_vk_bots_edit', 
        description: 'Управление 6 автоворонками: Каталог, Retention, NPS, Колесо фортуны, Умные рассылки, Реферальная программа' 
      },
      { 
        title: 'Канал MAX (Личный номер)', 
        viewCode: 'marketing_bots_max_manage', 
        description: 'Настройка отправки сообщений в мессенджер MAX от личного номера Web Bridge, лимитов и шаблонов' 
      },
      { 
        title: 'Автопостинг ВКонтакте', 
        viewCode: 'marketing_group_posting_view', 
        editCode: 'marketing_group_posting_edit', 
        description: 'Публикация записей и розыгрышей на стену сообществ ВКонтакте' 
      },
      { 
        title: 'Планировщик публикаций ВК', 
        viewCode: 'marketing_vk_scheduler_view', 
        editCode: 'marketing_vk_scheduler_edit', 
        description: 'Календарь контент-плана и автопубликация постов по расписанию' 
      },
      { title: 'Контентная информация', viewCode: 'promotions_content_view', editCode: 'promotions_content_edit', description: 'Управление баннерами акций, текстами и условиями спецпредложений' },
      { title: 'Шкала подарков', viewCode: 'promotions_scale_view', editCode: 'promotions_scale_edit', description: 'Настройка подарков в корзине в зависимости от суммы заказа' },
      { title: 'Истории (Stories)', viewCode: 'marketing_stories_view', editCode: 'marketing_stories_edit', description: 'Создание и редактирование историй (Stories) для мобильного приложения' },
      { title: 'Промокоды', viewCode: 'promo_codes_view', editCode: 'promo_codes_edit', description: 'Генерация промокодов, настройка скидок и ограничений по ним' },
      { title: 'Воронки вовлеченности', viewCode: 'marketing_funnels_view', editCode: 'marketing_funnels_edit', description: 'Анализ шагов воронки продаж и активности пользователей' },
      { title: 'Программа лояльности', viewCode: 'loyalty_view', editCode: 'loyalty_edit', description: 'Настройка процента кешбэка, правил начисления и списания бонусов' }
    ]
  },
  {
    title: 'Рассылки и Боты',
    icon: 'ri-mail-send-line',
    items: [
      { title: 'Общие рассылки', viewCode: 'mailings_general_view', editCode: 'mailings_general_edit', description: 'Создание и отправка массовых пуш/смс рассылок по сегментам гостей' },
      { title: 'Каскады рассылок', viewCode: 'mailings_cascades_view', editCode: 'mailings_cascades_edit', description: 'Настройка цепочек отправки сообщений (например: push -> vk -> sms)' },
      { title: 'Настройки Telegram бота', viewCode: 'settings_bot_view', editCode: 'settings_bot_edit', description: 'Просмотр и изменение токена бота Telegram и параметров запуска' },
      { title: 'Настройки VK ботов', viewCode: 'settings_vk_view', editCode: 'settings_vk_edit', description: 'Управление токенами и подключениями сообществ ВКонтакте' },
      { title: 'Системные рассылки сотрудникам', viewCode: 'settings_vk_notifications_view', editCode: 'settings_vk_notifications_edit', description: 'Настройка рассылок уведомлений о заказах и сменах для сотрудников в VK' },
      { title: 'Интеграция MAX', viewCode: 'settings_max_view', editCode: 'settings_max_edit', description: 'Настройка интеграции с платформой автоматизации рассылок MAX' },
      { title: 'Команды ботов', viewCode: 'settings_bot_commands_view', editCode: 'settings_bot_commands_edit', description: 'Редактирование автоматических текстовых ответов и команд ботов' },
      { title: 'Интеграция Senler', viewCode: 'settings_senler_view', editCode: 'settings_senler_edit', description: 'Настройки токенов и группы Senler, просмотр подписчиков и статистики рассылок' },
      { title: 'Настройки парсера ВК', viewCode: 'settings_vk_parser_view', editCode: 'settings_vk_parser_edit', description: 'Управление ключевыми фразами парсинга заказов из групп ВК' },
      { title: 'Парсер: Вкладка "Настройки"', viewCode: 'vk_parser_tab_settings_view', editCode: 'vk_parser_tab_settings_edit', description: 'Изменение настроек ключевых фраз парсинга и стоп-слов' },
      { title: 'Парсер: Вкладка "Уведомления"', viewCode: 'vk_parser_tab_notifications_view', editCode: 'vk_parser_tab_notifications_edit', description: 'Редактирование шаблонов ответов клиентам в ВК по статусам' },
      { title: 'Парсер: Вкладка "Мониторинг"', viewCode: 'vk_parser_tab_monitoring_view', editCode: 'vk_parser_tab_monitoring_edit', description: 'Просмотр логов сообщений, запуск сканирования и очистка истории' },
      { title: 'Парсер: Вкладка "Связанные аккаунты"', viewCode: 'vk_parser_tab_accounts_view', editCode: 'vk_parser_tab_accounts_edit', description: 'Просмотр связанных страниц ВКонтакте, ручная отвязка аккаунтов' }
    ]
  },
  {
    title: 'Каталог товаров',
    icon: 'ri-book-open-line',
    items: [
      { title: 'Разделы меню', viewCode: 'menu_categories_view', editCode: 'menu_categories_edit', description: 'Управление категориями и подкатегориями товаров' },
      { title: 'Товары', viewCode: 'menu_products_view', editCode: 'menu_products_edit', description: 'Просмотр списка товаров, цен, описаний и привязка картинок' },
      { title: 'Опции и Модификаторы', viewCode: 'menu_options_view', editCode: 'menu_options_edit', description: 'Просмотр и редактирование групп модификаторов, размеров и опций блюд' },
      { title: 'Импорт из iiko', viewCode: 'menu_import_view', editCode: 'menu_import_edit', description: 'Доступ к синхронизации меню и принудительному обновлению каталога из iiko' }
    ]
  },
  {
    title: 'Кухня',
    icon: 'ri-restaurant-line',
    items: [
      { title: 'Технологические карты', viewCode: 'kitchen_recipes_view', editCode: 'kitchen_recipes_edit', description: 'Доступ к каталогу техкарт блюд, рецептам ингредиентов и печати карточек' },
      { title: 'Экран повара (KDS)', viewCode: 'kitchen_screen_view', editCode: 'kitchen_screen_edit', description: 'Просмотр экрана повара, фильтрация по цехам, запуск и готовность блюд' },
      { title: 'Управление цехами (Зонами)', viewCode: 'kitchen_zones_manage', description: 'Право на создание, редактирование цветов и удаление зон приготовления на кухне' }
    ]
  },
  {
    title: 'Операции банка',
    icon: 'ri-bank-card-line',
    items: [
      { title: 'Входящие платежи', viewCode: 'bank_payments_view', editCode: 'bank_payments_edit', description: 'Просмотр банковских реестров, ручное проведение оплат по заказам' },
      { title: 'Монитор Т-Банка', viewCode: 'bank_tbank_payments_view', editCode: 'bank_tbank_payments_edit', description: 'Мониторинг транзакций Т-Банка в реальном времени, ручной запуск сверки' }
    ]
  },
  {
    title: 'Закупки',
    icon: 'ri-shopping-bag-line',
    items: [
      { title: 'Списки закупа', viewCode: 'purchase_lists_view', editCode: 'purchase_lists_edit', description: 'Просмотр списков потребностей и закупок' },
      { title: 'Справочники закупа', viewCode: 'purchase_positions_view', editCode: 'purchase_positions_edit', description: 'Просмотр и редактирование товаров, поставщиков и подкатегорий закупа' },
      { title: 'Закуп: Вкладка "Магазин"', viewCode: 'purchase_tab_shop_view', editCode: 'purchase_tab_shop_edit', description: 'Просмотр и заведение потребностей направления "Магазин"' },
      { title: 'Закуп: Вкладка "Хозка"', viewCode: 'purchase_tab_household_view', editCode: 'purchase_tab_household_edit', description: 'Просмотр и заведение потребностей направления "Хозка"' },
      { title: 'Закуп: Вкладка "Поставки"', viewCode: 'purchase_tab_supply_view', editCode: 'purchase_tab_supply_edit', description: 'Просмотр и заведение потребностей направления "Поставки"' },
      { title: 'Справочник: Товары закупа', viewCode: 'purchase_positions_tab_positions_view', editCode: 'purchase_positions_tab_positions_edit', description: 'Управление номенклатурой товаров закупа' },
      { title: 'Справочник: Поставщики', viewCode: 'purchase_positions_tab_suppliers_view', editCode: 'purchase_positions_tab_suppliers_edit', description: 'Управление реестром поставщиков товаров закупа' },
      { title: 'Справочник: Подкатегории', viewCode: 'purchase_positions_tab_subcategories_view', editCode: 'purchase_positions_tab_subcategories_edit', description: 'Управление подкатегориями товаров закупа' }
    ]
  },
  {
    title: 'Отзывы и NPS',
    icon: 'ri-star-line',
    items: [
      { title: 'Отзывы клиентов', viewCode: 'nps_reviews_view', editCode: 'nps_reviews_edit', description: 'Просмотр отзывов и оценок о заказах, отправка официальных ответов гостям' },
      { title: 'Оценка блюд', viewCode: 'nps_dishes_view', editCode: 'nps_dishes_edit', description: 'Мониторинг оценок конкретных блюд из меню, скрытие/модерация' },
      { title: 'Аналитика NPS', viewCode: 'nps_analytics_view', editCode: 'nps_analytics_edit', description: 'Графики удовлетворенности клиентов, расчет индекса NPS' }
    ]
  },
  {
    title: 'Компании и филиалы',
    icon: 'ri-building-line',
    items: [
      { title: 'Мои компании', viewCode: 'companies_view', editCode: 'companies_edit', description: 'Просмотр и изменение юридических лиц, реквизитов и настроек компании' },
      { title: 'Все филиалы', viewCode: 'branches_view', editCode: 'branches_edit', description: 'Управление точками продаж, адресами филиалов, временем работы' },
      { title: 'Зоны доставки', viewCode: 'zones_view', editCode: 'zones_edit', description: 'Просмотр и редактирование полигонов доставки на карте' }
    ]
  },
  {
    title: 'Система',
    icon: 'ri-settings-4-line',
    items: [
      { title: 'ИИ Агенты (Чат и Аналитика)', viewCode: 'ai_agents_chat_view', description: 'Доступ к интерактивному окну чата с ИИ агентами в корне меню' },
      { title: 'Агенты ИИ', viewCode: 'settings_ai_agents_view', editCode: 'settings_ai_agents_edit', description: 'Настройка пула прокси, API-ключей Gemini/OpenAI/GigaChat/YandexGPT и ролей агентов' },
      { title: 'Мониторинг сервера', viewCode: 'system_server_view', description: 'Мониторинг ресурсов сервера VPS (CPU, RAM, диск)' },
      { title: 'Фоновые процессы (Celery)', viewCode: 'system_tasks_view', editCode: 'system_tasks_edit', description: 'Просмотр фоновых задач, запуск синхронизаций, перезапуск зависших задач' },
      { title: 'Метки клиентов', viewCode: 'system_tags_view', editCode: 'system_tags_edit', description: 'Управление справочником тегов/меток для сегментации гостей' },
      { title: 'Настройки iiko', viewCode: 'settings_iiko_view', editCode: 'settings_iiko_edit', description: 'Реквизиты интеграции iiko, API-ключи, ID организации' },
      { title: 'Настройки Яндекс Карт', viewCode: 'settings_yandex_view', editCode: 'settings_yandex_edit', description: 'API-ключи Геокодера Яндекс и карт' },
      { title: 'Настройки T-API Т-Банка', viewCode: 'settings_tbank_view', editCode: 'settings_tbank_edit', description: 'Реквизиты терминалов оплаты, секретные ключи Т-Банк Merchant API' },
      { title: 'Интеграция с Mango Office', viewCode: 'settings_mango_view', editCode: 'settings_mango_edit', description: 'Настройки ВАТС Mango Office, звонки, вебхуки, аудиозаписи и статистика' },
      { title: 'Настройки валидации', viewCode: 'settings_validation_view', editCode: 'settings_validation_edit', description: 'Настройка сервисов подтверждения телефонов (RedSMS) и каналов связи' },
      { title: 'Настройки уведомлений', viewCode: 'settings_notifications_view', editCode: 'settings_notifications_edit', description: 'Настройка Web Push уведомлений (VAPID ключи) и звуков уведомлений' },
      { title: 'Логи синхронизации', viewCode: 'settings_sync_logs_view', description: 'Просмотр отчетов по автоматической синхронизации клиентов с iiko' },
      { title: 'Логи системы', viewCode: 'system_logs_view', description: 'Просмотр файла системных логов бэкенда для отладки ошибок' }
    ]
  },
  {
    title: 'Отчеты',
    icon: 'ri-bar-chart-box-line',
    items: [
      { title: 'Общие финансовые отчеты', viewCode: 'reports_view', description: 'Доступ к отчетам по выручке, продажам, дням, клиентам и типам оплат (OLAP)' },
      { title: 'Отчеты курьеров', viewCode: 'courier_reports_view', description: 'Просмотр логов, статистики и детализации по доставкам курьеров' }
    ]
  },
  {
    title: 'Администрирование',
    icon: 'ri-user-settings-line',
    items: [
      { title: 'Список сотрудников', viewCode: 'employees_view', editCode: 'employees_edit', description: 'Просмотр реестра сотрудников из iiko, привязка их к пользователям' },
      { title: 'Список пользователей', viewCode: 'users_view', editCode: 'users_edit', description: 'Создание, редактирование учетных записей администраторов, привязка ролей' },
      { title: 'Управление ролями', viewCode: 'roles_view', editCode: 'roles_edit', description: 'Создание ролей, редактирование прав доступа и матрицы разрешений' }
    ]
  }
]

// Преобразование выбранных ID в строковые коды прав и наоборот
const selectedPermissionCodes = computed({
  get() {
    const codes = []
    selectedPermissions.value.forEach(id => {
      const perm = permissions.value.find(p => p.id === id)
      if (perm) {
        codes.push(perm.code)
      }
    })
    return codes
  },
  set(newCodes) {
    const ids = []
    newCodes.forEach(code => {
      const perm = permissions.value.find(p => p.code === code)
      if (perm) {
        ids.push(perm.id)
      }
    })
    selectedPermissions.value = ids
  }
})

const hasPermission = (code) => {
  return selectedPermissionCodes.value.includes(code)
}

// Проверка наличия права у конкретной роли (для окна быстрого просмотра)
const roleHasPermission = (role, code) => {
  if (!role || !role.permissions) return false
  return role.permissions.some(p => p.code === code)
}

const toggleViewPermission = (viewCode, editCode) => {
  let codes = [...selectedPermissionCodes.value]
  if (codes.includes(viewCode)) {
    codes = codes.filter(c => c !== viewCode)
    if (editCode) {
      codes = codes.filter(c => c !== editCode)
    }
  } else {
    codes.push(viewCode)
  }
  selectedPermissionCodes.value = codes
}

const toggleEditPermission = (viewCode, editCode) => {
  if (!editCode) return
  let codes = [...selectedPermissionCodes.value]
  if (codes.includes(editCode)) {
    codes = codes.filter(c => c !== editCode)
  } else {
    codes.push(editCode)
    if (!codes.includes(viewCode)) {
      codes.push(viewCode)
    }
  }
  selectedPermissionCodes.value = codes
}

// Статистика группы прав
const getGroupStats = (group) => {
  let total = 0
  let active = 0
  group.items.forEach(item => {
    total += 1 // viewCode
    if (hasPermission(item.viewCode)) active += 1
    if (item.editCode) {
      total += 1
      if (hasPermission(item.editCode)) active += 1
    }
  })
  return { active, total, isFull: active === total && total > 0, isNone: active === 0 }
}

// Групповые действия для раздела
const enableGroupAll = (group) => {
  const codes = new Set(selectedPermissionCodes.value)
  group.items.forEach(item => {
    if (item.viewCode) codes.add(item.viewCode)
    if (item.editCode) codes.add(item.editCode)
  })
  selectedPermissionCodes.value = Array.from(codes)
}

const enableGroupViewOnly = (group) => {
  const codes = new Set(selectedPermissionCodes.value)
  group.items.forEach(item => {
    if (item.viewCode) codes.add(item.viewCode)
    if (item.editCode) codes.delete(item.editCode)
  })
  selectedPermissionCodes.value = Array.from(codes)
}

const disableGroupAll = (group) => {
  const codes = new Set(selectedPermissionCodes.value)
  group.items.forEach(item => {
    if (item.viewCode) codes.delete(item.viewCode)
    if (item.editCode) codes.delete(item.editCode)
  })
  selectedPermissionCodes.value = Array.from(codes)
}

// Развернуть / свернуть все панели
const expandAllPanels = () => {
  expandedPanels.value = permissionGroups.map((_, i) => i)
}

const collapseAllPanels = () => {
  expandedPanels.value = []
}

// Отфильтрованные группы для настройки прав (по поиску и тумблеру активных)
const filteredPermissionGroups = computed(() => {
  const q = (permSearchQuery.value || '').trim().toLowerCase()
  const mode = permFilterMode.value

  return permissionGroups
    .map((group, originalIdx) => {
      const items = group.items.filter(item => {
        // Проверка фильтра режима (Все / Действующие / Неактивные)
        const isActive = hasPermission(item.viewCode) || (item.editCode && hasPermission(item.editCode))
        if (mode === 'active' && !isActive) return false
        if (mode === 'inactive' && isActive) return false

        // Проверка поискового запроса
        if (!q) return true
        return (
          item.title.toLowerCase().includes(q) ||
          (item.description && item.description.toLowerCase().includes(q)) ||
          item.viewCode.toLowerCase().includes(q) ||
          (item.editCode && item.editCode.toLowerCase().includes(q)) ||
          group.title.toLowerCase().includes(q)
        )
      })

      return {
        ...group,
        originalIdx,
        items
      }
    })
    .filter(g => g.items.length > 0)
})

// Структурированные действующие позиции роли (для модального окна быстрого просмотра)
const viewRoleActiveGroups = computed(() => {
  if (!selectedRole.value) return []
  const role = selectedRole.value
  const q = (viewPermSearchQuery.value || '').trim().toLowerCase()

  return permissionGroups
    .map(group => {
      const activeItems = group.items
        .map(item => {
          const hasView = roleHasPermission(role, item.viewCode)
          const hasEdit = item.editCode ? roleHasPermission(role, item.editCode) : false
          if (!hasView && !hasEdit) return null

          if (q) {
            const matches = item.title.toLowerCase().includes(q) ||
              (item.description && item.description.toLowerCase().includes(q)) ||
              group.title.toLowerCase().includes(q)
            if (!matches) return null
          }

          return {
            ...item,
            hasView,
            hasEdit
          }
        })
        .filter(Boolean)

      return {
        ...group,
        items: activeItems
      }
    })
    .filter(g => g.items.length > 0)
})

const totalActivePermissionsCount = computed(() => {
  return selectedPermissionCodes.value.length
})

const fetchRoles = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/users/roles', {
      headers: getAuthHeaders()
    })
    if (response.ok) roles.value = await response.json()
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const fetchPermissions = async () => {
  try {
    const response = await fetch('/api/v1/users/permissions', {
      headers: getAuthHeaders()
    })
    if (response.ok) permissions.value = await response.json()
  } catch (e) { console.error(e) }
}

const editItem = (item) => {
  editedItem.value = { ...item }
  isDialogVisible.value = true
}

const openPermissions = (item) => {
  selectedRole.value = item
  selectedPermissions.value = item.permissions ? item.permissions.map(p => p.id) : []
  permSearchQuery.value = ''
  permFilterMode.value = 'all'
  expandedPanels.value = [0, 1] // Первые две панели раскрыты
  isPermissionDialogVisible.value = true
}

// Открытие модального окна быстрого аудита действующих прав
const openViewPermissions = (item) => {
  selectedRole.value = item
  viewPermSearchQuery.value = ''
  isViewPermissionsDialogVisible.value = true
}

const close = () => {
  isDialogVisible.value = false
  editedItem.value = { ...defaultItem }
}

const save = async () => {
  const method = editedItem.value.id ? 'PATCH' : 'POST'
  const url = editedItem.value.id ? `/api/v1/users/roles/${editedItem.value.id}` : '/api/v1/users/roles'
  
  try {
    const response = await fetch(url, {
      method,
      headers: getAuthHeaders(),
      body: JSON.stringify(editedItem.value)
    })
    if (response.ok) {
      await fetchRoles()
      close()
    } else {
      const error = await response.json()
      alert(`Ошибка: ${error.detail || 'Не удалось сохранить'}`)
    }
  } catch (e) { console.error(e) }
}

const savePermissions = async () => {
  try {
    const response = await fetch(`/api/v1/users/roles/${selectedRole.value.id}/permissions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ permission_ids: selectedPermissions.value })
    })
    if (response.ok) {
      await fetchRoles()
      isPermissionDialogVisible.value = false
    }
  } catch (e) { console.error(e) }
}

const confirmDelete = (item) => {
  roleToDelete.value = item
  deleteDialog.value = true
}

const deleteRole = async () => {
  isDeleting.value = true
  try {
    const response = await fetch(`/api/v1/users/roles/${roleToDelete.value.id}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      await fetchRoles()
      deleteDialog.value = false
    } else {
      const error = await response.json()
      alert(`Ошибка: ${error.detail || 'Не удалось удалить'}`)
    }
  } catch (e) { console.error(e) }
  finally { isDeleting.value = false }
}

const syncIikoRoles = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/users/sync-iiko-roles', {
      method: 'POST',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      await fetchRoles()
      alert('Синхронизация завершена')
    }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

onMounted(() => {
  fetchRoles()
  fetchPermissions()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Управление ролями и правами доступа">
        <template #append>
          <div class="d-flex gap-2">
            <VBtn
              color="info"
              variant="tonal"
              prepend-icon="ri-refresh-line"
              @click="syncIikoRoles"
            >
              Синхронизация iiko
            </VBtn>
            <VBtn
              color="primary"
              prepend-icon="ri-add-line"
              @click="isDialogVisible = true"
            >
              Добавить роль
            </VBtn>
          </div>
        </template>

        <VDataTable
          :headers="headers"
          :items="roles"
          :loading="loading"
          hover
        >
          <template #item.is_system="{ item }">
            <VChip
              :color="item.is_system ? 'secondary' : 'default'"
              size="small"
              label
            >
              {{ item.is_system ? 'Системная' : 'Пользовательская' }}
            </VChip>
          </template>

          <template #item.default_page="{ item }">
            <span class="text-body-2 text-primary font-weight-medium">
              {{ defaultPageOptions.find(o => o.value === item.default_page)?.title || 'По умолчанию' }}
            </span>
          </template>

          <!-- Столбец действующих прав: Клик открывает быстрый просмотр -->
          <template #item.permissions_count="{ item }">
            <VChip
              size="small"
              color="primary"
              variant="tonal"
              class="font-weight-medium cursor-pointer"
              prepend-icon="ri-shield-check-line"
              @click="openViewPermissions(item)"
              title="Нажмите для просмотра действующих позиций на страницах"
            >
              {{ item.permissions?.length || 0 }} прав (Обзор)
            </VChip>
          </template>

          <template #item.actions="{ item }">
            <div class="d-flex justify-end gap-1">
              <!-- Быстрый просмотр действующих прав роли -->
              <VBtn
                icon="ri-eye-line"
                size="small"
                variant="text"
                color="info"
                title="Просмотр действующих прав роли"
                @click="openViewPermissions(item)"
              />
              <!-- Редактирование прав роли -->
              <VBtn
                icon="ri-shield-keyhole-line"
                size="small"
                variant="text"
                color="warning"
                title="Настроить права доступа"
                @click="openPermissions(item)"
              />
              <!-- Редактирование роли -->
              <VBtn
                icon="ri-edit-line"
                size="small"
                variant="text"
                color="primary"
                title="Редактировать роль"
                @click="editItem(item)"
              />
              <!-- Удаление -->
              <VBtn
                icon="ri-delete-bin-line"
                size="small"
                variant="text"
                color="error"
                :disabled="item.is_system"
                title="Удалить роль"
                @click="confirmDelete(item)"
              />
            </div>
          </template>
        </VDataTable>
      </VCard>
    </VCol>

    <!-- Edit/Add Dialog -->
    <VDialog
      v-model="isDialogVisible"
      max-width="520px"
    >
      <VCard :title="formTitle">
        <VCardText>
          <VRow>
            <VCol cols="12">
              <VTextField
                v-model="editedItem.name"
                label="Название роли"
                placeholder="Менеджер филиала"
              />
            </VCol>
            <VCol cols="12">
              <VTextField
                v-model="editedItem.code"
                label="Код роли"
                placeholder="BRANCH_MANAGER"
                :disabled="editedItem.is_system"
              />
            </VCol>
            <VCol cols="12">
              <VTextarea
                v-model="editedItem.description"
                label="Описание"
                rows="2"
              />
            </VCol>
            <VCol cols="12">
              <VSelect
                v-model="editedItem.default_page"
                :items="defaultPageOptions"
                item-title="title"
                item-value="value"
                label="Главная страница по умолчанию"
                placeholder="Выберите страницу при входе"
                clearable
                prepend-inner-icon="ri-home-4-line"
              />
            </VCol>
          </VRow>
        </VCardText>

        <VCardActions class="border-t py-3">
          <VSpacer />
          <VBtn
            color="secondary"
            variant="tonal"
            @click="close"
          >
            Отмена
          </VBtn>
          <VBtn
            color="primary"
            variant="elevated"
            @click="save"
          >
            Сохранить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ДИАЛОГ 1: ПРОСМОТР ДЕЙСТВУЮЩИХ ПОЗИЦИЙ РОЛИ (Только активные права) -->
    <VDialog
      v-model="isViewPermissionsDialogVisible"
      max-width="900px"
      scrollable
    >
      <VCard>
        <VCardTitle class="d-flex align-center justify-space-between py-4 px-6 border-b">
          <div class="d-flex align-center gap-2">
            <VIcon icon="ri-shield-check-line" color="success" size="24" />
            <span class="text-h6 font-weight-bold">
              Действующие права роли: <span class="text-primary">{{ selectedRole?.name }}</span>
            </span>
          </div>
          <VChip color="primary" variant="tonal" size="small" class="font-weight-bold">
            Активно прав: {{ selectedRole?.permissions?.length || 0 }}
          </VChip>
        </VCardTitle>

        <VCardText class="pa-6" style="max-height: 650px;">
          <!-- Поиск действующих прав -->
          <div class="mb-4">
            <VTextField
              v-model="viewPermSearchQuery"
              placeholder="Поиск по действующим страницам и правам..."
              prepend-inner-icon="ri-search-line"
              density="compact"
              variant="outlined"
              hide-details
              clearable
            />
          </div>

          <div v-if="viewRoleActiveGroups.length === 0" class="text-center py-10">
            <VIcon icon="ri-shield-cross-line" size="48" color="secondary" class="mb-2" />
            <div class="text-h6 text-medium-emphasis">Действующих прав не найдено</div>
            <div class="text-caption text-disabled">
              У данной роли отключены все права или они не соответствуют критериям поиска.
            </div>
          </div>

          <!-- Сетка действующих разделов -->
          <div v-else class="d-flex flex-column gap-4">
            <VCard
              v-for="(grp, gIdx) in viewRoleActiveGroups"
              :key="gIdx"
              variant="outlined"
              class="border rounded-lg"
            >
              <VCardItem class="py-3 bg-var-theme-background border-b">
                <template #prepend>
                  <VIcon :icon="grp.icon" color="primary" class="me-2" size="20" />
                </template>
                <VCardTitle class="text-subtitle-1 font-weight-bold">
                  {{ grp.title }}
                </VCardTitle>
                <template #append>
                  <VChip size="x-small" color="success" variant="flat" class="font-weight-bold">
                    {{ grp.items.length }} позиций разрешено
                  </VChip>
                </template>
              </VCardItem>

              <VCardText class="pa-3">
                <div class="d-flex flex-column gap-2">
                  <div
                    v-for="(it, iIdx) in grp.items"
                    :key="iIdx"
                    class="d-flex flex-wrap align-center justify-space-between p-2 px-3 rounded bg-surface border"
                  >
                    <div class="pe-3 my-1" style="max-width: 65%;">
                      <div class="font-weight-bold text-body-2">{{ it.title }}</div>
                      <div class="text-caption text-medium-emphasis">{{ it.description }}</div>
                    </div>

                    <!-- Бейджи разрешений -->
                    <div class="d-flex align-center gap-2 my-1">
                      <VChip
                        v-if="it.hasView"
                        color="success"
                        size="small"
                        variant="tonal"
                        prepend-icon="ri-eye-line"
                      >
                        Просмотр
                      </VChip>
                      <VChip
                        v-if="it.hasEdit"
                        color="primary"
                        size="small"
                        variant="tonal"
                        prepend-icon="ri-edit-line"
                      >
                        Редактирование
                      </VChip>
                      <VChip
                        v-if="!it.editCode && it.hasView"
                        color="info"
                        size="small"
                        variant="tonal"
                        prepend-icon="ri-check-line"
                      >
                        Доступ открыт
                      </VChip>
                    </div>
                  </div>
                </div>
              </VCardText>
            </VCard>
          </div>
        </VCardText>

        <VCardActions class="border-t py-3 px-6">
          <VBtn
            color="primary"
            variant="tonal"
            prepend-icon="ri-shield-keyhole-line"
            @click="isViewPermissionsDialogVisible = false; openPermissions(selectedRole)"
          >
            Перейти к настройке прав
          </VBtn>
          <VSpacer />
          <VBtn
            color="secondary"
            variant="elevated"
            @click="isViewPermissionsDialogVisible = false"
          >
            Закрыть
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ДИАЛОГ 2: НАСТРОЙКА И РЕДАКТИРОВАНИЕ ПРАВ РОЛИ -->
    <VDialog
      v-model="isPermissionDialogVisible"
      max-width="950px"
      scrollable
    >
      <VCard>
        <VCardTitle class="d-flex align-center justify-space-between py-4 px-6 border-b">
          <div class="d-flex align-center gap-2">
            <VIcon icon="ri-shield-keyhole-line" color="warning" size="24" />
            <span class="text-h6 font-weight-bold">
              Настройка прав доступа: <span class="text-primary">{{ selectedRole?.name }}</span>
            </span>
          </div>
          <VChip color="success" variant="flat" size="small" class="font-weight-bold">
            Активно: {{ totalActivePermissionsCount }} прав
          </VChip>
        </VCardTitle>

        <!-- ТУЛБАР ФИЛЬТРОВ И ПОИСКА ПОЗИЦИЙ -->
        <div class="px-6 pt-4 pb-2 border-b bg-var-theme-background">
          <VRow align="center" dense>
            <!-- Поиск -->
            <VCol cols="12" md="6">
              <VTextField
                v-model="permSearchQuery"
                placeholder="Поиск по названию страницы, действию или коду..."
                prepend-inner-icon="ri-search-line"
                density="compact"
                variant="outlined"
                hide-details
                clearable
              />
            </VCol>

            <!-- Переключатель режима: Все / Действующие / Неактивные -->
            <VCol cols="12" md="6" class="d-flex justify-md-end gap-1 flex-wrap">
              <VBtnToggle
                v-model="permFilterMode"
                mandatory
                density="compact"
                color="primary"
                variant="outlined"
              >
                <VBtn value="all" size="small">
                  Все позиции
                </VBtn>
                <VBtn value="active" size="small" color="success">
                  <VIcon start icon="ri-check-line" size="14" />
                  Действующие
                </VBtn>
                <VBtn value="inactive" size="small" color="secondary">
                  Неактивные
                </VBtn>
              </VBtnToggle>

              <VBtn
                size="small"
                variant="text"
                color="secondary"
                icon="ri-expand-up-down-line"
                title="Развернуть все разделы"
                @click="expandAllPanels"
              />
              <VBtn
                size="small"
                variant="text"
                color="secondary"
                icon="ri-collapse-diagonal-line"
                title="Свернуть все"
                @click="collapseAllPanels"
              />
            </VCol>
          </VRow>
        </div>

        <VCardText class="pa-6" style="height: 600px;">
          <div v-if="filteredPermissionGroups.length === 0" class="text-center py-10">
            <VIcon icon="ri-filter-off-line" size="48" color="secondary" class="mb-2" />
            <div class="text-h6 text-medium-emphasis">Позиций не найдено</div>
            <div class="text-caption text-disabled">
              Попробуйте изменить поисковый запрос или переключить режим отображения на «Все позиции».
            </div>
          </div>

          <VExpansionPanels
            v-else
            v-model="expandedPanels"
            multiple
            variant="accordion"
            class="mb-4"
          >
            <VExpansionPanel
              v-for="group in filteredPermissionGroups"
              :key="group.originalIdx"
              :value="group.originalIdx"
              class="border rounded mb-2 overflow-hidden"
            >
              <VExpansionPanelTitle class="font-weight-medium py-3 px-4">
                <div class="d-flex align-center justify-space-between flex-grow-1 pe-2">
                  <div class="d-flex align-center">
                    <VIcon :icon="group.icon" class="me-3" color="primary" size="22" />
                    <span class="text-subtitle-1 font-weight-bold">{{ group.title }}</span>
                  </div>

                  <!-- Правая часть заголовка: счетчик и групповые кнопки -->
                  <div class="d-flex align-center gap-2" @click.stop>
                    <VChip
                      size="x-small"
                      :color="getGroupStats(group).isFull ? 'success' : (getGroupStats(group).isNone ? 'secondary' : 'info')"
                      variant="flat"
                      class="font-weight-bold"
                    >
                      {{ getGroupStats(group).active }} / {{ getGroupStats(group).total }} активно
                    </VChip>

                    <!-- Быстрые действия над группой -->
                    <VBtn
                      size="x-small"
                      variant="tonal"
                      color="primary"
                      @click="enableGroupAll(group)"
                      title="Включить все права в этом разделе"
                    >
                      Все
                    </VBtn>
                    <VBtn
                      size="x-small"
                      variant="tonal"
                      color="info"
                      @click="enableGroupViewOnly(group)"
                      title="Включить только просмотр"
                    >
                      Просмотр
                    </VBtn>
                    <VBtn
                      size="x-small"
                      variant="tonal"
                      color="secondary"
                      @click="disableGroupAll(group)"
                      title="Отключить раздел"
                    >
                      Снять
                    </VBtn>
                  </div>
                </div>
              </VExpansionPanelTitle>

              <VExpansionPanelText class="pt-2">
                <!-- Заголовки таблицы -->
                <VRow class="pb-2 mb-2 text-muted font-weight-bold text-uppercase border-bottom" style="font-size: 0.75rem; letter-spacing: 0.5px;">
                  <VCol cols="6">Страница / Сущность / Описание</VCol>
                  <VCol cols="3" class="text-center">Доступ (Просмотр)</VCol>
                  <VCol cols="3" class="text-center">Редактирование</VCol>
                </VRow>
                <VDivider class="mb-3" />

                <!-- Строки элементов -->
                <div v-for="(item, iIdx) in group.items" :key="iIdx" class="py-2 hover-row">
                  <VRow align="center" no-gutters>
                    <VCol cols="6" class="pe-3">
                      <div class="font-weight-semibold text-body-1">{{ item.title }}</div>
                      <div class="text-caption text-grey">{{ item.description }}</div>
                    </VCol>
                    <VCol cols="3" class="d-flex justify-center">
                      <VSwitch
                        :model-value="hasPermission(item.viewCode)"
                        color="primary"
                        hide-details
                        density="compact"
                        @update:model-value="toggleViewPermission(item.viewCode, item.editCode)"
                      />
                    </VCol>
                    <VCol cols="3" class="d-flex justify-center">
                      <VCheckbox
                        v-if="item.editCode"
                        :model-value="hasPermission(item.editCode)"
                        :disabled="!hasPermission(item.viewCode)"
                        color="success"
                        hide-details
                        density="compact"
                        @update:model-value="toggleEditPermission(item.viewCode, item.editCode)"
                      />
                      <span v-else class="text-caption text-grey-lighten-1 font-italic">-</span>
                    </VCol>
                  </VRow>
                  <VDivider class="mt-3" v-if="iIdx < group.items.length - 1" />
                </div>
              </VExpansionPanelText>
            </VExpansionPanel>
          </VExpansionPanels>
        </VCardText>

        <VCardActions class="border-t py-3 px-6">
          <div class="text-caption text-medium-emphasis">
            Всего активных прав у роли: <strong>{{ totalActivePermissionsCount }}</strong>
          </div>
          <VSpacer />
          <VBtn
            color="secondary"
            variant="tonal"
            @click="isPermissionDialogVisible = false"
          >
            Отмена
          </VBtn>
          <VBtn
            color="success"
            variant="elevated"
            prepend-icon="ri-save-line"
            @click="savePermissions"
          >
            Применить изменения
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Delete Confirmation -->
    <VDialog
      v-model="deleteDialog"
      max-width="400px"
    >
      <VCard title="Удаление роли">
        <VCardText>
          Вы уверены, что хотите удалить роль <strong>{{ roleToDelete?.name }}</strong>?
          Пользователи с этой ролью могут потерять доступ к системе.
        </VCardText>
        <VCardActions class="border-t py-3">
          <VSpacer />
          <VBtn
            color="secondary"
            variant="tonal"
            @click="deleteDialog = false"
          >
            Отмена
          </VBtn>
          <VBtn
            color="error"
            :loading="isDeleting"
            @click="deleteRole"
          >
            Удалить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VRow>
</template>

<style scoped>
.hover-row {
  transition: background-color 0.2s ease;
  border-radius: 4px;
}
.hover-row:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}
.border-bottom {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}
.cursor-pointer {
  cursor: pointer;
}
</style>
