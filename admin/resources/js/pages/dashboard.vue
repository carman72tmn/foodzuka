<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import AnalyticsCongratulations from '@/views/dashboard/AnalyticsCongratulations.vue'
import AnalyticsOrderStatistics from '@/views/dashboard/AnalyticsOrderStatistics.vue'
import AnalyticsProfitReport from '@/views/dashboard/AnalyticsProfitReport.vue'
import AnalyticsTotalRevenue from '@/views/dashboard/AnalyticsTotalRevenue.vue'
import AnalyticsTransactions from '@/views/dashboard/AnalyticsTransactions.vue'
import EmployeeStatus from '@/views/dashboard/EmployeeStatus.vue'

// 👉 Images
import chart from '@images/cards/chart-success.png'
import card from '@images/cards/credit-card-primary.png'
import paypal from '@images/cards/paypal-error.png'
import wallet from '@images/cards/wallet-info.png'

const loading = ref(false)
const lastUpdated = ref('')

const summary = ref({
  today: {
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
  },
  yesterday: {
    revenue: 0,
    revenue_formatted: '0 ₽',
    expected_revenue: 0,
    expected_revenue_formatted: '0 ₽',
    orders_count: 0,
    average_check: 0,
    average_check_formatted: '0 ₽',
  },
  growth: {
    revenue_change: 0,
    expected_revenue_change: 0,
    orders_change: 0,
    average_check_change: 0,
  },
  week_summary: {
    total_revenue: 0,
    total_revenue_formatted: '0 ₽',
    total_expected_revenue: 0,
    total_expected_revenue_formatted: '0 ₽',
    total_orders: 0,
    daily_trend: [],
  },
  order_types: {
    delivery: { count: 0, revenue: 0, revenue_formatted: '0 ₽' },
    pickup: { count: 0, revenue: 0, revenue_formatted: '0 ₽' },
    total_count: 0,
  },
  recent_transactions: [],
  open_shifts_count: 0,
})

let refreshTimer = null

const fetchDashboardSummary = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/v1/orders/dashboard-summary')
    if (res.ok) {
      const data = await res.json()
      if (data.status === 'success') {
        summary.value = data
        lastUpdated.value = data.updated_at || new Date().toLocaleTimeString('ru-RU')
      }
    }
  } catch (e) {
    console.error('Ошибка загрузки дашборда:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboardSummary()
  // Автообновление каждые 60 секунд
  refreshTimer = setInterval(fetchDashboardSummary, 60000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<template>
  <VRow>
    <!-- 👉 Header bar with refresh & time -->
    <VCol cols="12" class="d-flex align-center justify-space-between pb-0">
      <div>
        <h4 class="text-h4 font-weight-bold mb-1">
          Панель управления
        </h4>
        <div class="text-caption text-medium-emphasis">
          Актуальные показатели ресторанов в реальном времени
          <span v-if="lastUpdated">• Обновлено в {{ lastUpdated }}</span>
        </div>
      </div>

      <div>
        <VBtn
          variant="tonal"
          color="primary"
          size="small"
          prepend-icon="bx-refresh"
          :loading="loading"
          @click="fetchDashboardSummary"
        >
          Обновить
        </VBtn>
      </div>
    </VCol>

    <!-- 👉 Congratulations -->
    <VCol
      cols="12"
      md="8"
    >
      <AnalyticsCongratulations
        :today="summary.today"
        :growth="summary.growth"
      />
    </VCol>

    <VCol
      cols="12"
      sm="4"
    >
      <VRow>
        <!-- 👉 Текущая выручка (в кассе за оплаченные заказы) -->
        <VCol
          cols="12"
          md="6"
        >
          <CardStatisticsVertical
            v-bind="{
              title: 'Текущая выручка',
              image: chart,
              stats: summary.today.revenue_formatted,
              change: summary.growth.revenue_change,
            }"
          />
        </VCol>

        <!-- 👉 Ожидаемая выручка (с учетом неоплаченных заказов) -->
        <VCol
          cols="12"
          md="6"
        >
          <CardStatisticsVertical
            v-bind="{
              title: 'Ожидаемая выручка',
              image: card,
              stats: summary.today.expected_revenue_formatted || summary.today.revenue_formatted,
              change: summary.growth.expected_revenue_change || summary.growth.revenue_change,
            }"
          />
        </VCol>
      </VRow>
    </VCol>

    <!-- 👉 Total Revenue -->
    <VCol
      cols="12"
      md="8"
      order="2"
      order-md="1"
    >
      <AnalyticsTotalRevenue
        :week-summary="summary.week_summary"
        :today="summary.today"
        :yesterday="summary.yesterday"
      />
    </VCol>

    <VCol
      cols="12"
      sm="8"
      md="4"
      order="1"
      order-md="2"
    >
      <VRow>
        <!-- 👉 Orders Today -->
        <VCol
          cols="12"
          sm="6"
        >
          <CardStatisticsVertical
            v-bind="{
              title: 'Заказов сегодня',
              image: wallet,
              stats: `${summary.today.orders_count} шт`,
              change: summary.growth.orders_change,
            }"
          />
        </VCol>

        <!-- 👉 Average check -->
        <VCol
          cols="12"
          sm="6"
        >
          <CardStatisticsVertical
            v-bind="{
              title: 'Средний чек',
              image: paypal,
              stats: summary.today.average_check_formatted,
              change: summary.growth.average_check_change,
            }"
          />
        </VCol>
      </VRow>

      <VRow>
        <!-- 👉 Orders volume 7-day sparkline -->
        <VCol
          cols="12"
          sm="12"
        >
          <AnalyticsProfitReport
            :week-summary="summary.week_summary"
          />
        </VCol>
      </VRow>
    </VCol>

    <!-- 👉 Order Statistics (Delivery vs Pickup) -->
    <VCol
      cols="12"
      md="4"
      sm="6"
      order="3"
    >
      <AnalyticsOrderStatistics
        :order-types="summary.order_types"
      />
    </VCol>

    <!-- 👉 Employee Status -->
    <VCol
      cols="12"
      md="4"
      sm="6"
      order="3"
    >
      <EmployeeStatus />
    </VCol>

    <!-- 👉 Recent Transactions -->
    <VCol
      cols="12"
      md="4"
      sm="6"
      order="3"
    >
      <AnalyticsTransactions
        :transactions="summary.recent_transactions"
      />
    </VCol>
  </VRow>
</template>
