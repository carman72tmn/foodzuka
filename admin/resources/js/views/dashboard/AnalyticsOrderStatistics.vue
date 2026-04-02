<script setup>
import { useTheme } from 'vuetify'
import { hexToRgb } from '@core/utils/colorConverter'

const vuetifyTheme = useTheme()

const series = [
  45,
  80,
  20,
  40,
]

const chartOptions = computed(() => {
  const currentTheme = vuetifyTheme.current.value.colors
  const variableTheme = vuetifyTheme.current.value.variables
  const secondaryTextColor = `rgba(${ hexToRgb(String(currentTheme['on-surface'])) },${ variableTheme['medium-emphasis-opacity'] })`
  const primaryTextColor = `rgba(${ hexToRgb(String(currentTheme['on-surface'])) },${ variableTheme['high-emphasis-opacity'] })`
  
  return {
    chart: {
      sparkline: { enabled: true },
      animations: { enabled: false },
    },
    stroke: {
      width: 6,
      colors: [currentTheme.surface],
    },
    legend: { show: false },
    tooltip: { enabled: false },
    dataLabels: { enabled: false },
    labels: [
      'Суши',
      'Пицца',
      'Напитки',
      'Десерты',
    ],
    colors: [
      currentTheme.success,
      currentTheme.primary,
      currentTheme.secondary,
      currentTheme.info,
    ],
    grid: {
      padding: {
        top: -7,
        bottom: 5,
      },
    },
    states: {
      hover: { filter: { type: 'none' } },
      active: { filter: { type: 'none' } },
    },
    plotOptions: {
      pie: {
        expandOnClick: false,
        donut: {
          size: '75%',
          labels: {
            show: true,
            name: {
              offsetY: 17,
              fontSize: '13px',
              color: secondaryTextColor,
              fontFamily: 'Public Sans',
            },
            value: {
              offsetY: -17,
              fontSize: '18px',
              color: primaryTextColor,
              fontFamily: 'Public Sans',
              fontWeight: 500,
            },
            total: {
              show: true,
              label: 'Неделя',
              fontSize: '13px',
              lineHeight: '18px',
              formatter: () => '38%',
              color: secondaryTextColor,
              fontFamily: 'Public Sans',
            },
          },
        },
      },
    },
  }
})

const orders = [
  {
    amount: '82.5k',
    title: 'Пицца',
    avatarColor: 'primary',
    subtitle: 'Пепперони, Маргарита',
    avatarIcon: 'bx-pizza',
  },
  {
    amount: '23.8k',
    title: 'Суши',
    avatarColor: 'success',
    subtitle: 'Филадельфия, Калифорния',
    avatarIcon: 'bx-bowl-rice',
  },
  {
    amount: 849,
    title: 'Напитки',
    avatarColor: 'info',
    subtitle: 'Кола, Соки, Чай',
    avatarIcon: 'bx-drink',
  },
  {
    amount: 99,
    title: 'Десерты',
    avatarColor: 'secondary',
    subtitle: 'Чизкейк, Тирамису',
    avatarIcon: 'bx-cake',
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
  <VCard>
    <VCardItem>
      <VCardTitle>
        Статистика заказов
      </VCardTitle>
      <VCardSubtitle>42.82k Общих продаж</VCardSubtitle>

      <template #append>
        <MoreBtn :menu-list="moreList" />
      </template>
    </VCardItem>

    <VCardText>
      <div class="d-flex align-center justify-space-between mb-6">
        <div class="">
          <h3 class="text-h3 mb-1">
            8,258
          </h3>
          <div class="text-caption text-medium-emphasis">
            Всего заказов
          </div>
        </div>

        <div>
          <VueApexCharts
            type="donut"
            :height="120"
            width="100"
            :options="chartOptions"
            :series="series"
          />
        </div>
      </div>

      <VList class="card-list">
        <VListItem
          v-for="order in orders"
          :key="order.title"
        >
          <template #prepend>
            <VAvatar
              size="40"
              rounded
              variant="tonal"
              :color="order.avatarColor"
            >
              <VIcon :icon="order.avatarIcon" />
            </VAvatar>
          </template>

          <VListItemTitle class="font-weight-medium">
            {{ order.title }}
          </VListItemTitle>
          <VListItemSubtitle class="text-body-2">
            {{ order.subtitle }}
          </VListItemSubtitle>

          <template #append>
            <span>{{ order.amount }}</span>
          </template>
        </VListItem>
      </VList>
    </VCardText>
  </VCard>
</template>

<style lang="scss">
.card-list {
  --v-card-list-gap: 1.25rem;
}
</style>
