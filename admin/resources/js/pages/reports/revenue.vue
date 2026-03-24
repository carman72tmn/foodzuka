<template>
  <div>
    <VCard class="mb-6">
      <VCardTitle class="d-flex align-center justify-space-between flex-wrap gap-3 pa-4">
        <div>
          <div class="text-h5 font-weight-bold">📊 Отчет по выручке</div>
          <div class="text-caption text-medium-emphasis">
            Источник: iiko OLAP. Данные за сегодня — в режиме реального времени.
          </div>
        </div>
        <div class="d-flex align-center gap-2 flex-wrap">
          <VBtnToggle
            v-model="selectedPeriod"
            density="compact"
            color="primary"
            variant="outlined"
            divided
            @update:model-value="fetchReport"
          >
            <VBtn value="today">Сегодня</VBtn>
            <VBtn value="yesterday">Вчера</VBtn>
            <VBtn value="week">7 дней</VBtn>
            <VBtn value="month">Месяц</VBtn>
            <VBtn value="year">Год</VBtn>
            <VBtn value="custom">Произвольный</VBtn>
          </VBtnToggle>

          <VBtn
            :loading="loading"
            :disabled="loading"
            color="primary"
            variant="tonal"
            size="small"
            prepend-icon="ri-refresh-line"
            @click="fetchReport(true)"
          >
            Обновить
          </VBtn>
        </div>
      </VCardTitle>

      <!-- Фильтр по диапазону дат (если custom) -->
      <VCardText v-if="selectedPeriod === 'custom'">
        <VRow>
          <VCol cols="12" sm="6">
            <VTextField
              v-model="customFrom"
              type="datetime-local"
              label="Дата от"
              density="compact"
              variant="outlined"
            />
          </VCol>
          <VCol cols="12" sm="6">
            <VTextField
              v-model="customTo"
              type="datetime-local"
              label="Дата до"
              density="compact"
              variant="outlined"
            />
          </VCol>
          <VCol cols="12">
            <VBtn color="primary" @click="fetchReport(true)">
              Сформировать отчет
            </VBtn>
          </VCol>
        </VRow>
      </VCardText>

      <!-- Фильтр по удаленным заказам -->
      <VCardText class="pt-0">
        <VSwitch
          v-model="includeDeleted"
          label="Включать удаленные заказы"
          color="warning"
          hide-details
          density="compact"
          @update:model-value="fetchReport"
        />
      </VCardText>
    </VCard>

    <!-- Карточки с итогами -->
    <VRow class="mb-4">
      <VCol v-for="card in summaryCards" :key="card.title" cols="12" sm="6" md="4" lg="2">
        <VCard>
          <VCardText class="pa-3">
            <div class="text-caption text-medium-emphasis mb-1">{{ card.title }}</div>
            <div class="text-h6 font-weight-bold" :class="card.color">
              {{ card.value }}
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Таблица данных -->
    <VCard>
      <VCardTitle class="pa-4 text-subtitle-1 font-weight-medium">
        Детализация по торговым предприятиям
      </VCardTitle>

      <VDivider />

      <!-- Индикатор загрузки -->
      <div v-if="loading" class="d-flex justify-center align-center pa-8">
        <VProgressCircular indeterminate color="primary" />
      </div>

      <!-- Ошибка -->
      <VAlert
        v-else-if="error"
        color="error"
        class="ma-4"
        variant="tonal"
      >
        {{ error }}
      </VAlert>

      <!-- Нет данных -->
      <div v-else-if="!reportData.length" class="text-center pa-8 text-medium-emphasis">
        <VIcon icon="ri-bar-chart-2-line" size="48" class="mb-2" />
        <div>Нет данных для выбранного периода</div>
        <VBtn
          class="mt-3"
          color="primary"
          variant="tonal"
          @click="fetchReport(true)"
        >
          Загрузить данные из iiko
        </VBtn>
      </div>

      <!-- Таблица -->
      <VTable v-else hover>
        <thead>
          <tr>
            <th>Дата</th>
            <th>Торговое предприятие</th>
            <th class="text-right">Выручка</th>
            <th class="text-right">Средний чек</th>
            <th class="text-right">Сумма скидки</th>
            <th class="text-right">Наценка</th>
            <th class="text-right">Наценка %</th>
            <th class="text-right">Себестоимость</th>
            <th class="text-right">Себест. %</th>
            <th class="text-right">Кол-во заказов</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in reportData" :key="idx">
            <td>
              <div v-if="row.business_date" class="font-weight-medium">
                {{ row.business_date }}
              </div>
              <div v-else class="text-disabled">—</div>
            </td>
            <td>
              <div class="font-weight-medium">{{ row.organization_name || 'Все предприятия' }}</div>
            </td>
            <td class="text-right text-success font-weight-bold">
              {{ formatCurrency(row.revenue) }}
            </td>
            <td class="text-right">{{ formatCurrency(row.average_check) }}</td>
            <td class="text-right text-warning">{{ formatCurrency(row.discount_sum) }}</td>
            <td class="text-right">{{ formatCurrency(row.markup) }}</td>
            <td class="text-right">{{ formatPercent(row.markup_percent) }}</td>
            <td class="text-right">{{ formatCurrency(row.cost_price) }}</td>
            <td class="text-right">{{ formatPercent(row.cost_price_percent) }}</td>
            <td class="text-right">{{ row.orders_count }}</td>
          </tr>
        </tbody>
        <tfoot v-if="reportData.length > 1">
          <tr class="font-weight-bold bg-grey-lighten-4">
            <td>Итого</td>
            <td>—</td>
            <td class="text-right text-success">{{ formatCurrency(totals.revenue) }}</td>
            <td class="text-right">{{ formatCurrency(totals.average_check) }}</td>
            <td class="text-right text-warning">{{ formatCurrency(totals.discount_sum) }}</td>
            <td class="text-right">{{ formatCurrency(totals.markup) }}</td>
            <td class="text-right">{{ formatPercent(totals.markup_percent) }}</td>
            <td class="text-right">{{ formatCurrency(totals.cost_price) }}</td>
            <td class="text-right">{{ formatPercent(totals.cost_price_percent) }}</td>
            <td class="text-right">{{ totals.orders_count }}</td>
          </tr>
        </tfoot>
      </VTable>

      <!-- Мета-информация -->
      <VCardText v-if="!loading && lastUpdated" class="text-caption text-medium-emphasis">
        Источник: {{ dataSource === 'database' ? 'Кэш БД' : 'iiko API (live)' }} |
        Данные за: {{ periodLabel }} |
        <span v-if="dataSource === 'database'">Обновлены: {{ lastUpdated }}</span>
        <span v-else>Получены только что</span>
      </VCardText>
    </VCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const BACKEND_URL = '' // Используем относительные пути для проксирования

