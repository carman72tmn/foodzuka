<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue"
import { useRoute } from "vue-router"
import { formatDateTime, formatDate } from "@/utils/date"
import { getAuthHeaders } from "@/utils/auth"
import OrderDetailModal from "../../components/OrderDetailModal.vue"
import { useChatStore } from "@/stores/chatStore"

const route = useRoute()
const CACHE_KEY = 'foodtech_orders_fast_cache_v2'

// Определение статуса завершенности заказа
const isOrderCompleted = item => {
  const st = (item?.status || '').toLowerCase()
  return ['closed', 'cancelled', 'delivered'].includes(st)
}

// Загрузка заказов из быстрого локального кэша для мгновенного отображения (0 мс)
const loadOrdersFromCache = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    if (cached) {
      const parsed = JSON.parse(cached)
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed.map(o => ({
          ...o,
          orderItemsCount: o.orderItemsCount !== undefined ? o.orderItemsCount : (o.order_items_details?.length || o.items?.length || 0)
        }))
      }
    }
  } catch (e) {
    console.warn('Failed to load orders from fast cache', e)
  }
  return []
}

// Сохранение заказов в быстрый кэш localStorage
const saveOrdersToCache = (ordersList) => {
  try {
    if (!Array.isArray(ordersList)) return
    // Сохраняем до 300 последних заказов для моментального открытия страницы
    const toCache = ordersList.slice(0, 300)
    localStorage.setItem(CACHE_KEY, JSON.stringify(toCache))
  } catch (e) {
    console.warn('Failed to save orders to fast cache', e)
  }
}

const loading = ref(false)
const syncing = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

// Инициализируем реактивный список сразу из быстрого кэша
const orders = ref(loadOrdersFromCache())

// Для модального окна деталей заказа
const isModalOpen = ref(false)
const selectedOrder = ref(null)
const addressFormat = ref("line1")

const chatStore = useChatStore()

watch(() => chatStore.lastOrderUpdate, (newVal) => {
  if (newVal) {
    console.log("WebSocket order update received:", newVal)
    loadActiveOrders(true)
  }
})

const API_BASE = "/api/v1/orders"

const search = ref("")

const headers = [
  { title: "", key: "courier_notification_indicator", sortable: false, width: 34, align: "center", cellProps: { class: "column-indicator" }, headerProps: { class: "column-indicator" } },
  { title: "ID / iiko", key: "id", sortable: true, width: 95 },
  { title: "Кухня / Курьер", key: "cooking_and_courier", sortable: false, minWidth: "165px" },
  { title: "ОПЛ.", key: "is_paid", sortable: true, width: 45, align: "center", cellProps: { class: "column-narrow" }, headerProps: { class: "column-narrow" } },
  { title: "Город", key: "city", sortable: true, width: 50 },
  { title: "Клиент", key: "customer_name", sortable: true },
  { title: "Телефон", key: "customer_phone", sortable: false, width: 130 },
  { title: "Тип заказа", key: "order_type_and_delivery", sortable: false, minWidth: "200px" },
  { title: "Оплата", key: "payment_summary", sortable: false, minWidth: "140px" },
  { title: "Доставить", key: "delivery_status_summary", sortable: false, minWidth: "160px" },
  { title: "Создан", key: "created_at", sortable: true, width: 130 },
]

/* eslint-disable camelcase */
const statusColorsMap = {
  new: "info",
  unconfirmed: "warning",
  confirmed: "info",
  preparing: "info",
  cooking: "warning",
  ready: "success",
  ready_for_pickup: "success",
  delivering: "primary",
  delivered: "success",
  closed: "secondary",
  cancelled: "error",
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
  return statusColorsMap[status] || "secondary"
}

let updateInterval = null
let activeInterval = null

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// Фильтр табов: 'all' | 'active' | 'archive'
const orderFilterTab = ref('all')

const activeCount = computed(() => orders.value.filter(o => !isOrderCompleted(o)).length)
const archiveCount = computed(() => orders.value.filter(o => isOrderCompleted(o)).length)
const allCount = computed(() => orders.value.length)

// Слияние списка активных заказов со списком всех заказов
const mergeActiveOrders = (activeList) => {
  if (!Array.isArray(activeList)) return

  const formattedActive = activeList.map(o => ({
    ...o,
    orderItemsCount: o.order_items_details?.length || o.items?.length || 0,
  }))

  const activeIds = new Set(formattedActive.map(a => a.id))
  const currentList = [...orders.value]
  let hasChanges = false

  // 1. Обновляем существующие активные заказы или добавляем новые в начало
  for (const fresh of formattedActive) {
    const idx = currentList.findIndex(o => o.id === fresh.id)
    if (idx !== -1) {
      currentList[idx] = { ...currentList[idx], ...fresh }
      hasChanges = true
    } else {
      currentList.unshift(fresh)
      hasChanges = true
    }
  }

  // 2. Если заказ в кэше числился активным (!isOrderCompleted), но его НЕТ в списке свежих активных,
  // отмечаем его закрытым ТОЛЬКО если с сервера пришел непустой список активных заказов
  // (защита от случайного стирания кэша при пустых ответах)
  if (formattedActive.length > 0) {
    for (let i = 0; i < currentList.length; i++) {
      const item = currentList[i]
      if (!isOrderCompleted(item) && !activeIds.has(item.id)) {
        currentList[i] = {
          ...item,
          status: 'closed'
        }
        hasChanges = true
      }
    }
  }

  if (hasChanges) {
    orders.value = currentList
    saveOrdersToCache(orders.value)
  }
}

// Быстрая подгрузка только активных заказов (в работе) за 15-30 мс
const loadActiveOrders = async (silent = true) => {
  try {
    const res = await fetch(`${API_BASE}/active`, { headers: getAuthHeaders() })
    if (res.ok) {
      const activeList = await res.json()
      mergeActiveOrders(activeList)
    } else if (res.status === 401) {
      if (activeInterval) clearInterval(activeInterval)
      if (updateInterval) clearInterval(updateInterval)
    }
  } catch (e) {
    console.warn("Failed to load active orders:", e)
  }
}

// Фоновая загрузка полного архива заказов (до 250 штук)
const loadOrders = async (silent = false) => {
  // Показываем спиннер только если в кэше еще нет заказов
  if (!silent && orders.value.length === 0) loading.value = true

  try {
    const res = await fetch(`${API_BASE}/?limit=250`, { headers: getAuthHeaders() })
    if (res.ok) {
      const data = await res.json()

      // Добавляем вычисляемые поля для таблицы
      const mapped = data.map(o => ({
        ...o,
        orderItemsCount: o.order_items_details?.length || o.items?.length || 0,
      }))
      orders.value = mapped
      saveOrdersToCache(mapped)
    } else if (res.status === 401) {
      if (activeInterval) clearInterval(activeInterval)
      if (updateInterval) clearInterval(updateInterval)
    }
  } catch (e) {
    if (!silent && orders.value.length === 0) showMessage("Ошибка загрузки заказов", "error")
  } finally {
    if (!silent) loading.value = false
  }
}

