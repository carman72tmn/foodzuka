<script setup>
import { ref, onMounted, computed } from "vue"

const loading = ref(false)
const logs = ref([])
const selectedType = ref(null)

const API_BASE = "/api/v1/iiko"

const headers = [
  { title: "ID", key: "id", sortable: true, width: 60 },
  { title: "Тип", key: "sync_type", sortable: true, width: 120 },
  { title: "Статус", key: "status", sortable: true, width: 100 },
  { title: "Категорий", key: "categories_count", sortable: true, width: 100 },
  { title: "Товаров", key: "products_count", sortable: true, width: 100 },
  { title: "Детали", key: "details", sortable: false },
  { title: "Дата", key: "created_at", sortable: true, width: 170 },
]

const syncTypes = [
  { title: "Все", value: null },
  { title: "Меню", value: "menu" },
  { title: "Цены", value: "prices" },
  { title: "Стоп-лист", value: "stop_lists" },
  { title: "Заказы", value: "orders" },
]

const loadLogs = async () => {
  loading.value = true
  try {
    let url = `${API_BASE}/sync-logs?limit=100`
    if (selectedType.value) {
      url += `&sync_type=${selectedType.value}`
    }
    const res = await fetch(url)
    if (res.ok) {
      logs.value = await res.json()
    }
  } catch (e) {
    // Ошибка загрузки
  } finally {
    loading.value = false
  }
}

const formatDate = dateStr => {
  return new Date(dateStr).toLocaleString("ru-RU")
}

const statusColor = status => {
  const map = {
    success: "success",
    error: "error",
    running: "info",
    partial: "warning",
  }

  
  return map[status] || "grey"
}

const typeLabel = type => {
  const map = {
    menu: "Меню",
    prices: "Цены",
    stop_lists: "Стоп-лист",
    orders: "Заказы",
  }

  
  return map[type] || type
}

onMounted(loadLogs)
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center flex-wrap gap-4">
          <VIcon
            icon="mdi-history"
            class="me-2"
          />
          Логи синхронизации
          <VSpacer />
          <VSelect
            v-model="selectedType"
            :items="syncTypes"
            density="compact"
            style="max-width: 200px"
            hide-details
            @update:model-value="loadLogs"
          />
          <VBtn
            icon="mdi-refresh"
            variant="text"
            @click="loadLogs"
          />
        </VCardTitle>
        <VCardText>
          <VDataTable
            :headers="headers"
            :items="logs"
            :loading="loading"
            :items-per-page="25"
            class="elevation-1"
            density="compact"
          >
            <template #item.sync_type="{ item }">
              <VChip
                variant="tonal"
                size="small"
                color="primary"
              >
                {{ typeLabel(item.sync_type) }}
              </VChip>
            </template>
            <template #item.status="{ item }">
              <VChip
                :color="statusColor(item.status)"
                variant="tonal"
                size="small"
              >
                {{ item.status }}
              </VChip>
            </template>
            <template #item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>
            <template #item.details="{ item }">
              <span class="text-caption">
                {{ item.details || "—" }}
              </span>
            </template>
          </VDataTable>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>
</template>
