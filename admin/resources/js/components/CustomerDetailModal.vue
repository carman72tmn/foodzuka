<template>
  <VDialog
    v-model="isVisible"
    max-width="1200px"
    scrollable
    transition="dialog-bottom-transition"
  >
    <VCard 
      class="customer-detail-card overflow-hidden"
      :class="{ 'high-risk-border': customer?.is_high_risk }"
    >
      <!-- Toolbar / Header -->
      <VToolbar
        :color="customer?.is_high_risk ? '#ff4d4f' : 'primary'"
        class="px-4 transition-all"
        :class="{ 'high-risk-header': customer?.is_high_risk }"
        elevation="0"
      >
        <VAvatar
          size="40"
          color="white"
          variant="tonal"
          class="me-3"
        >
          <VImg :src="guestAvatar" />
        </VAvatar>
        
        <div class="d-flex flex-column">
          <span class="text-h6 font-weight-bold text-white line-height-1">
            {{ customer?.name || 'Гость' }} {{ customer?.surname || '' }}
          </span>
          <span class="text-caption text-white opacity-80">
            {{ customer?.phone || 'Нет телефона' }}
          </span>
        </div>

        <VSpacer />

        <div class="d-flex ga-2">
          <VChip
            v-if="customer?.is_new_guest && (customer?.total_orders_count || 0) <= 1"
            color="success"
            size="small"
            class="font-weight-bold"
            variant="elevated"
          >
            НОВЫЙ ГОСТЬ
          </VChip>

          <VChip
            v-if="isLongTimeAgo(customer?.last_order_date)"
            color="warning"
            size="small"
            class="font-weight-bold"
            variant="elevated"
            prepend-icon="ri-history-line"
          >
            ВЕРНУЛСЯ
          </VChip>

          <VChip
            v-if="customer?.is_high_risk"
            color="white"
            size="small"
            class="font-weight-bold pulse-animation"
            variant="elevated"
            prepend-icon="ri-error-warning-fill"
          >
            ВЫСОКИЙ РИСК
          </VChip>
        </div>

        <VBtn
          icon="ri-close-line"
          variant="text"
          color="white"
          @click="close"
        />
      </VToolbar>

      <VDivider />

      <VCardText class="pa-0 flex-grow-1">
        <VRow no-gutters class="fill-height">
          <!-- Sidebar -->
          <VCol
            cols="12"
            md="3"
            class="bg-grey-lighten-5 border-e d-flex flex-column pa-4"
          >
            <div class="sidebar-analytics-box mb-6 pa-4 rounded-lg bg-white elevation-1">
              <div class="text-overline text-disabled mb-2">
                Общая аналитика
              </div>
              
              <div class="mb-4">
                <div class="text-caption text-muted">
                  LTV (Выручка)
                </div>
                <div class="text-h6 font-weight-bold text-primary">
                  {{ formatPrice(customer?.total_purchases_sum || customer?.total_orders_amount || 0) }}
                </div>
              </div>

              <div class="mb-4">
                <div class="text-caption text-muted">Средний чек</div>
                <div class="text-h6 font-weight-bold">
                  {{ formatPrice(analytics?.average_check || 0) }}
                </div>
              </div>

              <div class="mb-4">
                <div class="text-caption text-muted">Всего заказов</div>
                <div class="text-h6 font-weight-bold">
                  {{ customer?.total_orders_count || 0 }}
                </div>
              </div>

              <div v-if="customer?.last_order_date">
                <div class="text-caption text-muted">Последний визит</div>
                <div class="text-body-2 font-weight-medium">
                  {{ formatDate(customer?.last_order_date) }}
                </div>
              </div>

              <!-- Barcode Section -->
              <div class="mt-6 text-center barcode-container pa-2 rounded bg-white border">
                <div class="text-overline text-disabled mb-1">Карта лояльности</div>
                <canvas id="barcode-canvas" />
                <div class="text-caption font-weight-bold mt-1">
                  {{ customer?.card_number || (customer?.iiko_card_numbers?.length ? customer?.iiko_card_numbers[0] : 'НЕТ КАРТЫ') }}
                </div>
              </div>
            </div>

            <VBtn
              color="primary"
              block
              variant="tonal"
              prepend-icon="bx-sync"
              :loading="isSyncing"
              class="mt-auto"
              @click="syncFullData"
            >
              Синхронизировать
            </VBtn>
          </VCol>

          <!-- Main Content -->
          <VCol cols="12" md="9" class="d-flex flex-column">
            <VTabs
              v-model="activeTab"
              color="primary"
              align-tabs="start"
              density="compact"
              class="border-b"
            >
              <VTab
                v-for="tab in tabs"
                :key="tab.id"
                :value="tab.id"
                class="text-none"
              >
                <VIcon :icon="tab.icon" start />
                {{ tab.title }}
              </VTab>
            </VTabs>

            <VWindow v-model="activeTab" class="flex-grow-1 overflow-y-auto" style="height: 600px;">
              <!-- 1. Анкета -->
              <VWindowItem value="profile">
                <VContainer class="pa-6">
                  <VRow>
                    <VCol 
                      cols="12" 
                      md="4"
                    >
                      <VTextField 
                        v-model="form.surname" 
                        label="Фамилия" 
                        variant="outlined" 
                        density="compact" 
                      />
                    </VCol>
                    <VCol 
                      cols="12" 
                      md="4"
                    >
                      <VTextField 
                        v-model="form.name" 
                        label="Имя" 
                        variant="outlined" 
                        density="compact" 
                      />
                    </VCol>
                    <VCol 
                      cols="12" 
                      md="4"
                    >
                      <VTextField 
                        v-model="form.middleName" 
                        label="Отчество" 
                        variant="outlined" 
                        density="compact" 
                      />
                    </VCol>

                    <VCol 
                      cols="12" 
                      md="6"
                    >
                      <VTextField 
                        :model-value="customer?.phone" 
                        label="Основной телефон (iiko)" 
                        variant="outlined" 
                        density="compact" 
                        readonly 
                        bg-color="grey-lighten-4" 
                      />
                    </VCol>
                    <VCol 
                      cols="12" 
                      md="6"
                    >
                      <VSelect
                        v-model="form.gender"
                        label="Пол"
                        :items="[
                          { title: 'Мужской', value: 'Мужской' },
                          { title: 'Женский', value: 'Женский' },
                          { title: 'Не указан', value: 'NotSpecified' }
                        ]"
                        variant="outlined"
                        density="compact"
                      />
                    </VCol>

                    <VCol 
                      cols="12" 
                      md="6"
                    >
                      <VTextField 
                        v-model="form.email" 
                        label="Email" 
                        variant="outlined" 
                        density="compact" 
                      />
                    </VCol>
                    <VCol 
                      cols="12" 
                      md="6"
                    >
                      <VTextField 
                        v-model="form.birthday" 
                        label="Дата рождения" 
                        type="date" 
                        variant="outlined" 
                        density="compact" 
                      />
                    </VCol>

                    <!-- Дополнительные поля -->
                    <VCol 
                      cols="12" 
                      md="4"
                    >
                      <VTextField 
                        v-model="form.referrer" 
                        label="Рекомендатель (ID)" 
                        variant="outlined" 
                        density="compact" 
                      />
                    </VCol>
                    <VCol 
                      cols="12" 
                      md="4"
                    >
                      <VTextField 
                        v-model="form.registrationSource" 
                        label="Источник регистрации" 
                        variant="outlined" 
                        density="compact" 
                      />
                    </VCol>
                    <VCol 
                      cols="12" 
                      md="4"
                    >
                      <VTextField 
                        v-model="form.registeredOrganization" 
                        label="Организация" 
                        variant="outlined" 
                        density="compact" 
                      />
                    </VCol>

                    <VCol cols="12">
                      <VTextarea 
                        v-model="form.iikoNotes" 
                        label="Заметки iiko / Комментарий" 
                        variant="outlined" 
                        density="compact" 
                        rows="2" 
                      />
                    </VCol>
                  </VRow>

                  <!-- Дополнительные телефоны -->
                  <div class="mt-6 border rounded-lg pa-4 bg-grey-lighten-5">
                    <div class="text-subtitle-2 font-weight-bold mb-3 d-flex align-center">
                      <VIcon icon="ri-phone-line" size="small" class="me-2" />
                      Дополнительные телефоны
                    </div>
                    
                    <VRow v-if="localPhones.length" class="mb-2">
                      <VCol v-for="p in localPhones" :key="p.id" cols="auto">
                        <VChip
                          closable
                          color="info"
                          variant="tonal"
                          @click:close="deletePhone(p.id)"
                        >
                          {{ p.phone }}
                        </VChip>
                      </VCol>
                    </VRow>

                    <div class="d-flex gap-2">
                      <VTextField
                        v-model="newPhone"
                        placeholder="+7 (___) ___-__-__"
                        variant="outlined"
                        density="compact"
                        hide-details
                        @keyup.enter="addPhone"
                      />
                      <VBtn
                        icon="ri-add-line"
                        color="success"
                        variant="elevated"
                        :loading="isAddingPhone"
                        @click="addPhone"
                      />
                    </div>
                  </div>

                  <!-- Карты iiko -->
                  <div class="mt-6" v-if="customer?.iiko_card_numbers?.length">
                    <div class="text-subtitle-2 font-weight-bold mb-2 d-flex align-center">
                      <VIcon icon="ri-id-card-line" size="small" class="me-2" />
                      Карты лояльности iiko
                    </div>
                    <div class="d-flex flex-wrap gap-2">
                      <VChip
                        v-for="card in customer.iiko_card_numbers"
                        :key="card"
                        size="small"
                        variant="outlined"
                      >
                        {{ card }}
                      </VChip>
                    </div>
                  </div>

                  <!-- Категории iiko -->
                  <div class="mt-6">
                    <div class="text-subtitle-2 font-weight-bold mb-2 d-flex align-center">
                      <VIcon icon="ri-price-tag-3-line" size="small" class="me-2" />
                      Категории iiko
                    </div>
                    <div class="d-flex flex-wrap gap-2 align-center">
                      <template v-for="cat in form.iikoCategories" :key="cat">
                        <VMenu location="bottom">
                          <template #activator="{ props: activatorProps }">
                            <VChip
                              v-bind="activatorProps"
                              size="small"
                              color="secondary"
                              variant="tonal"
                              class="cursor-pointer"
                            >
                              {{ cat }}
                            </VChip>
                          </template>
                          <VList density="compact">
                            <VListItem
                              prepend-icon="ri-delete-bin-line"
                              title="Удалить из категории"
                              color="error"
                              @click="removeCategory(cat)"
                            />
                          </VList>
                        </VMenu>
                      </template>
                      
                      <VMenu v-model="categoryMenu" :close-on-content-click="false">
                        <template #activator="{ props: menuProps }">
                          <VBtn
                            v-bind="menuProps"
                            icon="ri-add-line"
                            size="x-small"
                            color="primary"
                            variant="tonal"
                          />
                        </template>
                        <VList density="compact" max-height="300" min-width="200">
                          <VListItem
                            v-for="cat in availableCategories"
                            :key="cat.id"
                            :title="cat.name"
                            @click="addCategory(cat.name)"
                          />
                          <VListItem v-if="!availableCategories.length" title="Нет доступных категорий" disabled />
                        </VList>
                      </VMenu>
                    </div>
                  </div>

                  <div class="d-flex justify-end mt-6">
                    <VBtn color="primary" @click="saveProfile">Сохранить изменения</VBtn>
                  </div>
                </VContainer>
              </VWindowItem>

              <!-- 2. Бонусы -->
              <VWindowItem value="bonuses">
                <VContainer class="pa-6">
                  <VRow>
                    <VCol cols="12" md="4">
                      <VCard variant="tonal" color="primary" class="pa-4 text-center">
                        <div class="text-h4 font-weight-bold">{{ customer?.bonus_points || 0 }}</div>
                        <div class="text-caption">Баланс баллов</div>
                      </VCard>
                    </VCol>
                  </VRow>
                  
                  <VRow class="mt-4">
                    <VCol cols="12">
                      <VCard variant="outlined" class="pa-4">
                        <div class="text-subtitle-1 font-weight-bold mb-3">Ручное изменение баланса</div>
                        <VRow>
                          <VCol cols="12" md="4">
                            <VTextField
                              v-model="bonusAdjustment.amount"
                              label="Сумма (±)"
                              type="number"
                              variant="outlined"
                              density="compact"
                              hint="Положительная для начисления, отрицательная для списания"
                              persistent-hint
                            />
                          </VCol>
                          <VCol cols="12" md="6">
                            <VTextField
                              v-model="bonusAdjustment.comment"
                              label="Комментарий для iiko"
                              variant="outlined"
                              density="compact"
                            />
                          </VCol>
                          <VCol cols="12" md="2" class="d-flex align-center">
                            <VBtn
                              color="primary"
                              block
                              :loading="isAdjustingBonuses"
                              :disabled="!bonusAdjustment.amount"
                              @click="adjustBonuses"
                            >
                              ОК
                            </VBtn>
                          </VCol>
                        </VRow>
                      </VCard>
                    </VCol>
                  </VRow>

                  <h3 class="text-h6 mt-6 mb-4">История транзакций</h3>
                  <VDataTable
                    :headers="[
                      { title: 'Дата', key: 'transaction_date' },
                      { title: 'Тип', key: 'type' },
                      { title: 'Сумма', key: 'amount', align: 'end' },
                      { title: 'Комментарий', key: 'comment' }
                    ]"
                    :items="bonusHistory"
                    density="compact"
                    class="elevation-0 border rounded"
                  >
                    <template #item.transaction_date="{ value }">{{ formatDate(value) }}</template>
                    <template #item.amount="{ value, item }">
                      <span :class="item.type === 'accrual' ? 'text-success' : 'text-error'">
                        {{ item.type === 'accrual' ? '+' : '-' }}{{ value }}
                      </span>
                    </template>
                  </VDataTable>
                </VContainer>
              </VWindowItem>

              <!-- 3. Заказы -->
              <VWindowItem value="orders">
                <VContainer class="pa-6">
                  <VDataTable
                    :headers="[
                      { title: 'Дата', key: 'date' },
                      { title: 'Сумма', key: 'sum', align: 'end' },
                      { title: 'Статус', key: 'status' },
                      { title: 'Тип', key: 'order_type' }
                    ]"
                    :items="ordersHistory"
                    density="compact"
                    class="elevation-0 border rounded"
                  >
                    <template #item.date="{ value }">{{ formatDate(value) }}</template>
                    <template #item.sum="{ value }">{{ formatPrice(value) }}</template>
                  </VDataTable>
                </VContainer>
              </VWindowItem>

              <!-- 4. Аналитика -->
              <VWindowItem value="analytics">
                <VContainer class="pa-6">
                  <VRow v-if="!olapLoading && !olapError">
                    <VCol cols="12" md="4" v-for="(stat, idx) in [
                      { label: 'Всего выручка (LTV)', value: formatPrice(analytics.total_sum || 0) },
                      { label: 'Средний чек', value: formatPrice(analytics.average_check || 0) },
                      { label: 'Заказов всего', value: analytics.total_count || 0 },
                      { label: 'Частота заказов (дн)', value: analytics.frequency_days || '-' },
                      { label: 'Дней с последнего заказа', value: analytics.days_since_last_order || '-' }
                    ]" :key="idx">
                      <VCard variant="outlined" class="pa-4">
                        <div class="text-caption text-muted">{{ stat.label }}</div>
                        <div class="text-h6 font-weight-bold">{{ stat.value }}</div>
                      </VCard>
                    </VCol>
                  </VRow>
                  <div v-else-if="olapLoading" class="text-center py-10">
                    <VProgressCircular indeterminate color="primary" />
                    <div class="mt-2 text-caption">Загрузка OLAP-аналитики...</div>
                  </div>
                  <VAlert v-else type="warning" variant="tonal" class="mt-4">
                    {{ olapError }}
                  </VAlert>
                </VContainer>
              </VWindowItem>

              <!-- 5. Риски -->
              <VWindowItem value="risks">
                <VContainer class="pa-6">
                  <VRow>
                    <VCol cols="12">
                      <VSwitch v-model="form.isHighRisk" label="Статус высокого риска" color="error" />
                      <VTextarea v-model="form.riskReason" label="Причина риска" variant="outlined" density="compact" rows="3" />
                    </VCol>
                  </VRow>
                  <div class="d-flex justify-end mt-4">
                    <VBtn color="error" @click="saveProfile">Обновить статус</VBtn>
                  </div>
                </VContainer>
              </VWindowItem>

              <!-- 6. Адреса -->
              <VWindowItem value="addresses">
                <VContainer class="pa-6">
                  <div class="d-flex justify-space-between align-center mb-4">
                    <h3 class="text-h6 mb-0">Связанные адреса</h3>
                    <VBtn
                      color="info"
                      variant="tonal"
                      size="small"
                      prepend-icon="ri-sync-line"
                      :loading="isSyncing"
                      @click="syncFullData"
                    >
                      Обновить из iiko
                    </VBtn>
                  </div>
                  <VList v-if="guestAddresses.length" density="compact">
                    <VListItem v-for="(addr, idx) in guestAddresses" :key="idx" :title="addr.address || addr" prepend-icon="ri-map-pin-2-line">
                      <template #subtitle v-if="addr.last_used_at">
                        Использован: {{ formatDate(addr.last_used_at) }}
                      </template>
                    </VListItem>
                  </VList>
                  <div v-else class="text-center py-10 text-disabled">Адреса не найдены</div>
                </VContainer>
              </VWindowItem>

              <!-- 7. Инфо -->
              <VWindowItem value="notifications">
                <VContainer class="pa-6">
                  <VList>
                    <VListItem title="Рекламная рассылка" :subtitle="customer?.is_marketing_consented ? 'Подписан' : 'Отписан'">
                      <template #prepend>
                        <VIcon :icon="customer?.is_marketing_consented ? 'ri-checkbox-circle-line' : 'ri-close-circle-line'" :color="customer?.is_marketing_consented ? 'success' : 'error'" />
                      </template>
                    </VListItem>
                    <VListItem title="Системные уведомления" subtitle="Активны (статусы заказов)">
                      <template #prepend>
                        <VIcon icon="ri-checkbox-circle-line" color="success" />
                      </template>
                    </VListItem>
                  </VList>
                </VContainer>
              </VWindowItem>

              <!-- 8. Лог -->
              <VWindowItem value="extra">
                <VContainer class="pa-6">
                  <pre class="bg-grey-darken-4 text-white pa-4 rounded text-caption overflow-x-auto">{{ JSON.stringify(customer, null, 2) }}</pre>
                </VContainer>
              </VWindowItem>

              <!-- 9. Локальные заказы -->
              <VWindowItem value="local-orders">
                <VContainer class="pa-6">
                  <div class="d-flex justify-space-between align-center mb-4">
                    <h3 class="text-subtitle-1 font-weight-bold mb-0">История локальных заказов (База)</h3>
                    <div class="d-flex align-center ga-2">
                      <VBtn
                        icon="ri-arrow-left-s-line"
                        variant="tonal"
                        size="small"
                        :disabled="localOrdersPage === 0 || localOrdersLoading"
                        @click="prevLocalPage"
                      />
                      <span class="text-caption font-weight-bold">Стр. {{ localOrdersPage + 1 }}</span>
                      <VBtn
                        icon="ri-arrow-right-s-line"
                        variant="tonal"
                        size="small"
                        :disabled="localOrders.length <= 7 || localOrdersLoading"
                        @click="nextLocalPage"
                      />
                    </div>
                  </div>

                  <VProgressLinear
                    v-if="localOrdersLoading"
                    indeterminate
                    color="primary"
                    height="2"
                    class="mb-4"
                  />

                  <VTable density="compact" class="border rounded-lg overflow-hidden">
                    <thead>
                      <tr>
                        <th class="text-left py-3">Дата / ID</th>
                        <th class="text-left py-3">Позиции</th>
                        <th class="text-right py-3">Сумма</th>
                        <th class="text-center py-3">Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="order in localOrders.slice(0, 7)" :key="order.id">
                        <td class="py-2">
                          <div class="font-weight-bold">{{ formatDate(order.created_at) }}</div>
                          <div class="text-caption text-disabled">#{{ order.id }}</div>
                        </td>
                        <td class="py-2">
                          <div class="text-caption line-height-1" v-for="item in order.items" :key="item.id">
                            {{ item.name }} x{{ item.amount }}
                          </div>
                        </td>
                        <td class="text-right py-2 font-weight-bold">
                          {{ formatPrice(order.total_sum) }}
                        </td>
                        <td class="text-center py-2">
                          <VChip
                            size="x-small"
                            :color="order.status === 'cancelled' ? 'error' : (order.status === 'delivered' ? 'success' : 'info')"
                            variant="tonal"
                          >
                            {{ order.status }}
                          </VChip>
                        </td>
                      </tr>
                      <tr v-if="!localOrders.length && !localOrdersLoading">
                        <td colspan="4" class="text-center py-10 text-disabled">
                          Заказы не найдены
                        </td>
                      </tr>
                    </tbody>
                  </VTable>
                </VContainer>
              </VWindowItem>
            </VWindow>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>
  </VDialog>
