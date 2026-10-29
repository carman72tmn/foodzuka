<script setup>
import { useTheme } from 'vuetify'
import illustrationJohnDark from '@images/cards/illustration-john-dark.png'
import illustrationJohnLight from '@images/cards/illustration-john-light.png'

const props = defineProps({
  today: {
    type: Object,
    default: () => ({
      revenue: 0,
      revenue_formatted: '0 ₽',
      expected_revenue: 0,
      expected_revenue_formatted: '0 ₽',
      unpaid_revenue: 0,
      unpaid_revenue_formatted: '0 ₽',
      orders_count: 0,
      paid_orders_count: 0,
      unpaid_orders_count: 0,
      average_check: 0,
      average_check_formatted: '0 ₽',
      active_orders: 0,
      delivered_orders: 0,
    }),
  },
  growth: {
    type: Object,
    default: () => ({
      revenue_change: 0,
      expected_revenue_change: 0,
      orders_change: 0,
      average_check_change: 0,
    }),
  },
})

const { global } = useTheme()
const illustrationJohn = computed(() => global.name.value === 'dark' ? illustrationJohnDark : illustrationJohnLight)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return 'Доброе утро'
  if (hour >= 12 && hour < 17) return 'Добрый день'
  if (hour >= 17 && hour < 23) return 'Добрый вечер'
  return 'Доброй ночи'
})
</script>

<template>
  <VCard class="text-center text-sm-start">
    <VRow no-gutters>
      <VCol
        cols="12"
        sm="8"
        order="2"
        order-sm="1"
      >
        <VCardItem class="pb-2">
          <VCardTitle class="text-primary font-weight-bold">
            {{ greeting }}, Администратор! 🍣
          </VCardTitle>
          <VCardSubtitle>
            Сводка работы ресторана на сегодня
          </VCardSubtitle>
        </VCardItem>

        <VCardText>
          <div class="d-flex flex-wrap align-center gap-x-5 gap-y-2 mb-2">
            <div>
              <span class="text-caption text-medium-emphasis d-block">Текущая выручка (в кассе):</span>
              <strong class="text-h6 font-weight-bold text-success">{{ props.today.revenue_formatted }}</strong>
            </div>
            <div class="border-s ps-4">
              <span class="text-caption text-medium-emphasis d-block">Ожидаемая выручка:</span>
              <strong class="text-h6 font-weight-bold text-info">{{ props.today.expected_revenue_formatted || props.today.revenue_formatted }}</strong>
            </div>
          </div>
          <div v-if="props.today.unpaid_revenue && props.today.unpaid_revenue > 0" class="text-caption font-weight-medium text-warning mb-2">
            ⏳ Ожидает оплаты: {{ props.today.unpaid_revenue_formatted }} ({{ props.today.unpaid_orders_count }} зак.)
          </div>
          <div class="text-body-2 text-medium-emphasis">
            Всего заказов: <strong>{{ props.today.orders_count }}</strong> (оплачено: <strong>{{ props.today.paid_orders_count ?? props.today.orders_count }}</strong>) • Средний чек: <strong>{{ props.today.average_check_formatted }}</strong>
          </div>
          <div class="text-caption text-medium-emphasis mt-1">
            <span v-if="props.today.active_orders > 0" class="text-warning font-weight-medium">
              🔥 В работе: {{ props.today.active_orders }} заказ(ов)
            </span>
            <span v-else class="text-success">
              ✅ Все текущие заказы обработаны
            </span>
            • Доставлено: {{ props.today.delivered_orders }}
          </div>

          <VBtn
            variant="tonal"
            class="mt-4"
            size="small"
            to="/orders"
            color="primary"
            prepend-icon="bx-receipt"
          >
            Перейти к заказам
          </VBtn>
        </VCardText>
      </VCol>

      <VCol
        cols="12"
        sm="4"
        order="1"
        order-sm="2"
        class="text-center"
      >
        <img
          :src="illustrationJohn"
          :height="$vuetify.display.xs ? '140' : '175'"
          :class="$vuetify.display.xs ? 'mt-4 mb-n2' : 'position-absolute'"
          class="john-illustration flip-in-rtl"
        >
      </VCol>
    </VRow>
  </VCard>
</template>

<style lang="scss" scoped>
.john-illustration {
  inset-block-end: -0.125rem;
  inset-inline-end: 2.5rem;
}
</style>
