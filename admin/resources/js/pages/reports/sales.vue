<template>
  <div>
    <VCard class="mb-6">
      <VCardTitle class="d-flex align-center justify-space-between flex-wrap gap-3 pa-4">
        <div>
          <div class="text-h5 font-weight-bold">📈 Отчет по продажам</div>
          <div class="text-caption text-medium-emphasis">
            Детализация по категориям и филиалам. Источник: iiko OLAP.
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
            <VBtn value="custom">Период</VBtn>
          </VBtnToggle>

          <VBtn
            :loading="loading"
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

      <VCardText v-if="selectedPeriod === 'custom'">
        <VRow>
          <VCol cols="12" sm="5">
            <VTextField v-model="customFrom" type="date" label="От" density="compact" />
          </VCol>
          <VCol cols="12" sm="5">
            <VTextField v-model="customTo" type="date" label="До" density="compact" />
          </VCol>
          <VCol cols="12" sm="2">
            <VBtn color="primary" block @click="fetchReport(true)">Ок</VBtn>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <VRow class="mb-4">
      <VCol cols="12" sm="4">
        <VCard>
          <VCardText class="pa-4">
            <div class="text-caption text-medium-emphasis">Всего позиций</div>
            <div class="text-h6 font-weight-bold">{{ totals.count }}</div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" sm="4">
        <VCard>
          <VCardText class="pa-4">
            <div class="text-caption text-medium-emphasis">Сумма продаж</div>
            <div class="text-h6 font-weight-bold text-success">{{ formatCurrency(totals.sum) }}</div>
          </VCardText>
        </VCard>
      </VCol>
      <VCol cols="12" sm="4">
        <VCard>
          <VCardText class="pa-4">
            <div class="text-caption text-medium-emphasis">Сумма скидок</div>
            <div class="text-h6 font-weight-bold text-warning">{{ formatCurrency(totals.discount) }}</div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <VCard>
      <VDataTable
        :headers="headers"
        :items="reportData"
        :loading="loading"
        hover
        class="text-no-wrap"
      >
        <template #item.DishSum="{ item }">
          {{ formatCurrency(item.DishSum) }}
        </template>
        <template #item.DishDiscountSum="{ item }">
          {{ formatCurrency(item.DishDiscountSum) }}
        </template>
      </VDataTable>
    </VCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const selectedPeriod = ref('today')
const customFrom = ref('')
const customTo = ref('')
const loading = ref(false)
const reportData = ref([])
const totals = ref({ count: 0, sum: 0, discount: 0 })

const headers = [
  { title: 'Категория', key: 'DishCategory' },
  { title: 'Блюдо', key: 'DishName' },
  { title: 'Кол-во', key: 'DishAmount', align: 'end' },
  { title: 'Сумма', key: 'DishSum', align: 'end' },
  { title: 'Скидка', key: 'DishDiscountSum', align: 'end' },
  { title: 'Филиал', key: 'Branch' },
]

function formatCurrency(val) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(val || 0)
}

async function fetchReport(forceRefresh = false) {
  loading.value = true
  try {
    const params = new URLSearchParams({
      period: selectedPeriod.value,
      refresh: forceRefresh
    })
    if (selectedPeriod.value === 'custom') {
      params.set('date_from', customFrom.value)
      params.set('date_to', customTo.value)
    }

    const resp = await fetch(`/api/v1/reports/olap/sales?${params}`)
    const json = await resp.json()
    reportData.value = json.data || []
    totals.value = json.total || { count: 0, sum: 0, discount: 0 }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchReport)
</script>