</template>

<script setup>
import {
  ref,
  computed,
  watch,
  onMounted,
  nextTick,
} from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import JsBarcode from 'jsbarcode'
import { isLongTimeAgo } from '@/utils/date'

const props = defineProps({
  modelValue: Boolean,
  customer: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['update:modelValue', 'updated'])

const toast = useToast()

const activeTab = ref('profile')
const isSyncing = ref(false)
const olapLoading = ref(false)
const olapError = ref(null)
const analytics = ref({})
const localOrders = ref([])
const localOrdersLoading = ref(false)
const localOrdersPage = ref(0)

const loadLocalOrders = async () => {
  if (!props.customer?.phone) return
  localOrdersLoading.value = true
  try {
    const skip = localOrdersPage.value * 7
    const response = await fetch(`/api/v1/orders/by-phone/${props.customer.phone}?limit=8&skip=${skip}`)
    if (!response.ok) throw new Error('Failed to fetch local orders')
    localOrders.value = await response.json()
  } catch (e) {
    console.warn('Local orders fetch failed', e)
  } finally {
    localOrdersLoading.value = false
  }
}

const prevLocalPage = () => {
  if (localOrdersPage.value > 0) {
    localOrdersPage.value--
    loadLocalOrders()
  }
}

const nextLocalPage = () => {
  if (localOrders.value.length > 7) {
    localOrdersPage.value++
    loadLocalOrders()
  }
}

const bonusHistory = ref([])
const ordersHistory = ref([])
const guestAddresses = ref([])
const isAdjustingBonuses = ref(false)
const bonusAdjustment = ref({
  amount: 0,
  comment: 'Ручная корректировка из админ-панели'
})

const allIikoCategories = ref([])
const categoryMenu = ref(false)

const form = ref({
  name: '',
  surname: '',
  middleName: '',
  email: '',
  birthday: '',
  gender: 'NotSpecified',
  referrer: '',
  registrationSource: '',
  registeredOrganization: '',
  iikoNotes: '',
  isHighRisk: false,
  riskReason: '',
  iikoCategories: [],
})

const localPhones = ref([])
const newPhone = ref('')
const isAddingPhone = ref(false)

const availableCategories = computed(() => {
  return allIikoCategories.value.filter(cat => !form.value.iikoCategories.includes(cat.name))
})

const tabs = [
  { id: 'profile', title: 'Анкета', icon: 'ri-id-card-line' },
  { id: 'bonuses', title: 'Бонусы', icon: 'ri-coin-line' },
  { id: 'orders', title: 'Заказы', icon: 'ri-shopping-bag-line' },
  { id: 'analytics', title: 'Аналитика', icon: 'ri-bar-chart-line' },
  { 
    id: 'risks', 
    title: 'Риски', 
    icon: props.customer?.is_high_risk ? 'ri-error-warning-fill' : 'ri-error-warning-line',
    color: props.customer?.is_high_risk ? 'error' : ''
  },
  { id: 'addresses', title: 'Адреса', icon: 'ri-map-pin-line' },
  { id: 'notifications', title: 'Инфо', icon: 'ri-notification-line' },
  { id: 'local-orders', title: 'Локальные заказы', icon: 'ri-history-line' },
  { id: 'extra', title: 'Лог', icon: 'ri-code-line' },
]

const isVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const guestAvatar = computed(() => {
  const name = props.customer?.name || 'G'
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=c5a059&color=000&bold=true&size=128`
})

const close = () => {
  isVisible.value = false
}

const generateBarcode = () => {
  nextTick(() => {
    const cardNumber = props.customer?.card_number || (props.customer?.iiko_card_numbers?.length ? props.customer?.iiko_card_numbers[0] : null)
    if (cardNumber) {
      JsBarcode("#barcode-canvas", cardNumber, {
        format: "CODE128",
        width: 1.5,
        height: 40,
        displayValue: false,
        margin: 0,
        background: "transparent",
      })
    }
  })
}

const parseAddresses = () => {
  if (!props.customer?.addresses) {
    guestAddresses.value = []
    return
  }

  if (Array.isArray(props.customer.addresses)) {
    guestAddresses.value = props.customer.addresses
    return
  }

  try {
    guestAddresses.value = JSON.parse(props.customer.addresses)
  } catch {
    guestAddresses.value = [props.customer.addresses]
  }
}

const loadOlapStats = async () => {
  if (!props.customer?.id) return
  olapLoading.value = true
  olapError.value = null
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/olap-stats`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    
    const data = await response.json()
    if (data.error) {
      olapError.value = data.error === 'REST_API_LICENSE_REQUIRED'
        ? 'Отсутствует лицензия iiko Resto API'
        : data.message
    } else {
      analytics.value = data
    }
  } catch (error) {
    olapError.value = 'Не удалось загрузить аналитику'
    console.warn('OLAP Stats error:', error)
  } finally {
    olapLoading.value = false
  }
}

const loadOrderHistory = async () => {
  if (!props.customer?.id) return
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/history`)
    if (!response.ok) throw new Error('Failed to fetch history')
    const data = await response.json()
    ordersHistory.value = Array.isArray(data) ? data : []
  } catch (e) {
    ordersHistory.value = props.customer.orders_history || []
  }
}

const loadBonusHistory = async () => {
  if (!props.customer?.id) return
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/bonuses`)
    if (!response.ok) throw new Error('Failed to fetch bonuses')
    const data = await response.json()
    bonusHistory.value = data
  } catch (e) {
    console.warn('Bonus history failed')
  }
}

