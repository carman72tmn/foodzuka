<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import { formatDateTime, formatDate } from "@/utils/date"
import { getAuthHeaders } from "@/utils/auth"
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
const addressFormat = ref("line1")

const API_BASE = "/api/v1/orders"

const search = ref("")

const headers = [
  { title: "ID", key: "id", sortable: true, width: 30 },
  { title: "iiko #", key: "external_number", sortable: true, width: 90 },
  { title: "ОПЛ.", key: "is_paid", sortable: true, width: 40, align: "center", cellProps: { class: "column-narrow" }, headerProps: { class: "column-narrow" } },
  { title: "Город", key: "city", sortable: true, width: 50 },
  { title: "Клиент", key: "customer_name", sortable: true },
  { title: "Телефон", key: "customer_phone", sortable: false, width: 130 },
  { title: "Адрес", key: "delivery_address", sortable: false },
  { title: "Зона", key: "resolved_delivery_zone_name", sortable: true, width: 120 },
  { title: "Курьер", key: "courier_name", sortable: true, width: 130 },
  { title: "К ОПЛАТЕ", key: "total_with_discount", sortable: true, width: 110 },
  { title: "ОПЛАЧЕНО", key: "total_paid", sortable: true, width: 100 },
  { title: "Скидка", key: "total_discount", sortable: true, width: 100 },
  { title: "ОЖИДАЕМ", key: "expected_time", sortable: true, width: 80 },
  { title: "Статус", key: "status", sortable: true, width: 130 },
  { title: "Создан", key: "created_at", sortable: true, width: 140 },
]

/* eslint-disable camelcase */
const statusColorsMap = {
  new: "#E3F2FD",
  unconfirmed: "#FFF3E0",
  confirmed: "#E1F5FE",
  preparing: "#E0F2F1",
  cooking: "#FFF8E1",
  ready: "#E8F5E9",
  ready_for_pickup: "#E8F5E9",
  delivering: "#E8EAF6",
  delivered: "#F1F8E9",
  closed: "#F5F5F5",
  cancelled: "#FFEBEE",
}
/* eslint-enable camelcase */

const statusNames = {
  new: "Новый",
  unconfirmed: "Не подтвержден",
  confirmed: "Принят",
  preparing: "В сборке",
  cooking: "Готовится",
  ready: "Готов",
  ready_for_pickup: "Готов к выдаче",
  delivering: "У курьера",
  delivered: "Доставлен",
  closed: "Закрыт",
  cancelled: "Отменен",
}

const getStatusColor = status => {
  return statusColorsMap[status] || "#F5F5F5"
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
    const res = await fetch(`${API_BASE}/`, { headers: getAuthHeaders() })
    if (res.ok) {
      const data = await res.json()

      // Добавляем вычисляемые поля для таблицы
      orders.value = data.map(o => ({
        ...o,
        orderItemsCount: o.order_items_details?.length || o.items?.length || 0,
      }))
    } else if (res.status === 401) {
      if (updateInterval) clearInterval(updateInterval)
      // Сессия истекла, прекращаем автоматическое обновление
    }
  } catch (e) {
    if (!silent) showMessage("Ошибка загрузки заказов", "error")
  } finally {
    if (!silent) loading.value = false
  }
}

const sortedOrders = computed(() => {
  return [...orders.value].sort((a, b) => {
    // Статусы, которые считаются активными
    const activeStatuses = ["new", "unconfirmed", "confirmed", "preparing", "cooking", "ready", "ready_for_pickup", "delivering", "delivered"]

    const isAActive = activeStatuses.includes(a.status)
    const isBActive = activeStatuses.includes(b.status)

    // Приоритет 1: Активные сверху
    if (isAActive && !isBActive) return -1
    if (!isAActive && isBActive) return 1

    // Приоритет 2: Внутри групп по ID (новые выше)
    return b.id - a.id
  })
})

