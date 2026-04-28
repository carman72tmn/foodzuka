<script setup>
import { ref, watch, computed } from "vue"
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
})

const emit = defineEmits(["update:modelValue"])

const dialog = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val)
})

const formatDate = (dateString, showOnlyTime = false) => {
  if (!dateString) return '';
  let dateToFormat = dateString;
  if (typeof dateString === 'string' && !dateString.endsWith('Z') && !dateString.includes('+')) {
    dateToFormat += 'Z';
  }
  return formatDateTime(dateToFormat, showOnlyTime ? { day: undefined, month: undefined, year: undefined } : {})
}

const yandexMapLink = computed(() => {
  if (!props.order?.delivery_address) return '#'
  return `https://yandex.ru/maps/?text=${encodeURIComponent(props.order.delivery_address)}`
})

const twoGisLink = computed(() => {
  if (!props.order?.delivery_address) return '#'
  return `https://2gis.ru/search/${encodeURIComponent(props.order.delivery_address)}`
})

const statusColor = computed(() => {
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
  
  return statusColors[props.order?.status] || 'grey'
})

// Честный перерасчет суммы без учета скидок на основе позиций заказа
const realBaseAmount = computed(() => {
  let sum = 0;
  const items = props.order?.order_items_details || props.order?.items || [];
  
  if (!items.length && props.order?.base_amount > 0) return props.order.base_amount;
  
  items.forEach(item => {
    const qty = parseFloat(item.amount || item.quantity || 1);
    const prc = parseFloat(item.price || 0);
    sum += qty * prc;

    if (item.modifiers && item.modifiers.length > 0) {
      item.modifiers.forEach(mod => {
        const mq = parseFloat(mod.amount || mod.quantity || 1);
        const mp = parseFloat(mod.price || 0);
        sum += mq * mp;
      });
    }
  });
  
  return sum > 0 ? sum : (props.order?.total_amount || 0);
});

const statusName = computed(() => {
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
  return statusNames[props.order?.status] || props.order?.status
})

const getStatusHistoryColor = (status) => {
  const colors = {
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
  return colors[status] || "grey"
}

const getStatusHistoryName = (status) => {
  const names = {
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
  return names[status] || status
}
</script>

<template>
  <VDialog v-model="dialog" max-width="900" scrollable>
    <VCard v-if="order">
      <VCardTitle class="d-flex align-center bg-primary text-white py-3">
        Заказ #{{ order.id }} 
        <span v-if="order.external_number" class="ms-2 text-caption opacity-80">(iiko: {{ order.external_number }})</span>
        <VChip size="small" :color="statusColor" variant="elevated" class="ms-3">
          {{ statusName }}
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

      <VCardText class="pa-4 pt-6">
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
              <div class="pa-3 rounded bg-lightprimary border-primary border-opacity-25 mb-3" style="border: 1px solid">
                <p class="mb-0 text-body-1 font-weight-medium line-height-1-4">
                  {{ order.delivery_address || 'Самовывоз' }}
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
                <VListItemTitle>{{ order.courier_name || 'Не назначен' }}</VListItemTitle>
                <VListItemSubtitle>Курьер</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0" v-if="order.delivery_zone">
                <template #prepend><VIcon icon="bx-map-alt" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ order.delivery_zone }}</VListItemTitle>
                <VListItemSubtitle>Зона доставки</VListItemSubtitle>
              </VListItem>
            </VList>

            <VDivider class="my-4" />

            <h3 class="text-h6 mb-3 d-flex align-center">
              <VIcon icon="bx-time" class="me-2" color="primary" /> История статусов (Тайминг)
            </h3>
            
            <div v-if="order.status_history && order.status_history.length" class="mt-2 mb-4">
              <div 
                v-for="(history, idx) in order.status_history" 
                :key="idx"
                class="pa-2 mb-1 rounded-lg"
                :style="`border-left: 6px solid rgb(var(--v-theme-${getStatusHistoryColor(history.status)})) !important; background-color: rgba(var(--v-theme-${getStatusHistoryColor(history.status)}), 0.08);`"
              >
                <div class="text-caption font-weight-black text-uppercase text-high-emphasis mb-1" style="line-height: 1">
                  {{ getStatusHistoryName(history.status) }}
                </div>
                <div v-if="history.comment && !history.comment.includes('Автоматическое')" class="text-caption text-medium-emphasis mb-1" style="font-size: 0.75rem !important; line-height: 1.2">
                  <VIcon icon="bx-sync" size="12" class="me-1" /> {{ history.comment }}
                </div>
                <div class="text-caption text-primary font-weight-bold" style="font-size: 0.75rem !important; line-height: 1">
                  {{ formatDate(history.time, true) }}
                </div>
              </div>
            </div>
            
            <VList density="compact" class="bg-transparent pa-0" v-else>
              <VListItem class="px-0">
                <VListItemTitle>{{ formatDate(order.created_at) }}</VListItemTitle>
                <VListItemSubtitle>Время заказа</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0" v-if="order.expected_time">
                <VListItemTitle class="font-weight-bold text-warning">{{ formatDate(order.expected_time) }}</VListItemTitle>
                <VListItemSubtitle>Обещано клиенту</VListItemSubtitle>
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
                      <td class="text-center">{{ item.price }} ₽</td>
                      <td class="text-right font-weight-bold">{{ item.sum || (item.amount * item.price) }} ₽</td>
                    </tr>
                    <!-- Модификаторы из деталей iiko -->
                    <tr v-for="(mod, modIdx) in item.modifiers" :key="mod.id || mod.productId || 'mod-det-' + modIdx" class="text-caption opacity-80">
                      <td class="ps-6">• {{ mod.name }}</td>
                      <td class="text-center">{{ mod.amount }}</td>
                      <td class="text-center">{{ mod.price }} ₽</td>
                      <td class="text-right">{{ (mod.sum || (mod.amount * mod.price)) ? (mod.sum || (mod.amount * mod.price)) + ' ₽' : '—' }}</td>
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
                      <td class="text-center">{{ item.price }} ₽</td>
                      <td class="text-right font-weight-bold">{{ item.total || (item.quantity * item.price) }} ₽</td>
                    </tr>
                    <tr v-for="(mod, modIdx) in item.modifiers" :key="mod.iiko_id || mod.id || 'mod-' + modIdx" class="text-caption opacity-70">
                      <td class="ps-6">• {{ mod.name }}</td>
                      <td class="text-center">{{ mod.amount }}</td>
                      <td class="text-center">{{ mod.price }} ₽</td>
                      <td class="text-right">{{ (mod.sum || (mod.amount * mod.price)) ? (mod.sum || (mod.amount * mod.price)) + ' ₽' : '—' }}</td>
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
                <span class="font-weight-bold">{{ realBaseAmount }} ₽</span>
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
</style>
