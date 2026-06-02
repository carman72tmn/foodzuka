<script setup>
import VerticalNavSectionTitle from "@/@layouts/components/VerticalNavSectionTitle.vue"
import VerticalNavGroup from "@layouts/components/VerticalNavGroup.vue"
import VerticalNavLink from "@layouts/components/VerticalNavLink.vue"
import { hasPermission, authState } from "@/utils/auth"
</script>

<template>
  <!-- Управление компанией -->
  <template v-if="hasPermission('settings_view')">
    <VerticalNavSectionTitle :item="{ heading: 'Управление компанией' }" />
    <VerticalNavLink :item="{ title: 'Мои компании', icon: 'bx-buildings', to: '/companies' }" />

    <VerticalNavGroup :item="{ title: 'Филиалы', icon: 'bx-store' }">
      <VerticalNavLink :item="{ title: 'Все филиалы', to: '/branches' }" />
      <VerticalNavLink :item="{ title: 'Зоны доставки', to: '/branches/zones' }" />
    </VerticalNavGroup>
  </template>

  <!-- Каталог -->
  <VerticalNavGroup
    v-if="hasPermission('menu_view')"
    :item="{ title: 'Каталог', icon: 'bx-food-menu' }"
  >
    <VerticalNavLink :item="{ title: 'Разделы', to: '/menu/categories' }" />
    <VerticalNavLink :item="{ title: 'Товары', to: '/menu/products' }" />
    <VerticalNavLink :item="{ title: 'Опции', to: '/menu/options' }" />
    <VerticalNavLink
      v-if="hasPermission('menu_sync')"
      :item="{ title: 'Импорт', to: '/menu/import' }"
    />
  </VerticalNavGroup>

  <VerticalNavLink
    v-if="hasPermission('orders_view')"
    :item="{ title: 'Заказы', icon: 'bx-receipt', to: '/orders' }"
  />

  <!-- Курьеры (Мониторинг) -->
  <VerticalNavLink
    v-if="hasPermission('orders_view') || hasPermission('courier_reports_view') || authState.user?.iiko_id || authState.user?.employee?.iiko_id"
    :item="{ title: 'Курьеры', icon: 'bx-cycling', to: '/courier' }"
  />

  <!-- Клиенты -->
  <VerticalNavGroup
    v-if="hasPermission('customers_view')"
    :item="{ title: 'Клиенты', icon: 'bx-group' }"
  >
    <VerticalNavLink :item="{ title: 'Все клиенты', to: '/clients' }" />
  </VerticalNavGroup>

  <!-- NPS -->
  <VerticalNavGroup
    v-if="hasPermission('reports_view')"
    :item="{ title: 'NPS', icon: 'bx-message-square-detail' }"
  >
    <VerticalNavLink :item="{ title: 'Отзывы', to: '/nps/reviews' }" />
    <VerticalNavLink :item="{ title: 'Оценка блюд', to: '/nps/dishes' }" />
    <VerticalNavLink :item="{ title: 'NPS', to: '/nps/analytics' }" />
  </VerticalNavGroup>

  <!-- Акции и Маркетинг -->
  <template v-if="hasPermission('settings_view')">
    <VerticalNavGroup :item="{ title: 'Акции', icon: 'bx-gift' }">
      <VerticalNavLink :item="{ title: 'Контентная информация', to: '/promotions/content' }" />
      <VerticalNavLink :item="{ title: 'Шкала подарков', to: '/promotions/scale' }" />
    </VerticalNavGroup>

    <VerticalNavGroup :item="{ title: 'Маркетинг и вовлеченность', icon: 'bx-badge-check' }">
      <VerticalNavLink :item="{ title: 'Истории', to: '/marketing/stories' }" />
      <VerticalNavLink :item="{ title: 'Промокоды', to: '/promo' }" />
      <VerticalNavLink :item="{ title: 'Воронки', to: '/marketing/funnels' }" />
      <VerticalNavLink :item="{ title: 'Программа лояльности', to: '/loyalty' }" />
    </VerticalNavGroup>
  </template>

  <!-- Рассылки -->
  <VerticalNavGroup
    v-if="hasPermission('settings_view')"
    :item="{ title: 'Рассылки', icon: 'bx-broadcast' }"
  >
    <VerticalNavLink :item="{ title: 'Общие рассылки', to: '/marketing/mailings' }" />
    <VerticalNavLink :item="{ title: 'Настройки Telegram Бота', to: '/settings/bot' }" />
    <VerticalNavLink :item="{ title: 'Настройки VK Бота', to: '/settings/vk' }" />
    <VerticalNavLink :item="{ title: 'Уведомления VK Бота', to: '/settings/vk-notifications' }" />
    <VerticalNavLink :item="{ title: 'Парсер ВК', to: '/settings/vk-parser' }" />
    <VerticalNavLink :item="{ title: 'Настройка MAX', icon: 'bx-cog', to: '/settings/max' }" />
    <VerticalNavLink :item="{ title: 'Настройка каскада', icon: 'bx-git-branch', to: '/mailings/cascades' }" />
  </VerticalNavGroup>

  <!-- Система -->
  <VerticalNavGroup
    v-if="hasPermission('settings_view')"
    :item="{ title: 'Система', icon: 'bx-cog' }"
  >
    <VerticalNavLink :item="{ title: 'Сервер', icon: 'bx-server', to: '/system/server' }" />
    <VerticalNavLink :item="{ title: 'Метки', to: '/system/tags' }" />
    <VerticalNavLink :item="{ title: 'Настройки iiko', to: '/settings/iiko' }" />
    <VerticalNavLink :item="{ title: 'Логи синхронизации', to: '/settings/sync-logs' }" />
    <VerticalNavLink :item="{ title: 'Настройки Яндекс', to: '/settings/yandex' }" />
    <VerticalNavLink :item="{ title: 'Фоновые процессы', icon: 'bx-refresh', to: '/system/tasks' }" />
    <VerticalNavLink :item="{ title: 'Логи системы', icon: 'bx-list-ul', to: '/system/logs' }" />
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
  <template v-if="hasPermission('users_view')">
    <VerticalNavSectionTitle :item="{ heading: 'Администрирование' }" />
    <VerticalNavLink
      v-if="hasPermission('courier_reports_view')"
      :item="{ title: 'Сотрудники', icon: 'bx-id-card', to: '/employees' }"
    />
    <VerticalNavGroup :item="{ title: 'Пользователи', icon: 'bx-user' }">
      <VerticalNavLink :item="{ title: 'Все пользователи', to: '/users' }" />
      <VerticalNavLink
        v-if="hasPermission('roles_manage')"
        :item="{ title: 'Управление ролями', to: { path: '/users', query: { tab: 'roles' } } }"
      />
    </VerticalNavGroup>
  </template>
</template>
