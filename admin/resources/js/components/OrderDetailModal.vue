<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from "vue"
import { formatDate, formatDateTime, formatTime, formatStatusTime } from "@/utils/date"
import CustomerDetailModal from "./CustomerDetailModal.vue"
import axios from "axios"

// Импорт новых стилей
import "../../styles/order-detail-soft.css"

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  order: {
    type: Object,
    default: () => ({}),
  },
  addressFormat: {
    type: String,
    default: "line1",
  },
  isReadOnly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(["update:modelValue", "update:order"])

const dialog = computed({
  get: () => props.modelValue,
  set: val => emit("update:modelValue", val),
})

const customerInfo = ref(null)
const isLoadingCustomer = ref(false)
const customerModalVisible = ref(false)
const selectedItem = ref(null)
const isSyncing = ref(false)

const activeCouriersList = ref([])
const courierMenuOpen = ref(false)
const assigningCourier = ref(false)

const fetchActiveCouriers = async () => {
  try {
    const response = await fetch('/api/v1/orders/active-couriers', {
      headers: {
        "Authorization": localStorage.getItem("access_token") ? `Bearer ${localStorage.getItem("access_token")}` : ""
      }
    })
    if (response.ok) {
      const resData = await response.json()
      if (resData.status === 'success') {
        activeCouriersList.value = resData.data
      }
    }
  } catch (e) {
    console.error("Failed to fetch active couriers:", e)
  }
}

const selectCourier = async (courier) => {
  if (!props.order?.id || assigningCourier.value) return
  
  assigningCourier.value = true
  courierMenuOpen.value = false
  try {
    const response = await fetch(`/api/v1/orders/${props.order.id}/courier`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": localStorage.getItem("access_token") ? `Bearer ${localStorage.getItem("access_token")}` : ""
      },
      body: JSON.stringify({ courier_iiko_id: courier.id }),
    })
    
    if (response.ok) {
      emit("update:order", props.order.id)
      window.location.reload()
    } else {
      const err = await response.json()
      alert(err.detail || "Ошибка при назначении курьера")
    }
  } catch (e) {
    console.error("Error assigning courier:", e)
    alert("Ошибка сети при назначении курьера")
  } finally {
    assigningCourier.value = false
  }
}

const syncWithIiko = async () => {
  if (!props.order?.id || isSyncing.value) return

  isSyncing.value = true
  try {
    const response = await fetch(`/api/v1/orders/${props.order.id}/sync-iiko`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (response.ok) {
      // Оповещаем родителя о необходимости обновить данные
      emit("update:order", props.order.id)
      
      // Временное решение: перезагрузка страницы для отображения изменений
      window.location.reload()
    } else {
      const err = await response.json()
      alert(err.detail || "Ошибка синхронизации")
    }
  } catch (e) {
    console.error("Sync error:", e)
    alert("Ошибка сети")
  } finally {
    isSyncing.value = false
  }
}

const isForceClosing = ref(false)
const confirmCloseDialog = ref(false)

const isOrderActive = computed(() => {
  const st = (props.order?.status || '').toLowerCase()
  return Boolean(props.order?.id && !['closed', 'delivered', 'cancelled'].includes(st))
})

const openForceCloseConfirm = () => {
  confirmCloseDialog.value = true
}

const forceCloseOrder = async () => {
  if (!props.order?.id || isForceClosing.value) return

  isForceClosing.value = true
  try {
    const token = localStorage.getItem("access_token") || localStorage.getItem("token")
    const headers = {
      "Content-Type": "application/json",
    }
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    const response = await fetch(`/api/v1/orders/${props.order.id}/force-close`, {
      method: "POST",
      headers,
    })

    if (response.ok) {
      const data = await response.json()
      confirmCloseDialog.value = false
      emit("update:order", props.order.id)
      window.location.reload()
    } else {
      const err = await response.json()
      alert(err.detail || "Ошибка при закрытии заказа")
    }
  } catch (e) {
    console.error("Force close error:", e)
    alert("Ошибка сети при закрытии заказа")
  } finally {
    isForceClosing.value = false
  }
}

const fetchCustomerInfo = async () => {
  if (!props.order?.customer_phone) return

  isLoadingCustomer.value = true
  try {
    const response = await fetch(`/api/v1/customers/by-phone/${encodeURIComponent(props.order.customer_phone)}`)
    if (response.ok) {
      customerInfo.value = await response.json()
    }
  } catch (e) {
    console.error("Failed to fetch customer info:", e)
    customerInfo.value = null
  } finally {
    isLoadingCustomer.value = false
  }
}

const showDetails = item => {
  selectedItem.value = item
}

const openCustomerModal = async () => {
  if (!customerInfo.value) {
    await fetchCustomerInfo()
  }

  if (customerInfo.value) {
    customerModalVisible.value = true
  }
}

watch(dialog, newVal => {
  if (newVal) {
    fetchCustomerInfo()
    fetchActiveCouriers()
  }
})

const formatDateFunc = (dateString, showOnlyTime = false) => {
  if (!dateString) return "—"

  return formatDateTime(dateString, showOnlyTime ? { day: undefined, month: undefined, year: undefined } : {})
}

const formatPrice = value => {
  const num = parseFloat(value)

  return isNaN(num) ? "0.00" : num.toFixed(2)
}

const canEditStatus = computed(() => {
  return !props.isReadOnly
})

const callCustomer = phone => {
  if (!phone) return

  window.location.href = `tel:${phone}`
}

const openMaps = (provider) => {
  const addr = (formattedAddress.value || '').replace(/^[❗\s]+/, '').trim() || props.order?.delivery_address
  if (!addr || addr === 'Адрес не указан' || addr.includes('Самовывоз')) {
    return
  }
  
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent)
  const isAndroid = /Android/i.test(navigator.userAgent)
  
  let webUrl = ''
  let mobileScheme = ''
  
  switch (provider) {
    case 'yandex':
      webUrl = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
      mobileScheme = `yandexmaps://maps.yandex.ru/?text=${encodeURIComponent(addr)}`
      break
    case 'yandexnavi':
      webUrl = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
      mobileScheme = `yandexnavi://map_search?text=${encodeURIComponent(addr)}`
      break
    case '2gis':
      webUrl = `https://2gis.ru/search/${encodeURIComponent(addr)}`
      mobileScheme = `dgis://2gis.ru/search/${encodeURIComponent(addr)}`
      break
    case 'google':
      webUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(addr)}`
      if (isIOS) {
        mobileScheme = `comgooglemaps://?q=${encodeURIComponent(addr)}`
      } else if (isAndroid) {
        mobileScheme = `geo:0,0?q=${encodeURIComponent(addr)}`
      } else {
        mobileScheme = `comgooglemaps://?q=${encodeURIComponent(addr)}`
      }
      break
    case 'petal':
      webUrl = `https://www.petalmaps.com/search/?q=${encodeURIComponent(addr)}`
      mobileScheme = `petalmaps://search?q=${encodeURIComponent(addr)}`
      break
    default:
      webUrl = `https://yandex.ru/maps/?text=${encodeURIComponent(addr)}`
      mobileScheme = `yandexmaps://maps.yandex.ru/?text=${encodeURIComponent(addr)}`
  }
  
  if (isMobile && mobileScheme) {
    const start = Date.now()
    window.location.href = mobileScheme
    
    setTimeout(() => {
      if (Date.now() - start < 1500) {
        window.open(webUrl, '_blank', 'noopener,noreferrer')
      }
    }, 1000)
  } else {
    window.open(webUrl, '_blank', 'noopener,noreferrer')
  }
}