const loadLocalPhones = async () => {
  if (!props.customer?.id) return
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/local-phones`)
    const data = await response.json()
    localPhones.value = data.phones || []
  } catch (e) {
    console.warn('Failed to load local phones')
  }
}

const addPhone = async () => {
  if (!newPhone.value || isAddingPhone.value) return
  isAddingPhone.value = true
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/local-phones`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: newPhone.value })
    })
    if (!response.ok) throw new Error('Failed to add phone')
    newPhone.value = ''
    await loadLocalPhones()
    toast.success('Телефон добавлен')
  } catch (e) {
    toast.error('Ошибка при добавлении телефона')
  } finally {
    isAddingPhone.value = false
  }
}

const deletePhone = async (phoneId) => {
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/local-phones/${phoneId}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete phone')
    await loadLocalPhones()
    toast.success('Телефон удален')
  } catch (e) {
    toast.error('Ошибка при удалении телефона')
  }
}

const loadAllCategories = async () => {
  try {
    const response = await fetch('/api/v1/customers/all-iiko-categories')
    if (!response.ok) throw new Error('Failed to fetch categories')
    allIikoCategories.value = await response.json()
  } catch (e) {
    console.warn('Failed to load iiko categories', e)
  }
}

const addCategory = (name) => {
  if (!form.value.iikoCategories.includes(name)) {
    form.value.iikoCategories.push(name)
  }
  categoryMenu.value = false
}

