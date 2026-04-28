<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from "vue"
import { formatDateTime } from "@/utils/date"

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
    default: 'line1',
  },
})

const emit = defineEmits(["update:modelValue"])

const dialog = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val)
})




const formatDate = (dateString, showOnlyTime = false) => {
  if (!dateString) return '—'
  return formatDateTime(dateString, showOnlyTime ? { day: undefined, month: undefined, year: undefined } : {})
}

const cookingTime = computed(() => {
  if (!props.order?.creation_date || !props.order?.actual_time) return null
  const start = new Date(props.order.creation_date)
  const end = new Date(props.order.actual_time)
  const diffMs = end - start
  if (diffMs < 0) return null
  const diffMins = Math.floor(diffMs / 60000)
  return `${diffMins} мин`
})

const formatPrice = (value) => {
  const num = parseFloat(value)
  return isNaN(num) ? '0.00' : num.toFixed(2)
}

const yandexMapLink = computed(() => {
  if (!props.order?.delivery_address) return '#'
  return `https://yandex.ru/maps/?text=${encodeURIComponent(props.order.delivery_address)}`
})

const twoGisLink = computed(() => {
  if (!props.order?.delivery_address) return '#'
  return `https://2gis.ru/search/${encodeURIComponent(props.order.delivery_address)}`
})

const formattedAddress = computed(() => {
  if (!props.order) return '—'
  if (props.order.order_type === 'Самовывоз' || !props.order.delivery_address) return '🙍 Самовывоз'
  
  // Условие для предупреждения ❗
  const status = (props.order.status || '').toLowerCase()
  const isPending = !['closed', 'cancelled'].includes(status)
  const flat = (props.order.flat || '').toString().trim()
  const noFlat = !flat || flat === '0' || flat === '-'
  const showWarning = isPending && noFlat && props.order.order_type !== 'Самовывоз'
  const warningPrefix = showWarning ? '❗ ' : ''

  if (props.addressFormat === 'line1') {
    return warningPrefix + props.order.delivery_address
  }
  
  const parts = []
  const o = props.order
  
  if (o.city) {
    const cityPref = o.city.toLowerCase().startsWith('г.') ? o.city : `г. ${o.city}`
    parts.push(cityPref)
  }
  
  if (o.street) {
    if (!/ул\.|пр\.|пер\.|б-р/.test(o.street.toLowerCase())) {
      parts.push(`ул. ${o.street}`)
    } else {
      parts.push(o.street)
    }
  }
  
  if (o.house && o.house !== '0') parts.push(`д. ${o.house}`)
  if (o.flat) parts.push(`кв. ${o.flat}`)
  if (o.entrance) parts.push(`под. ${o.entrance}`)
  if (o.floor) parts.push(`эт. ${o.floor}`)
  if (o.doorphone) parts.push(`домофон: ${o.doorphone}`)
  
  if (parts.length <= 1 && o.delivery_address) return warningPrefix + o.delivery_address
  
  return warningPrefix + parts.join(', ')
})

const statusColor = computed(() => {
  const statusColors = {
    new: "indigo-lighten-2",
    unconfirmed: "deep-orange-darken-1",
    confirmed: "blue-lighten-3",
    preparing: "light-blue-lighten-3",
    cooking: "light-blue-lighten-3",
    ready: "orange",
    ready_for_pickup: "orange-lighten-1",
    delivering: "cyan-darken-1",
    delivered: "green",
    closed: "green",
    cancelled: "red"
  }
  
  return statusColors[props.order?.status] || 'grey'
})

const getStatusLabel = (status) => {
  if (!status) return '—'
  const labels = {
    'new': 'Новый',
    'unconfirmed': 'Не подтвержден',
    'waitapproval': 'Ожидает подтверждения',
    'waitingforselection': 'Выбор...',
    'accepted': 'Принят',
    'confirmed': 'Принят',
    'inprogress': 'В сборке',
    'readyforcooking': 'Ожидает готовки',
    'preparing': 'В сборке',
    'cooking': 'Готовится',
    'cookingstarted': 'Готовится',
    'cookingcompleted': 'Приготовлен',
    'ready': 'Готов',
    'ready_for_pickup': 'Готов к выдаче',
    'waiting': 'Ожидает отправки',
    'onway': 'В пути',
    'delivering': 'У курьера',
    'delivered': 'Доставлен',
    'closed': 'Закрыт',
    'cancelled': 'Отменен',
    'cookingcompleted': 'Приготовлен',
    'readyforcooking': 'Ожидает готовки'
  }
  return labels[status.toLowerCase()] || status
}

