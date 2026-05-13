<script setup>
import { ref, watch, computed } from "vue"
import { formatDateTime, isLongTimeAgo } from "@/utils/date"
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
})

const emit = defineEmits(["update:modelValue"])

const dialog = computed({
  get: () => props.modelValue,
  set: val => emit("update:modelValue", val),
})

const customerInfo = ref(null)
const isLoadingCustomer = ref(false)
const customerModalVisible = ref(false)

const fetchCustomerInfo = async () => {
  if (!props.order?.customer_phone) return

  isLoadingCustomer.value = true
  try {
    const response = await fetch(`/api/v1/customers/by-phone/${encodeURIComponent(props.order.customer_phone)}`)
    if (response.ok) {
      customerInfo.value = await response.json()
    } else {
      customerInfo.value = null
    }
  } catch (e) {
    console.error("Failed to fetch customer info:", e)
    customerInfo.value = null
  } finally {
    isLoadingCustomer.value = false
  }
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

const formatDate = (dateString, showOnlyTime = false) => {
  if (!dateString) return "—"

  return formatDateTime(dateString, showOnlyTime ? { day: undefined, month: undefined, year: undefined } : {})
}

const formatPrice = value => {
  const num = parseFloat(value)

  return isNaN(num) ? "0.00" : num.toFixed(2)
}

const yandexMapLink = computed(() => {
  if (!props.order?.delivery_address) return "#"

  return `https://yandex.ru/maps/?text=${encodeURIComponent(props.order.delivery_address)}`
})

const twoGisLink = computed(() => {
  if (!props.order?.delivery_address) return "#"

  return `https://2gis.ru/search/${encodeURIComponent(props.order.delivery_address)}`
})

const formattedAddress = computed(() => {
  if (!props.order) return "—"
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
    new: "#E3F2FD",
    unconfirmed: "#FFF3E0",
    confirmed: "#E1F5FE",
    preparing: "#E0F2F1",
    cooking: "#FFF8E1",
    ready: "#E8F5E9",
    readyForPickup: "#E8F5E9",
    delivering: "#E8EAF6",
    delivered: "#F1F8E9",
    closed: "#F5F5F5",
    cancelled: "#FFEBEE",
  }

  const key = props.order?.status ? props.order.status.replace(/_([a-z])/g, g => g[1].toUpperCase()) : "new"

  return statusColors[key] || "#F5F5F5"
})