const formattedAddress = computed(() => {
  if (!props.order) return "—"

  if (props.order.order_type === "Самовывоз" || (!props.order.delivery_address && !props.order.street)) return "🙍 Самовывоз"

  const status = (props.order.status || "").toLowerCase()
  const isPending = !["closed", "cancelled"].includes(status)
  const flat = (props.order.flat || "").toString().trim()
  const noFlat = !flat || flat === "0" || flat === "-"
  const showWarning = isPending && noFlat && props.order.order_type !== "Самовывоз"
  const warningPrefix = showWarning ? "❗ " : ""

  const o = props.order
  const baseAddr = (o.delivery_address || "").trim()

  // Если есть базовая строка адреса (delivery_address / line1)
  if (baseAddr && baseAddr !== "Самовывоз" && baseAddr !== "Адрес не указан") {
    let resultAddr = baseAddr

    // Проверяем, не потерялись ли важные поля клиента
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

  // Если готовой строки нет, собираем по компонентам
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
})

const statusColor = computed(() => {
  const statusColors = {
    new: "#F0F9FF",          // Light Blue
    unconfirmed: "#FFFBEB",  // Light Amber
    confirmed: "#EFF6FF",    // Light Blue
    preparing: "#F0FDF4",    // Light Green
    cooking: "#FFFBEB",      // Light Amber
    ready: "#ECFDF5",        // Light Emerald
    readyForPickup: "#ECFDF5",
    delivering: "#EEF2FF",   // Light Indigo
    delivered: "#F0FDF4",    // Light Green
    closed: "#F8FAFC",       // Slate 50
    cancelled: "#FEF2F2",    // Light Red
  }

  const key = props.order?.status ? props.order.status.replace(/_([a-z])/g, g => g[1].toUpperCase()) : "new"

  return statusColors[key] || "#F8FAFC"
})

const statusTextColor = computed(() => {
  const textColors = {
    new: "#0369A1",          // Darker Blue
    unconfirmed: "#B45309",  // Darker Amber
    confirmed: "#1D4ED8",    // Darker Blue
    preparing: "#15803D",    // Darker Green
    cooking: "#B45309",
    ready: "#047857",        // Darker Emerald
    readyForPickup: "#047857",
    delivering: "#4338CA",   // Darker Indigo
    delivered: "#15803D",
    closed: "#475569",       // Slate 600
    cancelled: "#B91C1C",    // Darker Red
  }

  const key = props.order?.status ? props.order.status.replace(/_([a-z])/g, g => g[1].toUpperCase()) : "new"

  return textColors[key] || "#475569"
})

const currentTimeNow = ref(new Date())
let statusTimerId = null

onMounted(() => {
  statusTimerId = setInterval(() => {
    currentTimeNow.value = new Date()
  }, 10000)
})

onUnmounted(() => {
  if (statusTimerId) clearInterval(statusTimerId)
})

const getStatusLabel = status => {
  if (!status) return "—"
  const labels = {
    new: "Заказ принят",
    unconfirmed: "Принят (Ожидает подтверждения)",
    waitapproval: "Ожидает подтверждения",
    accepted: "Подтвержден",
    confirmed: "Подтвержден",
    waitcooking: "Подтвержден (Кухня)",
    readyforcooking: "Подтвержден",
    preparing: "В сборке",
    cooking: "Готовится",
    cookingstarted: "Готовится",
    assembling: "На сборке",
    ready: "Готов",
    cookingfinished: "Готов",
    cookingcompleted: "Готов",
    waiting: "Готов (Ожидает курьера)",
    readyforpickup: "Готов к выдаче",
    ready_for_pickup: "Готов к выдаче",
    delivering: "У курьера",
    onway: "У курьера",
    delivered: "Доставлен",
    closed: "Закрыт",
    cancelled: "Отменен",
  }

  const s = String(status).toLowerCase().replace(/_/g, "")
  for (const [k, v] of Object.entries(labels)) {
    if (k.toLowerCase().replace(/_/g, "") === s) return v
  }
  return status
}

const getStatusColor = status => {
  if (!status) return "#94a3b8"
  const colors = {
    new: "#64748b",
    unconfirmed: "#f59e0b",
    waitapproval: "#f59e0b",
    confirmed: "#3b82f6",
    accepted: "#3b82f6",
    waitcooking: "#3b82f6",
    preparing: "#10b981",
    cooking: "#f59e0b",
    cookingstarted: "#f59e0b",
    assembling: "#10b981",
    ready: "#10b981",
    cookingfinished: "#10b981",
    cookingcompleted: "#10b981",
    waiting: "#10b981",
    readyforpickup: "#10b981",
    ready_for_pickup: "#10b981",
    delivering: "#6366f1",
    onway: "#6366f1",
    delivered: "#10b981",
    closed: "#64748b",
    cancelled: "#ef4444",
  }

  const s = String(status).toLowerCase().replace(/_/g, "")
  for (const [k, v] of Object.entries(colors)) {
    if (k.toLowerCase().replace(/_/g, "") === s) return v
  }
  return "#94a3b8"
}

const cleanCourierName = name => {
  if (!name || name.toLowerCase().includes("none none") || name.toLowerCase().trim() === "не назначен") return "Не назначен"

  return name.replace(/(\s+None)+$/i, "").replace(/None\s+None/i, "").trim()
}

const formatSeconds = sec => {
  if (!sec || sec < 0) return "0 сек"
  if (sec < 60) return `${sec} сек`
  const mins = Math.floor(sec / 60)
  if (mins < 60) {
    const remSec = sec % 60
    if (remSec > 0 && mins < 5) return `${mins} мин ${remSec} сек`
    return `${mins} мин`
  }
  const hours = Math.floor(mins / 60)
  const remMins = mins % 60
  return remMins > 0 ? `${hours} ч ${remMins} мин` : `${hours} ч`
}

const normalizedStatusHistory = computed(() => {
  const rawList = props.order?.status_history
  const result = []

  if (Array.isArray(rawList) && rawList.length > 0) {
    for (const item of rawList) {
      if (item && typeof item === 'object') {
        result.push({ ...item })
      }
    }
  }

  // Если у заказа есть время создания, но в истории нет начального статуса создания/принятия
  const creationTime = props.order?.iiko_creation_time || props.order?.created_at
  if (creationTime) {
    const hasInitial = result.some(h => {
      const s = String(h.status || '').toLowerCase()
      return s === 'new' || s === 'unconfirmed' || s === 'waitapproval'
    })
    if (!hasInitial) {
      result.unshift({
        status: 'new',
        title: 'Заказ принят',
        time: creationTime,
        comment: 'Заказ принят в систему',
        user: 'System'
      })
    }
  }

  return result
})

const getStatusDurationInfo = idx => {
  const list = normalizedStatusHistory.value
  if (!list || idx < 0 || idx >= list.length) return null

  const item = list[idx]
  const next = list[idx + 1]

  // Если уже есть сохраненный готовый текст
  if (item.duration_text) {
    return { text: item.duration_text, isCurrent: false, isTerminal: false }
  }

  // Если есть следующий статус - считаем точную разницу
  if (next && next.time && item.time) {
    const curDt = new Date(item.time)
    const nextDt = new Date(next.time)
    const diffSec = Math.floor((nextDt - curDt) / 1000)
    if (diffSec >= 0) {
      return { text: formatSeconds(diffSec), isCurrent: false, isTerminal: false }
    }
  }

  // Если это последний статус
  if (idx === list.length - 1) {
    const orderStatus = String(props.order?.status || '').toLowerCase()
    const itemStatus = String(item.status || '').toLowerCase()
    const isTerm = orderStatus === 'closed' || orderStatus === 'cancelled' || itemStatus === 'closed' || itemStatus === 'cancelled'

    if (isTerm) {
      if (item.total_duration_text) {
        return { text: `Общее время: ${item.total_duration_text}`, isCurrent: false, isTerminal: true }
      }
      if (list.length > 1 && list[0].time && item.time) {
        const totalSec = Math.floor((new Date(item.time) - new Date(list[0].time)) / 1000)
        if (totalSec >= 0) {
          return { text: `Заказ завершен (всего: ${formatSeconds(totalSec)})`, isCurrent: false, isTerminal: true }
        }
      }
      return { text: 'Учет времени завершен', isCurrent: false, isTerminal: true }
    }

    // Для активного заказа учет времени продолжается
    if (item.time) {
      const curDt = new Date(item.time)
      const diffSec = Math.floor((currentTimeNow.value - curDt) / 1000)
      if (diffSec >= 0) {
        return { text: `${formatSeconds(diffSec)} (в процессе)`, isCurrent: true, isTerminal: false }
      }
    }
  }

  return null
}

const printOrder = () => {
  window.print()
}

const getLoyaltyIcon = type => {
  switch (type) {
  case 'free_product':
  case 'gift': return 'bx-gift'
  case 'coupon_series': return 'bx-purchase-tag'
  case 'promotion': return 'bx-star'
  case 'manual_condition': return 'bx-cog'
  case 'discount': return 'bx-badge-percent'
  case 'bonus_spending': return 'bx-coin-stack'
  default: return 'bx-purchase-tag-alt'
  }
}

const getLoyaltyColor = type => {
  switch (type) {
  case 'coupon_series': return 'blue-lighten-5'
  case 'promotion': return 'pink-lighten-5'
  case 'manual_condition': return 'amber-lighten-5'
  case 'discount': return 'red-lighten-5'
  default: return 'grey-lighten-5'
  }
}

const getLoyaltyIconColor = type => {
  switch (type) {
  case 'coupon_series': return 'blue-darken-1'
  case 'promotion': return 'pink-darken-1'
  case 'manual_condition': return 'amber-darken-2'
  case 'discount': return 'red-darken-1'
  default: return 'grey-darken-1'
  }
}

// --- Лояльность, акции, подарки и бонусы iiko ---
const paymentStatusInfo = computed(() => {
  const pStatus = props.order?.payment_status || props.order?.payments_details?.payment_status
  const isPaid = props.order?.is_paid
  const totalPaid = parseFloat(props.order?.total_paid || 0)
  const leftToPay = parseFloat(props.order?.left_to_pay !== undefined && props.order?.left_to_pay !== null ? props.order?.left_to_pay : 0)
  const totalWithDisc = parseFloat(props.order?.total_with_discount || props.order?.total_amount || 0)

  if (pStatus === 'paid' || isPaid || (totalWithDisc > 0 && leftToPay <= 0 && totalPaid >= totalWithDisc)) {
    return {
      status: 'paid',
      label: 'ОПЛАЧЕН (IIKO)',
      color: 'success',
      colorClass: 'status-soft-success',
      variant: 'flat',
      isPartial: false
    }
  }

  if (pStatus === 'partially_paid' || (totalPaid > 0 && leftToPay > 0)) {
    return {
      status: 'partially_paid',
      label: 'ЧАСТИЧНО ОПЛАЧЕН',
      color: 'warning',
      colorClass: 'status-soft-warning',
      variant: 'flat',
      isPartial: true
    }
  }

  return {
    status: 'unpaid',
    label: 'НЕ ОПЛАЧЕН',
    color: 'error',
    colorClass: 'status-soft-warning',
    variant: 'flat',
    isPartial: false
  }
})

const loyaltyGifts = computed(() => {
  const list = []
  const items = props.order?.discounts_details?.items || []
  for (const it of items) {
    if (it.is_gift || it.type === 'free_product' || it.type === 'gift') {
      list.push(it)
    }
  }
  const orderItems = props.order?.order_items_details || props.order?.items || []
  for (const it of orderItems) {
    const isFree = parseFloat(it.price || 0) === 0 && parseFloat(it.sum || 0) === 0
    if ((it.is_gift || isFree) && !list.some(g => (g.product_name || g.name) === it.name)) {
      list.push({
        name: `Подарок: ${it.name}`,
        product_name: it.name,
        sum: 0,
        type: 'free_product',
        is_gift: true
      })
    }
  }
  return list
})

const loyaltyDiscountsAndPromos = computed(() => {
  const items = props.order?.discounts_details?.items || []
  return items.filter(it => !it.is_gift && it.type !== 'free_product' && it.type !== 'gift' && it.type !== 'bonus_spending' && !it.is_bonus)
})

const loyaltyBonusSpending = computed(() => {
  const spent = parseFloat(props.order?.bonus_spent || 0)
  if (spent > 0) return spent
  const items = props.order?.discounts_details?.items || []
  const bonusItem = items.find(it => it.is_bonus || it.type === 'bonus_spending' || (it.name || '').toLowerCase().includes('списание бонус'))
  return bonusItem ? parseFloat(bonusItem.sum || 0) : 0
})

const hasLoyaltySection = computed(() => {
  return loyaltyGifts.value.length > 0 ||
    loyaltyDiscountsAndPromos.value.length > 0 ||
    loyaltyBonusSpending.value > 0 ||
    parseFloat(props.order?.bonus_accrued || 0) > 0 ||
    parseFloat(props.order?.total_discount || 0) > 0
})

const filteredDiscounts = computed(() => {
  return props.order?.discounts_details?.items || []
})

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

// --- Интеграция T-Bank СБП QR-оплат ---
const sbpQrData = ref(null)
const isSbpLoading = ref(false)
const sbpStatus = ref('')
const sbpStatusInterval = ref(null)
const sbpAmount = ref(0)

const stopSbpStatusPolling = () => {
  if (sbpStatusInterval.value) {
    clearInterval(sbpStatusInterval.value)
    sbpStatusInterval.value = null
  }
}

const startSbpStatusPolling = (qrId) => {
  stopSbpStatusPolling()
  sbpStatus.value = 'CREATED'
  sbpStatusInterval.value = setInterval(async () => {
    try {
      const response = await fetch(`/api/v1/settings/tbank/sbp/qr/${qrId}/state`)
      if (response.ok) {
        const state = await response.json()
        sbpStatus.value = state.status
        if (state.status === 'PAID') {
          stopSbpStatusPolling()
          // Автоматически обновляем заказ у родителя через 2 секунды
          setTimeout(() => {
            emit('update:order', props.order.id)
            sbpQrData.value = null
            sbpStatus.value = ''
          }, 2000)
        }
      }
    } catch (err) {
      console.error("Error polling SBP status:", err)
    }
  }, 2000)
}

const generateSbpQr = async () => {
  if (!props.order?.id || isSbpLoading.value) return
  
  isSbpLoading.value = true
  sbpQrData.value = null
  sbpStatus.value = ''
  
  // Берем остаток к оплате (или общую сумму, если остаток 0 или не определен)
  const amountToPay = props.order.left_to_pay && parseFloat(props.order.left_to_pay) > 0 
    ? parseFloat(props.order.left_to_pay) 
    : parseFloat(props.order.total_with_discount || props.order.sum || 0)
    
  sbpAmount.value = amountToPay

  try {
    const response = await fetch('/api/v1/settings/tbank/sbp/create-qr', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        order_id: props.order.id,
        amount: amountToPay
      })
    })
    
    if (response.ok) {
      const qrData = await response.json()
      sbpQrData.value = qrData
      startSbpStatusPolling(qrData.id)
    } else {
      const err = await response.json()
      alert(err.detail || "Не удалось сгенерировать QR-код СБП")
    }
  } catch (err) {
    console.error("Error creating SBP QR:", err)
    alert("Ошибка сети при обращении к API Т-Банка")
  } finally {
    isSbpLoading.value = false
  }
}

// Очистка при закрытии/размонтировании
watch(dialog, (newVal) => {
  if (!newVal) {
    stopSbpStatusPolling()
    sbpQrData.value = null
    sbpStatus.value = ''
  }
})

const kitchenCookingTime = ref(0)

const cookingTimeItems = computed(() => {
  const items = [0]
  for (let i = 5; i <= 365; i += 5) {
    items.push(i)
  }
  return items
})

const isOrderClosed = computed(() => {
  const st = (props.order?.status || '').toLowerCase()
  return ['closed', 'cancelled', 'delivered'].includes(st)
})

const orderCookingDuration = computed(() => {
  const o = props.order
  if (!o) return ''
  let cookTime = null
  let closeTime = null
  if (o.status_history && Array.isArray(o.status_history)) {
    for (const ev of o.status_history) {
      const st = (ev.status || '').toLowerCase()
      if (['cooking', 'preparing'].includes(st) && !cookTime && ev.time) {
        cookTime = new Date(ev.time)
      }
      if (['closed', 'delivered', 'cancelled'].includes(st) && ev.time) {
        closeTime = new Date(ev.time)
      }
    }
    if (!cookTime && o.status_history.length > 0 && o.status_history[0].time) {
      cookTime = new Date(o.status_history[0].time)
    }
  }
  if (!cookTime && (o.iiko_creation_time || o.created_at)) {
    cookTime = new Date(o.iiko_creation_time || o.created_at)
  }
  if (!closeTime && (o.actual_time || o.updated_at)) {
    closeTime = new Date(o.actual_time || o.updated_at)
  }
  if (cookTime && closeTime) {
    const diffMs = closeTime.getTime() - cookTime.getTime()
    if (diffMs > 0) {
      const totalMinutes = Math.round(diffMs / 60000)
      if (totalMinutes < 60) return `${totalMinutes} мин.`
      return `${Math.floor(totalMinutes / 60)}ч ${totalMinutes % 60}м`
    }
  }
  return ''
})

