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

// Map links
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
    preparing: "Готовится",
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
        <VChip size="small" :color="statusColor" variant="elevated" class="ms-3">
          {{ statusName }}
        </VChip>
        <VSpacer />
        <VBtn icon variant="text" @click="dialog = false" color="white">
          <VIcon icon="bx-x" />
        </VBtn>
      </VCardTitle>

      <VCardText class="pa-4 pt-6">
        <VRow>
          <!-- Левая колонка: Детали клиента и доставки -->
          <VCol cols="12" md="6">
            <h3 class="text-h6 mb-3 d-flex align-center">
              <VIcon icon="bx-user" class="me-2" color="primary" /> О клиенте
            </h3>
            <VList density="compact" class="bg-transparent pa-0">
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-user-circle" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle class="font-weight-medium">{{ order.customer_name || 'Не указано' }}</VListItemTitle>
                <VListItemSubtitle>Имя</VListItemSubtitle>
              </VListItem>
              
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-phone" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>
                  <a :href="'tel:' + order.customer_phone" class="text-primary text-decoration-none">
                    {{ order.customer_phone || 'Не указано' }}
                  </a>
                </VListItemTitle>
                <VListItemSubtitle>Телефон</VListItemSubtitle>
              </VListItem>

              <VListItem class="px-0" v-if="order.telegram_username">
                <template #prepend><VIcon icon="bxl-telegram" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>
                  <a :href="'https://t.me/' + order.telegram_username" target="_blank" class="text-primary text-decoration-none">
                    @{{ order.telegram_username }}
                  </a>
                </VListItemTitle>
                <VListItemSubtitle>Telegram</VListItemSubtitle>
              </VListItem>
            </VList>

            <VDivider class="my-4" />

            <h3 class="text-h6 mb-3 d-flex align-center">
              <VIcon icon="bx-map-pin" class="me-2" color="primary" /> Доставка
            </h3>
            <p class="mb-2 font-weight-medium text-body-1">{{ order.delivery_address || 'Самовывоз / Не указано' }}</p>
            
            <div class="d-flex gap-2 mb-4" v-if="order.delivery_address">
              <VBtn :href="yandexMapLink" target="_blank" size="small" variant="tonal" color="success" prepend-icon="bx-map">
                Я.Карты
              </VBtn>
              <VBtn :href="twoGisLink" target="_blank" size="small" variant="tonal" color="primary" prepend-icon="bx-map-alt">
                2GIS
              </VBtn>
            </div>

            <VList density="compact" class="bg-transparent pa-0">
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-package" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ order.order_type || 'Не указан' }}</VListItemTitle>
                <VListItemSubtitle>Тип заказа</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0">
                <template #prepend><VIcon icon="bx-user" size="small" class="me-3 text-medium-emphasis" /></template>
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
              <VIcon icon="bx-time" class="me-2" color="primary" /> Тайминг (iiko)
            </h3>
            <VList density="compact" class="bg-transparent pa-0">
              <VListItem class="px-0">
                <VListItemTitle>{{ formatDate(order.iiko_creation_time || order.created_at) }}</VListItemTitle>
                <VListItemSubtitle>Создан</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0">
                <VListItemTitle>{{ formatDate(order.expected_time) }}</VListItemTitle>
                <VListItemSubtitle>Обещано</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0">
                <VListItemTitle>{{ formatDate(order.actual_time) }}</VListItemTitle>
                <VListItemSubtitle>Фактически выдано/доставлено</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0" v-if="order.delay_minutes > 0">
                <VListItemTitle class="text-error font-weight-bold">{{ order.delay_minutes }} мин.</VListItemTitle>
                <VListItemSubtitle>Опоздание</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0" v-else-if="order.actual_time">
                <VListItemTitle class="text-success font-weight-bold">
                  Вовремя
                </VListItemTitle>
                <VListItemSubtitle>Статус доставки</VListItemSubtitle>
              </VListItem>
              <VListItem 
                v-if="order.is_on_time"
                class="px-0"
              >
                <template #prepend>
                  <VIcon 
                    icon="bx-calendar-event" 
                    size="small" 
                    class="me-3 text-warning" 
                  />
                </template>
                <VListItemTitle class="text-warning font-weight-bold">
                  Предзаказ (на время)
                </VListItemTitle>
                <VListItemSubtitle>Тип времени</VListItemSubtitle>
              </VListItem>
              <VListItem class="px-0" v-if="order.admin_name">
                <template #prepend><VIcon icon="bx-user-check" size="small" class="me-3 text-medium-emphasis" /></template>
                <VListItemTitle>{{ order.admin_name }}</VListItemTitle>
                <VListItemSubtitle>Администратор (iiko)</VListItemSubtitle>
              </VListItem>
            </VList>

          </VCol>

          <!-- Правая колонка: Состав и финансы -->
          <VCol cols="12" md="6">
            <h3 class="text-h6 mb-3 d-flex align-center">
              <VIcon icon="bx-receipt" class="me-2" color="primary" /> Состав заказа
            </h3>
            
            <VTable density="compact" class="border rounded mb-4">
              <thead>
                <tr>
                  <th>Позиция</th>
                  <th class="text-center">Кол-во</th>
                  <th class="text-right">Сумма</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in order.items" :key="item.id">
                  <td>{{ item.product_name }}</td>
                  <td class="text-center">{{ item.quantity }}</td>
                  <td class="text-right">{{ item.total }} ₽</td>
                </tr>
                <tr v-if="!order.items || order.items.length === 0">
                  <td colspan="3" class="text-center text-medium-emphasis py-4">
                    Детали товаров отсутствуют
                  </td>
                </tr>
              </tbody>
            </VTable>

            <h3 class="text-h6 mb-3 d-flex align-center mt-6">
              <VIcon icon="bx-wallet" class="me-2" color="primary" /> Финансы
            </h3>

            <VCard variant="outlined" color="primary" class="pa-3 bg-var-theme-background">
              <div class="d-flex justify-space-between mb-2">
                <span class="text-body-2">Сумма товаров:</span>
                <span class="font-weight-medium">{{ order.total_amount }} ₽</span>
              </div>
              <div class="mb-2" v-if="order.total_discount > 0">
                <div class="d-flex justify-space-between text-error">
                  <span class="text-body-2">Скидка:</span>
                  <span class="font-weight-medium">-{{ order.total_discount }} ₽</span>
                </div>
                <div v-if="order.discounts_details && order.discounts_details.discounts" class="ms-4">
                  <div v-for="d in order.discounts_details.discounts" :key="d.name" class="d-flex justify-space-between text-caption text-error opacity-70">
                    <span>• {{ d.name }}</span>
                    <span>-{{ d.sum }} ₽</span>
                  </div>
                </div>
              </div>
              <div class="d-flex justify-space-between mb-2 text-warning" v-if="order.bonus_spent > 0">
                <span class="text-body-2">Оплачено бонусами:</span>
                <span class="font-weight-medium">-{{ order.bonus_spent }} ₽</span>
              </div>
              <VDivider class="my-2" />
              <div class="d-flex justify-space-between align-center">
                <span class="text-subtitle-1 font-weight-bold">Итого к оплате:</span>
                <span class="text-h5 font-weight-bold text-primary">{{ order.total_with_discount || order.total_amount - (order.total_discount || 0) }} ₽</span>
              </div>
              <div class="d-flex justify-space-between mt-2 text-medium-emphasis">
                <span class="text-caption">Способ оплаты:</span>
                <span class="text-caption font-weight-medium">{{ order.payment_method || 'Не указан' }}</span>
              </div>
            </VCard>

            <div class="d-flex align-center mt-4 text-success" v-if="order.bonus_accrued > 0">
              <VIcon icon="bx-gift" class="me-2" />
              <span class="text-body-2 font-weight-medium">Начислено бонусов: +{{ order.bonus_accrued }}</span>
            </div>

            <VAlert v-if="order.comment" type="info" variant="tonal" class="mt-4 text-body-2" density="compact" icon="bx-message-square-detail">
              <strong>Комментарий:</strong> {{ order.comment }}
            </VAlert>

            <div class="mt-4 text-right">
              <div class="text-caption text-medium-emphasis">
                iiko Order ID: {{ order.iiko_order_id || 'Нет' }}
              </div>
            </div>

          </VCol>
        </VRow>
      </VCardText>
      
      <VDivider />
      
      <VCardActions class="pa-4 bg-var-theme-background">
        <VSpacer />
        <VBtn variant="outlined" @click="dialog = false">Закрыть</VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