const statusTextColor = computed(() => {
  const textColors = {
    new: "#1565C0",
    unconfirmed: "#E65100",
    confirmed: "#0277BD",
    preparing: "#00695C",
    cooking: "#F57F17",
    ready: "#2E7D32",
    readyForPickup: "#2E7D32",
    delivering: "#283593",
    delivered: "#33691E",
    closed: "#616161",
    cancelled: "#C62828",
  }

  const key = props.order?.status ? props.order.status.replace(/_([a-z])/g, g => g[1].toUpperCase()) : "new"

  return textColors[key] || "#616161"
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
  // Logic for printing
  window.print()
}
</script>

<template>
  <VDialog
    v-model="dialog"
    max-width="1000"
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
              color="grey-lighten-1"
              size="24"
            />
            <span class="text-h5 font-weight-bold text-slate-800">Заказ #{{ order.id }}</span>
            <VChip
              size="x-small"
              color="blue-grey-lighten-5"
              variant="flat"
              class="text-uppercase font-weight-bold text-blue-grey-lighten-1"
            >
              {{ order.source || 'iiko' }}
            </VChip>
          </div>
          <span
            v-if="order.external_number"
            class="text-caption text-disabled ms-9"
          >
            Внешний ID: {{ order.external_number }}
          </span>
        </div>

        <VSpacer />

        <div class="d-flex align-center ga-3">
          <VChip
            :style="{ backgroundColor: statusColor + ' !important', color: statusTextColor + ' !important' }"
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
              color="grey-darken-1"
            />
          </VBtn>
        </div>
      </VCardTitle>

      <VCardText class="pa-0 bg-slate-50">
        <VRow no-gutters>
          <!-- Left Column: Info Blocks -->
          <VCol
            cols="12"
            md="5"
            class="border-e pa-6 d-flex flex-column ga-1"
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
                <VAvatar
                  size="40"
                  color="blue-grey-lighten-5"
                  class="me-3 border"
                >
                  <VIcon
                    icon="bx-user"
                    size="20"
                    color="blue-grey-lighten-2"
                  />
                </VAvatar>
                <div class="d-flex flex-column overflow-hidden">
                  <span class="text-body-2 font-weight-bold text-truncate">{{ order.customer_info_details?.name || order.customer_name || 'Гость' }}</span>
                  <span class="text-caption text-disabled">{{ order.customer_phone }}</span>
                </div>
                <VSpacer />
                <div class="d-flex ga-2 px-2">
                  <VTooltip
                    v-if="(order.customer_info_details?.is_new_guest && (order.customer_info_details?.total_orders_count || 0) <= 1) || order.is_first_order"
                    text="Новый гость"
                  >
                    <template #activator="{ props: tooltipProps }">
                      <VIcon
                        v-bind="tooltipProps"
                        icon="bx-star"
                        color="amber-lighten-3"
                        size="20"
                      />
                    </template>
                  </VTooltip>
                  <VTooltip
                    v-if="isLongTimeAgo(order.customer_info_details?.last_order_date)"
                    text="Вернувшийся клиент"
                  >
                    <template #activator="{ props: tooltipProps }">
                      <VIcon
                        v-bind="tooltipProps"
                        icon="ri-history-line"
                        color="warning"
                        size="20"
                      />
                    </template>
                  </VTooltip>
                  <VTooltip :text="order.customer_info_details?.is_high_risk ? 'Высокий риск' : 'Проверен'">
                    <template #activator="{ props: tooltipProps }">
                      <VIcon
                        v-bind="tooltipProps"
                        :icon="order.customer_info_details?.is_high_risk ? 'bx-shield-x' : 'bx-shield-quarter'"
                        :color="order.customer_info_details?.is_high_risk ? 'red-lighten-4' : 'green-lighten-4'"
                        size="20"
                      />
                    </template>
                  </VTooltip>
                </div>
                <VIcon
                  icon="bx-chevron-right"
                  color="grey-lighten-3"
                />
              </div>
            </div>

            <!-- 2. Execution Time -->
            <div class="info-section-soft">
              <div class="section-label-soft">
                <VIcon
                  icon="bx-time-five"
                  size="14"
                  class="me-1"
                /> ВРЕМЯ ИСПОЛНЕНИЯ
              </div>
              <div
                class="glass-block-soft d-flex align-center"
                :class="order.is_asap ? 'time-asap-soft' : 'time-preorder-soft'"
              >
                <div class="me-4 text-h5 opacity-50">
                  {{ order.is_asap ? '⚡' : '📅' }}
                </div>
                <div class="d-flex flex-column">
                  <span class="text-overline font-weight-black leading-none mb-1 opacity-50">
                    {{ order.is_asap ? 'КАК МОЖНО СКОРЕЕ' : 'ПРЕДЗАКАЗ' }}
                  </span>
                  <div class="d-flex align-baseline ga-2">
                    <span class="text-h6 font-weight-bold leading-none text-slate-700">
                      {{ formatDateTime(order.expected_time || order.creation_date, { day: undefined, month: undefined, year: undefined }) }}
                    </span>
                    <span
                      v-if="!order.is_asap"
                      class="text-caption font-weight-medium text-slate-500"
                    >
                      {{ formatDateTime(order.expected_time, { hour: undefined, minute: undefined, second: undefined }) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. Comment -->
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
              <div class="glass-block-soft bg-white border-slate-100 text-body-2 italic text-slate-600">
                "{{ order.comment }}"
              </div>
            </div>

            <!-- 4. Address -->
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
                  <VBtn
                    :href="yandexMapLink"
                    target="_blank"
                    rel="noopener noreferrer"
                    size="x-small"
                    variant="text"
                    color="grey-lighten-2"
                    icon="bx-map"
                  />
                  <VBtn
                    :href="twoGisLink"
                    target="_blank"
                    rel="noopener noreferrer"
                    size="x-small"
                    variant="text"
                    color="grey-lighten-2"
                    icon="bx-navigation"
                  />
                </div>
              </div>
              <div class="glass-block-soft">
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

            <!-- 5. Courier -->
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

            <!-- 6. State & Payment Type -->
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
                    :color="order.is_paid ? '#E8F5E9' : '#FFF3E0'"
                    size="x-small"
                    variant="flat"
                    class="font-weight-bold"
                    :style="{ color: order.is_paid ? '#2E7D32' : '#E65100' }"
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

            <!-- 7. Financials Mini -->
            <div class="info-section-soft mt-auto mb-0">
              <div class="financial-panel-glass-soft">
                <div class="financial-row">
                  <span>Подытог:</span>
                  <span class="value">{{ formatPrice(parseFloat(order.total_with_discount || 0) + parseFloat(order.total_discount || 0)) }} ₽</span>
                </div>
                <div
                  v-if="parseFloat(order.total_discount || 0) > 0"
                  class="financial-row discount"
                >
                  <span>Скидка:</span>
                  <span class="value">-{{ formatPrice(order.total_discount) }} ₽</span>
                </div>
                <div class="financial-row total">
                  <span>ИТОГО:</span>
                  <span class="value">{{ formatPrice(order.total_with_discount) }} ₽</span>
                </div>
                <VDivider class="my-3 opacity-30" />
                <div class="d-flex justify-space-between align-center mb-3">
                  <span class="text-subtitle-1 font-weight-bold text-slate-600">ИТОГО К ОПЛАТЕ:</span>
                  <span class="text-h5 font-weight-black text-indigo-accent-2">{{ formatPrice(order.total_with_discount) }} ₽</span>
                </div>
                <div class="d-flex justify-space-between align-center pt-2 border-t">
                  <span class="text-caption text-disabled">Метод оплаты:</span>
                  <VChip
                    size="x-small"
                    variant="tonal"
                    color="grey-lighten-1"
                    class="font-weight-bold"
                  >
                    {{ order.payment_method || '—' }}
                  </VChip>
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
                    <tr>
                      <td class="py-3">
                        <div class="font-weight-bold text-body-2 text-slate-700">
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
                      <td class="text-right font-weight-bold text-body-2 text-slate-600">
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

            <!-- 2. Financials Duplicate -->
            <div class="glass-block-soft d-flex flex-wrap justify-space-between align-center ga-4 mb-8">
              <div class="d-flex ga-6 align-center">
                <div class="d-flex flex-column">
                  <span class="text-caption text-disabled uppercase">Подытог</span>
                  <span class="text-body-2 font-weight-bold text-slate-600">{{ formatPrice(parseFloat(order.total_with_discount || 0) + parseFloat(order.total_discount || 0)) }} ₽</span>
                </div>
                <VDivider
                  vertical
                  length="24"
                  class="mx-0 opacity-30"
                />
                <div class="d-flex flex-column">
                  <span class="text-caption text-disabled uppercase">Скидка</span>
                  <span class="text-body-2 font-weight-bold text-red-lighten-2">-{{ formatPrice(order.total_discount) }} ₽</span>
                </div>
                <VDivider
                  vertical
                  length="24"
                  class="mx-0 opacity-30"
                />
                <div class="d-flex flex-column">
                  <span class="text-caption text-disabled uppercase">Итого</span>
                  <span class="text-h6 font-weight-black text-indigo-accent-2">{{ formatPrice(order.total_with_discount) }} ₽</span>
                </div>
              </div>
              <div class="d-flex flex-column align-end">
                <span class="text-caption text-disabled uppercase mb-1">Метод оплаты</span>
                <span class="text-caption font-weight-bold text-slate-500 bg-slate-100 px-2 py-1 rounded">{{ order.payment_method || '—' }}</span>
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
  box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.12) !important;
  background-color: #ffffff !important;
  border-radius: 24px !important;
}

/* Colors & Typography */
.text-slate-800 { color: #1e293b !important; }
.text-slate-700 { color: #334155 !important; }
.text-slate-600 { color: #475569 !important; }
.text-slate-500 { color: #64748b !important; }
.text-slate-400 { color: #94a3b8 !important; }
.bg-slate-50 { background-color: #f8fafc !important; }
.bg-slate-100 { background-color: #f1f5f9 !important; }
.border-slate-100 { border-color: #f1f5f9 !important; }

.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
}

.uppercase { text-transform: uppercase !important; letter-spacing: 0.08em !important; }

/* Content Blocks */
.info-section-soft {
  margin-bottom: 28px;
}

.section-label-soft {
  font-size: 11px;
  font-weight: 800;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 12px;
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
  margin-bottom: 10px;
  font-size: 14px;
  color: #475569;
}

.financial-row.discount {
  color: #ef4444;
  font-weight: 600;
}

.financial-row.total {
  margin-top: 16px;
  padding-top: 16px;
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
.items-table-soft {
  border-radius: 16px !important;
  overflow: hidden !important;
  border: 1px solid #f1f5f9 !important;
  background: white !important;
}

.items-table-soft :deep(th) {
  background: #fcfdfe !important;
  color: #64748b !important;
  font-size: 11px !important;
  font-weight: 800 !important;
  height: 48px !important;
  border-bottom: 1px solid #f1f5f9 !important;
}

.modifier-soft td {
  background: #f9fafb !important;
  border-bottom: none !important;
  color: #94a3b8 !important;
  font-size: 12px !important;
  padding-top: 4px !important;
  padding-bottom: 4px !important;
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
  background-color: #cbd5e1;
  border-radius: 20px;
}
</style>
