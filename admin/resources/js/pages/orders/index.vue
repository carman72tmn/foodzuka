<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import OrderDetailModal from "../../components/OrderDetailModal.vue"

const loading = ref(false)
const syncing = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const orders = ref([])

// Для модального окна деталей заказа
const isModalOpen = ref(false)
const selectedOrder = ref(null)

const API_BASE = "/api/v1/orders"

const headers = [
  { title: "ID", key: "id", sortable: true, width: 70 },
  { title: "iiko ID", key: "iiko_order_id", sortable: false },
  { title: "Клиент", key: "customer_name", sortable: true },
  { title: "Телефон", key: "customer_phone", sortable: false },
  { title: "Адрес", key: "delivery_address", sortable: false },
  { title: "Сумма", key: "total_amount", sortable: true },
  { title: "Статус", key: "status", sortable: true },
  { title: "Создан", key: "created_at", sortable: true },
]

const statusColors = {
  new: "info",
  confirmed: "primary",
  preparing: "warning",
  cooking: "warning",
  ready: "success",
  delivering: "info",
  delivered: "success",
  cancelled: "error"
}

const statusNames = {
  new: "Новый",
  confirmed: "Подтвержден",
  preparing: "В подготовке",
  cooking: "Готовится",
  ready: "Готов",
  delivering: "В пути",
  delivered: "Доставлен",
  cancelled: "Отменен"
}

let updateInterval = null

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const loadOrders = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const res = await fetch(`${API_BASE}/`)
    if (res.ok) {
      orders.value = await res.json()
    }
  } catch (e) {
    if (!silent) showMessage("Ошибка загрузки заказов", "error")
  } finally {
    if (!silent) loading.value = false
  }
}

const syncRecentOrders = async () => {
  syncing.value = true
  try {
    const res = await fetch(`${API_BASE}/sync`, { method: 'POST' })
    if (res.ok) {
      showMessage("Синхронизация запущена в фоновом режиме", "info")
      // Перезагрузим список через пару секунд чтобы увидеть первые результаты
      setTimeout(() => loadOrders(false), 3000)
    } else {
      showMessage("Ошибка при запуске синхронизации", "error")
    }
  } catch (e) {
    showMessage("Ошибка соединения при синхронизации", "error")
  } finally {
    syncing.value = false
  }
}

const openOrderDetails = (order) => {
  selectedOrder.value = order
  isModalOpen.value = true
}

const cancelOrder = async (id) => {
  if (!confirm("Вы уверены, что хотите отменить этот заказ?")) return
  
  try {
    const res = await fetch(`${API_BASE}/${id}/cancel`, {
      method: 'POST'
    })
    if (res.ok) {
      showMessage("Заказ успешно отменен")
      loadOrders(false)
      // Если отменяем из открытого модального окна, обновим и его данные
      if (selectedOrder.value && selectedOrder.value.id === id) {
        const updatedOrd = await res.json()
        selectedOrder.value = updatedOrd
      }
    } else {
      const data = await res.json()
      showMessage(data.detail || "Ошибка при отмене", "error")
    }
  } catch (e) {
    showMessage("Ошибка при отмене заказа", "error")
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ""
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  }).format(date)
}

onMounted(() => {
  loadOrders()
  // Автообновление каждые 30 секунд
  updateInterval = setInterval(() => {
    loadOrders(true)
  }, 30000)
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon icon="bx-cart" class="me-2" />
          Управление заказами
          <VSpacer />
          <VBtn color="warning" @click="syncRecentOrders" class="me-2" :loading="syncing" variant="tonal" size="small">
            <VIcon icon="bx-cloud-download" /> Обновить (23ч) из iiko
          </VBtn>
          <VBtn color="primary" @click="loadOrders(false)" :loading="loading" variant="tonal" size="small">
            <VIcon icon="bx-refresh" /> Обновить
          </VBtn>
        </VCardTitle>
        <VCardText>
          <VDataTable
            :headers="headers"
            :items="orders"
            :loading="loading"
            :items-per-page="15"
            item-value="id"
            class="elevation-1"
            density="compact"
            hover
            @click:row="(_, { item }) => openOrderDetails(item)"
            style="cursor: pointer"
          >
            <template #item.iiko_order_id="{ item }">
              <span v-if="item.iiko_order_id" class="text-caption text-medium-emphasis">
                {{ item.iiko_order_id.substring(0, 8) }}...
              </span>
              <VChip v-else size="x-small" color="grey" variant="tonal">В iiko не передан</VChip>
            </template>
            
            <template #item.total_amount="{ item }">
              <strong>{{ item.total_amount }} ₽</strong>
            </template>

            <template #item.status="{ item }">
              <VChip
                :color="statusColors[item.status] || 'grey'"
                variant="elevated"
                size="small"
              >
                {{ statusNames[item.status] || item.status }}
              </VChip>
            </template>

            <template #item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>
            
          </VDataTable>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <OrderDetailModal v-model="isModalOpen" :order="selectedOrder" />

  <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000" location="top">
    {{ snackbarText }}
  </VSnackbar>
</template>
