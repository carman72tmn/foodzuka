<script setup>
import chartInfo from '@images/cards/chart-info.png'
import creditCardSuccess from '@images/cards/credit-card-success.png'
import creditCardWarning from '@images/cards/credit-card-warning.png'
import paypalError from '@images/cards/paypal-error.png'
import walletPrimary from '@images/cards/wallet-primary.png'

const transactions = [
  {
    amount: +82.6,
    paymentMethod: 'PayPal',
    description: 'Перевод средств',
    icon: paypalError,
    color: 'error',
  },
  {
    paymentMethod: 'Кошелек',
    amount: +270.69,
    description: 'Обед в МакД',
    icon: walletPrimary,
    color: 'primary',
  },
  {
    amount: +637.91,
    paymentMethod: 'Перевод',
    description: 'Возврат средств',
    icon: chartInfo,
    color: 'info',
  },
  {
    paymentMethod: 'Кредитная карта',
    amount: -838.71,
    description: 'Заказ еды',
    icon: creditCardSuccess,
    color: 'success',
  },
  {
    paymentMethod: 'Кошелек',
    amount: +203.33,
    description: 'Кофе Старбакс',
    icon: walletPrimary,
    color: 'primary',
  },
  {
    paymentMethod: 'Mastercard',
    amount: -92.45,
    description: 'Заказ еды',
    icon: creditCardWarning,
    color: 'warning',
  },
]

const moreList = [
  {
    title: 'Поделиться',
    value: 'Share',
  },
  {
    title: 'Обновить',
    value: 'Refresh',
  },
  {
    title: 'Изменить',
    value: 'Update',
  },
]
</script>

<template>
  <VCard title="Транзакции">
    <template #append>
      <MoreBtn :menu-list="moreList" />
    </template>

    <VCardText>
      <VList class="card-list">
        <VListItem
          v-for="item in transactions"
          :key="item.paymentMethod"
        >
          <template #prepend>
            <VAvatar
              rounded
              variant="tonal"
              :color="item.color"
              :image="item.icon"
              size="40"
            />
          </template>

          <VListItemSubtitle>
            {{ item.paymentMethod }}
          </VListItemSubtitle>
          <VListItemTitle>
            {{ item.description }}
          </VListItemTitle>

          <template #append>
            <VListItemAction>
              <span class="me-2">{{ item.amount > 0 ? `+${Math.abs(item.amount)} ₽` : `-${Math.abs(item.amount)} ₽` }}</span>
              <span class="text-disabled">RUB</span>
            </VListItemAction>
          </template>
        </VListItem>
      </VList>
    </VCardText>
  </VCard>
</template>

<style lang="scss" scoped>
  .card-list {
    --v-card-list-gap: 1.5rem;
  }
</style>