const removeCategory = (name) => {
  form.value.iikoCategories = form.value.iikoCategories.filter(c => c !== name)
}

const initData = async () => {
  if (!props.customer?.id) return

  form.value = {
    name: props.customer.name || '',
    surname: props.customer.surname || '',
    middleName: props.customer.middle_name || '',
    email: props.customer.email || '',
    birthday: props.customer.birthday ? String(props.customer.birthday).split('T')[0] : '',
    gender: props.customer.gender || 'NotSpecified',
    referrer: props.customer.referrer || '',
    registrationSource: props.customer.registration_source || '',
    registeredOrganization: props.customer.registered_organization || '',
    iikoNotes: props.customer.iiko_notes || props.customer.notes || '',
    isHighRisk: props.customer.is_high_risk || false,
    riskReason: props.customer.risk_reason || '',
    iikoCategories: (() => {
      // Пытаемся взять из основного массива
      if (Array.isArray(props.customer.iiko_categories) && props.customer.iiko_categories.length > 0) {
        return [...props.customer.iiko_categories]
      }
      
      // Если пусто, пробуем распарсить из строки loyalty_categories (иногда iiko присылает JSON-строку)
      const loyaltyCats = props.customer.loyalty_categories || props.customer.categories
      if (loyaltyCats) {
        if (Array.isArray(loyaltyCats)) return [...loyaltyCats]
        if (typeof loyaltyCats === 'string') {
          if (loyaltyCats.trim().startsWith('[')) {
            try {
              const parsed = JSON.parse(loyaltyCats)
              if (Array.isArray(parsed)) return parsed
            } catch (e) {
              console.error('Failed to parse loyalty_categories JSON', e)
            }
          }
          // Если это строка через запятую
          return loyaltyCats.split(',').map(s => s.trim()).filter(Boolean)
        }
      }
      return []
    })(),
  }

  parseAddresses()

  await Promise.all([
    loadOlapStats(),
    loadOrderHistory(),
    loadLocalOrders(),
    loadBonusHistory(),
    loadAllCategories(),
    loadLocalPhones(),
  ])

  generateBarcode()
}

