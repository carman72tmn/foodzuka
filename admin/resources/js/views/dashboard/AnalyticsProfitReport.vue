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
      total_orders: 0,
      total_revenue_formatted: '0 ₽',
      daily_trend: [],
    }),
  },
})

const vuetifyTheme = useTheme()
const display = useDisplay()

const series = computed(() => [{
  name: 'Заказов',
  data: (props.weekSummary.daily_trend || []).map(d => d.orders_count),
}])

const chartOptions = computed(() => {
  const currentTheme = vuetifyTheme.current.value.colors
  
  return {
    chart: {
      parentHeightOffset: 0,
      toolbar: { show: false },
      dropShadow: {
        top: 8,
        blur: 4,
        left: 0,
        enabled: true,
        opacity: 0.12,
        color: currentTheme.warning,
      },
    },
    tooltip: {
      enabled: true,
      y: {
        formatter: val => `${val} заказов`,
      },
    },
    colors: [`rgba(${ hexToRgb(String(currentTheme.warning)) }, 1)`],
    stroke: {
      width: 4,
      curve: 'smooth',
      lineCap: 'round',
    },
    grid: {
      show: false,
      padding: {
        top: -21,
        left: -5,
        bottom: -8,
      },
    },
    xaxis: {
      labels: { show: false },
      axisTicks: { show: false },
      axisBorder: { show: false },
    },
    yaxis: { labels: { show: false } },
    responsive: [
      {
        breakpoint: display.thresholds.value.lg,
        options: {
          chart: {
            height: 140,
            width: '100%',
          },
        },
      },
      {
        breakpoint: display.thresholds.value.md,
        options: {
          chart: {
            height: 120,
            width: '100%',
          },
        },
      },
    ],
  }
})
</script>

<template>
  <VCard>
    <VCardText class="d-flex justify-space-between h-100">
      <div class="d-flex flex-column justify-space-between gap-y-3">
        <div>
          <h5 class="text-h6 mb-1 font-weight-bold">
            Объем заказов
          </h5>
          <VChip
            color="warning"
            size="small"
            variant="tonal"
          >
            За 7 дней
          </VChip>
        </div>

        <div>
          <div class="d-flex gap-1 align-center text-success mb-1">
            <VIcon
              icon="bx-trending-up"
              size="18"
            />
            <span class="text-caption font-weight-medium">Активность</span>
          </div>

          <h4 class="text-h4 font-weight-bold">
            {{ props.weekSummary.total_orders }} шт
          </h4>
        </div>
      </div>

      <div class="h-100 d-flex align-center" style="min-width: 140px;">
        <VueApexCharts
          type="line"
          :height="120"
          width="100%"
          :options="chartOptions"
          :series="series"
        />
      </div>
    </VCardText>
  </VCard>
</template>
