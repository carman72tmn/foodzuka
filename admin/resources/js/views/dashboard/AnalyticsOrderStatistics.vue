<script setup>
import { useTheme } from 'vuetify'
import { hexToRgb } from '@core/utils/colorConverter'

const props = defineProps({
  orderTypes: {
    type: Object,
    default: () => ({
      delivery: { count: 0, revenue: 0, revenue_formatted: '0 ₽' },
      pickup: { count: 0, revenue: 0, revenue_formatted: '0 ₽' },
      total_count: 0,
    }),
  },
})

const vuetifyTheme = useTheme()

const series = computed(() => {
  const d = props.orderTypes.delivery?.count || 0
  const p = props.orderTypes.pickup?.count || 0
  if (d === 0 && p === 0) return [1, 1]
  return [d, p]
})

const chartOptions = computed(() => {
  const currentTheme = vuetifyTheme.current.value.colors
  const variableTheme = vuetifyTheme.current.value.variables
  const secondaryTextColor = `rgba(${ hexToRgb(String(currentTheme['on-surface'])) },${ variableTheme['medium-emphasis-opacity'] })`
  const primaryTextColor = `rgba(${ hexToRgb(String(currentTheme['on-surface'])) },${ variableTheme['high-emphasis-opacity'] })`
  
  const total = props.orderTypes.total_count || 0
  const deliveryPct = total > 0 ? Math.round((props.orderTypes.delivery.count / total) * 100) : 0

  return {
    chart: {
      sparkline: { enabled: true },
      animations: { enabled: true },
    },
    stroke: {
      width: 4,
      colors: [currentTheme.surface],
    },
    legend: { show: false },
    tooltip: { enabled: true },
    dataLabels: { enabled: false },
    labels: [
      'Доставка',
      'Самовывоз',
    ],
    colors: [
      currentTheme.primary,
      currentTheme.success,
    ],
    grid: {
      padding: {
        top: -7,
        bottom: 5,
      },
    },
    plotOptions: {
      pie: {
        expandOnClick: false,
        donut: {
          size: '72%',
          labels: {
            show: true,
            name: {
              offsetY: 17,
              fontSize: '12px',
              color: secondaryTextColor,
              fontFamily: 'Public Sans',
            },
            value: {
              offsetY: -17,
              fontSize: '16px',
              color: primaryTextColor,
              fontFamily: 'Public Sans',
              fontWeight: 600,
            },
            total: {
              show: true,
              label: 'Доставка',
              fontSize: '11px',
              lineHeight: '16px',
              formatter: () => `${deliveryPct}%`,
              color: secondaryTextColor,
              fontFamily: 'Public Sans',
            },
          },
        },
      },
    },
  }
})

const orderItems = computed(() => {
  const total = props.orderTypes.total_count || 1
  const delivCount = props.orderTypes.delivery?.count || 0
  const pickupCount = props.orderTypes.pickup?.count || 0
  
  const delivPct = Math.round((delivCount / total) * 100)
  const pickupPct = Math.round((pickupCount / total) * 100)

  return [
    {
      title: 'Самовывоз',
      subtitle: `${pickupCount} заказов (${pickupPct}%)`,
      amount: props.orderTypes.pickup?.revenue_formatted || '0 ₽',
      avatarColor: 'success',
      avatarIcon: 'bx-store',
    },
    {
      title: 'Доставка курьером',
      subtitle: `${delivCount} заказов (${delivPct}%)`,
      amount: props.orderTypes.delivery?.revenue_formatted || '0 ₽',
      avatarColor: 'primary',
      avatarIcon: 'bx-cycling',
    },
  ]
})
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle>
        Типы заказов (7 дней)
      </VCardTitle>
      <VCardSubtitle>Распределение заказов ресторана</VCardSubtitle>
    </VCardItem>

    <VCardText>
      <div class="d-flex align-center justify-space-between mb-6">
        <div>
          <h3 class="text-h3 mb-1 font-weight-bold">
            {{ props.orderTypes.total_count || 0 }}
          </h3>
          <div class="text-caption text-medium-emphasis">
            Всего заказов за неделю
          </div>
        </div>

        <div>
          <VueApexCharts
            type="donut"
            :height="125"
            width="125"
            :options="chartOptions"
            :series="series"
          />
        </div>
      </div>

      <VList class="card-list">
        <VListItem
          v-for="order in orderItems"
          :key="order.title"
        >
          <template #prepend>
            <VAvatar
              size="40"
              rounded
              variant="tonal"
              :color="order.avatarColor"
            >
              <VIcon :icon="order.avatarIcon" size="22" />
            </VAvatar>
          </template>

          <VListItemTitle class="font-weight-medium">
            {{ order.title }}
          </VListItemTitle>
          <VListItemSubtitle class="text-body-2">
            {{ order.subtitle }}
          </VListItemSubtitle>

          <template #append>
            <span class="font-weight-bold text-subtitle-2">{{ order.amount }}</span>
          </template>
        </VListItem>
      </VList>
    </VCardText>
  </VCard>
</template>

<style lang="scss">
.card-list {
  --v-card-list-gap: 1.25rem;
}
</style>