const getStatusColor = (status) => {
  if (!status) return 'grey'
  const colors = {
    'new': 'indigo-lighten-2',
    'unconfirmed': 'deep-orange-darken-1',
    'confirmed': 'blue-lighten-1',
    'preparing': 'amber-darken-1',
    'cooking': 'orange-darken-1',
    'ready': 'success',
    'cookingcompleted': 'success',
    'delivered': 'green-darken-1',
    'closed': 'grey-darken-1',
    'cancelled': 'red-darken-1',
    'delivering': 'cyan-darken-1'
  }
  return colors[status.toLowerCase()] || 'blue-grey-lighten-2'
}

const cleanCourierName = (name) => {
  if (!name || name.toLowerCase().includes('none none') || name.toLowerCase().trim() === 'не назначен') return 'Не назначен'
  
  return name.replace(/(\s+None)+$/i, '').replace(/None\s+None/i, '').trim()
}

const getStatusDuration = (idx) => {
  if (!props.order?.status_history || idx >= props.order.status_history.length - 1) return null
  
  const current = new Date(props.order.status_history[idx].time)
  const next = new Date(props.order.status_history[idx + 1].time)
  
  const diffMs = next - current
  if (diffMs <= 0) return null
  
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return '< 1м'
  
  if (diffMins >= 60) {
    const hours = Math.floor(diffMins / 60)
    const mins = diffMins % 60
    
    return mins > 0 ? `${hours}ч ${mins}м` : `${hours}ч`
  }
  
  return `${diffMins}м`
}
</script>