const syncRecentOrders = async () => {
  syncing.value = true
  try {
    const res = await fetch(`${API_BASE}/sync`, { 
      method: "POST",
      headers: getAuthHeaders() 
    })
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

const openOrderDetails = order => {
  selectedOrder.value = order
  isModalOpen.value = true
}

const cancelOrder = async id => {
  if (!confirm("Вы уверены, что хотите отменить этот заказ?")) return

  try {
    const res = await fetch(`${API_BASE}/${id}/cancel`, {
      method: "POST",
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

const loadSettings = async () => {
  try {
    const res = await fetch("/api/v1/settings/iiko")
    if (res.ok) {
      const data = await res.json()
      addressFormat.value = data.address_format || "line1"
    }
  } catch (e) {
    console.error("Error loading iiko settings:", e)
  }
}

const formatAddress = order => {
  if (!order) return "—"
  if (order.order_type === "Самовывоз" || !order.delivery_address) return "🙍 Самовывоз"

  // Условие для предупреждения ❗
  // Только для доставочных заказов, пока статус не закрыт или не отменен
  const status = (order.status || "").toLowerCase()
  const isPending = !["closed", "cancelled"].includes(status)

  // Проверяем квартиру/офис. Если поле отсутствует, равно 0, - или пусто
  const flat = (order.flat || "").toString().trim()
  const noFlat = !flat || flat === "0" || flat === "-"

  const showWarning = isPending && noFlat && order.order_type !== "Самовывоз"
  const warningPrefix = showWarning ? "❗ " : ""

  if (addressFormat.value === "line1") {
    return warningPrefix + order.delivery_address
  }

  const parts = []
  const o = order

  if (o.city) {
    const cityPref = o.city.toLowerCase().startsWith("г.") ? o.city : `г. ${o.city}`
    parts.push(cityPref)
  }

  if (o.street) {
    if (!/ул\.|пр\.|пер\.|б-р/.test(o.street.toLowerCase())) {
      parts.push(`ул. ${o.street}`)
    } else {
      parts.push(o.street)
    }
  }

  if (o.house && o.house !== "0") parts.push(`д. ${o.house}`)
  if (o.flat) parts.push(`кв. ${o.flat}`)
  if (o.entrance) parts.push(`под. ${o.entrance}`)
  if (o.floor) parts.push(`эт. ${o.floor}`)
  if (o.doorphone) parts.push(`домофон: ${o.doorphone}`)

  if (parts.length <= 1 && o.delivery_address) return warningPrefix + o.delivery_address

  return warningPrefix + parts.join(", ")
}

onMounted(() => {
  loadSettings()
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

const formatPrice = val => {
  if (val === null || val === undefined) return "0.00"
  const num = parseFloat(val)

  return isNaN(num) ? "0.00" : num.toFixed(2)
}

const getRowProps = ({ item }) => {
  const status = (item.status || "").toLowerCase()
  const isClosed = status === "closed"

  // Определяем цвет фона в зависимости от статуса
  let bgColor = "rgba(245, 245, 245, 1)" // по умолчанию
  if (status === "unconfirmed") bgColor = "rgba(255, 243, 224, 1)"
  else if (["preparing", "cooking"].includes(status)) bgColor = "rgba(255, 253, 231, 1)"
  else if (isClosed || status.includes("cancel")) bgColor = "#FFFFFF"

  return {
    style: {
      opacity: "1",
      backgroundColor: bgColor,
    },
  }
}

const getPaymentIcon = kind => {
  const icons = {
    cash: 'bx-money',
    card: 'bx-credit-card',
    online: 'bx-globe',
    external: 'bx-link-external',
    iikocard: 'bx-gift',
  }

  return icons[kind] || 'bx-wallet'
}

const getPaymentLabel = kind => {
  const labels = {
    cash: 'Наличные',
    card: 'Карта',
    online: 'Онлайн',
    external: 'Внешняя',
    iikocard: 'Бонусы/Карта',
  }

  return labels[kind] || kind || 'Оплата'
}
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center flex-wrap ga-2 py-4">
          <VIcon
            icon="bx-cart"
            class="me-2"
          />
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
          <VBtn
            color="warning"
            variant="tonal"
            size="small"
            :loading="syncing"
            @click="syncRecentOrders"
          >
            <VIcon
              icon="bx-cloud-download"
              class="me-1"
            /> Синхронизировать iiko
          </VBtn>
          <VBtn
            color="primary"
            variant="tonal"
            size="small"
            :loading="loading"
            @click="loadOrders(false)"
          >
            <VIcon
              icon="bx-refresh"
              class="me-1"
            /> Обновить
          </VBtn>
        </VCardTitle>
        <VCardText>
          <VDataTable
            :headers="headers"
            :items="sortedOrders"
            :loading="loading"
            :search="search"
            :items-per-page="15"
            item-value="id"
            class="elevation-1"
            density="compact"
            hover
            :row-props="getRowProps"
            style="cursor: pointer"
            @click:row="(_, { item }) => openOrderDetails(item)"
          >
            <template #item.customer_name="{ item }">
              <div class="d-flex align-center flex-wrap ga-1">
                <span class="font-weight-medium">{{ item.customer_name }}</span>

                <!-- Индикатор нового клиента -->
                <VTooltip
                  v-if="item.customer_is_new"
                  text="Новый клиент"
                >
                  <template #activator="{ props: ttProps }">
                    <VIcon
                      v-bind="ttProps"
                      icon="bx-star"
                      color="#ffb74d"
                      size="16"
                    />
                  </template>
                </VTooltip>

                <VTooltip :text="item.customer_is_risk ? 'Высокий риск!' : 'Клиент проверен'">
                  <template #activator="{ props: ttProps }">
                    <VIcon
                      v-bind="ttProps"
                      :icon="item.customer_is_risk ? 'bx-shield-x' : 'bx-shield-quarter'"
                      :color="item.customer_is_risk ? '#e57373' : '#81c784'"
                      size="16"
                    />
                  </template>
                </VTooltip>
              </div>
            </template>

            <template #item.is_paid="{ item }">
              <VTooltip location="top">
                <template #activator="{ props: ttProps }">
                  <VIcon
                    v-bind="ttProps"
                    :icon="item.is_paid ? 'bx-check-circle' : 'bx-x-circle'"
                    :color="item.is_paid ? 'success' : 'error'"
                    size="24"
                  />
                </template>
                <span>{{ item.is_paid ? 'Оплачен' : 'Не оплачен' }}</span>
              </VTooltip>
            </template>

            <template #item.customer_phone="{ item }">
              <div class="d-flex align-center">
                <span>{{ item.customer_phone || '—' }}</span>
                <VTooltip
                  v-if="item.is_spam || item.spam_score > 0"
                  location="top"
                >
                  <template #activator="{ props: ttProps }">
                    <VIcon
                      v-bind="ttProps"
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

            <template #item.total_with_discount="{ item }">
              <div class="d-flex flex-column align-end">
                <span
                  class="text-subtitle-2"
                  :class="(item.status === 'closed' || (item.status && item.status.toLowerCase().includes('cancel'))) ? 'font-weight-regular' : 'font-weight-bold'"
                  :style="{ color: (item.status === 'closed' || (item.status && item.status.toLowerCase().includes('cancel'))) ? '#000000' : 'inherit' }"
                >
                  {{ formatPrice(item.total_with_discount || item.total_amount || item.sum || 0) }} ₽
                </span>
                
                <div v-if="parseFloat(item.left_to_pay) > 0" class="mt-n1">
                  <span class="text-tiny font-weight-bold text-error">
                    ост. {{ formatPrice(item.left_to_pay) }} ₽
                  </span>
                </div>
              </div>
            </template>

            <template #item.total_paid="{ item }">
              <div class="d-flex flex-column align-end">
                <span
                  class="text-subtitle-2 font-weight-bold"
                  :style="{ color: (parseFloat(item.total_paid) > 0 || (parseFloat(item.total_with_discount || 0) - parseFloat(item.left_to_pay || 0)) > 0) ? '#2e7d32' : '#455a64' }"
                >
                  {{ formatPrice(parseFloat(item.total_paid) > 0 ? item.total_paid : (parseFloat(item.total_with_discount || item.total_amount || item.sum || 0) - parseFloat(item.left_to_pay || 0))) }} ₽
                </span>
                <span v-if="item.is_paid && parseFloat(item.left_to_pay) <= 0" class="text-tiny text-success font-weight-black">
                  ОПЛАЧЕНО
                </span>
              </div>
            </template>

            <template #item.resolved_delivery_zone_name="{ item }">
              <span v-if="item.order_type === 'Самовывоз'">
                Самовывоз
              </span>
              <span v-else-if="item.delivery_zone">
                {{ item.delivery_zone }}
              </span>
              <span
                v-else
                class="text-caption text-grey"
              >
                Не опред.
              </span>
            </template>

            <template #item.courier_name="{ item }">
              <span
                v-if="!item.courier_name || item.courier_name.toLowerCase().includes('none none') || item.courier_name.toLowerCase().trim() === 'не назначен'"
                class="text-grey text-caption"
              >
                Не назначен
              </span>
              <span
                v-else
                class="font-weight-medium"
              >
                {{ item.courier_name.replace(/(\s+None)+$/i, '').replace(/None\s+None/i, '') }}
              </span>
            </template>

            <template #item.total_discount="{ item }">
              <VChip
                v-if="item.total_discount > 0"
                size="x-small"
                variant="tonal"
                color="error"
              >
                -{{ item.total_discount }} ₽
              </VChip>
              <span
                v-else
                class="text-caption text-grey"
              >—</span>
            </template>

            <template #item.external_number="{ item }">
              <div class="d-flex flex-column">
                <span class="font-weight-bold">{{ item.external_number || '—' }}</span>
                <div v-if="item.change_indicators && Object.values(item.change_indicators).some(v => v)" class="d-flex flex-wrap ga-1 mt-1">
                  <VTooltip
                    v-if="item.change_indicators.items"
                    text="Состав изменен"
                  >
                    <template #activator="{ props: ttProps }">
                      <VIcon
                        v-bind="ttProps"
                        icon="bx-list-plus"
                        color="error"
                        size="14"
                      />
                    </template>
                  </VTooltip>
                  <VTooltip
                    v-if="item.change_indicators.amount"
                    text="Сумма изменена"
                  >
                    <template #activator="{ props: ttProps }">
                      <VIcon
                        v-bind="ttProps"
                        icon="bx-ruble"
                        color="error"
                        size="14"
                      />
                    </template>
                  </VTooltip>
                  <VTooltip
                    v-if="item.change_indicators.address"
                    text="Адрес изменен"
                  >
                    <template #activator="{ props: ttProps }">
                      <VIcon
                        v-bind="ttProps"
                        icon="bx-map-alt"
                        color="error"
                        size="14"
                      />
                    </template>
                  </VTooltip>
                  <VTooltip
                    v-if="item.change_indicators.time"
                    text="Время изменено"
                  >
                    <template #activator="{ props: ttProps }">
                      <VIcon
                        v-bind="ttProps"
                        icon="bx-time"
                        color="error"
                        size="14"
                      />
                    </template>
                  </VTooltip>
                  <VTooltip
                    v-if="item.change_indicators.payment"
                    text="Оплата изменена"
                  >
                    <template #activator="{ props: ttProps }">
                      <VIcon
                        v-bind="ttProps"
                        icon="bx-credit-card"
                        color="error"
                        size="14"
                      />
                    </template>
                  </VTooltip>
                </div>
              </div>
            </template>

            <template #item.delivery_address="{ item }">
              <span
                class="text-body-2 font-weight-medium"
                style="opacity: 1 !important; color: #000 !important;"
              >
                {{ formatAddress(item) }}
              </span>
            </template>

            <template #item.status="{ item }">
              <div class="d-flex align-center">
                <VChip
                  :color="getStatusColor(item.status)"
                  size="small"
                  class="text-uppercase"
                  :class="(item.status === 'closed' || (item.status && item.status.toLowerCase().includes('cancel'))) ? 'font-weight-regular' : 'font-weight-bold'"
                  :variant="(item.status === 'closed' || (item.status && item.status.toLowerCase().includes('cancel'))) ? 'flat' : 'tonal'"
                  :style="{
                    color: (item.status === 'closed' || (item.status && item.status.toLowerCase().includes('cancel'))) ? '#000000 !important' : 'inherit',
                    backgroundColor: (item.status === 'closed' || (item.status && item.status.toLowerCase().includes('cancel'))) ? 'transparent !important' : ''
                  }"
                >
                  {{ statusNames[item.status] || item.status }}
                </VChip>
              </div>
            </template>

            <template #item.expected_time="{ item }">
              <VTooltip location="top">
                <template #activator="{ props: ttProps }">
                  <div
                    v-bind="ttProps"
                    class="d-flex flex-column align-center justify-center pa-1 rounded-lg"
                    :class="(item.status === 'closed' || item.status.toLowerCase().includes('cancel')) ? '' : 'elevation-1'"
                    :style="{
                      backgroundColor: (item.status === 'closed' || item.status.toLowerCase().includes('cancel')) ? 'transparent' : (item.is_asap ? '#FFFDE7' : '#E1F5FE'),
                      border: (item.status === 'closed' || item.status.toLowerCase().includes('cancel')) ? 'none' : `1px solid ${item.is_asap ? '#FDD835' : '#4FC3F7'}`,
                      minWidth: '70px',
                      lineHeight: '1.1',
                      cursor: 'help',
                      color: (item.status === 'closed' || item.status.toLowerCase().includes('cancel')) ? '#000000' : 'inherit'
                    }"
                  >
                    <div
                      class="text-h6 mb-0"
                      style="opacity: 1"
                    >
                      {{ item.is_asap ? '⚡' : '⏰' }}
                    </div>

                    <div class="text-center">
                      <div
                        class="text-caption font-weight-black"
                        :style="{ color: (item.status === 'closed' || item.status.toLowerCase().includes('cancel')) ? '#000000' : (item.is_asap ? '#F57F17' : '#01579B') }"
                      >
                        {{ formatDateTime(item.expected_time || item.iiko_creation_time || item.created_at, { day: undefined, month: undefined, year: undefined }) }}
                      </div>

                      <!-- НОВОЕ: Дата для предзаказов на будущие дни -->
                      <div
                        v-if="!item.is_asap && item.expected_time && formatDate(item.expected_time) !== formatDate(new Date())"
                        class="text-caption font-weight-bold mt-n1"
                        :style="{ color: (item.status === 'closed' || item.status.toLowerCase().includes('cancel')) ? '#666' : '#1565C0', fontSize: '0.65rem' }"
                      >
                        {{ formatDateTime(item.expected_time, { hour: undefined, minute: undefined, second: undefined }) }}
                      </div>
                    </div>
                  </div>
                </template>
                <span>{{ item.is_asap ? '⚡ Как можно быстрее (ASAP)' : '⏰ Предзаказ на время (Time)' }}</span>
              </VTooltip>
            </template>

            <template #item.created_at="{ item }">
              <span v-if="item.iiko_creation_time || item.created_at" class="text-caption">
                {{ formatDateTime(item.iiko_creation_time || item.created_at) }}
              </span>
              <span v-else class="text-caption text-grey">Нет данных</span>
            </template>
          </VDataTable>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <OrderDetailModal
    v-model="isModalOpen"
    :order="selectedOrder"
    :address-format="addressFormat"
  />

  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="3000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>

<style>
.column-narrow {
  width: 40px !important;
  min-width: 40px !important;
  max-width: 40px !important;
  padding: 0 4px !important;
  text-align: center !important;
}

/* Стили для таблицы */
.v-data-table__th.column-narrow {
  width: 40px !important;
}
</style>