const syncFullData = async () => {
  if (!props.customer?.id) return
  isSyncing.value = true
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/sync-premium`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to sync data')
    const data = await response.json()
    emit('updated', data)
    toast.success('Данные синхронизированы')
    await initData()
  } catch (error) {
    toast.error('Ошибка: ' + error.message)
  } finally {
    isSyncing.value = false
  }
}

const saveProfile = async () => {
  if (!props.customer?.id) return
  try {
    // Преобразование camelCase в snake_case для бэкенда
    const payload = {
      ...form.value,
      ['middle_name']: form.value.middleName,
      ['registration_source']: form.value.registrationSource,
      ['registered_organization']: form.value.registeredOrganization,
    }

    const response = await fetch(`/api/v1/customers/${props.customer.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!response.ok) throw new Error('Failed to save profile')
    const data = await response.json()

    emit('updated', data)
    toast.success('Сохранено')
  } catch (error) {
    toast.error('Ошибка: ' + error.message)
  }
}

const adjustBonuses = async () => {
  if (!props.customer?.id || !bonusAdjustment.value.amount) return
  isAdjustingBonuses.value = true
  try {
    const response = await fetch(`/api/v1/customers/${props.customer.id}/adjust-bonuses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: bonusAdjustment.value.amount,
        comment: bonusAdjustment.value.comment
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to adjust bonuses')
    }
    
    toast.success('Баланс изменен')
    bonusAdjustment.value.amount = 0
    // Перезагружаем данные
    await loadBonusHistory()
    await syncFullData() 
  } catch (error) {
    toast.error('Ошибка: ' + error.message)
  } finally {
    isAdjustingBonuses.value = false
  }
}

const formatPrice = (value) => {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value || 0)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

watch(() => props.modelValue, (newVal) => {
  if (newVal && props.customer?.id) {
    initData()
  }
})

onMounted(() => {
  if (props.modelValue && props.customer?.id) {
    initData()
  }
})
</script>

<style scoped>
.customer-detail-card {
  border-radius: 12px;
}
.line-height-1 {
  line-height: 1.2;
}
.opacity-80 {
  opacity: 0.8;
}
.text-muted {
  color: rgba(0, 0, 0, 0.6);
}

.high-risk-header {
  background: linear-gradient(90deg, #ff4d4f 0%, #ff7875 100%) !important;
}

.high-risk-border {
  border: 2px solid #ff4d4f !important;
}

.pulse-animation {
  animation: pulse-red 2s infinite;
}

@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(255, 77, 79, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 77, 79, 0); }
}

.barcode-container canvas {
  max-width: 100%;
}

.transition-all {
  transition: all 0.3s ease;
}
</style>