const sortedOrders = computed(() => {
  let list = orders.value

  if (orderFilterTab.value === 'active') {
    list = list.filter(o => !isOrderCompleted(o))
  } else if (orderFilterTab.value === 'archive') {
    list = list.filter(o => isOrderCompleted(o))
  }

  return [...list].sort((a, b) => {
    const isAActive = !isOrderCompleted(a)
    const isBActive = !isOrderCompleted(b)

    // Приоритет 1: Активные сверху (в режиме 'all')
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

const openOrderById = async (orderId) => {
  if (!orderId) return
  let ord = orders.value.find(o => String(o.id) === String(orderId) || String(o.order_number) === String(orderId) || String(o.external_number) === String(orderId))
  if (ord) {
    openOrderDetails(ord)
    return
  }
  try {
    const res = await fetch(`${API_BASE}/${orderId}`, {
      headers: getAuthHeaders()
    })
    if (res.ok) {
      const data = await res.json()
      openOrderDetails(data)
    }
  } catch (e) {
    console.warn('Failed to load order details by id:', e)
  }
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

const handleOrderUpdated = async (orderId) => {
  await loadOrders(true)
  if (selectedOrder.value && selectedOrder.value.id === orderId) {
    try {
      const res = await fetch(`${API_BASE}/${orderId}`, { headers: getAuthHeaders() })
      if (res.ok) {
        const data = await res.json()
        selectedOrder.value = {
          ...data,
          orderItemsCount: data.order_items_details?.length || data.items?.length || 0,
        }
      }
    } catch (e) {
      console.error("Error refreshing selected order:", e)
    }
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
  if (order.order_type === "Самовывоз" || (!order.delivery_address && !order.street)) return "🙍 Самовывоз"

  // Условие для предупреждения ❗
  // Только для доставочных заказов, пока статус не закрыт или не отменен
  const status = (order.status || "").toLowerCase()
  const isPending = !["closed", "cancelled"].includes(status)

  // Проверяем квартиру/офис. Если поле отсутствует, равно 0, - или пусто
  const flat = (order.flat || "").toString().trim()
  const noFlat = !flat || flat === "0" || flat === "-"

  const showWarning = isPending && noFlat && order.order_type !== "Самовывоз"
  const warningPrefix = showWarning ? "❗ " : ""

  const o = order
  const baseAddr = (o.delivery_address || "").trim()

  if (baseAddr && baseAddr !== "Самовывоз" && baseAddr !== "Адрес не указан") {
    let resultAddr = baseAddr
    const extras = []
    const ent = (o.entrance || "").toString().trim()
    const flr = (o.floor || "").toString().trim()
    const flt = (o.flat || "").toString().trim()
    const dp = (o.doorphone || "").toString().trim()

    if (ent && ent !== "0" && ent !== "-") {
      const hasEnt = new RegExp(`(?:под(?:ъезд|\\.|\\s*)|(?<=[,\\s])п\\.\\s*)\\s*${ent}\\b`, 'i').test(resultAddr)
      if (!hasEnt) extras.push(`под. ${ent}`)
    }
    if (flr && flr !== "0" && flr !== "-") {
      const hasFlr = new RegExp(`(?:эт(?:аж|\\.|\\s*)|(?<=[,\\s])э\\.\\s*)\\s*${flr}\\b`, 'i').test(resultAddr)
      if (!hasFlr) extras.push(`эт. ${flr}`)
    }
    if (flt && flt !== "0" && flt !== "-") {
      const hasFlt = new RegExp(`(?:кв(?:артира|\\.|\\s*)|оф(?:ис|\\.|\\s*)|пом(?:ещение|\\.|\\s*))\\s*${flt}\\b`, 'i').test(resultAddr)
      if (!hasFlt) extras.push(`кв. ${flt}`)
    }
    if (dp && dp !== "0" && dp !== "-") {
      const hasDp = new RegExp(`(?:код|домофон|д/ф|код\\s*домофона)\\s*[:#]?\\s*${dp}\\b`, 'i').test(resultAddr)
      if (!hasDp) extras.push(`код ${dp}`)
    }

    if (extras.length > 0) {
      resultAddr = `${resultAddr}, ${extras.join(', ')}`
    }
    return warningPrefix + resultAddr
  }

  const parts = []
  if (o.city) {
    const cityPref = o.city.toLowerCase().startsWith("г.") ? o.city : `г. ${o.city}`
    parts.push(cityPref)
  }

  if (o.street) {
    if (!/ул\.|пр\.|пер\.|б-р|тракт|шоссе|проезд/i.test(o.street)) {
      parts.push(`ул. ${o.street}`)
    } else {
      parts.push(o.street)
    }
  }

  if (o.house && o.house !== "0" && o.house !== "-") parts.push(`д. ${o.house}`)
  if (o.entrance && o.entrance !== "0" && o.entrance !== "-") parts.push(`под. ${o.entrance}`)
  if (o.floor && o.floor !== "0" && o.floor !== "-") parts.push(`эт. ${o.floor}`)
  if (o.flat && o.flat !== "0" && o.flat !== "-") parts.push(`кв. ${o.flat}`)
  if (o.doorphone && o.doorphone !== "0" && o.doorphone !== "-") parts.push(`домофон: ${o.doorphone}`)

  return parts.length > 0 ? (warningPrefix + parts.join(", ")) : (warningPrefix + (o.delivery_address || "Адрес не указан"))
}

const cookingTimeItems = computed(() => {
  const items = [0]
  for (let i = 5; i <= 365; i += 5) {
    items.push(i)
  }
  return items
})

const saveCookingTime = async (orderId, minutes) => {
  const targetOrder = orders.value.find(o => o.id === orderId)
  if (targetOrder && isOrderCompleted(targetOrder)) return

  try {
    const response = await fetch(`/api/v1/orders/${orderId}/cooking-time?minutes=${minutes}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": localStorage.getItem("access_token") ? `Bearer ${localStorage.getItem("access_token")}` : ""
      },
    })
    if (response.ok) {
      const order = orders.value.find(o => o.id === orderId)
      if (order) {
        order.cooking_time_minutes = minutes
      }
      snackbarText.value = "Время готовности обновлено"
      snackbarColor.value = "success"
      snackbar.value = true
    } else {
      const err = await response.json()
      alert(err.detail || "Не удалось сохранить время готовности")
    }
  } catch (e) {
    console.error("Save cooking time error:", e)
    alert("Ошибка сети при сохранении времени готовности")
  }
}

const activeCouriersList = ref([])
const loadingActiveCouriers = ref(false)
const assigningCourierOrderId = ref(null)

const fetchActiveCouriers = async () => {
  if (loadingActiveCouriers.value) return
  loadingActiveCouriers.value = true
  try {
    const res = await fetch('/api/v1/orders/active-couriers', {
      headers: getAuthHeaders(),
    })
    if (res.ok) {
      const data = await res.json()
      if (data.status === 'success' && Array.isArray(data.data)) {
        activeCouriersList.value = data.data
      }
    }
  } catch (e) {
    console.warn('Failed to fetch active couriers:', e)
  } finally {
    loadingActiveCouriers.value = false
  }
}

const assignCourierToOrder = async (orderId, courierIikoId, courierName) => {
  if (assigningCourierOrderId.value) return
  assigningCourierOrderId.value = orderId

  try {
    const response = await fetch(`${API_BASE}/${orderId}/courier`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ courier_iiko_id: courierIikoId }),
    })

    if (response.ok) {
      const resData = await response.json()
      const effectiveName = resData.courier_name || courierName
      const order = orders.value.find(o => o.id === orderId)
      if (order) {
        order.courier_name = effectiveName
        order.courier_notification_status = null
        order.courier_accepted_at = null
        order.courier_accepted_source = null
        order.courier_read_at = null
        orders.value = [...orders.value]
        saveOrdersToCache(orders.value)
      }
      showMessage(`Курьер ${effectiveName} успешно назначен`, 'success')
    } else {
      const err = await response.json()
      showMessage(err.detail || 'Ошибка при назначении курьера', 'error')
    }
  } catch (e) {
    console.error('Error assigning courier:', e)
    showMessage('Ошибка сети при назначении курьера', 'error')
  } finally {
    assigningCourierOrderId.value = null
  }
}

const handleOrderUpdateEvent = (event) => {
  console.log("WebSocket event: order-updated-event", event.detail)
  const detail = event.detail

  // Моментальное обновление статуса курьера (зеленый кружок принятия заказа)
  if (detail && detail.courier_notification_status && (detail.order_id || detail.order_num)) {
    const targetOrder = orders.value.find(o => 
      o.id === detail.order_id || 
      String(o.id) === String(detail.order_id) || 
      (detail.order_num && (String(o.external_number) === String(detail.order_num) || String(o.id) === String(detail.order_num)))
    )
    if (targetOrder) {
      targetOrder.courier_notification_status = detail.courier_notification_status
      if (detail.courier_last_message_text) {
        targetOrder.courier_last_message_text = detail.courier_last_message_text
      }
      orders.value = [...orders.value]
      saveOrdersToCache(orders.value)
    }
  }

  if (detail && detail.order && detail.order.id) {
    const idx = orders.value.findIndex(o => o.id === detail.order.id)
    const newItemsCount = detail.order.order_items_details?.length || detail.order.items?.length
    if (idx !== -1) {
      orders.value.splice(idx, 1, {
        ...orders.value[idx],
        ...detail.order,
        orderItemsCount: newItemsCount !== undefined ? newItemsCount : orders.value[idx].orderItemsCount,
      })
    } else {
      orders.value.unshift({
        ...detail.order,
        orderItemsCount: newItemsCount || 0,
      })
    }
    // Принудительный триггер реактивности для вычисляемых свойств (activeCount и др.)
    orders.value = [...orders.value]
    saveOrdersToCache(orders.value)
  }
  loadActiveOrders(true)
}

onMounted(async () => {
  loadSettings()

  // 1. Мгновенная подгрузка активных заказов в работе (~15-30 мс) и активных курьеров
  await loadActiveOrders(true)
  fetchActiveCouriers()

  // 2. Фоновая загрузка полного архива заказов
  loadOrders(orders.value.length > 0)

  // 3. Автообновление заказов в работе каждые 15 секунд, курьеров каждые 30 секунд
  activeInterval = setInterval(() => {
    loadActiveOrders(true)
  }, 15000)
  setInterval(() => {
    fetchActiveCouriers()
  }, 30000)

  // 4. Фоновое автообновление полного архива заказов каждые 60 секунд
  updateInterval = setInterval(() => {
    loadOrders(true)
  }, 60000)

  // 5. Подключение WebSocket Мультичата для приема входящих диалогов в реальном времени
  chatStore.connectWs()

  window.addEventListener('order-updated-event', handleOrderUpdateEvent)

  // Автооткрытие заказа при переходе из уведомлений (?order_id=...)
  const queryOrderId = route.query?.order_id || route.query?.id
  if (queryOrderId) {
    setTimeout(() => {
      openOrderById(queryOrderId)
    }, 400)
  }
})

watch(() => route.query?.order_id, (newId) => {
  if (newId) {
    openOrderById(newId)
  }
})

onUnmounted(() => {
  if (activeInterval) {
    clearInterval(activeInterval)
  }
  if (updateInterval) {
    clearInterval(updateInterval)
  }
  window.removeEventListener('order-updated-event', handleOrderUpdateEvent)
})

const formatPrice = val => {
  if (val === null || val === undefined) return "0.00"
  const num = parseFloat(val)

  return isNaN(num) ? "0.00" : num.toFixed(2)
}

const getRowProps = ({ item }) => {
  const status = (item.status || "").toLowerCase()
  
  // Элегантные адаптивные полупрозрачные фоны на базе CSS-переменных темы Vuetify
  let style = {}
  
  if (status === "new" || status === "unconfirmed") {
    style = { backgroundColor: "rgba(var(--v-theme-warning), 0.05)" }
  } else if (["preparing", "cooking"].includes(status)) {
    style = { backgroundColor: "rgba(var(--v-theme-info), 0.05)" }
  } else if (status === "ready" || status === "ready_for_pickup") {
    style = { backgroundColor: "rgba(var(--v-theme-success), 0.05)" }
  } else if (status.includes("cancel") || status === "cancelled") {
    style = { backgroundColor: "rgba(var(--v-theme-error), 0.05)" }
  }

  return {
    style: {
      ...style,
      cursor: "pointer",
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

const cleanCourierName = name => {
  if (!name) return 'Не назначен'
  const cleaned = name.replace(/(\s+None)+$/i, '').replace(/None\s+None/i, '').trim()
  return cleaned || 'Не назначен'
}

const getPaymentStatusInfo = item => {
  const total = parseFloat(item.total_with_discount || item.total_amount || item.sum || 0)
  const paid = parseFloat(item.total_paid || 0)
  const left = parseFloat(item.left_to_pay !== undefined && item.left_to_pay !== null ? item.left_to_pay : (total - paid))

  let status = 'unpaid'
  let color = 'error'
  let label = 'Не оплачен'

  if (item.is_paid || (total > 0 && left <= 0)) {
    status = 'paid'
    color = 'success'
    label = 'Оплачен полностью'
  } else if (paid > 0 && left > 0) {
    status = 'partial'
    color = 'warning'
    label = `Оплачен не полностью (остаток ${formatPrice(left)} ₽)`
  } else {
    status = 'unpaid'
    color = 'error'
    label = `Не оплачен (к оплате ${formatPrice(total)} ₽)`
  }

  // Определение способа оплаты и иконки
  const payMethod = (item.payment_method || '').toLowerCase()
  let icon = 'bx-check-circle'
  if (payMethod.includes('нал') || payMethod.includes('cash')) {
    icon = 'bx-money'
  } else if (payMethod.includes('карт') || payMethod.includes('card') || payMethod.includes('pos') || payMethod.includes('терминал')) {
    icon = 'bx-credit-card'
  } else {
    icon = status === 'unpaid' ? 'bx-x-circle' : 'bx-check-circle'
  }

  return { status, color, icon, label, method: item.payment_method || 'Не указан' }
}

const getOrderCompletionTime = order => {
  if (!order) return ''
  if (order.status === 'cancelled') {
    if (order.status_history && Array.isArray(order.status_history)) {
      const cancelEvent = order.status_history.find(e => e.status === 'cancelled' || (e.description && e.description.toLowerCase().includes('отмен')))
      if (cancelEvent && cancelEvent.time) {
        return formatDateTime(cancelEvent.time)
      }
    }
    return formatDateTime(order.updated_at || order.created_at)
  }
  if (order.status === 'delivered' || order.status === 'closed') {
    if (order.actual_time) {
      return formatDateTime(order.actual_time)
    }
    if (order.status_history && Array.isArray(order.status_history)) {
      const delEvent = order.status_history.find(e => ['delivered', 'closed'].includes(e.status))
      if (delEvent && delEvent.time) {
        return formatDateTime(delEvent.time)
      }
    }
    return formatDateTime(order.updated_at || order.created_at)
  }
  return ''
}

const getOrderCookingDuration = item => {
  if (!item) return ''
  
  let cookTime = null
  let closeTime = null

  if (item.status_history && Array.isArray(item.status_history)) {
    for (const ev of item.status_history) {
      const st = (ev.status || '').toLowerCase()
      if (['cooking', 'preparing'].includes(st) && !cookTime && ev.time) {
        cookTime = new Date(ev.time)
      }
      if (['closed', 'delivered', 'cancelled'].includes(st) && ev.time) {
        closeTime = new Date(ev.time)
      }
    }
    // Если в истории не было прямого cooking, берем первое событие
    if (!cookTime && item.status_history.length > 0 && item.status_history[0].time) {
      cookTime = new Date(item.status_history[0].time)
    }
  }

  if (!cookTime) {
    const rawCook = item.iiko_creation_time || item.created_at
    if (rawCook) cookTime = new Date(rawCook)
  }

  if (!closeTime) {
    const rawClose = item.actual_time || item.updated_at
    if (rawClose) closeTime = new Date(rawClose)
  }

  if (cookTime && closeTime) {
    const diffMs = closeTime.getTime() - cookTime.getTime()
    if (diffMs > 0) {
      const totalMinutes = Math.round(diffMs / 60000)
      if (totalMinutes < 60) {
        return `${totalMinutes} мин.`
      } else {
        const hours = Math.floor(totalMinutes / 60)
        const mins = totalMinutes % 60
        return `${hours}ч ${mins}м`
      }
    }
  }

  return ''
}


const openCustomerChat = (item) => {
  if (!item) return
  // Переход в основной раздел Мультичата без тяжелых плавающих окон
  window.open('/admin/multichat', '_blank')
}
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center flex-wrap ga-2 py-4">
          <div class="d-flex align-center me-2">
            <VIcon
              icon="bx-cart"
              class="me-2"
            />
            <span class="font-weight-bold text-no-wrap me-2">Управление заказами</span>
          </div>

          <!-- Табы фильтрации: Все / Текущие / Архив -->
          <div
            class="d-inline-flex align-center border rounded-lg pa-1 my-1 me-2"
            style="gap: 4px; background: rgba(var(--v-theme-on-surface), 0.04);"
          >
            <VBtn
              size="small"
              :variant="orderFilterTab === 'all' ? 'flat' : 'text'"
              :color="orderFilterTab === 'all' ? 'primary' : 'default'"
              class="text-none font-weight-bold px-3 rounded-md"
              height="32"
              @click="orderFilterTab = 'all'"
            >
              Все
            </VBtn>

            <VBtn
              size="small"
              :variant="orderFilterTab === 'active' ? 'flat' : 'text'"
              :color="orderFilterTab === 'active' ? 'primary' : 'default'"
              class="text-none font-weight-bold px-3 rounded-md"
              height="32"
              @click="orderFilterTab = 'active'"
            >
              <span>Текущие</span>
              <VChip
                size="x-small"
                :color="orderFilterTab === 'active' ? 'white' : (activeCount > 0 ? 'error' : 'secondary')"
                :variant="orderFilterTab === 'active' ? 'elevated' : 'flat'"
                class="ms-2 font-weight-black px-1.5"
                style="height: 18px; min-width: 18px;"
                :style="orderFilterTab === 'active' ? 'color: var(--v-theme-primary) !important; background: white !important;' : ''"
              >
                {{ activeCount }}
              </VChip>
            </VBtn>

            <VBtn
              size="small"
              :variant="orderFilterTab === 'archive' ? 'flat' : 'text'"
              :color="orderFilterTab === 'archive' ? 'primary' : 'default'"
              class="text-none font-weight-bold px-3 rounded-md"
              height="32"
              @click="orderFilterTab = 'archive'"
            >
              Архив
            </VBtn>
          </div>

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
          <!-- Десктопная версия (таблица) -->
          <div class="d-none d-md-block">
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
              <!-- Индикатор статуса уведомления курьера (в самом начале строчки) -->
              <template #item.courier_notification_indicator="{ item }">
                <div class="d-flex align-center justify-center" style="min-width: 24px;">
                  <!-- Красный крестик: не доставлено в соцсети -->
                  <VTooltip v-if="item.courier_notification_status === 'failed'" location="top">
                    <template #activator="{ props: ttProps }">
                      <VIcon
                        v-bind="ttProps"
                        icon="bx-x"
                        color="error"
                        size="22"
                        class="font-weight-black cursor-pointer"
                      />
                    </template>
                    <span>Ошибка отправки в соцсеть{{ item.courier_last_message_text ? (': ' + item.courier_last_message_text) : '' }}</span>
                  </VTooltip>

                  <!-- Красный кружок: отправлено, но не прочитано -->
                  <VTooltip v-else-if="item.courier_notification_status === 'unread' || item.courier_notification_status === 'sent'" location="top">
                    <template #activator="{ props: ttProps }">
                      <span
                        v-bind="ttProps"
                        class="courier-indicator-dot dot-red cursor-pointer"
                      ></span>
                    </template>
                    <span>Курьер не прочитал уведомление о заказе</span>
                  </VTooltip>

                  <!-- Желтый кружок: прочитано курьером -->
                  <VTooltip v-else-if="item.courier_notification_status === 'read'" location="top">
                    <template #activator="{ props: ttProps }">
                      <span
                        v-bind="ttProps"
                        class="courier-indicator-dot dot-yellow cursor-pointer"
                      ></span>
                    </template>
                    <span>Курьер прочитал уведомление о заказе</span>
                  </VTooltip>

                  <!-- Зеленый кружок: поставил реакцию / ответил / нажал 'Принял заказ' -->
                  <VTooltip v-else-if="item.courier_notification_status === 'accepted'" location="top">
                    <template #activator="{ props: ttProps }">
                      <span
                        v-bind="ttProps"
                        class="courier-indicator-dot dot-green cursor-pointer"
                      ></span>
                    </template>
                    <span>{{ item.courier_last_message_text ? ('Курьер подтвердил: ' + item.courier_last_message_text) : 'Курьер принял заказ / ответил / поставил реакцию' }}</span>
                  </VTooltip>

                  <span v-else class="text-caption text-disabled opacity-30">—</span>
                </div>
              </template>

              <!-- Столбец: ID / iiko (объединенный с построчным выводом и пояснениями) -->
              <template #item.id="{ item }">
                <div class="d-flex flex-column py-1 ga-0 text-body-2" style="line-height: 1.25;">
                  <div class="d-flex align-center ga-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold">ID:</span>
                    <span class="font-weight-black text-high-emphasis">#{{ item.id }}</span>
                  </div>
                  <div class="d-flex align-center ga-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold">iiko:</span>
                    <span class="font-weight-bold text-high-emphasis">{{ item.external_number || '—' }}</span>
                  </div>
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

              <!-- Столбец: Кухня / Курьер (время готовки и назначение/переназначение курьера на доставку) -->
              <template #item.cooking_and_courier="{ item }">
                <div class="d-flex flex-column py-1 ga-1" style="line-height: 1.25;" @click.stop>
                  <!-- Строка 1: Время приготовления от кухни -->
                  <div class="d-flex align-center">
                    <!-- Для закрытых/отмененных заказов: фактическое время от готовки до закрытия -->
                    <template v-if="isOrderCompleted(item)">
                      <VTooltip v-if="getOrderCookingDuration(item)" location="top">
                        <template #activator="{ props: tipProps }">
                          <VChip
                            v-bind="tipProps"
                            size="small"
                            color="secondary"
                            variant="tonal"
                            class="font-weight-bold rounded-lg px-2"
                            style="font-size: 11px !important; height: 26px; cursor: help;"
                          >
                            ⏱️ {{ getOrderCookingDuration(item) }}
                          </VChip>
                        </template>
                        <span>Время приготовления: {{ getOrderCookingDuration(item) }} (от статуса «Готовится» до «Закрыт»)</span>
                      </VTooltip>
                      <span v-else class="text-caption text-disabled">—</span>
                    </template>

                    <!-- Для активных заказов: интерактивный выбор времени (покрупнее для доставки) -->
                    <template v-else>
                      <VMenu scrollable max-height="320">
                        <template #activator="{ props: menuProps }">
                          <VChip
                            v-bind="menuProps"
                            size="small"
                            color="indigo"
                            variant="flat"
                            class="font-weight-black text-white rounded-lg px-2 cursor-pointer shadow-sm"
                            :style="item.order_type !== 'Самовывоз' ? 'min-width: 84px; height: 28px; font-size: 12px !important;' : 'min-width: 72px; height: 26px; font-size: 11px !important;'"
                          >
                            <VIcon icon="bx-time" size="14" class="me-1" />
                            {{ item.cooking_time_minutes !== undefined && item.cooking_time_minutes !== null ? item.cooking_time_minutes : 0 }} мин.
                            <VIcon icon="bx-chevron-down" size="12" class="ms-0.5" />
                          </VChip>
                        </template>
                        <VList density="compact">
                          <VListItem
                            v-for="mins in cookingTimeItems"
                            :key="mins"
                            @click="saveCookingTime(item.id, mins)"
                            :active="item.cooking_time_minutes === mins"
                          >
                            <VListItemTitle class="font-weight-bold">{{ mins }} мин.</VListItemTitle>
                          </VListItem>
                        </VList>
                      </VMenu>
                    </template>
                  </div>

                  <!-- Строка 2: Курьер (только для заказов на доставку) -->
                  <div v-if="item.order_type !== 'Самовывоз'" class="d-flex align-center mt-0.5">
                    <!-- Для завершенных заказов: просто текст курьера без меню переназначения -->
                    <template v-if="isOrderCompleted(item)">
                      <span v-if="item.courier_name && !item.courier_name.toLowerCase().includes('none none') && item.courier_name.toLowerCase().trim() !== 'не назначен'" class="text-caption text-medium-emphasis text-truncate" style="max-width: 155px;">
                        <span class="font-weight-bold">Курьер:</span> {{ cleanCourierName(item.courier_name) }}
                      </span>
                      <span v-else class="text-caption text-disabled">Курьер: Не назначен</span>
                    </template>

                    <!-- Для активных заказов: интерактивный выбор / переназначение курьера из открытых смен -->
                    <template v-else>
                      <!-- Если курьер еще не назначен в iiko -->
                      <VMenu
                        v-if="!item.courier_name || item.courier_name.toLowerCase().includes('none none') || item.courier_name.toLowerCase().trim() === 'не назначен'"
                        location="bottom start"
                        @update:model-value="val => { if (val) fetchActiveCouriers() }"
                      >
                        <template #activator="{ props: courierMenuProps }">
                          <div
                            v-bind="courierMenuProps"
                            class="d-inline-flex align-center cursor-pointer text-primary font-weight-bold text-caption courier-assign-btn"
                            title="Нажмите, чтобы назначить курьера с открытой сменой"
                          >
                            <VIcon icon="bx-user-plus" size="14" class="me-1 text-primary" />
                            <span>Назначить курьера</span>
                          </div>
                        </template>
                        <VCard min-width="250" max-width="320" class="pa-1 rounded-xl shadow-lg border">
                          <VCardTitle class="text-caption font-weight-bold px-2 py-1 d-flex align-center justify-space-between">
                            <span class="d-flex align-center">
                              <VIcon icon="bx-cycling" size="15" class="me-1 text-primary" />
                              Курьеры на смене iiko:
                            </span>
                            <VBtn icon="bx-refresh" size="20" variant="text" density="compact" :loading="loadingActiveCouriers" @click.stop="fetchActiveCouriers" title="Обновить список" />
                          </VCardTitle>
                          <VDivider class="my-1" />
                          <VList v-if="activeCouriersList.length > 0" density="compact" class="pa-0">
                            <VListItem
                              v-for="c in activeCouriersList"
                              :key="c.id"
                              @click="assignCourierToOrder(item.id, c.id, c.name)"
                              class="rounded-lg cursor-pointer my-0.5"
                              :disabled="assigningCourierOrderId === item.id"
                            >
                              <template #prepend>
                                <VIcon icon="bx-cycling" size="16" color="success" class="me-2" />
                              </template>
                              <VListItemTitle class="font-weight-medium text-body-2">{{ c.name }}</VListItemTitle>
                            </VListItem>
                          </VList>
                          <div v-else class="pa-3 text-center text-caption text-medium-emphasis">
                            <VIcon icon="bx-info-circle" size="18" color="warning" class="mb-1" /><br />
                            Нет курьеров с открытой сменой в iiko
                          </div>
                        </VCard>
                      </VMenu>

                      <!-- Если курьер выбран: отображаем Курьер: и имя курьера, при нажатии даем возможность переназначить -->
                      <VMenu
                        v-else
                        location="bottom start"
                        @update:model-value="val => { if (val) fetchActiveCouriers() }"
                      >
                        <template #activator="{ props: reassignMenuProps }">
                          <div
                            v-bind="reassignMenuProps"
                            class="d-inline-flex align-center cursor-pointer text-caption courier-reassign-btn"
                            title="Нажмите, чтобы переназначить курьера"
                          >
                            <span class="text-medium-emphasis font-weight-bold me-1">Курьер:</span>
                            <span class="font-weight-bold text-high-emphasis text-decoration-underline-dashed text-truncate" style="max-width: 110px;">
                              {{ cleanCourierName(item.courier_name) }}
                            </span>
                            <VIcon icon="bx-chevron-down" size="13" class="ms-0.5 text-medium-emphasis" />
                          </div>
                        </template>
                        <VCard min-width="250" max-width="320" class="pa-1 rounded-xl shadow-lg border">
                          <VCardTitle class="text-caption font-weight-bold px-2 py-1 d-flex align-center justify-space-between">
                            <span class="d-flex align-center">
                              <VIcon icon="bx-transfer" size="15" class="me-1 text-warning" />
                              Переназначить курьера (iiko):
                            </span>
                            <VBtn icon="bx-refresh" size="20" variant="text" density="compact" :loading="loadingActiveCouriers" @click.stop="fetchActiveCouriers" title="Обновить список" />
                          </VCardTitle>
                          <VDivider class="my-1" />
                          <VList v-if="activeCouriersList.length > 0" density="compact" class="pa-0">
                            <VListItem
                              v-for="c in activeCouriersList"
                              :key="c.id"
                              @click="assignCourierToOrder(item.id, c.id, c.name)"
                              :active="cleanCourierName(item.courier_name) === cleanCourierName(c.name)"
                              class="rounded-lg cursor-pointer my-0.5"
                              :disabled="assigningCourierOrderId === item.id"
                            >
                              <template #prepend>
                                <VIcon :icon="cleanCourierName(item.courier_name) === cleanCourierName(c.name) ? 'bx-check' : 'bx-cycling'" size="16" :color="cleanCourierName(item.courier_name) === cleanCourierName(c.name) ? 'primary' : 'secondary'" class="me-2" />
                              </template>
                              <VListItemTitle class="font-weight-medium text-body-2">{{ c.name }}</VListItemTitle>
                            </VListItem>
                          </VList>
                          <div v-else class="pa-3 text-center text-caption text-medium-emphasis">
                            <VIcon icon="bx-info-circle" size="18" color="warning" class="mb-1" /><br />
                            Нет курьеров с открытой сменой в iiko
                          </div>
                        </VCard>
                      </VMenu>
                    </template>
                  </div>
                </div>
              </template>

              <template #item.customer_name="{ item }">
                <div class="d-flex align-center flex-wrap ga-1">
                  <span class="font-weight-medium text-high-emphasis">{{ item.customer_name }}</span>

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

                  <!-- Подключенные социальные сети гостя -->
                  <div class="d-flex align-center ga-1 ms-1">
                    <VTooltip v-if="item.customer_social_channels?.vk" text="Подключен ВКонтакте">
                      <template #activator="{ props: ttProps }">
                        <VIcon
                          v-bind="ttProps"
                          icon="ri-vk-fill"
                          color="#4c75a3"
                          size="16"
                        />
                      </template>
                    </VTooltip>
                    <VTooltip v-if="item.customer_social_channels?.telegram" text="Подключен Telegram">
                      <template #activator="{ props: ttProps }">
                        <VIcon
                          v-bind="ttProps"
                          icon="ri-telegram-fill"
                          color="#0088cc"
                          size="16"
                        />
                      </template>
                    </VTooltip>
                    <VTooltip v-if="item.customer_social_channels?.max" text="Подключен MAX Messenger">
                      <template #activator="{ props: ttProps }">
                        <VIcon
                          v-bind="ttProps"
                          icon="ri-message-3-line"
                          color="#7360F2"
                          size="16"
                        />
                      </template>
                    </VTooltip>
                  </div>

                  <!-- Кнопка быстрого открытия плавающего чата -->
                  <VTooltip text="Написать в мессенджер (плавающий чат)">
                    <template #activator="{ props: ttProps }">
                      <VBtn
                        v-bind="ttProps"
                        icon="bx-chat"
                        size="x-small"
                        variant="tonal"
                        color="primary"
                        class="ms-1 px-1"
                        style="width: 22px; height: 22px; min-width: 22px;"
                        @click.stop="openCustomerChat(item)"
                      />
                    </template>
                  </VTooltip>
                </div>
              </template>

              <template #item.is_paid="{ item }">
                <div class="d-flex align-center justify-center">
                  <VTooltip location="top">
                    <template #activator="{ props: ttProps }">
                      <VIcon
                        v-bind="ttProps"
                        :icon="getPaymentStatusInfo(item).icon"
                        :color="getPaymentStatusInfo(item).color"
                        size="22"
                        class="cursor-pointer"
                      />
                    </template>
                    <div class="text-caption">
                      <div class="font-weight-bold">{{ getPaymentStatusInfo(item).label }}</div>
                      <div v-if="getPaymentStatusInfo(item).method">Способ: {{ getPaymentStatusInfo(item).method }}</div>
                    </div>
                  </VTooltip>
                </div>
              </template>

              <template #item.customer_phone="{ item }">
                <div class="d-flex align-center">
                  <span class="text-high-emphasis">{{ item.customer_phone || '—' }}</span>
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
                <span class="text-caption text-medium-emphasis">{{ item.city || '—' }}</span>
              </template>

              <!-- Столбец: Тип заказа (объединенные Тип, Адрес, Зона) -->
              <template #item.order_type_and_delivery="{ item }">
                <div class="d-flex flex-column py-1 ga-1 text-body-2" style="line-height: 1.25;">
                  <!-- 1. Тип заказа -->
                  <div class="d-flex align-center ga-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold">Тип:</span>
                    <VChip
                      size="x-small"
                      :color="item.order_type === 'Самовывоз' ? 'info' : 'primary'"
                      variant="tonal"
                      class="font-weight-bold"
                    >
                      <VIcon :icon="item.order_type === 'Самовывоз' ? 'bx-walk' : 'bx-cycling'" size="13" class="me-1" />
                      {{ item.order_type || 'Доставка' }}
                    </VChip>
                  </div>

                  <!-- 2. Адрес -->
                  <div class="d-flex align-start ga-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold">Адрес:</span>
                    <span class="text-high-emphasis font-weight-medium">
                      {{ formatAddress(item) }}
                    </span>
                  </div>

                  <!-- 3. Зона доставки -->
                  <div v-if="item.order_type !== 'Самовывоз'" class="d-flex align-center ga-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold">Зона:</span>
                    <span v-if="item.delivery_zone" class="text-caption font-weight-bold text-primary">
                      {{ item.delivery_zone }}
                    </span>
                    <span v-else class="text-caption text-disabled">
                      Не определена
                    </span>
                  </div>
                </div>
              </template>

              <!-- Столбец: Оплата (объединенные К Оплате, Оплачено, Скидка) -->
              <template #item.payment_summary="{ item }">
                <div class="d-flex flex-column py-1 ga-1 text-body-2" style="line-height: 1.25;">
                  <!-- 1. К оплате -->
                  <div class="d-flex align-center justify-space-between ga-2">
                    <span class="text-caption text-medium-emphasis font-weight-bold">К оплате:</span>
                    <span class="font-weight-black text-high-emphasis">
                      {{ formatPrice(item.total_with_discount || item.total_amount || item.sum || 0) }} ₽
                    </span>
                  </div>

                  <!-- 2. Оплачено -->
                  <div class="d-flex align-center justify-space-between ga-2">
                    <span class="text-caption text-medium-emphasis font-weight-bold">Оплачено:</span>
                    <span
                      class="font-weight-bold"
                      :class="(parseFloat(item.total_paid) > 0 || item.is_paid) ? 'text-success' : 'text-medium-emphasis'"
                    >
                      {{ formatPrice(parseFloat(item.total_paid) > 0 ? item.total_paid : (item.is_paid ? (item.total_with_discount || item.total_amount || item.sum || 0) : 0)) }} ₽
                    </span>
                  </div>

                  <!-- Остаток к оплате (если есть) -->
                  <div v-if="parseFloat(item.left_to_pay) > 0" class="d-flex align-center justify-space-between ga-2 mt-n1">
                    <span class="text-caption text-error font-weight-bold">Остаток:</span>
                    <span class="text-caption font-weight-black text-error">
                      {{ formatPrice(item.left_to_pay) }} ₽
                    </span>
                  </div>

                  <!-- 3. Скидка -->
                  <div class="d-flex align-center justify-space-between ga-2">
                    <span class="text-caption text-medium-emphasis font-weight-bold">Скидка:</span>
                    <span v-if="parseFloat(item.total_discount) > 0" class="text-caption font-weight-bold text-error">
                      -{{ formatPrice(item.total_discount) }} ₽
                    </span>
                    <span v-else class="text-caption text-disabled">0 ₽</span>
                  </div>
                </div>
              </template>

              <!-- Столбец: Доставить (объединенные Ожидаем, Статус, Время доставки/отмены) -->
              <template #item.delivery_status_summary="{ item }">
                <div class="d-flex flex-column py-1 ga-1 text-body-2" style="line-height: 1.25;">
                  <!-- 1. Время доставки (Предзаказ / Текущий) -->
                  <div class="d-flex align-center ga-1">
                    <span class="text-caption text-medium-emphasis font-weight-bold">
                      {{ item.is_asap ? 'Текущий:' : 'Предзаказ:' }}
                    </span>
                    <div class="d-inline-flex align-center ga-1">
                      <span class="text-caption font-weight-black" :class="item.is_asap ? 'text-warning' : 'text-info'">
                        {{ item.is_asap ? '⚡' : '⏰' }}
                        {{ formatDateTime(item.expected_time || item.iiko_creation_time || item.created_at, { day: undefined, month: undefined, year: undefined }) }}
                      </span>
                      <span
                        v-if="!item.is_asap && item.expected_time && formatDate(item.expected_time) !== formatDate(new Date())"
                        class="text-caption text-primary font-weight-bold"
                        style="font-size: 11px;"
                      >
                        ({{ formatDateTime(item.expected_time, { hour: undefined, minute: undefined, second: undefined }) }})
                      </span>
                    </div>
                  </div>

                  <!-- 2. Текущий статус заказа -->
                  <div class="d-flex align-center ga-2 mt-1">
                    <VChip
                      :color="getStatusColor(item.status)"
                      size="x-small"
                      class="text-uppercase font-weight-bold"
                      variant="tonal"
                    >
                      {{ statusNames[item.status] || item.status }}
                    </VChip>

                    <!-- Индикатор отправленного уведомления клиенту (VK / TG / MAX) -->
                    <VTooltip
                      v-if="item.status_notification?.configured"
                      location="top"
                    >
                      <template #activator="{ props: ttProps }">
                        <div v-bind="ttProps" class="d-flex align-center position-relative cursor-pointer">
                          <VIcon
                            :icon="item.status_notification.channel === 'vk' ? 'ri-vk-fill' : (item.status_notification.channel === 'telegram' ? 'ri-telegram-fill' : (item.status_notification.channel === 'max' ? 'ri-message-3-line' : 'ri-mail-send-line'))"
                            :color="item.status_notification.channel === 'vk' ? '#4c75a3' : (item.status_notification.channel === 'telegram' ? '#0088cc' : (item.status_notification.channel === 'max' ? '#7360F2' : 'warning'))"
                            size="18"
                          />
                          <span
                            class="position-absolute border border-white rounded-circle"
                            :style="{
                              bottom: '-2px',
                              right: '-2px',
                              width: '7px',
                              height: '7px',
                              backgroundColor: item.status_notification.status === 'success' ? '#4caf50' : '#f44336'
                            }"
                          ></span>
                        </div>
                      </template>
                      <div>
                        <div class="font-weight-bold">
                          Уведомление в {{ item.status_notification.channel === 'vk' ? 'ВКонтакте' : (item.status_notification.channel === 'telegram' ? 'Telegram' : (item.status_notification.channel === 'max' ? 'MAX' : (item.status_notification.channel === 'sms' ? 'SMS' : item.status_notification.channel))) }}
                        </div>
                        <div class="text-caption">
                          Статус: {{ item.status_notification.status === 'success' ? 'Успешно отправлено' : (item.status_notification.status === 'failed' ? 'Ошибка отправки' : 'Не отправлено') }}
                        </div>
                        <div v-if="item.status_notification.error_text" class="text-caption mt-1" style="color: var(--v-theme-error);">
                          Причина: {{ item.status_notification.error_text }}
                        </div>
                      </div>
                    </VTooltip>
                  </div>

                  <!-- 3. Время доставки или отмены заказа -->
                  <div v-if="item.status === 'cancelled' && getOrderCompletionTime(item)" class="d-flex align-center ga-1 mt-1 text-caption text-error font-weight-bold">
                    <VIcon icon="bx-x" size="14" color="error" />
                    <span>Отменен: {{ getOrderCompletionTime(item) }}</span>
                  </div>
                  <div v-else-if="(item.status === 'delivered' || item.status === 'closed') && getOrderCompletionTime(item)" class="d-flex align-center ga-1 mt-1 text-caption text-success font-weight-bold">
                    <VIcon icon="bx-check" size="14" color="success" />
                    <span>Доставлен: {{ getOrderCompletionTime(item) }}</span>
                  </div>
                </div>
              </template>

              <template #item.created_at="{ item }">
                <span v-if="item.iiko_creation_time || item.created_at" class="text-caption text-medium-emphasis">
                  {{ formatDateTime(item.iiko_creation_time || item.created_at) }}
                </span>
                <span v-else class="text-caption text-disabled">Нет данных</span>
              </template>
            </VDataTable>
          </div>

          <!-- Мобильная версия (карточки) -->
          <div class="d-block d-md-none mt-4">
            <div v-if="sortedOrders.length === 0" class="d-flex flex-column align-center my-8 py-8 bg-var-theme-surface rounded border elevation-1">
              <VIcon icon="bx-cart" size="48" color="disabled" class="mb-2" />
              <div class="text-body-1 text-disabled">Заказы не найдены</div>
            </div>
            <div v-else>
              <VCard
                v-for="item in sortedOrders"
                :key="item.id"
                class="mb-4 order-mobile-card border rounded-lg elevation-1 pa-4"
                :style="{
                  borderLeft: `5px solid ${
                    item.status === 'new' || item.status === 'unconfirmed' ? 'rgba(var(--v-theme-warning), 0.8)' :
                    ['preparing', 'cooking'].includes(item.status) ? 'rgba(var(--v-theme-info), 0.8)' :
                    item.status === 'ready' || item.status === 'ready_for_pickup' ? 'rgba(var(--v-theme-success), 0.8)' :
                    item.status === 'closed' ? 'rgba(var(--v-theme-secondary), 0.5)' :
                    item.status === 'cancelled' ? 'rgba(var(--v-theme-error), 0.8)' : 'rgba(var(--v-theme-primary), 0.5)'
                  }`
                }"
                @click="openOrderDetails(item)"
              >
                <!-- Шапка: Номер заказа, Тип (доставка/самовывоз), Статус -->
                <div class="d-flex justify-space-between align-center mb-3">
                  <div class="d-flex align-center gap-2 flex-wrap">
                    <!-- Мобильный индикатор статуса курьера -->
                    <span v-if="item.courier_notification_status === 'failed'" class="d-inline-flex align-center">
                      <VIcon icon="bx-x" color="error" size="20" class="font-weight-black" title="Ошибка отправки курьеру" />
                    </span>
                    <span v-else-if="item.courier_notification_status === 'unread' || item.courier_notification_status === 'sent'" class="courier-indicator-dot dot-red" title="Курьер не прочитал"></span>
                    <span v-else-if="item.courier_notification_status === 'read'" class="courier-indicator-dot dot-yellow" title="Курьер прочитал"></span>
                    <span v-else-if="item.courier_notification_status === 'accepted'" class="courier-indicator-dot dot-green" title="Курьер принял заказ"></span>

                    <div class="d-flex flex-column" style="line-height: 1.2;">
                      <span class="text-caption font-weight-bold text-medium-emphasis">ID: #{{ item.id }}</span>
                      <span class="font-weight-black text-body-2 text-primary">iiko: {{ item.external_number || '—' }}</span>
                    </div>
                    <!-- Для закрытых/отмененных заказов: скрываем выбор и показываем время от готовки до закрытия -->
                    <template v-if="isOrderCompleted(item)">
                      <VChip
                        v-if="getOrderCookingDuration(item)"
                        size="x-small"
                        color="secondary"
                        variant="tonal"
                        class="font-weight-bold rounded-pill px-1"
                        style="font-size: 10px !important; height: 16px;"
                      >
                        ⏱️ {{ getOrderCookingDuration(item) }}
                      </VChip>
                    </template>

                    <!-- Для активных заказов: выбор времени готовности -->
                    <template v-else>
                      <VMenu scrollable max-height="300">
                        <template #activator="{ props: menuProps }">
                          <VChip
                            v-bind="menuProps"
                            size="small"
                            color="indigo"
                            variant="flat"
                            class="font-weight-black text-white rounded-lg px-2 cursor-pointer shadow-sm"
                            style="font-size: 11px !important; height: 26px;"
                            @click.stop
                          >
                            <VIcon icon="bx-time" size="13" class="me-0.5" />
                            {{ item.cooking_time_minutes !== undefined && item.cooking_time_minutes !== null ? item.cooking_time_minutes : 0 }} мин.
                          </VChip>
                        </template>
                        <VList density="compact">
                          <VListItem
                            v-for="mins in cookingTimeItems"
                            :key="mins"
                            @click="saveCookingTime(item.id, mins)"
                          >
                            <VListItemTitle>{{ mins }} мин.</VListItemTitle>
                          </VListItem>
                        </VList>
                      </VMenu>
                    </template>
                    <VChip
                      size="x-small"
                      :color="item.order_type === 'Самовывоз' ? 'info' : 'primary'"
                      variant="tonal"
                      class="font-weight-bold"
                    >
                      {{ item.order_type === 'Самовывоз' ? 'Самовывоз' : 'Доставка' }}
                    </VChip>
                  </div>
                  <div class="d-flex align-center ga-2">
                    <VChip
                      :color="getStatusColor(item.status)"
                      size="small"
                      class="text-uppercase font-weight-black"
                      variant="tonal"
                    >
                      {{ statusNames[item.status] || item.status }}
                    </VChip>

                    <!-- Индикатор отправленного уведомления в мобильной версии -->
                    <div v-if="item.status_notification?.configured" class="d-flex align-center position-relative">
                      <VIcon
                        :icon="item.status_notification.channel === 'vk' ? 'ri-vk-fill' : (item.status_notification.channel === 'telegram' ? 'ri-telegram-fill' : (item.status_notification.channel === 'max' ? 'ri-message-3-line' : 'ri-mail-send-line'))"
                        :color="item.status_notification.channel === 'vk' ? '#4c75a3' : (item.status_notification.channel === 'telegram' ? '#0088cc' : (item.status_notification.channel === 'max' ? '#7360F2' : 'warning'))"
                        size="18"
                      />
                      <span
                        class="position-absolute border border-white rounded-circle"
                        :style="{
                          bottom: '-1px',
                          right: '-1px',
                          width: '6px',
                          height: '6px',
                          backgroundColor: item.status_notification.status === 'success' ? '#4caf50' : '#f44336'
                        }"
                      ></span>
                    </div>
                  </div>
                </div>

                <!-- Клиент и Телефон -->
                <div class="d-flex justify-space-between align-center mb-2">
                  <div class="d-flex align-center gap-1 flex-wrap">
                    <span class="font-weight-bold text-body-1 text-high-emphasis">{{ item.customer_name }}</span>
                    <VIcon
                      v-if="item.customer_is_new"
                      icon="bx-star"
                      color="#ffb74d"
                      size="16"
                      title="Новый клиент"
                    />
                    <VIcon
                      :icon="item.customer_is_risk ? 'bx-shield-x' : 'bx-shield-quarter'"
                      :color="item.customer_is_risk ? '#e57373' : '#81c784'"
                      size="16"
                      :title="item.customer_is_risk ? 'Высокий риск!' : 'Клиент проверен'"
                    />

                    <!-- Подключенные соцсети -->
                    <VIcon
                      v-if="item.customer_social_channels?.vk"
                      icon="ri-vk-fill"
                      color="#4c75a3"
                      size="14"
                      title="Подключен ВКонтакте"
                    />
                    <VIcon
                      v-if="item.customer_social_channels?.telegram"
                      icon="ri-telegram-fill"
                      color="#0088cc"
                      size="14"
                      title="Подключен Telegram"
                    />
                    <VIcon
                      v-if="item.customer_social_channels?.max"
                      icon="ri-message-3-line"
                      color="#7360F2"
                      size="14"
                      title="Подключен MAX"
                    />
                  </div>
                  <a
                    v-if="item.customer_phone"
                    :href="'tel:' + item.customer_phone"
                    class="text-body-2 font-weight-bold text-primary text-decoration-none"
                    @click.stop
                  >
                    {{ item.customer_phone }}
                  </a>
                </div>

                <!-- Адрес и зона -->
                <div class="mb-2 text-body-2 text-high-emphasis">
                  <div class="d-flex align-start">
                    <VIcon icon="bx-map" size="18" class="me-1 mt-0.5 text-primary" />
                    <span class="font-weight-medium">{{ formatAddress(item) }}</span>
                  </div>
                  <div v-if="item.order_type !== 'Самовывоз' && (item.resolved_delivery_zone_name || item.delivery_zone)" class="text-caption text-secondary ps-5 mt-0.5">
                    Зона: {{ item.resolved_delivery_zone_name || item.delivery_zone }}
                  </div>
                </div>

                 <!-- Курьер в мобильной карточке -->
                <div v-if="item.order_type !== 'Самовывоз'" class="mb-2 text-body-2" @click.stop>
                  <div class="d-flex align-center">
                    <VIcon icon="ri-truck-line" size="18" class="me-1 text-secondary" />
                    <span class="font-weight-medium me-1">Курьер:</span>
                    <template v-if="isOrderCompleted(item)">
                      <span
                        v-if="!item.courier_name || item.courier_name.toLowerCase().includes('none none') || item.courier_name.toLowerCase().trim() === 'не назначен'"
                        class="text-disabled font-weight-medium"
                      >
                        Не назначен
                      </span>
                      <span v-else class="font-weight-bold text-high-emphasis">
                        {{ cleanCourierName(item.courier_name) }}
                      </span>
                    </template>
                    <template v-else>
                      <VMenu
                        location="bottom start"
                        @update:model-value="val => { if (val) fetchActiveCouriers() }"
                      >
                        <template #activator="{ props: mobCourierProps }">
                          <span
                            v-if="!item.courier_name || item.courier_name.toLowerCase().includes('none none') || item.courier_name.toLowerCase().trim() === 'не назначен'"
                            v-bind="mobCourierProps"
                            class="text-primary font-weight-bold text-caption cursor-pointer"
                          >
                            + Назначить курьера
                          </span>
                          <span
                            v-else
                            v-bind="mobCourierProps"
                            class="font-weight-bold text-high-emphasis text-decoration-underline-dashed cursor-pointer d-inline-flex align-center"
                          >
                            {{ cleanCourierName(item.courier_name) }}
                            <VIcon icon="bx-chevron-down" size="14" class="ms-0.5 text-medium-emphasis" />
                          </span>
                        </template>
                        <VCard min-width="250" max-width="320" class="pa-1 rounded-xl shadow-lg border">
                          <VCardTitle class="text-caption font-weight-bold px-2 py-1 d-flex align-center justify-space-between">
                            <span>Курьеры на смене iiko:</span>
                            <VBtn icon="bx-refresh" size="20" variant="text" density="compact" :loading="loadingActiveCouriers" @click.stop="fetchActiveCouriers" />
                          </VCardTitle>
                          <VDivider class="my-1" />
                          <VList v-if="activeCouriersList.length > 0" density="compact" class="pa-0">
                            <VListItem
                              v-for="c in activeCouriersList"
                              :key="c.id"
                              @click="assignCourierToOrder(item.id, c.id, c.name)"
                              class="rounded-lg cursor-pointer my-0.5"
                              :disabled="assigningCourierOrderId === item.id"
                            >
                              <template #prepend>
                                <VIcon icon="bx-cycling" size="16" color="success" class="me-2" />
                              </template>
                              <VListItemTitle class="font-weight-medium text-body-2">{{ c.name }}</VListItemTitle>
                            </VListItem>
                          </VList>
                          <div v-else class="pa-3 text-center text-caption text-medium-emphasis">
                            <VIcon icon="bx-info-circle" size="18" color="warning" class="mb-1" /><br />
                            Нет курьеров с открытой сменой в iiko
                          </div>
                        </VCard>
                      </VMenu>
                    </template>
                  </div>
                </div>

                <VDivider class="my-2" />

                <!-- Финансовый блок -->
                <div class="d-flex justify-space-between align-end">
                  <div>
                    <div class="d-flex align-center gap-1 mb-1">
                      <VIcon
                        :icon="getPaymentStatusInfo(item).icon"
                        :color="getPaymentStatusInfo(item).color"
                        size="18"
                      />
                      <span class="text-caption font-weight-bold" :class="`text-${getPaymentStatusInfo(item).color}`">
                        {{ getPaymentStatusInfo(item).label }}
                      </span>
                    </div>
                    <div v-if="getPaymentStatusInfo(item).method" class="text-tiny text-medium-emphasis mb-1">
                      {{ getPaymentStatusInfo(item).method }}
                    </div>
                    <VChip
                      v-if="item.total_discount > 0"
                      size="x-small"
                      variant="tonal"
                      color="error"
                      class="font-weight-bold"
                    >
                      Скидка -{{ item.total_discount }} ₽
                    </VChip>
                  </div>

                  <div class="text-end">
                    <div class="text-caption text-medium-emphasis">
                      Оплачено: 
                      <span class="font-weight-bold text-success">
                        {{ formatPrice(parseFloat(item.total_paid) > 0 ? item.total_paid : (parseFloat(item.total_with_discount || item.total_amount || item.sum || 0) - parseFloat(item.left_to_pay || 0))) }} ₽
                      </span>
                    </div>
                    <div class="text-subtitle-1 font-weight-black text-high-emphasis">
                      Итого: {{ formatPrice(item.total_with_discount || item.total_amount || item.sum || 0) }} ₽
                    </div>
                    <div v-if="parseFloat(item.left_to_pay) > 0" class="mt-0.5">
                      <VChip size="x-small" color="error" class="font-weight-bold">
                        ост. {{ formatPrice(item.left_to_pay) }} ₽
                      </VChip>
                    </div>
                  </div>
                </div>

                <!-- Время создания и Ожидания -->
                <div class="d-flex justify-space-between align-center mt-3 pt-2 border-top text-caption text-disabled">
                  <div>
                    <span>Создан: {{ formatDateTime(item.iiko_creation_time || item.created_at) }}</span>
                  </div>
                  
                  <div 
                    class="d-flex align-center gap-1 px-2 py-0.5 rounded-lg border font-weight-bold"
                    :style="{
                      backgroundColor: item.is_asap ? 'rgba(var(--v-theme-warning), 0.1)' : 'rgba(var(--v-theme-info), 0.1)',
                      borderColor: item.is_asap ? 'rgba(var(--v-theme-warning), 0.3)' : 'rgba(var(--v-theme-info), 0.3)',
                      color: item.is_asap ? 'rgb(var(--v-theme-warning))' : 'rgb(var(--v-theme-info))'
                    }"
                  >
                    <span>{{ item.is_asap ? '⚡ Текущий:' : '⏰ Предзаказ:' }}</span>
                    <span>
                      {{ formatDateTime(item.expected_time || item.iiko_creation_time || item.created_at, { day: undefined, month: undefined, year: undefined }) }}
                    </span>
                    <span v-if="!item.is_asap && item.expected_time && formatDate(item.expected_time) !== formatDate(new Date())" style="font-size: 0.7rem">
                      ({{ formatDateTime(item.expected_time, { hour: undefined, minute: undefined, second: undefined }) }})
                    </span>
                  </div>
                </div>

                <!-- Время доставки или отмены заказа в мобильной версии -->
                <div v-if="item.status === 'cancelled' && getOrderCompletionTime(item)" class="mt-2 text-caption text-error font-weight-bold d-flex align-center gap-1">
                  <VIcon icon="bx-x" size="14" color="error" />
                  <span>Отменен: {{ getOrderCompletionTime(item) }}</span>
                </div>
                <div v-else-if="(item.status === 'delivered' || item.status === 'closed') && getOrderCompletionTime(item)" class="mt-2 text-caption text-success font-weight-bold d-flex align-center gap-1">
                  <VIcon icon="bx-check" size="14" color="success" />
                  <span>Доставлен: {{ getOrderCompletionTime(item) }}</span>
                </div>
              </VCard>
            </div>
          </div>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- Floating Action Buttons для мобильных -->
  <div class="d-block d-md-none position-fixed" style="bottom: 80px; right: 16px; z-index: 99;">
    <div class="d-flex flex-column gap-2">
      <VBtn
        color="warning"
        icon="bx-cloud-download"
        elevation="4"
        :loading="syncing"
        @click="syncRecentOrders"
      />
      <VBtn
        color="primary"
        icon="bx-refresh"
        elevation="4"
        :loading="loading"
        @click="loadOrders(false)"
      />
    </div>
  </div>

  <OrderDetailModal
    v-model="isModalOpen"
    :order="selectedOrder"
    :address-format="addressFormat"
    @update:order="handleOrderUpdated"
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

.column-indicator {
  width: 34px !important;
  min-width: 34px !important;
  max-width: 34px !important;
  padding: 0 2px !important;
  text-align: center !important;
}
.v-data-table__th.column-indicator {
  width: 34px !important;
}

.courier-indicator-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.courier-indicator-dot:hover {
  transform: scale(1.3);
}
.dot-red {
  background-color: #ef4444;
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.7);
}
.dot-yellow {
  background-color: #f59e0b;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.7);
}
.dot-green {
  background-color: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.7);
}

.text-decoration-underline-dashed {
  text-decoration: underline dashed;
  text-underline-offset: 3px;
}

.courier-assign-btn {
  transition: opacity 0.2s ease, transform 0.1s ease;
}
.courier-assign-btn:hover {
  opacity: 0.8;
  transform: scale(1.02);
}

.courier-reassign-btn {
  transition: opacity 0.2s ease;
}
.courier-reassign-btn:hover {
  opacity: 0.85;
}



.text-tiny {
  font-size: 11px;
}
</style>