const selectedPeriod = ref('today')
const customFrom = ref('')
const customTo = ref('')
const includeDeleted = ref(false)
const loading = ref(false)
const error = ref(null)
const reportData = ref([])
const dataSource = ref('iiko_live')
const lastUpdated = ref(null)
const periodDateFrom = ref(null)
const periodDateTo = ref(null)

const periodLabels = {
  today: 'Сегодня',
  yesterday: 'Вчера',
  week: 'Последние 7 дней',
  month: 'Последние 30 дней',
  year: 'Последний год',
  custom: 'Произвольный период',
}

const periodLabel = computed(() => periodLabels[selectedPeriod.value] || '')

const totals = computed(() => {
  if (!reportData.value.length) {
    return { revenue: 0, average_check: 0, discount_sum: 0, markup: 0, markup_percent: 0, cost_price: 0, cost_price_percent: 0, orders_count: 0 }
  }
  const count = reportData.value.length
  return {
    revenue: sum('revenue'),
    average_check: sum('average_check') / count,
    discount_sum: sum('discount_sum'),
    markup: sum('markup'),
    markup_percent: sum('markup_percent') / count,
    cost_price: sum('cost_price'),
    cost_price_percent: sum('cost_price_percent') / count,
    orders_count: sumInt('orders_count'),
  }
})

const summaryCards = computed(() => [
  { title: 'Выручка', value: formatCurrency(totals.value.revenue), color: 'text-success' },
  { title: 'Средний чек', value: formatCurrency(totals.value.average_check), color: '' },
  { title: 'Сумма скидки', value: formatCurrency(totals.value.discount_sum), color: 'text-warning' },
  { title: 'Наценка', value: formatCurrency(totals.value.markup), color: '' },
  { title: 'Себестоимость', value: formatCurrency(totals.value.cost_price), color: '' },
  { title: 'Кол-во заказов', value: totals.value.orders_count.toString(), color: 'text-info' },
])

function sum(field) {
  return reportData.value.reduce((acc, r) => acc + (parseFloat(r[field]) || 0), 0)
}

function sumInt(field) {
  return reportData.value.reduce((acc, r) => acc + (parseInt(r[field]) || 0), 0)
}

function formatCurrency(val) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(val || 0)
}

function formatPercent(val) {
  return `${(val || 0).toFixed(1)}%`
}

async function fetchReport(forceRefresh = false) {
  loading.value = true
  error.value = null

  try {
    const params = new URLSearchParams({
      period: selectedPeriod.value,
      include_deleted: includeDeleted.value,
      refresh: forceRefresh,
    })

    if (selectedPeriod.value === 'custom') {
      if (!customFrom.value || !customTo.value) {
        error.value = 'Укажите дату начала и конца периода'
        loading.value = false
        return
      }
      params.set('date_from', customFrom.value)
      params.set('date_to', customTo.value)
    }

    const resp = await fetch(`${BACKEND_URL}/api/v1/reports/olap/revenue?${params}`)
    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}))
      throw new Error(errData.detail || `Ошибка ${resp.status}`)
    }

    const json = await resp.json()
    reportData.value = json.data || []
    dataSource.value = json.source || 'iiko_live'
    periodDateFrom.value = json.date_from
    periodDateTo.value = json.date_to
    lastUpdated.value = new Date().toLocaleString('ru-RU')
  } catch (e) {
    error.value = `Ошибка получения данных: ${e.message}`
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchReport()
})
</script>
