<script setup>
import { ref, watch, computed } from "vue"

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  order: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(["update:modelValue"])

const dialog = computed({
  get: () => props.modelValue,
  set: (val) => emit("update:modelValue", val)
})

const formatDate = (dateString) => {
  if (!dateString) return "—"
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  }).format(date)
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
    new: "info",
    confirmed: "primary",
    preparing: "warning",
    cooking: "warning",
    ready: "success",
    delivering: "info",
    delivered: "success",
    cancelled: "error"
  }
  return statusColors[props.order?.status] || 'grey'
})

const statusName = computed(() => {
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
  return statusNames[props.order?.status] || props.order?.status
})
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
        <VAlert
          v-if="order.status === 'cancelled' && (order.cancellation_reason || order.comment)"
          type="error"
          variant="tonal"
          density="compact"
          class="mb-4 text-caption"
          icon="bx-error-circle"
        >
          <strong>Заказ отменен!</strong>
          <div v-if="order.cancellation_reason" class="mt-1">Причина: {{ order.cancellation_reason }}</div>
          <div v-if="order.cancelled_by" class="mt-1 opacity-70 italic text-right">Отменил: {{ order.cancelled_by }}</div>
        </VAlert>

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
                <VListItemTitle class="font-weight-bold">
                  <a :href="'tel:' + order.customer_phone" class="text-decoration-none text-primary">
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
              <p class="mb-1 fw-bold text-primary" v-if="order.city">г. {{ order.city }}</p>
              <p class="mb-2 text-body-1">{{ order.delivery_address || 'Самовывоз' }}</p>
              <div class="d-flex gap-2" v-if="order.delivery_address">
                <VBtn :href="yandexMapLink" target="_blank" size="x-small" variant="tonal" color="success">Яндекс</VBtn>
                <VBtn :href="twoGisLink" target="_blank" size="x-small" variant="tonal" color="primary">2GIS</VBtn>
              </div>
            </div>

            <VList density="compact" class="bg-transparent pa-0">
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-package" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ order.order_type || 'Доставка' }}</VListItemTitle>
                <VListItemSubtitle>Тип заказа</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0" v-if="order.courier_name">
                <template #prepend><VIcon icon="bx-cycling" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ order.courier_name }}</VListItemTitle>
                <VListItemSubtitle>Курьер</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0" v-if="order.delivery_zone">
                <template #prepend><VIcon icon="bx-map-alt" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ order.delivery_zone }}</VListItemTitle>
                <VListItemSubtitle>Зона доставки</VListItemSubtitle>
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
                  <th class="text-right">Сумма</th>
                </tr>
              </thead>
              <tbody>
                <template v-if="order.items && order.items.length > 0">
                  <template v-for="item in order.items" :key="item.id">
                    <tr>
                      <td class="font-weight-medium">
                        {{ item.product_name }}
                        <VChip v-if="item.size_name" size="x-small" variant="tonal" color="secondary" class="ms-1">
                          {{ item.size_name }}
                        </VChip>
                        <div v-if="item.comment" class="text-caption text-info mt-1 font-italic">
                          <VIcon icon="bx-comment-dots" size="12" class="me-1" /> {{ item.comment }}
                        </div>
                      </td>
                      <td class="text-center">{{ item.quantity }}</td>
                      <td class="text-right">{{ item.total }} ₽</td>
                    </tr>
                    <!-- Модификаторы -->
                    <tr v-for="mod in item.modifiers" :key="mod.iiko_id" class="text-caption opacity-70">
                      <td class="ps-6">• {{ mod.name }}</td>
                      <td class="text-center">{{ mod.amount }}</td>
                      <td class="text-right">{{ mod.sum ? mod.sum + ' ₽' : '—' }}</td>
                    </tr>
                  </template>
                </template>
                <template v-else-if="order.order_items_details && order.order_items_details.length > 0">
                  <template v-for="item in order.order_items_details" :key="item.id">
                    <tr>
                      <td class="font-weight-medium">
                        {{ item.name }}
                        <VChip v-if="item.size" size="x-small" variant="tonal" color="secondary" class="ms-1">
                            {{ typeof item.size === 'object' ? item.size.name : item.size }}
                        </VChip>
                      </td>
                      <td class="text-center">{{ item.amount }}</td>
                      <td class="text-right">{{ item.sum }} ₽</td>
                    </tr>
                    <tr v-for="mod in item.modifiers" :key="mod.id" class="text-caption opacity-70">
                      <td class="ps-6">• {{ mod.name }}</td>
                      <td class="text-center">{{ mod.amount }}</td>
                      <td class="text-right">{{ mod.sum ? mod.sum + ' ₽' : '—' }}</td>
                    </tr>
                    <tr v-if="item.comment" class="text-caption text-info">
                        <td colspan="3" class="ps-6 font-italic">{{ item.comment }}</td>
                    </tr>
                  </template>
                </template>
                <tr v-else>
                  <td colspan="3" class="text-center py-4 text-disabled">Нет данных о товарах</td>
                </tr>
              </tbody>
            </VTable>

            <VCard variant="outlined" color="primary" class="pa-4 bg-lightprimary">
              <div class="d-flex justify-space-between mb-2">
                <span>Сумма:</span>
                <span class="font-weight-bold">{{ order.total_amount }} ₽</span>
              </div>
              <div v-if="order.total_discount > 0" class="d-flex justify-space-between mb-2 text-error">
                <span>Скидка:</span>
                <span class="font-weight-bold">-{{ order.total_discount }} ₽</span>
              </div>
              <div v-if="order.bonus_spent > 0" class="d-flex justify-space-between mb-2 text-warning">
                <span>Бонусы:</span>
                <span class="font-weight-bold">-{{ order.bonus_spent }} ₽</span>
              </div>
              <VDivider class="my-2" />
              <div class="d-flex justify-space-between align-center">
                <span class="text-h6">Итого:</span>
                <span class="text-h5 font-weight-black text-primary">{{ order.total_with_discount || (order.total_amount - order.total_discount - order.bonus_spent) }} ₽</span>
              </div>
              <div class="mt-2 text-right d-flex gap-2 justify-end">
                <VChip size="x-small" variant="outlined">{{ order.payment_method || 'Способ оплаты не указан' }}</VChip>
                <VChip v-if="order.terminal_group_name" size="x-small" color="primary" variant="tonal">{{ order.terminal_group_name }}</VChip>
              </div>
            </VCard>

            <VAlert v-if="order.comment" type="info" variant="tonal" icon="bx-message-detail" class="mt-4 text-caption">
              <strong>Комментарий к заказу:</strong> {{ order.comment }}
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
