<script setup>
import {
  useDisplay,
  useTheme,
} from 'vuetify'
import { hexToRgb } from '@core/utils/colorConverter'

const props = defineProps({
  weekSummary: {
    type: Object,
    default: () => ({
      total_revenue: 0,
      total_revenue_formatted: '0 ₽',
      total_orders: 0,
      daily_trend: [],
    }),
  },
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
    }),
  },
  yesterday: {
    type: Object,
    default: () => ({
      revenue: 0,
      revenue_formatted: '0 ₽',
      orders_count: 0,
    }),
  },
})

const vuetifyTheme = useTheme()
const display = useDisplay()

const series = computed(() => [
  {
    name: 'В кассе (₽)',
    data: (props.weekSummary.daily_trend || []).map(d => d.revenue),
  },
  {
    name: 'Ожидаемая (₽)',
    data: (props.weekSummary.daily_trend || []).map(d => d.expected_revenue || d.revenue),
  },
])

const chartCategories = computed(() => {
  return (props.weekSummary.daily_trend || []).map(d => {
    return d.is_today ? `Сегодня (${d.date})` : `${d.date} ${d.day_name}`
  })
})

// Процент сегодняшней выручки от среднедневной за неделю
const weekAverageDaily = computed(() => {
  const days = (props.weekSummary.daily_trend || []).filter(d => d.revenue > 0)
  if (!days.length) return 0
  const sum = days.reduce((acc, d) => acc + d.revenue, 0)
  return sum / days.length
})

const radialPercentage = computed(() => {
  if (weekAverageDaily.value <= 0) return 0
  const pct = Math.round((props.today.revenue / weekAverageDaily.value) * 100)
  return Math.min(pct, 100)
})

const chartOptions = computed(() => {
  const currentTheme = vuetifyTheme.current.value.colors
  const variableTheme = vuetifyTheme.current.value.variables
  const secondaryTextColor = `rgba(${ hexToRgb(String(currentTheme['on-surface'])) },${ variableTheme['medium-emphasis-opacity'] })`
  const borderColor = `rgba(${ hexToRgb(String(variableTheme['border-color'])) },${ variableTheme['border-opacity'] })`
  
  return {
    bar: {
      chart: {
        parentHeightOffset: 6,
        toolbar: { show: false },
      },
      dataLabels: { enabled: false },
      stroke: {
        width: 2,
        colors: ['transparent'],
      },
      colors: [
        `rgba(${ hexToRgb(String(currentTheme.primary)) }, 1)`,
        `rgba(${ hexToRgb(String(currentTheme.info)) }, 0.85)`,
      ],
      states: {
        hover: { filter: { type: 'none' } },
        active: { filter: { type: 'none' } },
      },
      grid: {
        strokeDashArray: 6,
        borderColor,
        padding: { bottom: 5 },
      },
      plotOptions: {
        bar: {
          borderRadius: 8,
          columnWidth: '40%',
          distributed: false,
        },
      },
      xaxis: {
        categories: chartCategories.value,
        axisBorder: { show: false },
        axisTicks: { show: false },
        labels: {
          style: {
            colors: secondaryTextColor,
            fontSize: '12px',
            fontFamily: 'Public Sans',
          },
        },
      },
      yaxis: {
        labels: {
          formatter: val => `${Math.round(val / 1000)}k ₽`,
          style: {
            colors: secondaryTextColor,
            fontSize: '12px',
            fontFamily: 'Public Sans',
          },
        },
      },
      tooltip: {
        y: {
          formatter: val => `${Number(val).toLocaleString('ru-RU')} ₽`,
        },
      },
    },
    radial: {
      chart: { sparkline: { enabled: true } },
      labels: ['От средней'],
      stroke: { dashArray: 5 },
      colors: [`rgba(${ hexToRgb(String(currentTheme.primary)) }, 1)`],
      fill: {
        type: 'gradient',
        gradient: {
          shade: 'dark',
          opacityTo: 0.6,
          opacityFrom: 1,
          shadeIntensity: 0.5,
          stops: [30, 70, 100],
          inverseColors: false,
          gradientToColors: [currentTheme.success],
        },
      },
      plotOptions: {
        radialBar: {
          endAngle: 150,
          startAngle: -140,
          hollow: { size: '55%' },
          track: { background: 'transparent' },
          dataLabels: {
            name: {
              offsetY: 25,
              fontWeight: 500,
              fontSize: '14px',
              color: secondaryTextColor,
              fontFamily: 'Public Sans',
            },
            value: {
              offsetY: -15,
              fontWeight: 500,
              fontSize: '24px',
              color: currentTheme.primary,
              fontFamily: 'Public Sans',
              formatter: value => `${value}%`,
            },
          },
        },
      },
    },
  }
})

const balanceCards = computed(() => [
  {
    icon: 'bx-wallet',
    amount: props.today.revenue_formatted,
    label: 'В кассе (факт)',
    sub: `${props.today.paid_orders_count ?? props.today.orders_count} оплачено`,
    color: 'success',
  },
  {
    icon: 'bx-time-five',
    amount: props.today.expected_revenue_formatted || props.today.revenue_formatted,
    label: 'Ожидаемая',
    sub: `всего ${props.today.orders_count} заказов`,
    color: 'info',
  },
  {
    icon: 'bx-history',
    amount: props.yesterday.revenue_formatted,
    label: 'Вчера',
    sub: `${props.yesterday.orders_count} заказов`,
    color: 'secondary',
  },
])
</script>

<template>
  <VCard>
    <VRow no-gutters>
      <VCol
        cols="12"
        sm="7"
        xl="8"
        :class="$vuetify.display.smAndUp ? 'border-e' : 'border-b'"
      >
        <VCardItem class="pb-0">
          <VCardTitle>Динамика выручки за 7 дней</VCardTitle>
          <VCardSubtitle>Общая сумма за неделю: <strong class="text-primary">{{ props.weekSummary.total_revenue_formatted }}</strong> ({{ props.weekSummary.total_orders }} заказов)</VCardSubtitle>
        </VCardItem>

        <!-- bar chart -->
        <VCardText class="pb-2">
          <VueApexCharts
            type="bar"
            :height="320"
            :options="chartOptions.bar"
            :series="series"
          />
        </VCardText>
      </VCol>

      <VCol
        cols="12"
        sm="5"
        xl="4"
      >
        <VCardText class="text-center pt-6">
          <div class="text-subtitle-2 font-weight-bold mb-2">
            Темп дня vs Средняя недельная
          </div>

          <!-- radial chart -->
          <VueApexCharts
            type="radialBar"
            :height="190"
            :options="chartOptions.radial"
            :series="[radialPercentage]"
          />

          <div class="d-flex flex-column gap-3 mt-4 px-3">
            <div
              v-for="item in balanceCards"
              :key="item.label"
              class="d-flex align-center justify-space-between p-2 rounded"
              style="background-color: rgba(var(--v-theme-on-surface), 0.04); padding: 8px 12px;"
            >
              <div class="d-flex align-center gap-3">
                <VAvatar
                  size="36"
                  rounded
                  variant="tonal"
                  :color="item.color"
                >
                  <VIcon :icon="item.icon" size="20" />
                </VAvatar>
                <div class="text-start">
                  <div class="text-caption text-medium-emphasis">{{ item.label }}</div>
                  <div class="text-body-2 font-weight-medium">{{ item.sub }}</div>
                </div>
              </div>
              <div class="text-end">
                <span class="font-weight-bold text-subtitle-2">{{ item.amount }}</span>
              </div>
            </div>
          </div>
        </VCardText>
      </VCol>
    </VRow>
  </VCard>
</template>
