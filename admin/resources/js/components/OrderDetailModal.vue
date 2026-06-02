<script setup>
import { ref, watch, computed } from "vue"
import { formatDate, formatDateTime, formatTime } from "@/utils/date"
import CustomerDetailModal from "./CustomerDetailModal.vue"

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

const yandexMapLink = computed(() => {
  if (!props.order?.delivery_address) return "#"

  return `https://yandex.ru/maps/?text=${encodeURIComponent(props.order.delivery_address)}`
})

const twoGisLink = computed(() => {
  if (!props.order?.delivery_address) return "#"

  return `https://2gis.ru/search/${encodeURIComponent(props.order.delivery_address)}`
})

const googleMapsLink = computed(() => {
  if (!props.order?.delivery_address) return "#"

  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(props.order.delivery_address)}`
})

const petalMapsLink = computed(() => {
  if (!props.order?.delivery_address) return "#"

  return `https://www.petalmaps.com/search/?q=${encodeURIComponent(props.order.delivery_address)}`
})

const formattedAddress = computed(() => {
  if (!props.order) return "—"

  const timeStr = props.order.iiko_creation_time || props.order.actual_time || props.order.created_at

  if (props.order.order_type === "Самовывоз" || !props.order.delivery_address) return "🙍 Самовывоз"

  const status = (props.order.status || "").toLowerCase()
  const isPending = !["closed", "cancelled"].includes(status)
  const flat = (props.order.flat || "").toString().trim()
  const noFlat = !flat || flat === "0" || flat === "-"
  const showWarning = isPending && noFlat && props.order.order_type !== "Самовывоз"
  const warningPrefix = showWarning ? "❗ " : ""

  if (props.addressFormat === "line1") {
    return warningPrefix + props.order.delivery_address
  }

  const parts = []
  const o = props.order

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

const getStatusLabel = status => {
  if (!status) return "—"
  const labels = {
    new: "Новый",
    unconfirmed: "Не подтвержден",
    waitapproval: "Ожидает подтверждения",
    accepted: "Принят",
    confirmed: "Принят",
    preparing: "В сборке",
    cooking: "Готовится",
    ready: "Готов",
    readyForPickup: "Готов к выдаче",
    delivering: "У курьера",
    delivered: "Доставлен",
    closed: "Закрыт",
    cancelled: "Отменен",
  }

  return labels[status.toLowerCase()] || status
}

const getStatusColor = status => {
  if (!status) return "#94a3b8"
  const colors = {
    new: "#94a3b8",
    unconfirmed: "#f1b44c",
    confirmed: "#50a5f1",
    preparing: "#34c38f",
    cooking: "#f1b44c",
    ready: "#63d594",
    delivered: "#63d594",
    closed: "#74788d",
    cancelled: "#f46a6a",
    delivering: "#5b73e8",
  }

  return colors[status.toLowerCase()] || "#94a3b8"
}

const cleanCourierName = name => {
  if (!name || name.toLowerCase().includes("none none") || name.toLowerCase().trim() === "не назначен") return "Не назначен"

  return name.replace(/(\s+None)+$/i, "").replace(/None\s+None/i, "").trim()
}

const getStatusDuration = idx => {
  if (!props.order?.status_history || idx >= props.order.status_history.length - 1) return null

  const current = new Date(props.order.status_history[idx].time)
  const next = new Date(props.order.status_history[idx + 1].time)

  const diffMs = next - current
  if (diffMs <= 0) return null

  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return "< 1м"

  if (diffMins >= 60) {
    const hours = Math.floor(diffMins / 60)
    const mins = diffMins % 60

    return mins > 0 ? `${hours}ч ${mins}м` : `${hours}ч`
  }

  return `${diffMins}м`
}

const printOrder = () => {
  window.print()
}

const getLoyaltyIcon = type => {
  switch (type) {
  case 'coupon_series': return 'bx-purchase-tag'
  case 'promotion': return 'bx-gift'
  case 'manual_condition': return 'bx-cog'
  case 'discount': return 'bx-minus-circle'
  default: return 'bx-star'
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

      <!-- Quick Info Banner -->
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

      <VCardText
        class="pa-0 custom-scroll-premium"
        style="background-color: var(--pastel-gray)"
      >
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
              v-if="order.comment"
              class="info-section-soft"
            >
              <div class="section-label-soft">
                <VIcon
                  icon="bx-comment-detail"
                  size="14"
                  class="me-1"
                /> КОММЕНТАРИЙ
              </div>
              <div class="glass-block-soft bg-white text-body-2 italic text-slate-600">
                "{{ order.comment }}"
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

            <!-- 4. Loyalty & Discounts -->
            <div
              v-if="order.discounts_details?.items?.length || order.bonus_spent > 0 || order.bonus_accrued > 0"
              class="info-section-soft"
            >
              <div class="section-label-soft">
                <VIcon
                  icon="bx-gift"
                  size="14"
                  class="me-1"
                /> ЛОЯЛЬНОСТЬ
              </div>
              <div class="glass-block-soft bg-white pa-3">

                <!-- Discounts and Promotions -->
                <div 
                  v-for="(discount, idx) in filteredDiscounts" 
                  :key="idx"
                  class="d-flex align-center justify-space-between"
                  :class="idx < (filteredDiscounts.length - 1) || order.bonus_accrued > 0 ? 'mb-2' : ''"
                >
                  <div class="d-flex align-center overflow-hidden">
                    <VAvatar 
                      size="24" 
                      :color="getLoyaltyColor(discount.type)" 
                      class="me-2"
                    >
                      <VIcon 
                        :icon="getLoyaltyIcon(discount.type)" 
                        size="14" 
                        :color="getLoyaltyIconColor(discount.type)" 
                      />
                    </VAvatar>
                    <div class="d-flex flex-column overflow-hidden">
                      <span class="text-caption font-weight-bold text-truncate">{{ discount.name }}</span>
                      <span 
                        v-if="discount.type === 'coupon_series'" 
                        class="text-tiny text-blue-darken-1"
                      >
                        Купон: {{ discount.coupon || 'Применен' }}
                      </span>
                    </div>
                  </div>
                  <span class="text-caption font-weight-bold text-red-darken-1">-{{ formatPrice(discount.sum) }} ₽</span>
                </div>

                <!-- Accrued Bonuses -->
                <div 
                  v-if="order.bonus_accrued > 0" 
                  class="d-flex align-center justify-space-between mt-2 pt-2 border-t border-dashed"
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

            <!-- [NEW] 5.5 Applied Promotions (Loyalty Details) -->
            <div 
              v-if="order.discounts_details?.items?.length" 
              class="info-section-soft"
            >
              <div class="section-label-soft">
                <VIcon
                  icon="bx-gift"
                  size="14"
                  class="me-1"
                /> ПРИМЕНЕННЫЕ АКЦИИ (IIKO)
              </div>
              <div class="glass-block-soft pa-0">
                <VList density="compact" class="bg-transparent pa-0">
                  <VListItem
                    v-for="(item, idx) in order.discounts_details.items"
                    :key="idx"
                    class="py-2"
                    :class="{ 'border-b border-dashed': idx < order.discounts_details.items.length - 1 }"
                  >
                    <template #prepend>
                      <VAvatar 
                        size="32" 
                        :color="getLoyaltyColor(item.ui_info?.type || item.type)" 
                        class="me-3"
                      >
                        <VIcon 
                          :icon="getLoyaltyIcon(item.ui_info?.type || item.type)" 
                          size="18" 
                          :color="getLoyaltyIconColor(item.ui_info?.type || item.type)" 
                        />
                      </VAvatar>
                    </template>

                    <VListItemTitle class="text-body-2 font-weight-bold d-flex align-center justify-space-between">
                      <span class="text-truncate" style="max-width: 250px;">{{ item.name }}</span>
                      <span class="text-red-darken-1">-{{ formatPrice(item.sum) }} ₽</span>
                    </VListItemTitle>

                    <VListItemSubtitle class="mt-1 d-flex flex-column ga-1">
                      <div v-if="item.ui_info?.program_name" class="d-flex align-center ga-1">
                        <VIcon icon="bx-purchase-tag-alt" size="12" color="primary" />
                        <span class="text-caption font-weight-medium text-primary">Программа: {{ item.ui_info.program_name }}</span>
                      </div>
                      <div v-if="item.ui_info?.marketing_campaign_name" class="d-flex align-center ga-1">
                        <VIcon icon="bx-bullseye" size="12" color="pink" />
                        <span class="text-caption">Акция: {{ item.ui_info.marketing_campaign_name }}</span>
                      </div>
                      <div v-if="item.ui_info?.coupon || item.ui_info?.certificate" class="d-flex align-center ga-1">
                        <VIcon icon="bx-qr-scan" size="12" color="indigo" />
                        <span class="text-caption text-indigo-darken-2 font-weight-bold">
                          {{ item.ui_info.coupon ? `Купон: ${item.ui_info.coupon}` : `Сертификат: ${item.ui_info.certificate}` }}
                        </span>
                      </div>
                    </VListItemSubtitle>
                  </VListItem>
                </VList>
              </div>
            </div>



            <!-- 6. Address -->
            <div class="info-section-soft">
              <div class="section-label-soft d-flex justify-space-between w-100">
                <span>
                  <VIcon
                    icon="bx-map-alt"
                    size="14"
                    class="me-1"
                  /> АДРЕС ДОСТАВКИ
                </span>
                <div
                  v-if="order.delivery_address && order.order_type !== 'Самовывоз'"
                  class="d-flex ga-1 mt-n1"
                >
                  <VMenu>
                    <template #activator="{ props: menuProps }">
                      <VBtn
                        v-bind="menuProps"
                        size="x-small"
                        variant="tonal"
                        color="primary"
                        prepend-icon="bx-map"
                        class="soft-btn px-2"
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
                        :href="yandexMapLink"
                        target="_blank"
                        rel="noopener noreferrer"
                        prepend-icon="bx-map"
                      >
                        <VListItemTitle>Яндекс.Карты</VListItemTitle>
                      </VListItem>
                      <VListItem
                        :href="twoGisLink"
                        target="_blank"
                        rel="noopener noreferrer"
                        prepend-icon="bx-navigation"
                      >
                        <VListItemTitle>2GIS</VListItemTitle>
                      </VListItem>
                      <VListItem
                        :href="googleMapsLink"
                        target="_blank"
                        rel="noopener noreferrer"
                        prepend-icon="bx-globe"
                      >
                        <VListItemTitle>Google Maps</VListItemTitle>
                      </VListItem>
                      <VListItem
                        :href="petalMapsLink"
                        target="_blank"
                        rel="noopener noreferrer"
                        prepend-icon="bx-mobile-vibration"
                      >
                        <VListItemTitle>Petal Maps</VListItemTitle>
                      </VListItem>
                    </VList>
                  </VMenu>
                </div>
              </div>
              <div class="glass-block-soft pa-3">
                <div class="text-body-2 font-weight-bold text-slate-700">
                  {{ formattedAddress }}
                </div>
                <div
                  v-if="order.city"
                  class="text-caption text-disabled mt-1 d-flex align-center"
                >
                  <VIcon
                    icon="bx-buildings"
                    size="12"
                    class="me-1"
                  /> {{ order.city }}
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
                  color="grey-lighten-4"
                  class="me-3"
                  size="24"
                />
                <div>
                  <div class="text-body-2 font-weight-bold text-slate-600">
                    {{ cleanCourierName(order.courier_name) }}
                  </div>
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
                    :class="order.is_paid ? 'status-soft-success' : 'status-soft-warning'"
                    size="x-small"
                    variant="flat"
                    class="font-weight-bold px-3"
                  >
                    {{ order.is_paid ? 'ОПЛАЧЕН' : 'НЕ ОПЛАЧЕН' }}
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
                </tr>
              </thead>
              <tbody>
                <template v-if="order.order_items_details?.length">
                  <template
                    v-for="(item, idx) in order.order_items_details"
                    :key="'det-'+idx"
                  >
                    <tr :class="{ 'deleted-item-row': item.deleted }">
                      <td class="py-3">
                        <div 
                          class="font-weight-bold text-body-2"
                          :class="item.deleted ? 'text-disabled' : 'text-slate-700'"
                        >
                          <VIcon v-if="item.deleted" icon="bx-x" size="14" color="error" class="me-1" />
                          {{ item.name }}
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
                    </tr>
                    <tr
                      v-for="(mod, midx) in item.modifiers"
                      :key="'mod-'+idx+'-'+midx"
                      class="modifier-soft"
                    >
                      <td class="ps-8 py-1">
                        <VIcon
                          icon="bx-subdirectory-right"
                          size="14"
                          class="me-1 opacity-30"
                        /> {{ mod.name }}
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
                    </tr>
                  </template>
                </template>
                <tr v-else>
                  <td
                    colspan="4"
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
                  v-for="(hist, idx) in order.status_history"
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
                      <span class="timeline-time-soft">
                        {{ formatDate(hist.time, true) }}
                      </span>
                    </div>
                    <div
                      v-if="getStatusDuration(idx)"
                      class="text-caption text-disabled d-flex align-center mt-1"
                    >
                      <VIcon
                        icon="bx-stopwatch"
                        size="12"
                        class="me-1"
                      />
                      {{ getStatusDuration(idx) }}
                    </div>
                  </div>
                </VTimelineItem>
              </VTimeline>
            </div>
          </VCol>
        </VRow>
      </VCardText>

      <VCardActions class="pa-4 bg-white border-t">
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
          Закрыть
        </VBtn>
      </VCardActions>
    </VCard>

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
</style>
