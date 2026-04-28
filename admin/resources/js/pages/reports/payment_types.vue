<template>
  <div>
    <VCard class="mb-6">
      <VCardTitle class="d-flex align-center justify-space-between flex-wrap gap-3 pa-4">
        <div>
          <div class="text-h5 font-weight-bold">💳 Отчет по типам оплат</div>
          <div class="text-caption text-medium-emphasis">Разделение выручки по способам оплаты.</div>
        </div>
        <div class="d-flex align-center gap-2 flex-wrap">
          <VBtnToggle v-model="selectedPeriod" density="compact" color="primary" variant="outlined" divided @update:model-value="fetchReport">
            <VBtn value="today">Сегодня</VBtn>
            <VBtn value="yesterday">Вчера</VBtn>
            <VBtn value="week">7 дней</VBtn>
            <VBtn value="month">Месяц</VBtn>
            <VBtn value="custom">Период</VBtn>
          </VBtnToggle>
          <VBtn :loading="loading" color="primary" variant="tonal" size="small" prepend-icon="ri-refresh-line" @click="fetchReport(true)">
            Обновить
          </VBtn>
        </div>
      </VCardTitle>
    </VCard>

    <VCard>
      <VDataTable :headers="headers" :items="reportData" :loading="loading" hover>
        <template #item.DishSum="{ item }">
          {{ formatCurrency(item.DishSum) }}
        </template>
      </VDataTable>
    </VCard>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const selectedPeriod = ref('today')
const loading = ref(false)
const reportData = ref([])

const headers = [
  { title: 'Тип оплаты', key: 'PaymentType' },
  { title: 'Количество оплат', key: 'OrderCount', align: 'end' },
  { title: 'Сумма', key: 'DishSum', align: 'end' },
]

function formatCurrency(val) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(val || 0)
}

async function fetchReport(forceRefresh = false) {
  loading.value = true
  try {
    const params = new URLSearchParams({ period: selectedPeriod.value, refresh: forceRefresh })
    const resp = await fetch(`/api/v1/reports/olap/payments?${params}`)
    const json = await resp.json()
    reportData.value = json.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchReport)
</script>
