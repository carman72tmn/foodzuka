<script setup>
import { ref, onMounted, onUnmounted } from "vue"
import { formatDateTime } from "@/utils/date"
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

const search = ref("")

const headers = [
  { title: "ID", key: "id", sortable: true, width: 70 },
  { title: "iiko #", key: "external_number", sortable: true, width: 90 },
  { title: "Оплата", key: "is_paid", sortable: true, width: 110 },
  { title: "Город", key: "city", sortable: true, width: 100 },
  { title: "Клиент", key: "customer_name", sortable: true },
  { title: "Телефон", key: "customer_phone", sortable: false, width: 130 },
  { title: "Адрес", key: "delivery_address", sortable: false },
  { title: "Зона доставки", key: "delivery_zone", sortable: true, width: 140 },
  { title: "Курьер", key: "courier_name", sortable: true, width: 130 },
  { title: "Сумма", key: "total_amount", sortable: true, width: 90 },
  { title: "Товары", key: "order_items_count", sortable: false, width: 90 },
  { title: "Статус", key: "status", sortable: true, width: 130 },
  { title: "Создан", key: "created_at", sortable: true, width: 140 },
]

const statusColors = {
  new: "deep-purple-lighten-1",
  unconfirmed: "deep-orange-darken-1",
  confirmed: "indigo-darken-1",
  preparing: "amber-darken-3",
  cooking: "orange-darken-3",
  ready: "light-green-darken-1",
  ready_for_pickup: "teal-darken-2",
  delivering: "light-blue-darken-1",
  delivered: "green-darken-2",
  closed: "grey-darken-2",
  cancelled: "red-darken-1"
}

const statusNames = {
  new: "Новый",
  unconfirmed: "Не подтвержден",
  confirmed: "Принят",
  preparing: "В сборке",
  cooking: "Готовится",
  ready: "Пища готова",
  ready_for_pickup: "Готов к выдаче",
  delivering: "У курьера",
  delivered: "Доставлен",
  closed: "Закрыт",
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
      const data = await res.json()
      // Добавляем вычисляемые поля для таблицы
      orders.value = data.map(o => ({
        ...o,
        order_items_count: o.order_items_details?.length || o.items?.length || 0
      }))
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
  if (!dateString) return '';
  let dateToFormat = dateString;
  // Гарантируем, что дата будет восприниматься как UTC, если бэкенд отдает без 'Z'
  if (!dateString.endsWith('Z') && !dateString.includes('+')) {
    dateToFormat += 'Z';
  }
  return formatDateTime(dateToFormat);
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
        <VCardTitle class="d-flex align-center flex-wrap ga-2 py-4">
          <VIcon icon="bx-cart" class="me-2" />
          Управление заказами
          <VSpacer />
          <VTextField
            v-model="search"
            prepend-inner-icon="bx-search"
            label="Поиск по заказам..."
            single-line
            hide-details
            density="compact"
            variant="outlined"
            style="max-width: 300px"
            class="me-4"
          />
          <VBtn color="warning" @click="syncRecentOrders" :loading="syncing" variant="tonal" size="small">
            <VIcon icon="bx-cloud-download" class="me-1" /> Синхронизировать iiko
          </VBtn>
          <VBtn color="primary" @click="loadOrders(false)" :loading="loading" variant="tonal" size="small">
            <VIcon icon="bx-refresh" class="me-1" /> Обновить
          </VBtn>
        </VCardTitle>
        <VCardText>
          <VDataTable
            :headers="headers"
            :items="orders"
            :loading="loading"
            :search="search"
            :items-per-page="15"
            item-value="id"
            class="elevation-1"
            density="compact"
            hover
            @click:row="(_, { item }) => openOrderDetails(item)"
            style="cursor: pointer"
          >
            <template #item.is_paid="{ item }">
              <VChip
                :color="item.is_paid ? 'success' : 'error'"
                :prepend-icon="item.is_paid ? 'bx-check-circle' : 'bx-x-circle'"
                size="x-small"
                variant="tonal"
              >
                {{ item.is_paid ? 'Оплачен' : 'Не оплачен' }}
              </VChip>
            </template>

            <template #item.customer_phone="{ item }">
              <div class="d-flex align-center">
                <span>{{ item.customer_phone || '—' }}</span>
                <VTooltip v-if="item.is_spam || item.spam_score > 0" location="top">
                  <template #activator="{ props }">
                    <VIcon
                      v-bind="props"
                      :icon="item.spam_score >= 80 ? 'bx-error-circle' : 'bx-info-circle'"
                      :color="item.spam_score >= 80 ? 'error' : 'warning'"
                      size="small"
                      class="ms-1"
                    />
                  </template>
                  <span>{{ item.spam_info }}</span>
                </VTooltip>
              </div>
            </template>

            <template #item.city="{ item }">
              <span class="text-caption">{{ item.city || '—' }}</span>
            </template>

            <template #item.delivery_zone="{ item }">
              <VChip v-if="item.delivery_zone" size="x-small" variant="tonal" color="cyan">
                <VIcon icon="bx-map-alt" size="12" class="me-1" />
                {{ item.delivery_zone }}
              </VChip>
              <span v-else class="text-caption text-grey">—</span>
            </template>

            <template #item.order_items_count="{ item }">
              <VChip size="x-small" variant="outlined" color="primary">
                {{ item.order_items_count }} поз.
              </VChip>
            </template>

            <template #item.external_number="{ item }">
              <span class="font-weight-bold">{{ item.external_number || '—' }}</span>
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
