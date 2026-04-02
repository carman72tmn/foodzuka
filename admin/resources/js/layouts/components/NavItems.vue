<script setup>
import VerticalNavSectionTitle from "@/@layouts/components/VerticalNavSectionTitle.vue"
import VerticalNavGroup from "@layouts/components/VerticalNavGroup.vue"
import VerticalNavLink from "@layouts/components/VerticalNavLink.vue"
</script>

<template>
  <VerticalNavSectionTitle :item="{ heading: 'Управление компанией' }" />
  <VerticalNavLink :item="{ title: 'Мои компании', icon: 'bx-buildings', to: '/companies' }" />

  <VerticalNavGroup :item="{ title: 'Филиалы', icon: 'bx-store' }">
    <VerticalNavLink :item="{ title: 'Все филиалы', to: '/branches' }" />
    <VerticalNavLink :item="{ title: 'Зоны доставки', to: '/branches/zones' }" />
  </VerticalNavGroup>

  <VerticalNavGroup :item="{ title: 'Каталог', icon: 'bx-food-menu' }">
    <VerticalNavLink :item="{ title: 'Разделы', to: '/menu/categories' }" />
    <VerticalNavLink :item="{ title: 'Товары', to: '/menu/products' }" />
    <VerticalNavLink :item="{ title: 'Опции', to: '/menu/options' }" />
    <VerticalNavLink :item="{ title: 'Импорт', to: '/menu/import' }" />
  </VerticalNavGroup>

  <VerticalNavLink :item="{ title: 'Заказы', icon: 'bx-receipt', to: '/orders' }" />

  <VerticalNavGroup :item="{ title: 'Клиенты', icon: 'bx-group' }">
    <VerticalNavLink :item="{ title: 'Все клиенты', to: '/clients' }" />
    <VerticalNavLink :item="{ title: 'Посетители ВК', to: '/clients/vk' }" />
  </VerticalNavGroup>

  <VerticalNavGroup :item="{ title: 'NPS', icon: 'bx-message-square-detail' }">
    <VerticalNavLink :item="{ title: 'Отзывы', to: '/nps/reviews' }" />
    <VerticalNavLink :item="{ title: 'Оценка блюд', to: '/nps/dishes' }" />
    <VerticalNavLink :item="{ title: 'NPS', to: '/nps/analytics' }" />
  </VerticalNavGroup>

  <VerticalNavGroup :item="{ title: 'Акции', icon: 'bx-gift' }">
    <VerticalNavLink :item="{ title: 'Контентная информация', to: '/promotions/content' }" />
    <VerticalNavLink :item="{ title: 'Шкала подарков', to: '/promotions/scale' }" />
  </VerticalNavGroup>

  <VerticalNavGroup :item="{ title: 'Маркетинг и вовлеченность', icon: 'bx-badge-check' }">
    <VerticalNavLink :item="{ title: 'Истории', to: '/marketing/stories' }" />
    <VerticalNavLink :item="{ title: 'Промокоды', to: '/promo' }" />
    <VerticalNavLink :item="{ title: 'Воронки', to: '/marketing/funnels' }" />
    <VerticalNavLink :item="{ title: 'Рассылки', to: '/marketing/mailings' }" />
    <VerticalNavLink :item="{ title: 'Программа лояльности', to: '/loyalty' }" />
  </VerticalNavGroup>

  <VerticalNavGroup :item="{ title: 'Система', icon: 'bx-cog' }">
    <VerticalNavLink :item="{ title: 'Метки', to: '/system/tags' }" />
    <VerticalNavLink :item="{ title: 'Настройки iiko', to: '/settings/iiko' }" />
    <VerticalNavLink :item="{ title: 'Настройки Telegram Бота', to: '/settings/bot' }" />
    <VerticalNavLink :item="{ title: 'Настройки VK Бота', to: '/settings/vk' }" />
  </VerticalNavGroup>

  <VerticalNavGroup :item="{ title: 'Отчеты', icon: 'bx-bar-chart-alt-2' }">
    <VerticalNavLink :item="{ title: 'Выручка', to: '/reports/revenue' }" />
    <VerticalNavLink :item="{ title: 'Продажи', to: '/reports/sales' }" />
    <VerticalNavLink :item="{ title: 'Продажи (по товарам)', to: '/reports/products' }" />
    <VerticalNavLink :item="{ title: 'Продажи (по дням)', to: '/reports/days' }" />
    <VerticalNavLink :item="{ title: 'Клиенты', to: '/reports/clients' }" />
    <VerticalNavLink :item="{ title: 'Заказы', to: '/reports/orders' }" />
  </VerticalNavGroup>

  <VerticalNavSectionTitle :item="{ heading: 'Администрирование' }" />
  <VerticalNavLink :item="{ title: 'Сотрудники', icon: 'bx-id-card', to: '/employees' }" />
  <VerticalNavLink :item="{ title: 'Пользователи', icon: 'bx-user', to: '/users' }" />
</template>
