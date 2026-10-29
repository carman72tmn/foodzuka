<script setup>
import VerticalNavSectionTitle from "@/@layouts/components/VerticalNavSectionTitle.vue"
import VerticalNavGroup from "@layouts/components/VerticalNavGroup.vue"
import VerticalNavLink from "@layouts/components/VerticalNavLink.vue"
import { hasPermission, authState } from "@/utils/auth"
</script>

<template>
  <!-- Управление компанией -->
  <template v-if="hasPermission('companies_view') || hasPermission('branches_view') || hasPermission('zones_view')">
    <VerticalNavSectionTitle :item="{ heading: 'Управление компанией' }" />
    <VerticalNavLink
      v-if="hasPermission('companies_view')"
      :item="{ title: 'Мои компании', icon: 'bx-buildings', to: '/companies' }"
    />

    <VerticalNavGroup
      v-if="hasPermission('branches_view') || hasPermission('zones_view')"
      :item="{ title: 'Филиалы', icon: 'bx-store' }"
    >
      <VerticalNavLink
        v-if="hasPermission('branches_view')"
        :item="{ title: 'Все филиалы', to: '/branches' }"
      />
      <VerticalNavLink
        v-if="hasPermission('zones_view')"
        :item="{ title: 'Зоны доставки', to: '/branches/zones' }"
      />
    </VerticalNavGroup>
  </template>

  <!-- Каталог -->
  <VerticalNavGroup
    v-if="hasPermission('menu_categories_view') || hasPermission('menu_products_view') || hasPermission('menu_options_view') || hasPermission('menu_import_view')"
    :item="{ title: 'Каталог', icon: 'bx-food-menu' }"
  >
    <VerticalNavLink
      v-if="hasPermission('menu_categories_view')"
      :item="{ title: 'Разделы', to: '/menu/categories' }"
    />
    <VerticalNavLink
      v-if="hasPermission('menu_products_view')"
      :item="{ title: 'Товары', to: '/menu/products' }"
    />
    <VerticalNavLink
      v-if="hasPermission('menu_options_view')"
      :item="{ title: 'Опции', to: '/menu/options' }"
    />
    <VerticalNavLink
      v-if="hasPermission('menu_import_view')"
      :item="{ title: 'Импорт', to: '/menu/import' }"
    />
  </VerticalNavGroup>

  <!-- Кухня -->
  <template v-if="hasPermission('kitchen_recipes_view') || hasPermission('kitchen_screen_view')">
    <VerticalNavGroup
      :item="{ title: 'Кухня', icon: 'bx-restaurant' }"
    >
      <VerticalNavLink
        v-if="hasPermission('kitchen_recipes_view')"
        :item="{ title: 'Техкарты блюд', to: '/kitchen/recipes' }"
      />
      <VerticalNavLink
        v-if="hasPermission('kitchen_screen_view')"
        :item="{ title: 'Заказы на кухне', to: '/kitchen/screen' }"
      />
    </VerticalNavGroup>
  </template>

  <VerticalNavLink
    v-if="hasPermission('orders_view')"
    :item="{ title: 'Заказы', icon: 'bx-receipt', to: '/orders' }"
  />

  <VerticalNavLink
    v-if="hasPermission('ai_agents_chat_view') || hasPermission('settings_ai_agents_view') || hasPermission('settings_view')"
    :item="{ title: 'ИИ Агенты', icon: 'bx-bot', to: '/ai-chat' }"
  />

  <VerticalNavLink
    v-if="hasPermission('multichat_view')"
    :item="{ title: 'Мультичат', icon: 'bx-chat', to: '/multichat' }"
  />

  <VerticalNavLink
    v-if="hasPermission('notifications_feed_view') || hasPermission('orders_view')"
    :item="{ title: 'Уведомления', icon: 'bx-bell', to: '/notifications-feed' }"
  />

  <!-- Курьеры (Мониторинг) -->
  <VerticalNavLink
    v-if="hasPermission('courier_view') || authState.user?.iiko_id || authState.user?.employee?.iiko_id"
    :item="{ title: 'Курьеры', icon: 'bx-cycling', to: '/courier' }"
  />

  <!-- Клиенты -->
  <VerticalNavGroup
    v-if="hasPermission('clients_view')"
    :item="{ title: 'Клиенты', icon: 'bx-group' }"
  >
    <VerticalNavLink
      v-if="hasPermission('clients_view')"
      :item="{ title: 'Все клиенты', to: '/clients' }"
    />
  </VerticalNavGroup>

  <!-- Закуп -->
  <VerticalNavGroup
    v-if="hasPermission('purchase_lists_view') || hasPermission('purchase_positions_view')"
    :item="{ title: 'Закуп', icon: 'bx-shopping-bag' }"
  >
    <VerticalNavLink
      v-if="hasPermission('purchase_lists_view')"
      :item="{ title: 'Списки закупа', to: '/purchase' }"
    />
    <VerticalNavLink
      v-if="hasPermission('purchase_positions_view')"
      :item="{ title: 'Позиции закупа', to: '/purchase/positions' }"
    />
  </VerticalNavGroup>

  <!-- NPS -->
  <VerticalNavGroup
    v-if="hasPermission('nps_reviews_view') || hasPermission('nps_dishes_view') || hasPermission('nps_analytics_view')"
    :item="{ title: 'NPS', icon: 'bx-message-square-detail' }"
  >
    <VerticalNavLink
      v-if="hasPermission('nps_reviews_view')"
      :item="{ title: 'Отзывы', to: '/nps/reviews' }"
    />
    <VerticalNavLink
      v-if="hasPermission('nps_dishes_view')"
      :item="{ title: 'Оценка блюд', to: '/nps/dishes' }"
    />
    <VerticalNavLink
      v-if="hasPermission('nps_analytics_view')"
      :item="{ title: 'NPS', to: '/nps/analytics' }"
    />
  </VerticalNavGroup>

  <!-- Акции и Маркетинг -->
  <template v-if="hasPermission('promotions_content_view') || hasPermission('promotions_scale_view') || hasPermission('marketing_stories_view') || hasPermission('promo_codes_view') || hasPermission('marketing_funnels_view') || hasPermission('loyalty_view') || hasPermission('marketing_vk_bots_view') || hasPermission('settings_bot_commands_view') || hasPermission('marketing_group_posting_view')">
    <VerticalNavGroup
      v-if="hasPermission('promotions_content_view') || hasPermission('promotions_scale_view')"
      :item="{ title: 'Акции', icon: 'bx-gift' }"
    >
      <VerticalNavLink
        v-if="hasPermission('promotions_content_view')"
        :item="{ title: 'Контентная информация', to: '/promotions/content' }"
      />
      <VerticalNavLink
        v-if="hasPermission('promotions_scale_view')"
        :item="{ title: 'Шкала подарков', to: '/promotions/scale' }"
      />
    </VerticalNavGroup>

    <VerticalNavGroup
      v-if="hasPermission('marketing_stories_view') || hasPermission('promo_codes_view') || hasPermission('marketing_funnels_view') || hasPermission('loyalty_view') || hasPermission('marketing_vk_bots_view') || hasPermission('settings_bot_commands_view') || hasPermission('marketing_group_posting_view')"
      :item="{ title: 'Маркетинг и вовлеченность', icon: 'bx-badge-check' }"
    >
      <VerticalNavLink
        v-if="hasPermission('marketing_stories_view')"
        :item="{ title: 'Истории', to: '/marketing/stories' }"
      />
      <VerticalNavLink
        v-if="hasPermission('promo_codes_view')"
        :item="{ title: 'Промокоды', to: '/promo' }"
      />
      <VerticalNavLink
        v-if="hasPermission('marketing_funnels_view')"
        :item="{ title: 'Воронки', to: '/marketing/funnels' }"
      />
      <VerticalNavLink
        v-if="hasPermission('loyalty_view')"
        :item="{ title: 'Программа лояльности', to: '/loyalty' }"
      />
      <VerticalNavLink
        v-if="hasPermission('marketing_vk_bots_view')"
        :item="{ title: 'Боты ВКонтакте', to: '/marketing/vk-bots' }"
      />
      <VerticalNavLink
        v-if="hasPermission('marketing_group_posting_view') || hasPermission('marketing_vk_bots_view') || hasPermission('mailings_general_view')"
        :item="{ title: 'Постинг в группах', to: '/marketing/group-posting' }"
      />
      <VerticalNavLink
        v-if="hasPermission('settings_bot_commands_view')"
        :item="{ title: 'Команды ботов', to: '/settings/bot-commands' }"
      />
    </VerticalNavGroup>
  </template>

  <!-- Рассылки -->
  <VerticalNavGroup
    v-if="hasPermission('mailings_general_view') || hasPermission('settings_bot_view') || hasPermission('settings_vk_view') || hasPermission('settings_vk_notifications_view') || hasPermission('settings_vk_parser_view') || hasPermission('settings_max_view') || hasPermission('mailings_cascades_view') || hasPermission('settings_senler_view')"
    :item="{ title: 'Рассылки', icon: 'bx-broadcast' }"
  >
    <VerticalNavLink
      v-if="hasPermission('mailings_general_view')"
      :item="{ title: 'Общие рассылки', to: '/marketing/mailings' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_bot_view')"
      :item="{ title: 'Настройки Telegram Бота', to: '/settings/bot' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_vk_view')"
      :item="{ title: 'Настройки VK Бота', to: '/settings/vk' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_vk_notifications_view')"
      :item="{ title: 'Системные рассылки', to: '/settings/vk-notifications' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_vk_parser_view')"
      :item="{ title: 'Парсер ВК', to: '/settings/vk-parser' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_senler_view')"
      :item="{ title: 'Интеграция Senler', to: '/settings/senler' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_max_view')"
      :item="{ title: 'Настройка MAX', icon: 'bx-cog', to: '/settings/max' }"
    />
    <VerticalNavLink
      v-if="hasPermission('mailings_cascades_view')"
      :item="{ title: 'Уведомления и рассылки', icon: 'bx-message-detail', to: '/mailings/cascades' }"
    />
  </VerticalNavGroup>

  <!-- Операции банка -->
  <VerticalNavGroup
    v-if="hasPermission('bank_payments_view') || hasPermission('bank_tbank_payments_view')"
    :item="{ title: 'Операции банка', icon: 'bx-credit-card' }"
  >
    <VerticalNavLink
      v-if="hasPermission('bank_payments_view')"
      :item="{ title: 'Входящие платежи', to: '/bank/payments' }"
    />
    <VerticalNavLink
      v-if="hasPermission('bank_tbank_payments_view')"
      :item="{ title: 'Монитор Т-Банк', to: '/bank/tbank-payments' }"
    />
  </VerticalNavGroup>

  <!-- Система -->
  <VerticalNavGroup
    v-if="hasPermission('system_server_view') || hasPermission('system_tags_view') || hasPermission('settings_iiko_view') || hasPermission('settings_sync_logs_view') || hasPermission('settings_yandex_view') || hasPermission('settings_tbank_view') || hasPermission('settings_mango_view') || hasPermission('settings_notifications_view') || hasPermission('settings_validation_view') || hasPermission('system_tasks_view') || hasPermission('system_logs_view')"
    :item="{ title: 'Система', icon: 'bx-cog' }"
  >
    <VerticalNavLink
      v-if="hasPermission('system_server_view') || hasPermission('settings_view')"
      :item="{ title: 'Модули системы', icon: 'bx-extension', to: '/system/modules' }"
    />
    <VerticalNavLink
      v-if="hasPermission('system_server_view') || hasPermission('settings_view')"
      :item="{ title: 'Бэкапы и ИИ', icon: 'bx-shield-quarter', to: '/system/backups' }"
    />
    <VerticalNavLink
      v-if="hasPermission('system_server_view')"
      :item="{ title: 'Сервер', icon: 'bx-server', to: '/system/server' }"
    />
    <VerticalNavLink
      v-if="hasPermission('system_tags_view')"
      :item="{ title: 'Метки', to: '/system/tags' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_ai_agents_view') || hasPermission('settings_view')"
      :item="{ title: 'Агенты ИИ', icon: 'bx-bot', to: '/settings/ai-agents' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_ai_agents_view') || hasPermission('settings_view')"
      :item="{ title: 'Помощники ИИ', icon: 'bx-bot', to: '/settings/ai-assistants' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_iiko_view')"
      :item="{ title: 'Настройки iiko', to: '/settings/iiko' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_sync_logs_view')"
      :item="{ title: 'Логи синхронизации', to: '/settings/sync-logs' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_yandex_view')"
      :item="{ title: 'Настройки Яндекс', to: '/settings/yandex' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_tbank_view')"
      :item="{ title: 'Настройки T-API', to: '/settings/tbank' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_mango_view')"
      :item="{ title: 'Интеграция с Mango', icon: 'bx-phone-call', to: '/settings/mango' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_validation_view')"
      :item="{ title: 'Валидация', to: '/settings/validation' }"
    />
    <VerticalNavLink
      v-if="hasPermission('settings_notifications_view')"
      :item="{ title: 'Уведомления', to: '/settings/notifications' }"
    />
    <VerticalNavLink
      v-if="hasPermission('system_tasks_view')"
      :item="{ title: 'Фоновые процессы', icon: 'bx-refresh', to: '/system/tasks' }"
    />
    <VerticalNavLink
      v-if="hasPermission('system_logs_view')"
      :item="{ title: 'Логи системы', icon: 'bx-list-ul', to: '/system/logs' }"
    />
  </VerticalNavGroup>

  <!-- Отчеты -->
  <VerticalNavGroup
    v-if="hasPermission('reports_view')"
    :item="{ title: 'Отчеты', icon: 'bx-bar-chart-alt-2' }"
  >
    <VerticalNavLink :item="{ title: 'Выручка', to: '/reports/revenue' }" />
    <VerticalNavLink :item="{ title: 'Продажи', to: '/reports/sales' }" />
    <VerticalNavLink :item="{ title: 'Продажи (по товарам)', to: '/reports/products' }" />
    <VerticalNavLink :item="{ title: 'Продажи (по дням)', to: '/reports/days' }" />
    <VerticalNavLink :item="{ title: 'Клиенты', to: '/reports/clients' }" />
    <VerticalNavLink :item="{ title: 'Заказы', to: '/reports/orders' }" />
    <VerticalNavLink :item="{ title: 'Типы оплат', to: '/reports/payments' }" />
  </VerticalNavGroup>

  <!-- Администрирование -->
  <template v-if="hasPermission('employees_view') || hasPermission('users_view') || hasPermission('roles_view')">
    <VerticalNavSectionTitle :item="{ heading: 'Администрирование' }" />
    <VerticalNavLink
      v-if="hasPermission('employees_view')"
      :item="{ title: 'Сотрудники', icon: 'bx-id-card', to: '/employees' }"
    />
    <VerticalNavGroup
      v-if="hasPermission('users_view') || hasPermission('roles_view')"
      :item="{ title: 'Пользователи', icon: 'bx-user' }"
    >
      <VerticalNavLink
        v-if="hasPermission('users_view')"
        :item="{ title: 'Все пользователи', to: '/users' }"
      />
      <VerticalNavLink
        v-if="hasPermission('roles_view')"
        :item="{ title: 'Управление ролями', to: { path: '/users', query: { tab: 'roles' } } }"
      />
    </VerticalNavGroup>
  </template>
</template>