const saveCookingTime = async (minutes) => {
  if (!props.order?.id || isOrderClosed.value) return
  try {
    const response = await fetch(`/api/v1/orders/${props.order.id}/cooking-time?minutes=${minutes}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": localStorage.getItem("access_token") ? `Bearer ${localStorage.getItem("access_token")}` : ""
      },
    })
    if (response.ok) {
      if (props.order) {
        props.order.cooking_time_minutes = minutes
      }
      emit("update:order", props.order.id)
    } else {
      const err = await response.json()
      alert(err.detail || "Не удалось сохранить время готовности")
    }
  } catch (e) {
    console.error("Save cooking time error:", e)
    alert("Ошибка сети при сохранении времени готовности")
  }
}

const orderStatusOptions = [
  { value: 'new', title: 'Принят', icon: 'bx-plus-circle', color: '#64748b' },
  { value: 'unconfirmed', title: 'Ожидает подтверждения', icon: 'bx-time-five', color: '#f59e0b' },
  { value: 'confirmed', title: 'Подтвержден', icon: 'bx-check-circle', color: '#3b82f6' },
  { value: 'cooking', title: 'Готовится', icon: 'bx-restaurant', color: '#f59e0b' },
  { value: 'assembling', title: 'На сборке', icon: 'bx-package', color: '#10b981' },
  { value: 'ready', title: 'Готов (ожидает отправки)', icon: 'bx-check-double', color: '#10b981' },
  { value: 'ready_for_pickup', title: 'Готов к выдаче (самовывоз)', icon: 'bx-store-alt', color: '#10b981' },
  { value: 'delivering', title: 'У курьера (В пути)', icon: 'bx-cycling', color: '#6366f1' },
  { value: 'delivered', title: 'Доставлен', icon: 'bx-home-heart', color: '#10b981' },
  { value: 'closed', title: 'Закрыт', icon: 'bx-archive', color: '#64748b' },
  { value: 'cancelled', title: 'Отменен', icon: 'bx-x-circle', color: '#ef4444' },
]

const selectedOrderStatus = ref('')
const isUpdatingStatus = ref(false)
const statusSyncMessage = ref('')
const statusSyncSuccess = ref(true)
const statusConfirmDialog = ref(false)
const pendingNewStatus = ref('')

const handleStatusSelect = (newStatus) => {
  if (!newStatus || newStatus === props.order?.status) return

  // Для деструктивных статусов запрашиваем подтверждение
  if (['closed', 'cancelled'].includes(newStatus)) {
    pendingNewStatus.value = newStatus
    statusConfirmDialog.value = true
    return
  }

  applyOrderStatusChange(newStatus)
}

const confirmStatusChange = () => {
  statusConfirmDialog.value = false
  if (pendingNewStatus.value) {
    applyOrderStatusChange(pendingNewStatus.value)
    pendingNewStatus.value = ''
  }
}

const applyOrderStatusChange = async (newStatus) => {
  if (!props.order?.id || isUpdatingStatus.value) return

  isUpdatingStatus.value = true
  statusSyncMessage.value = ''

  try {
    const token = localStorage.getItem("access_token") || localStorage.getItem("token")
    const headers = {
      "Content-Type": "application/json",
    }
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }

    const response = await fetch(`/api/v1/orders/${props.order.id}/status`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        status: newStatus,
        comment: `Статус изменен на ${getStatusLabel(newStatus)} из карточки заказа`
      })
    })

    const data = await response.json()
    if (response.ok && data.status === 'success') {
      if (props.order) {
        props.order.status = data.order_status || newStatus
      }
      selectedOrderStatus.value = data.order_status || newStatus
      statusSyncSuccess.value = true

      if (data.iiko_synced) {
        statusSyncMessage.value = 'Статус изменен и синхронизирован с iiko!'
      } else if (data.iiko_error) {
        statusSyncMessage.value = `Статус изменен в БД. iiko: ${data.iiko_error}`
        statusSyncSuccess.value = false
      }

      emit("update:order", props.order.id)

      setTimeout(() => {
        statusSyncMessage.value = ''
      }, 4000)
    } else {
      selectedOrderStatus.value = props.order?.status || ''
      alert(data.detail || data.message || "Ошибка при смене статуса заказа")
    }
  } catch (e) {
    console.error("Change status error:", e)
    selectedOrderStatus.value = props.order?.status || ''
    alert("Ошибка сети при смене статуса")
  } finally {
    isUpdatingStatus.value = false
  }
}

watch(() => props.order, (newOrder) => {
  if (newOrder) {
    kitchenCookingTime.value = newOrder.cooking_time_minutes !== undefined && newOrder.cooking_time_minutes !== null
      ? newOrder.cooking_time_minutes 
      : 0
    selectedOrderStatus.value = newOrder.status || ''
  }
}, { immediate: true })

// --- УПРАВЛЕНИЕ КУХНЕЙ И ПРИГОТОВЛЕНИЕМ ---

const getKitchenItem = (item) => {
  if (!props.order || !props.order.items) return null
  
  // Пытаемся сопоставить по product_id
  let match = props.order.items.find(i => i.product_id === item.product_id)
  if (!match) {
    // В order_items_details может быть productId вместо product_id
    const pId = item.product_id || item.productId
    if (pId) {
      match = props.order.items.find(i => i.product_id === pId)
    }
  }
  if (!match) {
    // Если не нашли по id, попробуем по названию
    match = props.order.items.find(i => i.product_name === item.name)
  }
  return match
}

const changeItemStatus = async (itemId, newStatus) => {
  try {
    const response = await fetch(`/api/v1/kitchen/items/${itemId}/status?status_name=${newStatus}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": localStorage.getItem("access_token") ? `Bearer ${localStorage.getItem("access_token")}` : ""
      }
    })
    if (response.ok) {
      emit("update:order", props.order.id)
    } else {
      const err = await response.json()
      alert(err.detail || "Ошибка при изменении статуса блюда")
    }
  } catch (e) {
    console.error("Error changing item status:", e)
    alert("Ошибка сети")
  }
}

const startOrderCooking = async () => {
  if (!props.order?.id) return
  try {
    const response = await fetch(`/api/v1/kitchen/orders/${props.order.id}/start-cooking`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": localStorage.getItem("access_token") ? `Bearer ${localStorage.getItem("access_token")}` : ""
      }
    })
    if (response.ok) {
      emit("update:order", props.order.id)
    } else {
      const err = await response.json()
      alert(err.detail || "Не удалось начать приготовление")
    }
  } catch (e) {
    console.error("Error starting cooking:", e)
    alert("Ошибка сети")
  }
}

const startOrderAssembling = async () => {
  if (!props.order?.id) return
  try {
    const response = await fetch(`/api/v1/kitchen/orders/${props.order.id}/assembling`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": localStorage.getItem("access_token") ? `Bearer ${localStorage.getItem("access_token")}` : ""
      }
    })
    if (response.ok) {
      emit("update:order", props.order.id)
    } else {
      const err = await response.json()
      alert(err.detail || "Не удалось перевести на сборку")
    }
  } catch (e) {
    console.error("Error starting assembling:", e)
    alert("Ошибка сети")
  }
}

const makeOrderReady = async () => {
  if (!props.order?.id) return
  try {
    const response = await fetch(`/api/v1/kitchen/orders/${props.order.id}/ready`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": localStorage.getItem("access_token") ? `Bearer ${localStorage.getItem("access_token")}` : ""
      }
    })
    if (response.ok) {
      emit("update:order", props.order.id)
    } else {
      const err = await response.json()
      alert(err.detail || "Не удалось завершить приготовление")
    }
  } catch (e) {
    console.error("Error completing order:", e)
    alert("Ошибка сети")
  }
}

// --- ПРОСМОТР ТЕХНОЛОГИЧЕСКИХ КАРТ ---

const isRecipeDialogOpen = ref(false)
const recipeLoading = ref(false)
const selectedProductRecipe = ref(null)
const recipeHistory = ref([])

const viewRecipe = async (productId) => {
  if (!productId) return
  recipeLoading.value = true
  selectedProductRecipe.value = null
  recipeHistory.value = []
  isRecipeDialogOpen.value = true
  
  try {
    const res = await axios.get(`/api/v1/kitchen/recipes/${productId}`)
    selectedProductRecipe.value = res.data
  } catch (err) {
    alert('Не удалось загрузить техкарту блюда')
    isRecipeDialogOpen.value = false
  } finally {
    recipeLoading.value = false
  }
}

const viewRecipeByIikoId = async (iikoId) => {
  if (!iikoId) return
  recipeLoading.value = true
  
  if (selectedProductRecipe.value) {
    recipeHistory.value.push(selectedProductRecipe.value)
  }
  
  selectedProductRecipe.value = null
  isRecipeDialogOpen.value = true
  
  try {
    const res = await axios.get(`/api/v1/kitchen/recipes/by-iiko-id/${iikoId}`)
    selectedProductRecipe.value = res.data
  } catch (err) {
    alert('Техкарта для этой позиции отсутствует в БД')
    goBackRecipe()
  } finally {
    recipeLoading.value = false
  }
}

const goBackRecipe = () => {
  if (recipeHistory.value.length > 0) {
    selectedProductRecipe.value = recipeHistory.value.pop()
  }
}
</script>