<template>
  <VDialog 
    v-model="dialog" 
    max-width="900" 
    scrollable
  >
    <VCard v-if="order">
      <VCardTitle class="d-flex align-center bg-primary text-white py-3">
        Заказ #{{ order.id }} 
        <span v-if="order.external_number" class="ms-2 text-caption opacity-80">(iiko: {{ order.external_number }})</span>
        <VChip 
          size="small" 
          :color="statusColor" 
          variant="elevated" 
          class="ms-3"
        >
          <template #prepend>
            <span class="me-1">{{ order.is_asap ? '⚡' : '⏰' }}</span>
          </template>
        </VChip>
        <VChip v-if="order.source" size="x-small" color="secondary" variant="tonal" class="ms-2">
          {{ order.source }}
        </VChip>
        <VChip size="small" :color="order.is_paid ? 'success' : 'warning'" variant="elevated" class="ms-2">
          {{ order.is_paid ? 'Оплачен' : 'Не оплачен' }}
        </VChip>
        <VSpacer />
        <VBtn icon variant="text" @click="dialog = false" color="white">
          <VIcon icon="bx-x" />
        </VBtn>
      </VCardTitle>

      <VCardText class="pa-4 pt-4">
        <!-- Блок временных меток -->
        <div class="d-flex flex-wrap ga-4 mb-6 pa-3 bg-grey-lighten-4 rounded-lg">
          <div v-if="order?.creation_date" class="d-flex align-center">
            <VIcon icon="bx-time" color="primary" class="me-2" size="20" />
            <div>
              <div class="text-caption text-grey">Создан</div>
              <div class="text-body-2 font-weight-bold">{{ formatDateTime(order.creation_date) }}</div>
            </div>
          </div>
          
          <VDivider vertical />

          <div 
            class="d-flex align-center pa-3 rounded-xl"
            :class="(order?.status === 'closed' || order?.status === 'cancelled') ? '' : 'elevation-2'"
            :style="{
              backgroundColor: (order?.status === 'closed' || order?.status === 'cancelled') ? 'transparent' : (order?.is_asap ? '#FFFDE7' : '#E1F5FE'),
              border: (order?.status === 'closed' || order?.status === 'cancelled') ? 'none' : `2px solid ${order?.is_asap ? '#FDD835' : '#4FC3F7'}`,
              minWidth: '220px'
            }"
          >
            <div class="me-4 text-h3">{{ order?.is_asap ? '⚡' : '⏰' }}</div>
            <div>
              <div class="text-overline font-weight-black mb-n1" :style="{ color: order?.is_asap ? '#F57F17' : '#01579B' }">
                {{ order?.is_asap ? 'Как можно быстрее' : 'На время' }}
              </div>
              <div class="text-h5 font-weight-black" :style="{ color: order?.is_asap ? '#E65100' : '#0D47A1' }">
                {{ formatDateTime(order?.expected_time || order?.iiko_creation_time || order?.created_at, { day: undefined, month: undefined, year: undefined }) }}
              </div>
              <div v-if="order?.expected_time && (new Date(order.expected_time).toDateString() !== new Date(order.iiko_creation_time || order.created_at).toDateString())" 
                   class="text-caption font-weight-bold mt-n1"
                   :style="{ color: order?.is_asap ? '#FB8C00' : '#1565C0' }"
              >
                {{ formatDateTime(order.expected_time, { hour: undefined, minute: undefined, second: undefined }) }}
              </div>
            </div>
          </div>

          <VDivider vertical v-if="order?.actual_time" />

          <div v-if="order?.actual_time" class="d-flex align-center">
            <VIcon icon="bx-check-double" color="success" class="me-2" size="20" />
            <div>
              <div class="text-caption text-grey">Фактическое время</div>
              <div class="text-body-2 font-weight-bold">{{ formatDateTime(order.actual_time) }}</div>
            </div>
          </div>

          <VDivider vertical v-if="cookingTime" />

          <div v-if="cookingTime" class="d-flex align-center">
            <VIcon icon="bx-timer" color="info" class="me-2" size="20" />
            <div>
              <div class="text-caption text-grey">Время готовки</div>
              <div class="text-body-2 font-weight-bold">{{ cookingTime }}</div>
            </div>
          </div>
          
          <VSpacer />
          
          <div class="d-flex align-center">
             <VTooltip location="top">
               <template #activator="{ props }">
                 <span v-bind="props" class="me-2 text-h5" style="cursor: help">
                   {{ order?.is_asap ? '⚡' : '⏰' }}
                 </span>
               </template>
               <span>{{ order?.is_asap ? '⚡ Как можно скорее' : '⏰ На время' }}</span>
             </VTooltip>
          </div>
        </div>

        <VRow>
          <!-- Клиент и Доставка -->
          <VCol cols="12" md="6">
            <h3 class="text-h6 mb-3 d-flex align-center">
              <VIcon icon="bx-user" class="me-2" color="primary" /> О клиенте
            </h3>
            <VList density="compact" class="bg-transparent pa-0 mb-6">
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-user-circle" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle class="font-weight-bold">{{ order.customer_name || 'Гость' }}</VListItemTitle>
                <VListItemSubtitle>Имя клиента</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-phone" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle class="d-flex align-center">
                  <a :href="'tel:' + order.customer_phone" class="text-primary text-decoration-none font-weight-medium">
                    {{ order.customer_phone || 'Не указан' }}
                  </a>
                  <VChip
                    v-if="order.spam_score > 0"
                    :color="order.spam_score >= 80 ? 'error' : 'warning'"
                    size="x-small"
                    variant="tonal"
                    class="ms-2"
                  >
                    {{ order.spam_score >= 80 ? 'СПАМ/УГРОЗА' : 'ПОДОЗРИТЕЛЬНЫЙ' }}
                  </VChip>
                </VListItemTitle>
                <VListItemSubtitle>Телефон</VListItemSubtitle>
              </VListItem>

              <!-- Инфо о спаме -->
              <VAlert
                v-if="order.spam_score > 0"
                :type="order.spam_score >= 80 ? 'error' : 'warning'"
                variant="tonal"
                density="compact"
                class="mt-2 text-caption"
                icon="bx-shield-quarter"
              >
                {{ order.spam_info }}
              </VAlert>
            </VList>

            <VDivider class="my-4" />

            <h3 class="text-h6 mb-3 d-flex align-center">
              <VIcon icon="bx-map-pin" class="me-2" color="primary" /> Доставка
            </h3>
            <div class="mb-4">
              <p class="mb-1 text-primary font-weight-black" v-if="order.city">г. {{ order.city }}</p>
              <div class="pa-3 rounded bg-grey-lighten-4 border-grey-darken-1 mb-3" style="border: 2px solid; color: #000000 !important">
                <p class="mb-0 text-body-1 font-weight-black line-height-1-4">
                  {{ formattedAddress }}
                </p>
              </div>
              
              <!-- Дополнительные кнопки карт -->
              <div class="d-flex gap-2" v-if="order.delivery_address && order.delivery_address !== 'Самовывоз'">
                <VBtn :href="yandexMapLink" target="_blank" rel="noopener noreferrer" size="x-small" variant="tonal" color="success">
                  <VIcon icon="bx-map" size="14" class="me-1" /> Яндекс.Карты
                </VBtn>
                <VBtn :href="twoGisLink" target="_blank" rel="noopener noreferrer" size="x-small" variant="tonal" color="primary">
                  <VIcon icon="bx-navigation" size="14" class="me-1" /> 2GIS
                </VBtn>
              </div>
            </div>

            <VList density="compact" class="bg-transparent pa-0">
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-package" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ order.order_type || 'Доставка' }}</VListItemTitle>
                <VListItemSubtitle>Тип заказа</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-cycling" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ cleanCourierName(order.courier_name) }}</VListItemTitle>
                <VListItemSubtitle>Курьер</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0" v-if="order.delivery_zone">
                <template #prepend><VIcon icon="bx-map-alt" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ order.delivery_zone }}</VListItemTitle>
                <VListItemSubtitle>Зона доставки</VListItemSubtitle>
              </VListItem>
            </VList>

            <VDivider class="my-4" />

            <!-- История статусов (Compact Timeline) -->
            <v-card variant="flat" class="bg-grey-lighten-5 rounded-lg border">
              <v-card-text class="pa-3">
                <div class="d-flex align-center mb-2 px-1">
                  <v-icon icon="mdi-history" color="primary" class="me-2" size="18" />
                  <span class="text-caption font-weight-bold text-uppercase">Лента статусов</span>
                </div>

                <v-timeline density="compact" side="end" truncate-line="both" align="start" class="status-timeline-compact">
                  <v-timeline-item
                    v-for="(hist, idx) in order.status_history"
                    :key="idx"
                    :dot-color="getStatusColor(hist.status)"
                    size="6"
                    class="pb-2"
                  >
                    <div class="d-flex flex-column" style="margin-top: -4px">
                      <div class="d-flex justify-space-between align-center">
                        <span class="text-caption font-weight-black" :style="{ color: getStatusColor(hist.status) }">
                          {{ getStatusLabel(hist.status) }}
                        </span>
                        <span class="text-caption text-grey" style="font-size: 0.7rem !important">
                          {{ formatDate(hist.time, true) }}
                        </span>
                      </div>
                      
                      <div v-if="getStatusDuration(idx)" class="mt-n1">
                        <span class="text-caption text-grey-darken-1 font-weight-medium" style="font-size: 0.65rem !important">
                          <VIcon icon="mdi-clock-time-four-outline" size="10" class="me-1" />
                          {{ getStatusDuration(idx) }}
                        </span>
                      </div>
                    </div>
                  </v-timeline-item>
                </v-timeline>
              </v-card-text>
            </v-card>
            
            <VList density="compact" class="bg-transparent pa-0" v-if="!order.status_history?.length">
              <VListItem class="px-0">
                <VListItemTitle>{{ formatDateTime(order.created_at) }}</VListItemTitle>
                <VListItemSubtitle>Время создания</VListItemSubtitle>
              </VListItem>
            </VList>

            <div 
              class="d-flex align-center pa-3 rounded-lg mt-2 mb-4"
              :style="{
                backgroundColor: order?.is_asap ? '#FFFDE7' : '#E1F5FE',
                borderLeft: `6px solid ${order?.is_asap ? '#FDD835' : '#4FC3F7'}`
              }"
            >
              <div class="me-3 text-h5">{{ order?.is_asap ? '⚡' : '⏰' }}</div>
              <div>
                <div class="text-subtitle-2 font-weight-bold" :style="{ color: order?.is_asap ? '#F57F17' : '#01579B' }">
                  {{ order?.is_asap ? 'Как можно быстрее' : 'На время: ' + formatDateTime(order.expected_time, { day: undefined, month: undefined, year: undefined }) }}
                </div>
                <div class="text-caption" :style="{ color: order?.is_asap ? '#FB8C00' : '#1565C0' }">
                  {{ order?.is_asap ? 'Стандартный заказ (ASAP)' : 'Предзаказ на ' + formatDateTime(order.expected_time) }}
                </div>
              </div>
            </div>


            <VList density="compact" class="bg-transparent pa-0">
              <VListItem class="px-0">
                <VListItemTitle>{{ order.branch_name }}</VListItemTitle>
                <VListItemSubtitle>Ресторан</VListItemSubtitle>
              </VListItem>
            </VList>
          </VCol>

          <!-- Состав и финансы -->
          <VCol cols="12" md="6">
            <h3 class="text-h6 mb-3 d-flex align-center">
              <VIcon icon="bx-receipt" class="me-2" color="primary" /> Состав заказа
            </h3>
            
            <VTable density="compact" class="border rounded mb-6">
              <thead>
                <tr>
                  <th>Позиция</th>
                  <th class="text-center">Кол-во</th>
                  <th class="text-center">Цена</th>
                  <th class="text-right">Сумма</th>
                </tr>
              </thead>
              <tbody>
                <template v-if="order.order_items_details && order.order_items_details.length > 0">
                  <template v-for="(item, itemIdx) in order.order_items_details" :key="item.id || 'item-' + itemIdx">
                    <tr>
                      <td class="font-weight-medium text-wrap">
                        {{ item.name }}
                        <VChip v-if="item.size" size="x-small" variant="tonal" color="secondary" class="ms-1">
                            {{ (typeof item.size === 'object' && item.size !== null) ? item.size.name : item.size }}
                        </VChip>
                        <div v-if="item.comment" class="text-caption text-info mt-1 font-italic">
                          <VIcon icon="bx-comment-dots" size="12" class="me-1" /> {{ item.comment }}
                        </div>
                      </td>
                      <td class="text-center">{{ item.amount }}</td>
                      <td class="text-center">{{ formatPrice(item.price) }} ₽</td>
                      <td class="text-right font-weight-bold">{{ formatPrice(item.sum || (item.amount * item.price)) }} ₽</td>
                    </tr>
                    <!-- Модификаторы из деталей iiko -->
                    <tr v-for="(mod, modIdx) in item.modifiers" :key="mod.id || mod.productId || 'mod-det-' + modIdx" class="text-caption opacity-80">
                      <td class="ps-6">• {{ mod.name }}</td>
                      <td class="text-center">{{ mod.amount }}</td>
                      <td class="text-center">{{ formatPrice(mod.price) }} ₽</td>
                      <td class="text-right">{{ formatPrice(mod.sum || (mod.amount * mod.price)) }} ₽</td>
                    </tr>
                  </template>
                </template>
                <template v-else-if="order.items && order.items.length > 0">
                  <template v-for="item in order.items" :key="item.id">
                    <tr>
                      <td class="font-weight-medium text-wrap">
                        {{ item.product_name }}
                        <VChip v-if="item.size_name" size="x-small" variant="tonal" color="secondary" class="ms-1">
                          {{ item.size_name }}
                        </VChip>
                        <div v-if="item.comment" class="text-caption text-info mt-1 font-italic">
                          <VIcon icon="bx-comment-dots" size="12" class="me-1" /> {{ item.comment }}
                        </div>
                      </td>
                      <td class="text-center">{{ item.quantity }}</td>
                      <td class="text-center">{{ formatPrice(item.price) }} ₽</td>
                      <td class="text-right font-weight-bold">{{ formatPrice(item.total || (item.quantity * item.price)) }} ₽</td>
                    </tr>
                    <tr v-for="(mod, modIdx) in item.modifiers" :key="mod.iiko_id || mod.id || 'mod-' + modIdx" class="text-caption opacity-70">
                      <td class="ps-6">• {{ mod.name }}</td>
                      <td class="text-center">{{ mod.amount }}</td>
                      <td class="text-center">{{ formatPrice(mod.price) }} ₽</td>
                      <td class="text-right">{{ formatPrice(mod.sum || (mod.amount * mod.price)) }} ₽</td>
                    </tr>
                  </template>
                </template>
                <tr v-else>
                  <td colspan="4" class="text-center py-4 text-disabled">Нет данных о товарах</td>
                </tr>
              </tbody>
            </VTable>

            <VCard variant="outlined" color="primary" class="pa-4 bg-lightprimary mb-4">
              <div class="d-flex justify-space-between mb-2">
                <span>Сумма без скидок:</span>
                <span class="font-weight-bold">{{ order.base_amount || order.total_amount }} ₽</span>
              </div>
              <div v-if="parseFloat(order.total_discount) > 0" class="d-flex justify-space-between mb-2 text-error">
                <span>Скидка:</span>
                <span class="font-weight-bold">-{{ order.total_discount }} ₽</span>
              </div>
              <div v-if="parseFloat(order.bonus_spent) > 0" class="d-flex justify-space-between mb-2 text-warning">
                <span>Бонусы:</span>
                <span class="font-weight-bold">-{{ order.bonus_spent }} ₽</span>
              </div>
              <VDivider class="my-2" />
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-h6">Итого к оплате:</span>
                <span class="text-h5 font-weight-black text-primary">
                  {{ order.total_with_discount }} ₽
                </span>
              </div>
              
              <template v-if="order.payments_details?.total_paid > 0">
                 <VDivider class="my-2" />
                 <div class="d-flex justify-space-between text-success mb-1">
                   <span>Уже оплачено:</span>
                   <span class="font-weight-bold">{{ order.payments_details.total_paid }} ₽</span>
                 </div>
                 <div class="d-flex justify-space-between text-h6" :class="parseFloat(order.left_to_pay) > 0 ? 'text-error' : 'text-success'">
                   <span>Остаток:</span>
                   <span class="font-weight-bold">{{ order.left_to_pay }} ₽</span>
                 </div>
              </template>

              <div class="mt-2 text-right">
                <VChip size="x-small" variant="outlined" :color="order.is_paid ? 'success' : 'warning'">
                  {{ order.payment_method || 'Способ оплаты не указан' }}
                  <template v-if="order.is_paid"> (Оплачен)</template>
                </VChip>
              </div>
            </VCard>

            <!-- Детали оплат -->
            <div v-if="order.payments_details?.items?.length" class="mb-4">
               <div class="text-subtitle-2 mb-1 px-1">История транзакций:</div>
               <div v-for="(p, pIdx) in order.payments_details.items" :key="pIdx" 
                    class="d-flex justify-space-between align-center pa-2 border rounded mb-1 text-caption"
                    :class="p.is_processed ? 'bg-green-lighten-5' : 'bg-grey-lighten-4'">
                  <span>
                    <VIcon :icon="p.is_processed ? 'bx-check-circle' : 'bx-time'" size="14" :color="p.is_processed ? 'success' : 'grey'" class="me-1" />
                    {{ p.name }}
                  </span>
                  <span class="font-weight-bold">{{ p.sum }} ₽</span>
               </div>
            </div>

            <!-- Детали скидок из iiko (Fix 10) -->
            <VAlert v-if="order.discounts_details?.items?.length" type="success" variant="tonal" density="compact" class="mt-3 text-caption">
              <div v-for="d in order.discounts_details.items" :key="d.id || d.name">
                Скидка: {{ d.name }} — {{ d.sum }} ₽
              </div>
            </VAlert>

            <VAlert v-if="order.comment" type="info" variant="tonal" icon="bx-message-detail" class="mt-4 text-caption">
              <strong>Комментарий:</strong> {{ order.comment }}
            </VAlert>
          </VCol>
        </VRow>
      </VCardText>
      
      <VDivider />
      
      <VCardActions class="pa-4">
        <VSpacer />
        <VBtn variant="tonal" @click="dialog = false">Закрыть</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>

<style scoped>
.bg-lightprimary {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.status-timeline {
  padding-left: 8px;
}
.status-indicator {
  width: 20px;
}
.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 4px;
  z-index: 2;
  border: 2px solid white;
}
.status-line {
  width: 2px;
  flex-grow: 1;
  background-color: #e0e0e0;
  margin: -2px 0;
  z-index: 1;
}
.status-content {
  border-bottom: 1px solid rgba(0,0,0,0.05);
}
.status-item:last-child .status-content {
  border-bottom: none;
}
.status-duration {
  font-size: 0.7rem !important;
  white-space: nowrap;
}
</style>
