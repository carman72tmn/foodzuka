<script setup>
const props = defineProps({
  transactions: {
    type: Array,
    default: () => [],
  },
})

function getPaymentIcon(method) {
  const m = (method || '').toLowerCase()
  if (m.includes('t bank') || m.includes('т-банк') || m.includes('карт')) return 'bx-credit-card'
  if (m.includes('наличн')) return 'bx-money'
  return 'bx-wallet'
}

function getPaymentColor(method) {
  const m = (method || '').toLowerCase()
  if (m.includes('t bank') || m.includes('т-банк')) return 'primary'
  if (m.includes('наличн')) return 'warning'
  return 'info'
}

function getStatusColor(status) {
  const s = (status || '').toLowerCase()
  if (s === 'delivered' || s === 'closed') return 'success'
  if (s === 'delivering') return 'info'
  if (s === 'cooking' || s === 'assembling' || s === 'preparing') return 'warning'
  if (s === 'cancelled') return 'error'
  return 'secondary'
}
</script>

<template>
  <VCard title="Последние заказы">
    <template #subtitle>
      <span class="text-caption">Свежие транзакции ресторана</span>
    </template>

    <template #append>
      <VBtn
        variant="text"
        size="small"
        to="/orders"
        color="primary"
      >
        Все заказы
      </VBtn>
    </template>

    <VCardText>
      <VList v-if="props.transactions.length" class="card-list">
        <VListItem
          v-for="item in props.transactions"
          :key="item.id"
          :to="`/orders`"
          class="px-1 py-1"
        >
          <template #prepend>
            <VAvatar
              rounded
              variant="tonal"
              :color="getPaymentColor(item.payment_method)"
              size="38"
            >
              <VIcon :icon="getPaymentIcon(item.payment_method)" size="20" />
            </VAvatar>
          </template>

          <VListItemTitle class="font-weight-medium text-body-2">
            #{{ item.order_number }} • {{ item.customer_name }}
          </VListItemTitle>

          <VListItemSubtitle class="text-caption d-flex align-center gap-1 mt-1">
            <span>{{ item.time }}</span>
            <span>•</span>
            <span>{{ item.order_type }}</span>
            <span>•</span>
            <VChip
              size="x-small"
              variant="tonal"
              :color="getStatusColor(item.status)"
            >
              {{ item.status_ru }}
            </VChip>
          </VListItemSubtitle>

          <template #append>
            <div class="text-end">
              <span class="font-weight-bold text-success text-body-2">
                +{{ Number(item.amount).toLocaleString('ru-RU') }} ₽
              </span>
            </div>
          </template>
        </VListItem>
      </VList>

      <div v-else class="text-center py-6 text-medium-emphasis">
        Нет недавних заказов
      </div>
    </VCardText>
  </VCard>
</template>

<style lang="scss">
.card-list {
  --v-card-list-gap: 0.85rem;
}
</style>