<template>
  <VDialog
    v-model="dialog"
    max-width="1200"
    scrollable
    transition="fade-transition"
  >
    <VCard
      v-if="order"
      class="order-detail-card-soft overflow-hidden"
    >
      <!-- Header -->
      <VCardTitle class="d-flex align-center bg-white border-b px-6 py-5">
        <div class="d-flex flex-column">
          <div class="d-flex align-center ga-3">
            <VIcon
              icon="bx-receipt"
              color="blue-grey-lighten-4"
              size="24"
            />
            <span 
              class="text-h5 font-weight-bold" 
              style="color: var(--text-dark)"
            >
              Заказ №{{ order.external_number || order.number || order.id }}
            </span>
            <VChip
              size="x-small"
              color="indigo-lighten-5"
              variant="flat"
              class="text-uppercase font-weight-bold"
              style="color: #6366f1 !important"
            >
              {{ order.source || 'iiko' }}
            </VChip>
            <VChip
              v-if="isOrderClosed && orderCookingDuration"
              color="secondary"
              size="small"
              variant="flat"
              class="font-weight-black text-caption rounded-pill text-white ms-1"
            >
              <VIcon start size="14" icon="bx-time" class="me-1" />
              Готовка: {{ orderCookingDuration }}
            </VChip>
            <VChip
              v-else
              color="indigo"
              size="small"
              variant="flat"
              class="font-weight-black text-caption rounded-pill text-white ms-1"
            >
              <VIcon start size="14" icon="bx-restaurant" class="me-1" />
              Кухня: {{ order.cooking_time_minutes !== undefined && order.cooking_time_minutes !== null ? order.cooking_time_minutes : 0 }} мин.
            </VChip>
          </div>
          <span
            v-if="order.external_number"
            class="text-caption ms-9"
            style="color: var(--text-light)"
          >
            Внешний ID: {{ order.external_number }}
          </span>
        </div>

        <VSpacer />

        <div class="d-flex align-center ga-3">
          <VBtn
            v-if="order.iiko_order_id"
            icon
            variant="tonal"
            color="primary"
            size="small"
            class="rounded-lg"
            :loading="isSyncing"
            @click="syncWithIiko"
          >
            <VIcon icon="bx-refresh" />
            <VTooltip activator="parent">Обновить из iiko</VTooltip>
          </VBtn>

          <VChip
            :style="{ 
              backgroundColor: statusColor + ' !important', 
              color: statusTextColor + ' !important', 
              borderColor: 'rgba(0,0,0,0.05) !important' 
            }"
            variant="flat"
            class="px-5 font-weight-bold shadow-sm border"
          >
            {{ getStatusLabel(order.status) }}
          </VChip>
          
          <VBtn
            icon
            variant="tonal"
            color="grey-lighten-4"
            size="small"
            class="rounded-lg"
            @click="dialog = false"
          >
            <VIcon
              icon="bx-x"
              style="color: var(--text-muted)"
            />
          </VBtn>
        </div>
      </VCardTitle>

      <VCardText
        class="pa-0 custom-scroll-premium"
        style="background-color: var(--pastel-gray)"
      >
        <!-- Индикаторы изменений -->
        <div 
          v-if="order.change_indicators && Object.values(order.change_indicators).some(v => v)" 
          class="px-6 py-3 bg-error-lighten-5 border-b d-flex flex-wrap ga-2"
        >
          <VChip
            v-if="order.change_indicators.items"
            size="small"
            color="error"
            variant="flat"
            prepend-icon="bx-error"
            class="font-weight-bold animate-pulse shadow-sm"
          >
            ИЗМЕНИЛСЯ СОСТАВ ЗАКАЗА!
          </VChip>
          <VChip
            v-if="order.change_indicators.amount"
            size="small"
            color="error"
            variant="flat"
            prepend-icon="bx-error"
            class="font-weight-bold animate-pulse shadow-sm"
          >
            ИЗМЕНИЛАСЬ СУММА ОПЛАТЫ!
          </VChip>
          <VChip
            v-if="order.change_indicators.address"
            size="small"
            color="error"
            variant="flat"
            prepend-icon="bx-error"
            class="font-weight-bold animate-pulse shadow-sm"
          >
            ИЗМЕНИЛСЯ АДРЕС ДОСТАВКИ!
          </VChip>
          <VChip
            v-if="order.change_indicators.time"
            size="small"
            color="error"
            variant="flat"
            prepend-icon="bx-error"
            class="font-weight-bold animate-pulse shadow-sm"
          >
            ИЗМЕНИЛОСЬ ВРЕМЯ ДОСТАВКИ!
          </VChip>
          <VChip
            v-if="order.change_indicators.payment"
            size="small"
            color="error"
            variant="flat"
            prepend-icon="bx-error"
            class="font-weight-bold animate-pulse shadow-sm"
          >
            ИЗМЕНИЛСЯ СПОСОБ ОПЛАТЫ!
          </VChip>
        </div>

        <!-- Quick Info Banner (прокручивается вместе с телом заказа) -->
        <div 
          class="px-6 py-4 border-b d-flex flex-wrap align-center ga-6" 
          style="background-color: var(--soft-bg)"
        >
          <!-- Execution Time -->
          <div 
            class="d-flex align-center ga-3 py-1 px-4 rounded-xl bg-white shadow-sm border" 
            style="border-color: var(--soft-border) !important"
          >
            <div
              :class="order.is_asap ? 'time-asap-soft' : 'time-preorder-soft'"
              class="pa-2 rounded-lg border"
            >
              <VIcon
                :icon="order.is_asap ? 'bx-bolt-circle' : 'bx-calendar-event'"
                :color="order.is_asap ? 'amber-darken-1' : 'blue-darken-1'"
                size="24"
              />
            </div>
            <div class="d-flex flex-column">
              <span class="section-label-soft mb-0">Срок исполнения</span>
              <span class="data-value-soft">
                {{ order.is_asap ? 'Как можно скорее' : 'Ко времени: ' + formatTime(order.expected_time) }}
              </span>
            </div>
          </div>

          <!-- Delivery Zone -->
          <div
            v-if="order.delivery_zone"
            class="d-flex align-center ga-3 py-1 px-4 rounded-xl bg-white shadow-sm border"
            style="border-color: var(--soft-border) !important"
          >
            <div 
              class="pa-2 rounded-lg" 
              style="background-color: #ecfdf5"
            >
              <VIcon
                icon="bx-map-pin"
                color="emerald-darken-1"
                size="24"
              />
            </div>
            <div class="d-flex flex-column">
              <span class="section-label-soft mb-0">Зона доставки</span>
              <span class="data-value-soft">
                {{ order.delivery_zone }}
              </span>
            </div>
          </div>

          <!-- Terminal Group / Branch -->
          <div
            v-if="order.terminal_group_name"
            class="d-flex align-center ga-3 py-1 px-4 rounded-xl bg-white shadow-sm border"
            style="border-color: var(--soft-border) !important"
          >
            <div 
              class="pa-2 rounded-lg" 
              style="background-color: #f5f3ff"
            >
              <VIcon
                icon="bx-store-alt"
                color="purple-darken-1"
                size="24"
              />
            </div>
            <div class="d-flex flex-column">
              <span class="section-label-soft mb-0">Точка продаж</span>
              <span class="data-value-soft">
                {{ order.terminal_group_name }}
              </span>
            </div>
          </div>

          <!-- Admin / Creation -->
          <div 
            class="d-flex align-center ga-3 py-1 px-4 rounded-xl bg-white shadow-sm border" 
            style="border-color: var(--soft-border) !important"
          >
            <div 
              class="pa-2 rounded-lg" 
              style="background-color: #eef2ff"
            >
              <VIcon
                icon="bx-user-circle"
                color="indigo-darken-1"
                size="24"
              />
            </div>
            <div class="d-flex flex-column">
              <span class="section-label-soft mb-0">Администратор</span>
              <span class="data-value-soft">
                {{ order.admin_name || 'Автоматически' }}
              </span>
            </div>
          </div>

          <VSpacer />
        </div>

        <VRow no-gutters>
          <!-- Left Column: Info Blocks -->
          <VCol
            cols="12"
            md="5"
            class="border-e pa-6 d-flex flex-column ga-4"
          >
            <!-- 1. Client -->
            <div class="info-section-soft">
              <div class="section-label-soft">
                <VIcon
                  icon="bx-user"
                  size="14"
                  class="me-1"
                /> КЛИЕНТ
              </div>
              <div
                class="glass-block-soft d-flex align-center cursor-pointer"
                @click="openCustomerModal"
              >
                <div class="premium-icon-box">
                  <VIcon
                    icon="bx-user"
                    size="22"
                    color="blue-grey-lighten-2"
                  />
                </div>
                <div class="d-flex flex-column overflow-hidden">
                  <span
                    class="data-value-soft text-truncate"
                    style="font-size: 1rem"
                  >
                    {{ order.customer_info_details?.name || order.customer_name || 'Гость' }}
                  </span>
                  <div class="d-flex align-center ga-2">
                    <span class="text-caption text-slate-500 font-weight-bold">{{ order.customer_phone }}</span>
                    <VBtn
                      v-if="order.customer_phone"
                      icon="bx-phone-call"
                      size="20"
                      color="success"
                      variant="tonal"
                      density="compact"
                      class="rounded-sm"
                      @click.stop="callCustomer(order.customer_phone)"
                    />
                  </div>
                  
                  <div 
                    v-if="customerInfo || order.customer_info_details" 
                    class="d-flex align-center ga-3 mt-2"
                  >
                    <div class="d-flex align-center ga-1">
                      <VIcon 
                        icon="bx-wallet" 
                        size="12" 
                        color="indigo-lighten-2" 
                      />
                      <span class="text-tiny font-weight-black text-indigo-darken-1">
                        {{ formatPrice((customerInfo || order.customer_info_details).bonus_points || 0) }} Б
                      </span>
                    </div>
                    <div class="d-flex align-center ga-1">
                      <VIcon 
                        icon="bx-package" 
                        size="12" 
                        color="slate-400" 
                      />
                      <span class="text-tiny font-weight-bold text-slate-500">
                        Заказов: {{ (customerInfo || order.customer_info_details).total_orders_count || 0 }}
                      </span>
                    </div>
                  </div>
                </div>
                <VSpacer />
                <div class="d-flex ga-1 px-1">
                  <VChip
                    v-if="(customerInfo?.is_new_guest || order.customer_info_details?.is_new_guest) || order.is_first_order"
                    size="x-small"
                    class="loyalty-new font-weight-bold px-2"
                    variant="flat"
                  >
                    НОВЫЙ
                  </VChip>
                  <VIcon
                    v-if="order.customer_info_details?.is_high_risk"
                    icon="bx-shield-x"
                    color="error"
                    size="18"
                  />
                </div>
              </div>
            </div>

            <!-- 1.1. Comment (Moved here) -->
            <div
              v-if="order.comment || order.address_comment || order.additional_info || order.other_info"
              class="info-section-soft"
            >
              <div class="section-label-soft">
                <VIcon
                  icon="bx-comment-detail"
                  size="14"
                  class="me-1"
                /> ПРИМЕЧАНИЯ И КОММЕНТАРИИ
              </div>
              <div class="glass-block-soft pa-3 d-flex flex-column ga-2">
                <div v-if="order.comment">
                  <span class="text-caption font-weight-bold text-slate-400">КОММЕНТАРИЙ К ЗАКАЗУ:</span>
                  <div class="text-body-2 italic text-slate-600">"{{ order.comment }}"</div>
                </div>
                <div v-if="order.address_comment">
                  <span class="text-caption font-weight-bold text-slate-400">ПРИМЕЧАНИЕ К АДРЕСУ:</span>
                  <div class="text-body-2 italic text-slate-600">"{{ order.address_comment }}"</div>
                </div>
                <div v-if="order.additional_info">
                  <span class="text-caption font-weight-bold text-slate-400">ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:</span>
                  <div class="text-body-2 italic text-slate-600">"{{ order.additional_info }}"</div>
                </div>
                <div v-if="order.other_info">
                  <span class="text-caption font-weight-bold text-slate-400">ПРОЧЕЕ:</span>
                  <div class="text-body-2 italic text-slate-600">"{{ order.other_info }}"</div>
                </div>
              </div>
            </div>



            <!-- 3. Timing iiko -->
            <div class="info-section-soft">
              <div class="section-label-soft">
                <VIcon
                  icon="bx-time"
                  size="14"
                  class="me-1"
                /> ТАЙМИНГ (IIKO)
              </div>
              <div class="glass-block-soft pa-3">
                <div class="d-flex flex-column ga-2">
                  <div class="d-flex justify-space-between align-center">
                    <span class="text-caption text-slate-400 font-weight-bold uppercase">ОБЕЩАНО</span>
                    <span class="text-body-2 font-weight-bold text-slate-700">{{ formatDateTime(order.expected_time) }}</span>
                  </div>
                  <div 
                    v-if="order.actual_time" 
                    class="d-flex justify-space-between align-center"
                  >
                    <span class="text-caption text-slate-400 font-weight-bold uppercase">ИСПОЛНЕНО</span>
                    <span class="text-body-2 font-weight-bold text-slate-700">{{ formatDateTime(order.actual_time) }}</span>
                  </div>
                  <div 
                    v-if="order.delay_minutes > 0" 
                    class="d-flex justify-space-between align-center pt-2 border-t border-dashed"
                  >
                    <span class="text-caption text-error font-weight-bold uppercase">ОПОЗДАНИЕ</span>
                    <VChip 
                      size="x-small" 
                      color="error" 
                      variant="flat" 
                      class="font-weight-bold"
                    >
                      {{ order.delay_minutes }} мин.
                    </VChip>
                  </div>
                  <div 
                    v-else-if="order.actual_time" 
                    class="d-flex justify-space-between align-center pt-2 border-t border-dashed"
                  >
                    <span class="text-caption text-success font-weight-bold uppercase">СТАТУС</span>
                    <span class="text-caption font-weight-black text-success">ВОВРЕМЯ</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3.5. Kitchen Preparation & Status -->
            <div class="info-section-soft">
              <div class="section-label-soft">
                <VIcon
                  icon="bx-restaurant"
                  size="14"
                  class="me-1"
                /> ГОТОВНОСТЬ И СТАТУС ЗАКАЗА
              </div>
              <div class="glass-block-soft pa-3">
                <!-- Время приготовления -->
                <div class="d-flex align-center justify-space-between ga-3">
                  <span class="text-caption text-slate-400 font-weight-bold uppercase flex-shrink-0">ВРЕМЯ НА ПРИГОТОВЛЕНИЕ</span>
                  <VSelect
                    v-model="kitchenCookingTime"
                    :items="cookingTimeItems"
                    density="compact"
                    hide-details
                    variant="outlined"
                    class="max-width-150"
                    suffix="мин."
                    :disabled="isOrderClosed"
                    @update:model-value="saveCookingTime"
                  />
                </div>

                <VDivider class="my-3 opacity-20" />

                <!-- Смена статуса заказа с моментальной синхронизацией в iiko -->
                <div class="d-flex align-center justify-space-between ga-3 flex-wrap">
                  <div class="d-flex flex-column">
                    <span class="text-caption text-slate-400 font-weight-bold uppercase">СТАТУС ЗАКАЗА (IIKO)</span>
                    <span class="text-tiny text-slate-500">Синхронно обновляется в iiko Cloud</span>
                  </div>
                  
                  <div style="min-width: 210px; max-width: 250px;">
                    <VSelect
                      v-model="selectedOrderStatus"
                      :items="orderStatusOptions"
                      item-value="value"
                      item-title="title"
                      density="compact"
                      hide-details
                      variant="outlined"
                      class="flex-grow-1"
                      :loading="isUpdatingStatus"
                      :disabled="isUpdatingStatus"
                      @update:model-value="handleStatusSelect"
                    >
                      <template #selection="{ item }">
                        <div class="d-flex align-center ga-1 text-truncate">
                          <VIcon 
                            :icon="item.raw?.icon || 'bx-info-circle'" 
                            size="14" 
                            :style="{ color: item.raw?.color || '#3b82f6' }" 
                          />
                          <span class="text-caption font-weight-bold text-truncate" :style="{ color: item.raw?.color || 'inherit' }">
                            {{ item.raw?.title || getStatusLabel(selectedOrderStatus) }}
                          </span>
                        </div>
                      </template>
                      <template #item="{ item, props: itemProps }">
                        <VListItem v-bind="itemProps" class="py-1">
                          <template #prepend>
                            <VIcon 
                              :icon="item.raw.icon" 
                              size="16" 
                              :style="{ color: item.raw.color }" 
                              class="me-2" 
                            />
                          </template>
                          <VListItemTitle class="text-caption font-weight-medium">
                            {{ item.title }}
                          </VListItemTitle>
                        </VListItem>
                      </template>
                    </VSelect>
                  </div>
                </div>

                <!-- Сообщение о результате синхронизации с iiko -->
                <VAlert
                  v-if="statusSyncMessage"
                  :type="statusSyncSuccess ? 'success' : 'warning'"
                  variant="tonal"
                  density="compact"
                  class="mt-2 py-1 px-3 text-caption font-weight-medium"
                >
                  <template #prepend>
                    <VIcon size="16" :icon="statusSyncSuccess ? 'bx-check-shield' : 'bx-error-circle'" class="me-1" />
                  </template>
                  {{ statusSyncMessage }}
                </VAlert>

                <div v-if="isOrderClosed && orderCookingDuration" class="mt-2 text-caption font-weight-bold text-success d-flex align-center">
                  <VIcon icon="bx-time" size="14" class="me-1" />
                  Время от кухни до закрытия: {{ orderCookingDuration }}
                </div>
                <div v-else-if="isOrderClosed" class="mt-1 text-tiny text-medium-emphasis">
                  Заказ завершен.
                </div>
              </div>
            </div>

            <!-- 4. Loyalty, Promotions, Discounts & Gifts (Unified iiko loyalty block) -->
            <div
              v-if="hasLoyaltySection"
              class="info-section-soft"
            >
              <div class="section-label-soft">
                <VIcon
                  icon="bx-gift"
                  size="14"
                  class="me-1"
                /> ЛОЯЛЬНОСТЬ И АКЦИИ (IIKO)
              </div>
              <div class="glass-block-soft bg-white pa-3 d-flex flex-column ga-3">

                <!-- 1. Подарки к заказу (Free Products) -->
                <div v-if="loyaltyGifts.length" class="d-flex flex-column ga-2">
                  <div class="text-tiny font-weight-bold text-uppercase text-pink-darken-2 d-flex align-center ga-1">
                    <VIcon icon="bx-gift" size="12" color="pink" /> Подарки к заказу
                  </div>
                  <div 
                    v-for="(gift, gidx) in loyaltyGifts" 
                    :key="'gift-' + gidx"
                    class="d-flex align-center justify-space-between bg-pink-lighten-5 rounded pa-2"
                  >
                    <div class="d-flex align-center overflow-hidden">
                      <VAvatar size="24" color="pink-lighten-4" class="me-2">
                        <VIcon icon="bx-gift" size="14" color="pink-darken-2" />
                      </VAvatar>
                      <span class="text-caption font-weight-bold text-truncate text-pink-darken-4">
                        {{ gift.product_name || gift.name }}
                      </span>
                    </div>
                    <VChip size="x-small" color="pink-darken-1" variant="flat" class="font-weight-bold">
                      0 ₽ (Подарок)
                    </VChip>
                  </div>
                </div>

                <!-- 2. Скидки, акции и промокоды -->
                <div v-if="loyaltyDiscountsAndPromos.length" class="d-flex flex-column ga-2">
                  <div class="text-tiny font-weight-bold text-uppercase text-slate-500 d-flex align-center ga-1">
                    <VIcon icon="bx-purchase-tag-alt" size="12" color="primary" /> Примененные скидки и акции
                  </div>
                  <div 
                    v-for="(promo, pidx) in loyaltyDiscountsAndPromos" 
                    :key="'promo-' + pidx"
                    class="d-flex align-center justify-space-between py-1 border-b border-dashed"
                  >
                    <div class="d-flex align-center overflow-hidden">
                      <VAvatar 
                        size="24" 
                        :color="getLoyaltyColor(promo.type)" 
                        class="me-2"
                      >
                        <VIcon 
                          :icon="getLoyaltyIcon(promo.type)" 
                          size="14" 
                          :color="getLoyaltyIconColor(promo.type)" 
                        />
                      </VAvatar>
                      <div class="d-flex flex-column overflow-hidden">
                        <span class="text-caption font-weight-bold text-truncate">{{ promo.name }}</span>
                        <span 
                          v-if="promo.coupon || promo.type === 'coupon_series'" 
                          class="text-tiny text-blue-darken-2 font-weight-medium"
                        >
                          Промокод: {{ promo.coupon || 'Применен' }}
                        </span>
                      </div>
                    </div>
                    <span class="text-caption font-weight-bold text-red-darken-1">-{{ formatPrice(promo.sum) }} ₽</span>
                  </div>
                </div>

                <!-- 3. Оплата / Списание бонусов iikoCard -->
                <div v-if="loyaltyBonusSpending > 0" class="d-flex align-center justify-space-between bg-amber-lighten-5 rounded pa-2">
                  <div class="d-flex align-center">
                    <VAvatar size="24" color="amber-lighten-4" class="me-2">
                      <VIcon icon="bx-coin-stack" size="14" color="amber-darken-3" />
                    </VAvatar>
                    <div class="d-flex flex-column">
                      <span class="text-caption font-weight-bold text-amber-darken-4">Оплата бонусами iikoCard</span>
                      <span class="text-tiny text-amber-darken-2">Списано баллов со счета</span>
                    </div>
                  </div>
                  <span class="text-caption font-weight-black text-amber-darken-4">-{{ formatPrice(loyaltyBonusSpending) }} Б</span>
                </div>

                <!-- 4. Начисление бонусов -->
                <div 
                  v-if="parseFloat(order.bonus_accrued || 0) > 0" 
                  class="d-flex align-center justify-space-between pt-1 border-t border-dashed"
                >
                  <div class="d-flex align-center">
                    <VAvatar 
                      size="24" 
                      color="green-lighten-5" 
                      class="me-2"
                    >
                      <VIcon 
                        icon="bx-plus-circle" 
                        size="14" 
                        color="green-darken-1" 
                      />
                    </VAvatar>
                    <span class="text-caption font-weight-bold">Будет начислено</span>
                  </div>
                  <span class="text-caption font-weight-bold text-green-darken-2">+{{ formatPrice(order.bonus_accrued) }} Б</span>
                </div>

              </div>
            </div>



            <!-- 6. Address -->
            <div class="info-section-soft">
              <div class="section-label-soft">
                <VIcon
                  icon="bx-map-alt"
                  size="14"
                  class="me-1"
                /> АДРЕС ДОСТАВКИ
              </div>
              <div class="glass-block-soft pa-3">
                <div class="text-body-2 font-weight-bold text-slate-700">
                  {{ formattedAddress }}
                </div>
                <div
                  v-if="order.address_comment"
                  class="text-caption text-indigo-darken-2 font-weight-medium mt-1 d-flex align-center"
                >
                  <VIcon
                    icon="bx-comment-detail"
                    size="13"
                    color="indigo"
                    class="me-1"
                  /> Прим. к адресу: {{ order.address_comment }}
                </div>
                <div
                  v-if="order.city || order.delivery_zone"
                  class="text-caption text-disabled mt-1 d-flex align-center"
                >
                  <VIcon
                    icon="bx-buildings"
                    size="12"
                    class="me-1"
                  /> {{ order.city || 'Тюмень' }}
                  <span
                    v-if="order.delivery_zone"
                    class="mx-1"
                  >•</span>
                  <span
                    v-if="order.delivery_zone"
                    class="text-slate-500 font-weight-bold"
                  >{{ order.delivery_zone }}</span>
                </div>
              </div>
              <div
                v-if="order.delivery_address && order.order_type !== 'Самовывоз'"
                class="mt-2"
              >
                <VMenu>
                  <template #activator="{ props: menuProps }">
                    <VBtn
                      v-bind="menuProps"
                      size="small"
                      variant="tonal"
                      color="primary"
                      prepend-icon="bx-map"
                      class="soft-btn w-100 rounded-lg"
                    >
                      Открыть в навигаторе
                      <VIcon
                        icon="bx-chevron-down"
                        size="12"
                        class="ms-1"
                      />
                    </VBtn>
                  </template>
                  <VList density="compact">
                    <VListItem
                      @click="openMaps('yandex')"
                      prepend-icon="bx-map"
                    >
                      <VListItemTitle>Яндекс.Карты</VListItemTitle>
                    </VListItem>
                    <VListItem
                      @click="openMaps('yandexnavi')"
                      prepend-icon="bx-compass"
                    >
                      <VListItemTitle>Яндекс.Навигатор</VListItemTitle>
                    </VListItem>
                    <VListItem
                      @click="openMaps('2gis')"
                      prepend-icon="bx-navigation"
                    >
                      <VListItemTitle>2GIS</VListItemTitle>
                    </VListItem>
                    <VListItem
                      @click="openMaps('google')"
                      prepend-icon="bx-globe"
                    >
                      <VListItemTitle>Google Maps</VListItemTitle>
                    </VListItem>
                    <VListItem
                      @click="openMaps('petal')"
                      prepend-icon="bx-mobile-vibration"
                    >
                      <VListItemTitle>Petal Maps</VListItemTitle>
                    </VListItem>
                  </VList>
                </VMenu>
              </div>
            </div>

            <!-- 7. Courier -->
            <div class="info-section-soft">
              <div class="section-label-soft">
                <VIcon
                  icon="bx-car"
                  size="14"
                  class="me-1"
                /> КУРЬЕР
              </div>
              <div class="glass-block-soft d-flex align-center py-2">
                <VIcon
                  icon="bx-cycling"
                  :color="order.courier_user ? 'success' : 'grey-lighten-4'"
                  class="me-3"
                  size="24"
                />
                <div>
                  <div
                    v-if="!order.courier_name || order.courier_name.toLowerCase().includes('none none') || order.courier_name.toLowerCase().trim() === 'не назначен'"
                    class="text-body-2 font-weight-bold text-slate-400"
                  >
                    Не назначен
                  </div>
                  <div v-else-if="order.courier_user" class="text-body-2 font-weight-bold text-high-emphasis d-flex align-center">
                    <VIcon icon="bx-check-double" size="16" color="success" class="me-1" />
                    <span>
                      {{ cleanCourierName(order.courier_name) }}
                      <span class="text-caption text-secondary font-weight-regular ms-1">({{ order.courier_user.username }})</span>
                    </span>
                  </div>
                  <div v-else class="text-body-2 font-weight-bold text-medium-emphasis d-flex align-center">
                    {{ cleanCourierName(order.courier_name) }}
                    <VIcon icon="bx-error-circle" size="14" color="warning" class="ms-1" title="Нет аккаунта в админке" />
                  </div>
                </div>

                <!-- Кнопка ручного назначения курьера -->
                <div v-if="order.order_type === 'Доставка' && !isReadOnly" class="ms-auto">
                  <VMenu v-model="courierMenuOpen" :close-on-content-click="false" location="bottom end">
                    <template #activator="{ props }">
                      <VBtn
                        v-bind="props"
                        icon="bx-edit-alt"
                        variant="text"
                        density="comfortable"
                        color="primary"
                        :loading="assigningCourier"
                        title="Назначить курьера"
                      />
                    </template>
                    <VCard min-width="280" class="pa-2 rounded-xl shadow-lg border">
                      <VCardTitle class="text-subtitle-2 font-weight-bold pa-2 d-flex align-center">
                        <VIcon icon="bx-cycling" size="18" class="me-2" color="primary" />
                        Назначить курьера (iiko)
                      </VCardTitle>
                      <VDivider class="my-1" />
                      <VList v-if="activeCouriersList.length" class="pa-0">
                        <VListItem
                          v-for="c in activeCouriersList"
                          :key="c.id"
                          @click="selectCourier(c)"
                          class="rounded-lg my-1"
                        >
                          <template #prepend>
                            <VAvatar size="32" color="primary" variant="tonal" class="me-2">
                              <VIcon :icon="c.latitude ? 'bx-map-pin' : 'bx-user'" size="16" />
                            </VAvatar>
                          </template>
                          <VListItemTitle class="font-weight-medium text-body-2">{{ c.name }}</VListItemTitle>
                          <VListItemSubtitle class="text-caption text-grey" v-if="c.phone">{{ c.phone }}</VListItemSubtitle>
                        </VListItem>
                      </VList>
                      <div v-else class="text-caption text-center py-4 text-grey">
                        Нет активных курьеров с открытой сменой
                      </div>
                    </VCard>
                  </VMenu>
                </div>
              </div>
            </div>

            <!-- 8. State & Payment Type -->
            <div class="info-section-soft">
              <div class="section-label-soft">
                <VIcon
                  icon="bx-credit-card"
                  size="14"
                  class="me-1"
                /> СОСТОЯНИЕ И ТИП
              </div>
              <div class="d-flex flex-wrap ga-2">
                <div class="d-flex align-center ga-2 bg-white pa-2 px-3 rounded-lg border border-slate-100 shadow-sm">
                  <span class="text-caption text-disabled">Оплата:</span>
                  <VChip
                    :class="paymentStatusInfo.colorClass"
                    :color="paymentStatusInfo.color"
                    :variant="paymentStatusInfo.variant"
                    size="x-small"
                    class="font-weight-bold px-3"
                  >
                    {{ paymentStatusInfo.label }}
                  </VChip>
                </div>
                <div class="d-flex align-center ga-2 bg-white pa-2 px-3 rounded-lg border border-slate-100 shadow-sm">
                  <span class="text-caption text-disabled">Тип:</span>
                  <span class="text-caption font-weight-black text-slate-500 uppercase">{{ order.order_type }}</span>
                </div>
              </div>
            </div>

            <!-- 9. Order Meta (Moved to bottom) -->
            <div class="info-section-soft">
              <div class="section-label-soft">
                <VIcon
                  icon="bx-info-circle"
                  size="14"
                  class="me-1"
                /> ИНФОРМАЦИЯ О ЗАКАЗЕ
              </div>
              <div class="glass-block-soft pa-3">
                <div class="d-flex flex-column ga-2">
                  <div class="d-flex justify-space-between align-center">
                    <span class="text-caption text-slate-400 font-weight-bold uppercase">Источник</span>
                    <VChip 
                      size="x-small" 
                      variant="tonal" 
                      color="primary" 
                      class="font-weight-black px-2"
                    >
                      {{ order.source || 'Сайт' }}
                    </VChip>
                  </div>
                  <div 
                    v-if="order.order_number" 
                    class="d-flex justify-space-between align-center"
                  >
                    <span class="text-caption text-slate-400 font-weight-bold uppercase">Внешний ID</span>
                    <span class="text-caption font-weight-bold text-slate-600">{{ order.order_number }}</span>
                  </div>
                  <div class="d-flex justify-space-between align-center">
                    <span class="text-caption text-slate-400 font-weight-bold uppercase">Создан на сайте</span>
                    <span class="text-caption font-weight-medium text-slate-500">{{ formatDateTime(order.created_at) }}</span>
                  </div>
                  <div 
                    v-if="order.admin_name" 
                    class="d-flex justify-space-between align-center border-t border-dashed mt-1 pt-1"
                  >
                    <span class="text-caption text-slate-400 font-weight-bold uppercase">Админ</span>
                    <span class="text-caption font-weight-black text-indigo-accent-2">{{ order.admin_name }}</span>
                  </div>
                  <div class="d-flex justify-space-between align-center">
                    <span class="text-caption text-slate-400 font-weight-bold uppercase">Создан в iiko</span>
                    <span class="text-caption font-weight-bold text-slate-500">{{ formatDateTime(order.iiko_creation_time) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 9. Financials Mini -->
            <div class="info-section-soft mt-auto mb-0">
              <div class="financial-panel-glass-soft">
                <div class="financial-row">
                  <span>Сумма товаров:</span>
                  <span class="value">{{ formatPrice(props.order.total_amount || 0) }} ₽</span>
                </div>
                <div
                  v-if="parseFloat(order.total_discount || 0) > 0"
                  class="financial-row discount"
                >
                  <span>Скидка:</span>
                  <span class="value">-{{ formatPrice(order.total_discount) }} ₽</span>
                </div>

                <div class="financial-row total border-t-dotted mt-3 pt-3">
                  <span>ИТОГО К ОПЛАТЕ:</span>
                  <span class="value text-indigo-accent-2 font-weight-black" style="font-size: 1.1rem;">{{ formatPrice(order.total_with_discount) }} ₽</span>
                </div>

                <div class="financial-row mt-2" style="font-size: 0.85rem; opacity: 0.8;">
                  <span>Оплачено:</span>
                  <span class="value text-success font-weight-bold">{{ formatPrice(order.total_paid > 0 ? order.total_paid : (order.total_with_discount - (order.left_to_pay || 0))) }} ₽</span>
                </div>
                <div v-if="parseFloat(order.left_to_pay || 0) > 0" class="financial-row" style="font-size: 0.85rem; color: #f43f5e;">
                  <span>Остаток к оплате:</span>
                  <span class="value font-weight-bold">{{ formatPrice(order.left_to_pay) }} ₽</span>
                </div>

                <!-- Детализация оплат -->
                <VDivider class="my-3 opacity-30" />
                <div 
                  class="section-label-soft mb-2" 
                  style="font-size: 10px;"
                >
                  ДЕТАЛИ ОПЛАТЫ
                </div>
                
                <div v-if="order.payments_details?.items?.length">
                  <div 
                    v-for="(pay, pidx) in order.payments_details.items" 
                    :key="pidx"
                    class="d-flex justify-space-between align-center mb-1"
                  >
                    <div class="d-flex align-center">
                      <VIcon 
                        :icon="getPaymentIcon(pay.paymentType?.name || pay.type)" 
                        size="12" 
                        class="me-1 opacity-50" 
                      />
                      <span class="text-tiny text-slate-700">{{ pay.paymentType?.name || getPaymentLabel(pay.type) }}</span>
                    </div>
                    <span class="text-tiny text-slate-800">{{ formatPrice(pay.sum) }} ₽</span>
                  </div>
                </div>
                <div v-else class="d-flex justify-space-between align-center mb-1">
                  <div class="d-flex align-center">
                    <VIcon 
                      icon="bx-wallet" 
                      size="12" 
                      class="me-1 opacity-50" 
                    />
                    <span class="text-tiny text-slate-500">{{ order.payment_method || 'Способ не указан' }}</span>
                  </div>
                  <span class="text-tiny">{{ formatPrice(order.total_with_discount) }} ₽</span>
                </div>

                <!-- Остаток к оплате -->
                <div 
                  v-if="parseFloat(order.left_to_pay) > 0" 
                  class="d-flex justify-space-between align-center mt-2 pa-2 rounded bg-red-lighten-5 border border-red-lighten-4"
                >
                  <span class="text-caption font-weight-bold text-red-darken-2 uppercase">ОСТАЛОСЬ ОПЛАТИТЬ:</span>
                  <span class="text-subtitle-2 font-weight-black text-red-darken-2">{{ formatPrice(order.left_to_pay) }} ₽</span>
                </div>
                <div 
                  v-else-if="order.is_paid" 
                  class="d-flex justify-space-between align-center mt-2 pa-2 rounded bg-green-lighten-5 border border-green-lighten-4"
                >
                  <span class="text-caption font-weight-bold text-green-darken-2 uppercase">ПОЛНОСТЬЮ ОПЛАЧЕН</span>
                  <VIcon 
                    icon="bx-check-double" 
                    size="16" 
                    color="green-darken-2" 
                  />
                </div>
              </div>
            </div>
          </VCol>

          <!-- Right Column: Content -->
          <VCol
            cols="12"
            md="7"
            class="pa-6"
          >
            <!-- Панель управления кухней -->
            <div v-if="order && !['closed', 'cancelled'].includes(order.status)" class="mb-4 pa-3 rounded-lg bg-grey-lighten-4 border d-flex align-center justify-space-between flex-wrap ga-2">
              <div class="d-flex align-center">
                <VIcon icon="bx-restaurant" class="me-2 text-indigo-darken-1" size="20" />
                <span class="text-body-2 font-weight-bold text-slate-800">Управление приготовлением:</span>
              </div>
              <div class="d-flex ga-2">
                <!-- Начать готовить заказ -->
                <VBtn
                  v-if="['new', 'unconfirmed', 'confirmed', 'preparing'].includes(order.status)"
                  size="small"
                  color="blue"
                  variant="flat"
                  prepend-icon="bx-play-circle"
                  class="font-weight-bold text-white text-caption"
                  @click="startOrderCooking"
                >
                  Начать готовить
                </VBtn>

                <!-- Передать на сборку -->
                <VBtn
                  v-if="order.status === 'cooking'"
                  size="small"
                  color="orange"
                  variant="flat"
                  prepend-icon="bx-package"
                  class="font-weight-bold text-white text-caption"
                  @click="startOrderAssembling"
                >
                  На сборку
                </VBtn>

                <!-- Отметить собранным -->
                <VBtn
                  v-if="order.status === 'assembling'"
                  size="small"
                  color="success"
                  variant="flat"
                  prepend-icon="bx-check-square"
                  class="font-weight-bold text-black text-caption"
                  @click="makeOrderReady"
                >
                  Собран
                </VBtn>

                <!-- Кнопка Готов Полностью -->
                <VBtn
                  v-if="!['ready', 'ready_for_pickup'].includes(order.status)"
                  size="small"
                  color="green"
                  variant="outlined"
                  prepend-icon="bx-check-double"
                  class="font-weight-bold text-green text-caption"
                  @click="makeOrderReady"
                >
                  Готов полностью
                </VBtn>
              </div>
            </div>

            <!-- 1. Order Items -->
            <div class="d-flex align-center mb-4">
              <VIcon
                icon="bx-package"
                color="grey-lighten-1"
                class="me-2"
                size="20"
              />
              <span class="text-subtitle-1 font-weight-bold text-slate-700">Состав заказа</span>
              <VSpacer />
              <VChip
                size="x-small"
                variant="outlined"
                color="grey-lighten-2"
              >
                {{ (order.order_items_details || order.items || []).length }} поз.
              </VChip>
            </div>

            <VTable class="order-items-table-soft mb-6">
              <thead>
                <tr>
                  <th style="width: 64px"></th>
                  <th class="text-left">
                    Наименование
                  </th>
                  <th
                    class="text-center"
                    style="width: 60px"
                  >
                    Кол
                  </th>
                  <th
                    class="text-right"
                    style="width: 100px"
                  >
                    Цена
                  </th>
                  <th
                    class="text-right"
                    style="width: 110px"
                  >
                    Сумма
                  </th>
                  <th
                    class="text-center"
                    style="width: 140px"
                  >
                    Кухня
                  </th>
                </tr>
              </thead>
              <tbody>
                <template v-if="order.order_items_details?.length">
                  <template
                    v-for="(item, idx) in order.order_items_details"
                    :key="'det-'+idx"
                  >
                    <tr :class="{ 'deleted-item-row': item.deleted }">
                      <td class="py-3 text-center">
                        <VAvatar size="40" class="border rounded bg-light" variant="flat">
                          <VImg 
                            v-if="item.image_url" 
                            :src="item.image_url" 
                            cover 
                          />
                          <VIcon v-else icon="mdi-food-fork-drink" color="disabled" size="20" />
                        </VAvatar>
                      </td>
                      <td class="py-3">
                        <div 
                          class="font-weight-bold text-body-2 cursor-pointer text-decoration-underline text-blue-darken-2"
                          :class="item.deleted ? 'text-disabled' : ''"
                          @click="getKitchenItem(item) ? viewRecipe(getKitchenItem(item).product_id) : null"
                          title="Посмотреть техкарту"
                        >
                          <VIcon v-if="item.deleted" icon="bx-x" size="14" color="error" class="me-1" />
                          {{ item.name }}
                          <VChip
                            v-if="item.is_gift || (parseFloat(item.price || 0) === 0 && parseFloat(item.sum || 0) === 0)"
                            size="x-small"
                            color="pink"
                            variant="flat"
                            class="ms-2 font-weight-bold"
                          >
                            <VIcon start size="12" icon="bx-gift" /> Подарок
                          </VChip>
                        </div>
                        <div
                          v-if="item.size"
                          class="text-caption text-disabled mt-n1"
                        >
                          {{ (typeof item.size === 'object') ? item.size.name : item.size }}
                        </div>
                      </td>
                      <td class="text-center text-body-2">
                        {{ item.amount }}
                      </td>
                      <td class="text-right text-body-2">
                        {{ formatPrice(item.price) }} ₽
                      </td>
                      <td class="text-right font-weight-bold text-body-2" :class="item.deleted ? 'text-disabled' : 'text-slate-600'">
                        {{ formatPrice(item.sum || (item.amount * item.price)) }} ₽
                      </td>
                      <td class="text-center">
                        <div v-if="getKitchenItem(item)" class="d-flex align-center justify-center">
                          <VBtn
                            v-if="getKitchenItem(item).kitchen_status === 'pending'"
                            size="x-small"
                            color="blue"
                            variant="flat"
                            class="font-weight-bold text-white text-caption"
                            @click="changeItemStatus(getKitchenItem(item).id, 'cooking')"
                          >
                            <VIcon start size="12" icon="bx-play" /> Начать
                          </VBtn>
                          <VBtn
                            v-else-if="getKitchenItem(item).kitchen_status === 'cooking'"
                            size="x-small"
                            color="success"
                            variant="flat"
                            class="font-weight-bold text-black text-caption"
                            @click="changeItemStatus(getKitchenItem(item).id, 'ready')"
                          >
                            <VIcon start size="12" icon="bx-check" /> Готово
                          </VBtn>
                          <VChip
                            v-else-if="getKitchenItem(item).kitchen_status === 'ready'"
                            color="success"
                            variant="tonal"
                            size="x-small"
                            class="font-weight-bold"
                          >
                            <VIcon start size="12" icon="bx-check-double" /> Готово
                          </VChip>
                        </div>
                        <span v-else class="text-disabled">—</span>
                      </td>
                    </tr>
                    <tr
                      v-for="(mod, midx) in item.modifiers"
                      :key="'mod-'+idx+'-'+midx"
                      class="modifier-soft"
                    >
                      <td colspan="2" class="ps-8 py-1">
                        <!-- Если у модификатора есть productId или iiko_id, делаем его кликабельным -->
                        <span 
                          v-if="mod.productId || mod.iiko_id"
                          class="cursor-pointer text-decoration-underline text-blue-darken-2"
                          @click="viewRecipeByIikoId(mod.productId || mod.iiko_id)"
                          title="Посмотреть техкарту"
                        >
                          <VIcon
                            icon="bx-subdirectory-right"
                            size="14"
                            class="me-1 opacity-30"
                          /> {{ mod.name }}
                        </span>
                        <span v-else>
                          <VIcon
                            icon="bx-subdirectory-right"
                            size="14"
                            class="me-1 opacity-30"
                          /> {{ mod.name }}
                        </span>
                      </td>
                      <td class="text-center opacity-60">
                        {{ mod.amount }}
                      </td>
                      <td class="text-right opacity-60">
                        {{ formatPrice(mod.price) }} ₽
                      </td>
                      <td class="text-right opacity-60">
                        {{ formatPrice(mod.sum || (mod.amount * mod.price)) }} ₽
                      </td>
                      <td></td>
                    </tr>
                  </template>
                </template>
                <tr v-else>
                  <td
                    colspan="6"
                    class="text-center py-10 text-disabled"
                  >
                    Состав заказа не найден
                  </td>
                </tr>
              </tbody>
            </VTable>

            <!-- 2. Financial Summary Banner -->
            <div class="glass-block-soft d-flex flex-wrap justify-space-between align-center ga-6 mb-8 py-5 px-6 financial-banner-soft">
              <div class="d-flex ga-6 align-center flex-wrap">
                <div class="d-flex flex-column">
                  <span class="text-caption text-slate-400 font-weight-bold text-uppercase-bold mb-1">Сумма</span>
                  <span class="text-h6 font-weight-black text-slate-700">{{ formatPrice(order.total_amount) }} ₽</span>
                </div>
                
                <VDivider vertical length="32" class="mx-0 opacity-20" />
                
                <div class="d-flex flex-column">
                  <span class="text-caption text-error-darken-1 font-weight-bold text-uppercase-bold mb-1">Скидки</span>
                  <span class="text-h6 font-weight-black text-error">-{{ formatPrice(order.total_discount || 0) }} ₽</span>
                </div>



                <div class="d-flex flex-column">
                  <span class="text-caption text-indigo-darken-1 font-weight-bold text-uppercase-bold mb-1">К оплате</span>
                  <span class="text-h6 font-weight-black text-indigo-accent-4">{{ formatPrice(order.total_with_discount || order.sum) }} ₽</span>
                </div>
              </div>

              <div class="d-flex ga-6 align-center flex-wrap">
                <VDivider vertical length="32" class="mx-0 opacity-20 hidden-sm-and-down" />
                
                <div class="d-flex flex-column align-end">
                  <span class="text-caption text-success-darken-2 font-weight-bold text-uppercase-bold mb-1">Оплачено</span>
                  <div class="d-flex align-center">
                    <VIcon v-if="(order.total_paid > 0 ? order.total_paid : (order.total_with_discount - (order.left_to_pay || 0))) >= order.total_with_discount" icon="bx-check-circle" color="success" size="18" class="me-2" />
                    <span class="text-h6 font-weight-black text-success">{{ formatPrice(order.total_paid > 0 ? order.total_paid : (order.total_with_discount - (order.left_to_pay || 0))) }} ₽</span>
                  </div>
                </div>

                <div v-if="parseFloat(order.left_to_pay) > 0" class="d-flex flex-column align-end">
                  <span class="text-caption text-error font-weight-bold text-uppercase-bold mb-1">Остаток</span>
                  <span class="text-h6 font-weight-black text-error pulse-soft">{{ formatPrice(order.left_to_pay) }} ₽</span>
                </div>
              </div>
            </div>

            <div class="d-flex flex-column align-end mb-8">
              <div class="d-flex align-center ga-2 flex-wrap justify-end">
                <template v-if="order.payments_details?.items?.length">
                  <VChip
                    v-for="(pay, pidx) in order.payments_details.items"
                    :key="pidx"
                    size="small"
                    variant="outlined"
                    class="payment-chip-soft"
                    :class="pay.is_processed ? 'processed' : 'pending'"
                  >
                    <VIcon 
                      :icon="getPaymentIcon(pay.kind)" 
                      size="14" 
                      class="me-2" 
                    />
                    {{ pay.name || getPaymentLabel(pay.kind) }}: {{ formatPrice(pay.sum) }} ₽
                  </VChip>
                </template>
                <VChip 
                  v-else 
                  color="slate-100" 
                  class="text-slate-700 font-weight-bold border border-slate-200" 
                  variant="flat"
                >
                  {{ order.payment_method || 'Способ не указан' }}
                </VChip>
              </div>
            </div>

            <!-- T-Bank SBP QR Block [NEW] -->
            <div 
              v-if="parseFloat(order.left_to_pay || 0) > 0 || !order.is_paid" 
              class="glass-block-soft border border-indigo-lighten-4 mb-8 sbp-qr-panel-premium"
              style="background: linear-gradient(135deg, #f5f3ff 0%, #ffffff 100%) !important;"
            >
              <div class="d-flex align-center justify-space-between mb-4">
                <div class="d-flex align-center">
                  <div 
                    class="pa-2 rounded-lg bg-indigo-lighten-5 me-3"
                    style="color: #6366f1"
                  >
                    <VIcon icon="bx-qr-scan" size="20" />
                  </div>
                  <div>
                    <div class="font-weight-black text-slate-800" style="font-size: 14px;">
                      Оплата через СБП Т-Банк
                    </div>
                    <div class="text-caption text-slate-500">
                      Мгновенное зачисление и автоматический статус оплаты
                    </div>
                  </div>
                </div>
                
                <VBtn
                  v-if="!sbpQrData"
                  color="indigo-accent-4"
                  variant="flat"
                  size="small"
                  class="rounded-lg font-weight-bold"
                  :loading="isSbpLoading"
                  prepend-icon="bx-qr"
                  @click="generateSbpQr"
                >
                  Создать QR
                </VBtn>
              </div>

              <!-- QR Display Area -->
              <div 
                v-if="sbpQrData" 
                class="d-flex flex-column align-center justify-center py-4 bg-white rounded-xl border border-dashed border-indigo-lighten-3"
              >
                <!-- SVG QR Code (decoded from base64) -->
                <div 
                  class="mb-3 d-flex align-center justify-center rounded-lg pa-3 bg-white"
                  style="border: 2px solid #eef2f6; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.08)"
                  v-html="atob(sbpQrData.svg)"
                ></div>

                <div class="text-center px-4">
                  <div class="text-caption font-weight-bold text-indigo-darken-1 mb-1">
                    Сумма к оплате: <span class="text-subtitle-2 font-weight-black text-indigo-accent-4">{{ formatPrice(sbpAmount) }} ₽</span>
                  </div>
                  
                  <!-- Status Indicator -->
                  <div class="d-flex align-center justify-center ga-2 mt-2">
                    <template v-if="sbpStatus === 'PAID'">
                      <VChip color="success" size="small" variant="flat" class="font-weight-black animate-bounce shadow-sm">
                        <VIcon icon="bx-check-double" class="me-1" /> ОПЛАЧЕНО
                      </VChip>
                    </template>
                    <template v-else-if="sbpStatus === 'CREATED'">
                      <div class="d-flex align-center text-caption font-weight-bold text-slate-500">
                        <VProgressCircular indeterminate size="12" width="2" color="indigo-accent-3" class="me-2" />
                        Ожидание сканирования...
                      </div>
                    </template>
                    <template v-else>
                      <span class="text-caption text-slate-400 font-weight-bold">
                        Статус: {{ sbpStatus || 'Создан' }}
                      </span>
                    </template>
                  </div>
                  
                  <div class="text-tiny text-slate-400 mt-3 max-w-sm">
                    Направьте клиенту ссылку для оплаты или покажите QR-код на экране:
                    <a :href="sbpQrData.url" target="_blank" class="d-block text-indigo-accent-4 font-weight-bold text-decoration-none mt-1 word-break-all" style="font-size: 10px;">
                      {{ sbpQrData.url.substring(0, 45) }}...
                    </a>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. History -->
            <div class="mt-4">
              <div class="d-flex align-center mb-6">
                <VIcon
                  icon="bx-history"
                  color="grey-lighten-2"
                  size="20"
                  class="me-2"
                />
                <span class="text-subtitle-2 font-weight-bold text-slate-400 uppercase">История статусов</span>
              </div>

              <VTimeline
                density="compact"
                side="end"
                align="start"
                class="modern-timeline-soft"
              >
                <VTimelineItem
                  v-for="(hist, idx) in normalizedStatusHistory"
                  :key="idx"
                  :dot-color="getStatusColor(hist.status)"
                  size="small"
                  fill-dot
                >
                  <div class="d-flex flex-column">
                    <div class="d-flex justify-space-between align-center">
                      <span
                        class="text-body-2 font-weight-bold"
                        :style="{ color: getStatusColor(hist.status) }"
                      >
                        {{ getStatusLabel(hist.status) }}
                      </span>
                      <span class="timeline-time-soft font-mono text-caption text-slate-500 font-weight-medium">
                        {{ formatStatusTime(hist.time) }}
                      </span>
                    </div>

                    <!-- Источник или комментарий -->
                    <div
                      v-if="hist.comment || hist.user"
                      class="text-caption text-slate-400 mt-0.5"
                      style="font-size: 11px;"
                    >
                      {{ hist.comment || hist.user }}
                    </div>

                    <!-- Длительность нахождения в статусе -->
                    <div
                      v-if="getStatusDurationInfo(idx)"
                      class="text-caption mt-1 d-flex align-center"
                    >
                      <template v-if="getStatusDurationInfo(idx).isCurrent">
                        <span class="text-amber-darken-3 font-weight-bold d-flex align-center bg-amber-lighten-5 px-2 py-0.5 rounded">
                          <VIcon
                            icon="bx-stopwatch"
                            size="13"
                            class="me-1"
                          />
                          В статусе: {{ getStatusDurationInfo(idx).text }}
                        </span>
                      </template>
                      <template v-else-if="getStatusDurationInfo(idx).isTerminal">
                        <span class="text-slate-600 font-weight-bold d-flex align-center bg-slate-100 px-2 py-0.5 rounded">
                          <VIcon
                            icon="bx-check-double"
                            size="14"
                            class="me-1 text-success"
                          />
                          {{ getStatusDurationInfo(idx).text }}
                        </span>
                      </template>
                      <template v-else>
                        <span class="text-slate-500 d-flex align-center">
                          <VIcon
                            icon="bx-stopwatch"
                            size="13"
                            color="grey"
                            class="me-1"
                          />
                          Пробыл: {{ getStatusDurationInfo(idx).text }}
                        </span>
                      </template>
                    </div>
                  </div>
                </VTimelineItem>
              </VTimeline>
            </div>
          </VCol>
        </VRow>
      </VCardText>

      <VCardActions class="pa-4 bg-white border-t d-flex align-center">
        <!-- Кнопка принудительного закрытия заказа в БД и iiko -->
        <VBtn
          v-if="isOrderActive"
          color="success"
          variant="flat"
          class="font-weight-bold px-4"
          prepend-icon="bx-check-circle"
          :loading="isForceClosing"
          @click="openForceCloseConfirm"
        >
          Закрыть заказ
        </VBtn>

        <VSpacer />
        <VBtn
          color="primary"
          variant="flat"
          class="soft-btn soft-btn-primary me-2"
          prepend-icon="bx-printer"
          @click="printOrder"
        >
          Печать
        </VBtn>
        <VBtn
          variant="text"
          color="grey-darken-1"
          class="px-8 text-none font-weight-bold soft-btn"
          @click="dialog = false"
        >
          Закрыть окно
        </VBtn>
      </VCardActions>
    </VCard>

    <!-- Диалог подтверждения принудительного закрытия заказа -->
    <VDialog v-model="confirmCloseDialog" max-width="480px" style="z-index: 3100;">
      <VCard class="rounded-xl pa-4">
        <VCardTitle class="text-h6 font-weight-bold d-flex align-center">
          <VIcon icon="bx-check-circle" color="success" class="me-2" size="28" />
          Закрыть заказ в системе и iiko?
        </VCardTitle>
        <VCardText class="pt-2 text-body-1">
          Вы уверены, что хотите принудительно перевести заказ 
          <strong v-if="order.order_number || order.external_number || order.id">#{{ order.external_number || order.id }}</strong> 
          в статус <strong>«Закрыт»</strong>?
          <div class="text-caption text-medium-emphasis mt-2">
            Заказ будет отмечен как выполненный и оплаченный в базе данных, а также отправлена команда закрытия доставки в iiko.
          </div>
        </VCardText>
        <VCardActions class="pt-3 d-flex justify-end ga-2">
          <VBtn
            variant="tonal"
            color="grey-darken-1"
            class="px-4"
            :disabled="isForceClosing"
            @click="confirmCloseDialog = false"
          >
            Отмена
          </VBtn>
          <VBtn
            color="success"
            variant="flat"
            class="px-5 font-weight-bold"
            :loading="isForceClosing"
            @click="forceCloseOrder"
          >
            Да, закрыть заказ
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог подтверждения перевода в статус Закрыт / Отменен -->
    <VDialog
      v-model="statusConfirmDialog"
      max-width="460px"
      style="z-index: 3100;"
    >
      <VCard class="rounded-xl pa-4">
        <VCardTitle class="d-flex align-center ga-2 text-h6 font-weight-bold">
          <VIcon
            :icon="pendingNewStatus === 'cancelled' ? 'bx-x-circle' : 'bx-archive'"
            :color="pendingNewStatus === 'cancelled' ? 'error' : 'warning'"
            size="28"
          />
          Подтверждение смены статуса
        </VCardTitle>
        <VCardText class="text-body-2 text-slate-600 pt-2">
          Вы уверены, что хотите перевести заказ 
          <strong v-if="order?.external_number || order?.number || order?.id">#{{ order?.external_number || order?.number || order?.id }}</strong>
          в статус <strong>«{{ getStatusLabel(pendingNewStatus) }}»</strong>?
          <div class="mt-2 text-caption text-slate-500">
            Этот статус будет немедленно отправлен в <strong>iiko Cloud</strong>.
          </div>
        </VCardText>
        <VCardActions class="d-flex justify-end ga-2 pt-2">
          <VBtn
            variant="tonal"
            color="grey-darken-1"
            size="small"
            @click="statusConfirmDialog = false; selectedOrderStatus = order?.status"
          >
            Отмена
          </VBtn>
          <VBtn
            :color="pendingNewStatus === 'cancelled' ? 'error' : 'primary'"
            variant="flat"
            size="small"
            class="font-weight-bold"
            @click="confirmStatusChange"
          >
            Да, применить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог просмотра техкарты в деталях заказа -->
    <VDialog v-model="isRecipeDialogOpen" max-width="700px" style="z-index: 3000;">
      <VCard :loading="recipeLoading" color="grey-darken-3" class="text-white">
        <VCardTitle class="pa-4 bg-primary text-white d-flex justify-space-between align-center">
          <div class="d-flex align-center">
            <VBtn 
              v-if="recipeHistory.length > 0" 
              icon="bx-chevron-left" 
              color="white" 
              variant="text" 
              class="mr-2"
              @click="goBackRecipe"
            />
            <span class="text-h6">Рецепт: {{ selectedProductRecipe?.product_name }}</span>
          </div>
          <VBtn icon="bx-x" color="white" variant="text" @click="isRecipeDialogOpen = false" />
        </VCardTitle>

        <VCardText class="pa-4" v-if="selectedProductRecipe">
          <VRow>
            <!-- Фото и характеристики -->
            <VCol cols="12" sm="4" class="text-center">
              <VAvatar size="140" rounded="lg" class="border mb-3 bg-white">
                <VImg :src="selectedProductRecipe.image_url || '/images/default-dish.jpg'" cover />
              </VAvatar>
              <div class="text-body-1 font-weight-bold mb-1 text-white">Выход: {{ selectedProductRecipe.weight_grams || '—' }} г</div>
              <div class="text-caption text-grey-lighten-2">КБЖУ: {{ selectedProductRecipe.proteins || 0 }}/{{ selectedProductRecipe.fats || 0 }}/{{ selectedProductRecipe.carbohydrates || 0 }} ({{ selectedProductRecipe.calories || 0 }} ккал)</div>
            </VCol>

            <!-- Ингредиенты -->
            <VCol cols="12" sm="8">
              <h4 class="font-weight-bold mb-2 text-primary">Ингредиенты (Состав)</h4>
              <VTable density="compact" class="border rounded bg-grey-darken-4 text-white mb-3">
                <thead>
                  <tr class="text-grey-lighten-2">
                    <th class="text-left text-white">Сырье (заготовка/модификатор)</th>
                    <th class="text-right text-white">Нетто</th>
                    <th class="text-right text-white">Выход</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(ing, idx) in selectedProductRecipe.ingredients" :key="idx" class="text-white">
                    <td class="text-left">
                      <!-- Если есть iiko_id, делаем ссылку кликабельной для вложенного рецепта -->
                      <span 
                        v-if="ing.iiko_id" 
                        class="text-decoration-underline text-blue-lighten-3 cursor-pointer font-weight-bold"
                        @click="viewRecipeByIikoId(ing.iiko_id)"
                        title="Посмотреть техкарту заготовки"
                      >
                        {{ ing.name }}
                      </span>
                      <span v-else>{{ ing.name }}</span>
                    </td>
                    <td class="text-right font-weight-bold text-white">{{ ing.net }} г</td>
                    <td class="text-right font-weight-bold text-white">{{ ing.output }} г</td>
                  </tr>
                  <tr v-if="selectedProductRecipe.ingredients.length === 0">
                    <td colspan="3" class="text-center text-grey">Ингредиенты не указаны</td>
                  </tr>
                </tbody>
              </VTable>
            </VCol>
          </VRow>

          <!-- Технология приготовления -->
          <div class="mt-4 pa-3 rounded bg-grey-darken-4 border-left-active">
            <h4 class="font-weight-bold mb-2 text-primary">Технология приготовления</h4>
            <div class="text-body-1 text-justify text-white" style="white-space: pre-line; line-height: 1.6;">
              {{ selectedProductRecipe.technology || 'Процесс приготовления не описан.' }}
            </div>
          </div>

          <!-- Сноски подачи/ККТ -->
          <div v-if="selectedProductRecipe.appearance" class="mt-3 pa-2 rounded bg-grey-darken-4 border-left-comment text-white">
            <strong>Оформление и подача:</strong> {{ selectedProductRecipe.appearance }}
          </div>
        </VCardText>
        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn color="white" variant="text" @click="isRecipeDialogOpen = false">Закрыть</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <CustomerDetailModal
      v-model="customerModalVisible"
      :customer="customerInfo"
      @updated="fetchCustomerInfo"
    />
  </VDialog>
</template>

<style scoped>
.order-detail-card-soft {
  border-radius: 24px !important;
}

/* Colors & Typography */
.text-slate-800 { color: #1e293b !important; }
.text-slate-700 { color: #334155 !important; }
.text-slate-600 { color: #475569 !important; }
.text-slate-500 { color: #64748b !important; }
.text-slate-400 { color: #94a3b8 !important; }

.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
}

.uppercase { text-transform: uppercase !important; letter-spacing: 0.12em !important; font-weight: 600 !important; }

/* Content Blocks */
.info-section-soft {
  margin-bottom: 24px;
}

.section-label-soft {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  opacity: 0.8;
}

.glass-block-soft {
  background: #ffffff !important;
  border: 1px solid #f1f5f9 !important;
  border-radius: 18px !important;
  padding: 16px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02) !important;
}

.financial-panel-glass-soft {
  background: #f8fafc !important;
  border-radius: 22px !important;
  padding: 24px !important;
  border: 1px solid #eef2f6 !important;
}

.financial-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #475569;
}

.financial-row.discount {
  color: #ef4444;
  font-weight: 600;
}

.financial-row.total {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
  font-weight: 800;
  color: #1e293b;
  font-size: 16px;
}

/* Timeline Customization */
.timeline-time-soft {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

.modern-timeline-soft :deep(.v-timeline-divider__dot) {
  background: white !important;
  border: 2px solid currentColor !important;
}

/* Buttons Styling */
.soft-btn {
  border-radius: 14px !important;
  text-transform: none !important;
  letter-spacing: 0.02em !important;
  font-weight: 700 !important;
  padding: 0 24px !important;
  height: 44px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.soft-btn-primary {
  background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%) !important;
  color: white !important;
  box-shadow: 0 8px 20px -6px rgba(99, 102, 241, 0.4) !important;
}

.soft-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.15) !important;
}

/* Items Table Refinement */
.order-items-table-soft {
  border-radius: 16px !important;
  overflow: hidden !important;
  border: 1px solid #f1f5f9 !important;
  background: white !important;
}

.order-items-table-soft :deep(th) {
  background: #fcfdfe !important;
  color: #64748b !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  height: 48px !important;
  border-bottom: 1px solid #f1f5f9 !important;
}

.deleted-item-row {
  background-color: #fffafb !important;
}

.deleted-item-row td {
  text-decoration: line-through;
  color: #94a3b8 !important;
  opacity: 0.7;
}

.deleted-item-row .text-disabled {
  color: #cbd5e1 !important;
}

.modifier-soft td {
  background: #f9fafb !important;
  border-bottom: none !important;
  color: #94a3b8 !important;
  font-size: 12px !important;
  padding-top: 4px !important;
  padding-bottom: 4px !important;
}

/* Accrued Bonuses Chip (in Loyalty) */
.loyalty-new {
  background-color: #fff1f2 !important;
  color: #e11d48 !important;
  border: 1px solid #fecdd3 !important;
}

/* Scrollbar styling */
:deep(.v-card-text) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 transparent;
}

:deep(.v-card-text::-webkit-scrollbar) {
  width: 5px;
}

:deep(.v-card-text::-webkit-scrollbar-thumb) {
  background: #cbd5e1;
  border-radius: 10px;
}

.border-left-active {
  border-left: 3.5px solid #FFB300;
}

.border-left-comment {
  border-left: 3.5px solid #2196F3;
}
</style>
