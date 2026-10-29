<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()
const activeTab = ref('notifications')

// Loading states
const isLoading = ref(false)
const isSaving = ref(false)

// Dialogs
const isCascadeDialogOpen = ref(false)
const isReminderDialogOpen = ref(false)
const isBroadcastDialogOpen = ref(false)

// ------------------- TAB 1: NOTIFICATIONS (CASCADES) -------------------
const cascades = ref([])
const maxBots = ref([])
const currentCascade = ref({
  name: '',
  trigger_event: 'order_delivered',
  order_type: 'delivery',
  is_active: true,
  is_system: true,
  steps: []
})

const triggerEvents = [
  { title: 'Новый заказ', value: 'new_order' },
  { title: 'Заказ подтвержден', value: 'order_confirmed' },
  { title: 'Заказ готовится', value: 'order_cooking' },
  { title: 'Заказ готов', value: 'order_ready' },
  { title: 'Заказ готов к выдаче (Самовывоз)', value: 'order_ready_for_pickup' },
  { title: 'Заказ в пути (Доставка)', value: 'order_delivering' },
  { title: 'Заказ доставлен/выдан', value: 'order_delivered' },
  { title: 'Заказ завершен', value: 'order_closed' },
  { title: 'Заказ отменен', value: 'order_cancelled' },
  { title: 'Событие рассылки', value: 'broadcast' },
  { title: 'Событие напоминания', value: 'reminder' }
]

const orderTypes = [
  { title: 'Доставка', value: 'delivery' },
  { title: 'Самовывоз', value: 'pickup' },
  { title: 'Любой', value: 'any' }
]

const channels = [
  { title: 'ВКонтакте (VK)', value: 'vk' },
  { title: 'MAX Messenger', value: 'max' },
  { title: 'Telegram', value: 'telegram' },
  { title: 'SMS-сообщение', value: 'sms' }
]

const conditions = [
  { title: 'Отправлять всегда', value: 'always' },
  { title: 'Если предыдущий шаг не доставлен', value: 'if_previous_failed' },
  { title: 'Если предыдущий шаг не прочитан', value: 'if_not_read_previous' }
]

const variables = [
  { name: '{customer_name}', desc: 'Имя гостя' },
  { name: '{order_number}', desc: 'Номер заказа' },
  { name: '{total_sum}', desc: 'Сумма заказа' },
  { name: '{items}', desc: 'Список блюд в заказе' },
  { name: '{address}', desc: 'Адрес доставки' },
  { name: '{status}', desc: 'Статус текстом' },
  { name: '{message_text}', desc: 'Текст напоминания/рассылки' }
]

const fetchCascades = async () => {
  isLoading.value = true
  try {
    const response = await axios.get('/api/v1/mailings/cascades')
    cascades.value = response.data
  } catch (error) {
    toast.error('Не удалось загрузить цепочки уведомлений')
  } finally {
    isLoading.value = false
  }
}

const fetchMaxBots = async () => {
  try {
    const response = await axios.get('/api/v1/vk-bot/max-bots')
    maxBots.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки ботов MAX', error)
  }
}

const openCreateCascadeDialog = () => {
  currentCascade.value = {
    name: '',
    trigger_event: 'order_delivered',
    order_type: 'delivery',
    is_active: true,
    is_system: true,
    steps: []
  }
  isCascadeDialogOpen.value = true
}

const editCascade = (cascade) => {
  const cloned = JSON.parse(JSON.stringify(cascade))
  if (cloned.steps) {
    cloned.steps.forEach(s => {
      if (s.max_bot_id === undefined) s.max_bot_id = null
      if (s.max_send_mode === undefined) s.max_send_mode = 'cascade'
    })
  }
  currentCascade.value = cloned
  isCascadeDialogOpen.value = true
}

const addStep = () => {
  currentCascade.value.steps.push({
    channel: 'vk',
    delay_minutes: 0,
    template: 'Здравствуйте, {customer_name}! Ваш заказ №{order_number} на сумму {total_sum} ₽ доставлен. Оцените, пожалуйста, качество работы:',
    condition: 'always',
    priority: currentCascade.value.steps.length,
    image_path: '',
    buttons_json: '',
    max_bot_id: null,
    max_send_mode: 'cascade'
  })
}

const removeStep = (index) => {
  currentCascade.value.steps.splice(index, 1)
  reorderSteps()
}

const moveStep = (index, direction) => {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= currentCascade.value.steps.length) return
  const element = currentCascade.value.steps.splice(index, 1)[0]
  currentCascade.value.steps.splice(newIndex, 0, element)
  reorderSteps()
}

const reorderSteps = () => {
  currentCascade.value.steps.forEach((step, index) => {
    step.priority = index
  })
}

const saveCascade = async () => {
  if (!currentCascade.value.name) {
    toast.warning('Укажите название каскада')
    return
  }
  isSaving.value = true
  try {
    if (currentCascade.value.id) {
      await axios.put(`/api/v1/mailings/cascades/${currentCascade.value.id}`, currentCascade.value)
      toast.success('Настройки каскада обновлены')
    } else {
      await axios.post('/api/v1/mailings/cascades', currentCascade.value)
      toast.success('Каскад успешно создан')
    }
    isCascadeDialogOpen.value = false
    fetchCascades()
  } catch (error) {
    toast.error('Ошибка при сохранении каскада')
  } finally {
    isSaving.value = false
  }
}

const toggleCascadeActive = async (cascade) => {
  try {
    await axios.put(`/api/v1/mailings/cascades/${cascade.id}`, {
      ...cascade,
      is_active: cascade.is_active
    })
    toast.success(cascade.is_active ? 'Каскад активирован' : 'Каскад деактивирован')
  } catch (error) {
    cascade.is_active = !cascade.is_active
    toast.error('Не удалось изменить статус активности')
  }
}

const deleteCascade = async (id) => {
  if (!confirm('Вы уверены, что хотите удалить эту каскадную рассылку?')) return
  try {
    await axios.delete(`/api/v1/mailings/cascades/${id}`)
    toast.success('Каскад удален')
    fetchCascades()
  } catch (error) {
    toast.error('Ошибка при удалении каскада')
  }
}

const insertVariable = (stepIndex, variableName) => {
  currentCascade.value.steps[stepIndex].template += ` ${variableName}`
}

// Конструктор кнопок для шага
const quickConfigureRatingButtons = (stepIndex) => {
  const keyboard = {
    one_time: false,
    inline: true,
    buttons: [
      [
        {
          action: {
            type: 'text',
            payload: JSON.stringify({ action: 'rate_order', rating: 1, order_id: '{order_number}' }),
            label: '1 ⭐'
          },
          color: 'negative'
        },
        {
          action: {
            type: 'text',
            payload: JSON.stringify({ action: 'rate_order', rating: 2, order_id: '{order_number}' }),
            label: '2 ⭐'
          },
          color: 'negative'
        },
        {
          action: {
            type: 'text',
            payload: JSON.stringify({ action: 'rate_order', rating: 3, order_id: '{order_number}' }),
            label: 'secondary'
          },
          color: 'secondary'
        },
        {
          action: {
            type: 'text',
            payload: JSON.stringify({ action: 'rate_order', rating: 4, order_id: '{order_number}' }),
            label: '4 ⭐'
          },
          color: 'primary'
        },
        {
          action: {
            type: 'text',
            payload: JSON.stringify({ action: 'rate_order', rating: 5, order_id: '{order_number}' }),
            label: '5 ⭐'
          },
          color: 'positive'
        }
      ]
    ]
  }
  currentCascade.value.steps[stepIndex].buttons_json = JSON.stringify(keyboard, null, 2)
  toast.success('Быстрые кнопки оценки 1-5 добавлены в VK-формате!')
}


// ------------------- TAB 2: REVIEWS (ОТЗЫВЫ) -------------------
const reviews = ref([])
const reviewsStats = ref({
  average_rating: 0,
  total_count: 0,
  distribution: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
})
const reviewRatingFilter = ref(null)

const fetchReviews = async () => {
  try {
    const params = {}
    if (reviewRatingFilter.value) {
      params.rating = reviewRatingFilter.value
    }
    const response = await axios.get('/api/v1/mailings/reviews', { params })
    reviews.value = response.data
  } catch (error) {
    toast.error('Не удалось загрузить журнал отзывов')
  }
}

const fetchReviewsStats = async () => {
  try {
    const response = await axios.get('/api/v1/mailings/reviews/stats')
    reviewsStats.value = response.data
  } catch (error) {
    console.error('Ошибка статистики отзывов', error)
  }
}

const filterReviewsByRating = (rating) => {
  reviewRatingFilter.value = reviewRatingFilter.value === rating ? null : rating
  fetchReviews()
}


// ------------------- TAB 3: REMINDERS (НАПОМИНАНИЯ) -------------------
const reminders = ref([])
const currentReminder = ref({
  name: '',
  days_inactive: 14,
  template: 'Привет, {customer_name}! Давно не виделись. Дарим вам скидку 10% на следующий заказ по промокоду BACK10!',
  cascade_id: null,
  is_active: true
})

const fetchReminders = async () => {
  try {
    const response = await axios.get('/api/v1/mailings/reminders')
    reminders.value = response.data
  } catch (error) {
    toast.error('Не удалось загрузить правила напоминаний')
  }
}

const openCreateReminderDialog = () => {
  currentReminder.value = {
    name: '',
    days_inactive: 14,
    template: 'Привет, {customer_name}! Давно не виделись. Дарим вам скидку 10% на следующий заказ по промокоду BACK10!',
    cascade_id: null,
    is_active: true
  }
  isReminderDialogOpen.value = true
}

const editReminder = (reminder) => {
  currentReminder.value = JSON.parse(JSON.stringify(reminder))
  isReminderDialogOpen.value = true
}

const saveReminder = async () => {
  if (!currentReminder.value.name || !currentReminder.value.template) {
    toast.warning('Заполните название и шаблон сообщения')
    return
  }
  isSaving.value = true
  try {
    if (currentReminder.value.id) {
      await axios.patch(`/api/v1/mailings/reminders/${currentReminder.value.id}`, currentReminder.value)
      toast.success('Напоминание обновлено')
    } else {
      await axios.post('/api/v1/mailings/reminders', currentReminder.value)
      toast.success('Напоминание создано')
    }
    isReminderDialogOpen.value = false
    fetchReminders()
  } catch (error) {
    toast.error('Ошибка при сохранении напоминания')
  } finally {
    isSaving.value = false
  }
}

const toggleReminderActive = async (reminder) => {
  try {
    await axios.patch(`/api/v1/mailings/reminders/${reminder.id}`, {
      is_active: reminder.is_active
    })
    toast.success(reminder.is_active ? 'Правило напоминания включено' : 'Правило напоминания выключено')
  } catch (error) {
    reminder.is_active = !reminder.is_active
    toast.error('Не удалось изменить статус напоминания')
  }
}

const deleteReminder = async (id) => {
  if (!confirm('Удалить это правило напоминания?')) return
  try {
    await axios.delete(`/api/v1/mailings/reminders/${id}`)
    toast.success('Напоминание удалено')
    fetchReminders()
  } catch (error) {
    toast.error('Ошибка при удалении напоминания')
  }
}


// ------------------- TAB 4: BROADCASTS (РАССЫЛКИ) -------------------
const broadcasts = ref([])
const currentBroadcast = ref({
  title: '',
  template_text: 'Привет, {customer_name}! У нас для вас отличные новости! Попробуйте наши новые роллы со скидкой 15% по ссылке: https://vezuroll.ru/menu',
  cascade_id: null,
  audience_filters: {
    days_inactive: '',
    total_orders_amount_min: '',
    total_orders_count_min: ''
  }
})

const fetchBroadcasts = async () => {
  try {
    const response = await axios.get('/api/v1/mailings/broadcasts')
    broadcasts.value = response.data
  } catch (error) {
    toast.error('Не удалось загрузить список рассылок')
  }
}

const openCreateBroadcastDialog = () => {
  currentBroadcast.value = {
    title: '',
    template_text: 'Привет, {customer_name}! У нас для вас отличные новости! Попробуйте наши новые роллы со скидкой 15% по ссылке: https://vezuroll.ru/menu',
    cascade_id: null,
    audience_filters: {
      days_inactive: '',
      total_orders_amount_min: '',
      total_orders_count_min: ''
    }
  }
  isBroadcastDialogOpen.value = true
}

const saveBroadcast = async () => {
  if (!currentBroadcast.value.title || !currentBroadcast.value.template_text) {
    toast.warning('Заполните тему и текст рассылки')
    return
  }
  isSaving.value = true
  try {
    await axios.post('/api/v1/mailings/broadcasts', currentBroadcast.value)
    toast.success('Рассылка (черновик) создана')
    isBroadcastDialogOpen.value = false
    fetchBroadcasts()
  } catch (error) {
    toast.error('Ошибка при создании рассылки')
  } finally {
    isSaving.value = false
  }
}

const sendBroadcastNow = async (id) => {
  if (!confirm('Запустить рассылку немедленно по выбранной аудитории?')) return
  try {
    await axios.post(`/api/v1/mailings/broadcasts/${id}/send`)
    toast.success('Рассылка успешно запущена в фоновом режиме')
    fetchBroadcasts()
  } catch (error) {
    toast.error('Не удалось запустить рассылку')
  }
}

const deleteBroadcast = async (id) => {
  if (!confirm('Удалить эту рассылку?')) return
  try {
    await axios.delete(`/api/v1/mailings/broadcasts/${id}`)
    toast.success('Рассылка удалена')
    fetchBroadcasts()
  } catch (error) {
    toast.error('Ошибка при удалении рассылки')
  }
}


// ------------------- TAB 5: MESSAGE LOGS (СТАТУСЫ) -------------------
const messageLogs = ref([])
const logChannelFilter = ref(null)
const logStatusFilter = ref(null)

const fetchMessageLogs = async () => {
  try {
    const params = {}
    if (logChannelFilter.value) params.channel = logChannelFilter.value
    if (logStatusFilter.value) params.status = logStatusFilter.value
    const response = await axios.get('/api/v1/mailings/logs', { params })
    messageLogs.value = response.data
  } catch (error) {
    toast.error('Не удалось загрузить лог сообщений')
  }
}

// Helpers
const getStatusColor = (status) => {
  switch (status) {
    case 'pending': return 'warning'
    case 'sent': return 'info'
    case 'delivered': return 'success'
    case 'read': return 'primary'
    case 'clicked': return 'secondary'
    case 'failed': return 'error'
    default: return 'grey'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'pending': return 'В очереди'
    case 'sent': return 'Отправлено'
    case 'delivered': return 'Доставлено'
    case 'read': return 'Прочитано'
    case 'clicked': return 'Переход по ссылке'
    case 'failed': return 'Ошибка'
    default: return status
  }
}

// Initial mounting load based on active tab
const handleTabChange = () => {
  if (activeTab.value === 'notifications') fetchCascades()
  if (activeTab.value === 'reviews') {
    fetchReviews()
    fetchReviewsStats()
  }
  if (activeTab.value === 'reminders') {
    fetchReminders()
    fetchCascades() // for cascade selection dropdown
  }
  if (activeTab.value === 'broadcasts') {
    fetchBroadcasts()
    fetchCascades() // for cascade selection dropdown
  }
  if (activeTab.value === 'status') fetchMessageLogs()
}

onMounted(() => {
  fetchCascades()
  fetchMaxBots()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <!-- Title Card with beautiful modern styling -->
      <VCard class="mb-6 elevation-2 overflow-hidden gradient-header text-white">
        <VCardText class="pa-6 d-flex align-center justify-space-between">
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">Уведомления и рассылки</h1>
            <p class="text-subtitle-1 mb-0 opacity-80">
              Управление каскадной рассылкой сообщений, сбором отзывов, триггерами напоминаний и аналитикой активности
            </p>
          </div>
          <VIcon size="64" icon="bx-message-rounded-dots" class="opacity-30 d-none d-sm-block" />
        </VCardText>
      </VCard>

      <!-- Premium Navigation Tabs -->
      <VTabs 
        v-model="activeTab" 
        color="primary" 
        grow 
        class="bg-card rounded shadow-sm mb-6"
        @update:model-value="handleTabChange"
      >
        <VTab value="notifications" class="text-subtitle-2 font-weight-medium">
          <VIcon start icon="bx-git-commit" />
          Уведомления
        </VTab>
        <VTab value="reviews" class="text-subtitle-2 font-weight-medium">
          <VIcon start icon="bx-star" />
          Отзывы
        </VTab>
        <VTab value="reminders" class="text-subtitle-2 font-weight-medium">
          <VIcon start icon="bx-time-five" />
          Напоминания
        </VTab>
        <VTab value="broadcasts" class="text-subtitle-2 font-weight-medium">
          <VIcon start icon="bx-broadcast" />
          Рассылки
        </VTab>
        <VTab value="status" class="text-subtitle-2 font-weight-medium">
          <VIcon start icon="bx-list-check" />
          Статус отправки
        </VTab>
      </VTabs>

      <!-- Main Window Content -->
      <VWindow v-model="activeTab">
        
        <!-- ------------------- TAB 1: NOTIFICATIONS (CASCADES) ------------------- -->
        <VWindowItem value="notifications">
          <VCard class="mb-4">
            <VCardText class="d-flex align-center justify-space-between flex-wrap gap-4">
              <div>
                <h3 class="text-h6 mb-1">Системные триггеры и каскады</h3>
                <span class="text-body-2 text-muted"> цепочки уведомлений клиентов о статусах заказов в соцсетях. Отдельно для доставки и самовывоза.</span>
              </div>
              <VBtn color="primary" class="shadow-primary" @click="openCreateCascadeDialog">
                <VIcon start icon="bx-plus" />
                Создать каскад
              </VBtn>
            </VCardText>

            <VTable class="elevation-0">
              <thead>
                <tr class="bg-light">
                  <th class="font-weight-bold">Название</th>
                  <th class="font-weight-bold">Триггер-статус iiko</th>
                  <th class="font-weight-bold">Тип доставки</th>
                  <th class="font-weight-bold">Шагов</th>
                  <th class="font-weight-bold">Назначение</th>
                  <th class="font-weight-bold">Активность</th>
                  <th class="font-weight-bold text-center">Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="cascade in cascades" :key="cascade.id" class="hover-row">
                  <td class="font-weight-bold">{{ cascade.name }}</td>
                  <td>
                    <VChip size="small" color="primary" variant="tonal" class="rounded-pill">
                      {{ triggerEvents.find(e => e.value === cascade.trigger_event)?.title || cascade.trigger_event }}
                    </VChip>
                  </td>
                  <td>
                    <VChip size="small" :color="cascade.order_type === 'delivery' ? 'info' : cascade.order_type === 'pickup' ? 'warning' : 'secondary'" variant="flat">
                      {{ orderTypes.find(t => t.value === cascade.order_type)?.title || 'Любой' }}
                    </VChip>
                  </td>
                  <td>
                    <VBadge :content="cascade.steps?.length || 0" color="grey-lighten-1" inline />
                  </td>
                  <td>
                    <span class="text-caption text-uppercase font-weight-bold" :class="cascade.is_system ? 'text-primary' : 'text-success'">
                      {{ cascade.is_system ? 'Системное' : 'Ручное/Рассылка' }}
                    </span>
                  </td>
                  <td>
                    <VSwitch 
                      v-model="cascade.is_active" 
                      color="success" 
                      hide-details 
                      density="compact"
                      @change="toggleCascadeActive(cascade)"
                    />
                  </td>
                  <td class="text-center">
                    <VBtn icon variant="text" color="primary" size="small" @click="editCascade(cascade)">
                      <VIcon icon="bx-edit" />
                    </VBtn>
                    <VBtn icon variant="text" color="error" size="small" @click="deleteCascade(cascade.id)">
                      <VIcon icon="bx-trash" />
                    </VBtn>
                  </td>
                </tr>
                <tr v-if="cascades.length === 0">
                  <td colspan="7" class="text-center py-8 text-muted">
                    Каскадные сценарии не обнаружены. Создайте новый!
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </VWindowItem>

        <!-- ------------------- TAB 2: REVIEWS (ОТЗЫВЫ) ------------------- -->
        <VWindowItem value="reviews">
          <!-- Statistics KPI Section -->
          <VRow class="mb-4">
            <VCol cols="12" sm="4">
              <VCard class="pa-4 rounded elevation-1 card-gradient-primary text-white d-flex align-center justify-space-between">
                <div>
                  <div class="text-subtitle-1 opacity-80">Средняя оценка</div>
                  <div class="text-h3 font-weight-bold my-1">{{ reviewsStats.average_rating }} ⭐</div>
                  <span class="text-caption opacity-90">На основе отзывов клиентов</span>
                </div>
                <VIcon size="56" icon="bx-smile" class="opacity-20" />
              </VCard>
            </VCol>
            <VCol cols="12" sm="4">
              <VCard class="pa-4 rounded elevation-1 card-gradient-success text-white d-flex align-center justify-space-between">
                <div>
                  <div class="text-subtitle-1 opacity-80">Всего отзывов</div>
                  <div class="text-h3 font-weight-bold my-1">{{ reviewsStats.total_count }}</div>
                  <span class="text-caption opacity-90">В системе сбора через чаты</span>
                </div>
                <VIcon size="56" icon="bx-message-square-detail" class="opacity-20" />
              </VCard>
            </VCol>
            <VCol cols="12" sm="4">
              <VCard class="pa-4 rounded elevation-1 bg-card border">
                <div class="text-subtitle-2 text-muted mb-2">Распределение оценок (клик для фильтрации)</div>
                <div class="d-flex flex-column gap-1">
                  <div 
                    v-for="stars in [5, 4, 3, 2, 1]" 
                    :key="stars"
                    class="d-flex align-center cursor-pointer hover-bg rounded px-2 py-0.5"
                    :class="{ 'bg-primary-light': reviewRatingFilter === stars }"
                    @click="filterReviewsByRating(stars)"
                  >
                    <span class="text-caption font-weight-bold me-2" style="width: 15px">{{ stars }}</span>
                    <VProgressLinear 
                      :model-value="reviewsStats.total_count > 0 ? (reviewsStats.distribution[stars] / reviewsStats.total_count) * 100 : 0" 
                      color="warning" 
                      height="8" 
                      rounded
                      class="flex-grow-1"
                    />
                    <span class="text-caption font-weight-bold ms-3" style="width: 30px; text-align: right">
                      {{ reviewsStats.distribution[stars] || 0 }}
                    </span>
                  </div>
                </div>
              </VCard>
            </VCol>
          </VRow>

          <!-- Reviews Table -->
          <VCard>
            <VCardText class="d-flex align-center justify-space-between py-3 border-bottom flex-wrap gap-4">
              <h3 class="text-h6">Журнал оценок и отзывов гостей</h3>
              <div class="d-flex align-center gap-2">
                <VChip 
                  v-if="reviewRatingFilter" 
                  color="warning" 
                  closable 
                  @click:close="filterReviewsByRating(null)"
                >
                  Оценка: {{ reviewRatingFilter }} ⭐
                </VChip>
              </div>
            </VCardText>

            <VTable>
              <thead>
                <tr class="bg-light">
                  <th class="font-weight-bold">Дата</th>
                  <th class="font-weight-bold">Заказ в iiko</th>
                  <th class="font-weight-bold">Клиент</th>
                  <th class="font-weight-bold">Оценка</th>
                  <th class="font-weight-bold" style="width: 45%">Отзыв (текст)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rev in reviews" :key="rev.id" class="hover-row">
                  <td>{{ new Date(rev.created_at).toLocaleString('ru-RU') }}</td>
                  <td>
                    <span class="font-weight-bold">№ {{ rev.order_number }}</span>
                  </td>
                  <td>
                    <div>{{ rev.customer_name }}</div>
                    <span class="text-caption text-muted">{{ rev.customer_phone }}</span>
                  </td>
                  <td>
                    <span class="text-subtitle-2 text-warning font-weight-bold">
                      <VIcon icon="bx-star" size="16" class="me-1 mb-1" />{{ rev.rating }} / 5
                    </span>
                  </td>
                  <td>
                    <div class="text-body-2 font-italic py-1 text-high-emphasis">
                      {{ rev.comment || '— комментарий не оставлен —' }}
                    </div>
                  </td>
                </tr>
                <tr v-if="reviews.length === 0">
                  <td colspan="5" class="text-center py-8 text-muted">
                    Никаких отзывов по выбранному фильтру не найдено
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </VWindowItem>

        <!-- ------------------- TAB 3: REMINDERS (НАПОМИНАНИЯ) ------------------- -->
        <VWindowItem value="reminders">
          <VCard class="mb-4">
            <VCardText class="d-flex align-center justify-space-between flex-wrap gap-4">
              <div>
                <h3 class="text-h6 mb-1">Сценарии реактивации (Напоминания)</h3>
                <span class="text-body-2 text-muted">Настройка автоматической отправки сообщений спящим клиентам на основе дней неактивности</span>
              </div>
              <VBtn color="primary" class="shadow-primary" @click="openCreateReminderDialog">
                <VIcon start icon="bx-plus" />
                Создать напоминание
              </VBtn>
            </VCardText>

            <VTable>
              <thead>
                <tr class="bg-light">
                  <th class="font-weight-bold">Название правила</th>
                  <th class="font-weight-bold">Срок неактивности</th>
                  <th class="font-weight-bold">Текст сообщения</th>
                  <th class="font-weight-bold">Используемый каскад</th>
                  <th class="font-weight-bold">Статус</th>
                  <th class="font-weight-bold text-center">Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rem in reminders" :key="rem.id" class="hover-row">
                  <td class="font-weight-bold">{{ rem.name }}</td>
                  <td>
                    <VChip color="error" size="small" variant="tonal">
                      {{ rem.days_inactive }} дн. без заказов
                    </VChip>
                  </td>
                  <td>
                    <div class="text-truncate text-caption" style="max-width: 300px">
                      {{ rem.template }}
                    </div>
                  </td>
                  <td>{{ rem.cascade_name || 'Напрямую' }}</td>
                  <td>
                    <VSwitch 
                      v-model="rem.is_active" 
                      color="success" 
                      hide-details 
                      density="compact"
                      @change="toggleReminderActive(rem)"
                    />
                  </td>
                  <td class="text-center">
                    <VBtn icon variant="text" color="primary" size="small" @click="editReminder(rem)">
                      <VIcon icon="bx-edit" />
                    </VBtn>
                    <VBtn icon variant="text" color="error" size="small" @click="deleteReminder(rem.id)">
                      <VIcon icon="bx-trash" />
                    </VBtn>
                  </td>
                </tr>
                <tr v-if="reminders.length === 0">
                  <td colspan="6" class="text-center py-8 text-muted">
                    Сценарии автонапоминаний отсутствуют
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </VWindowItem>

        <!-- ------------------- TAB 4: BROADCASTS (РАССЫЛКИ) ------------------- -->
        <VWindowItem value="broadcasts">
          <VCard class="mb-4">
            <VCardText class="d-flex align-center justify-space-between flex-wrap gap-4">
              <div>
                <h3 class="text-h6 mb-1">Массовые каскадные рассылки</h3>
                <span class="text-body-2 text-muted">Инструмент планирования и отправки рекламных рассылок с выбором каналов (каскадов) и фильтрацией гостей</span>
              </div>
              <VBtn color="primary" class="shadow-primary" @click="openCreateBroadcastDialog">
                <VIcon start icon="bx-plus" />
                Создать рассылку
              </VBtn>
            </VCardText>

            <VTable>
              <thead>
                <tr class="bg-light">
                  <th class="font-weight-bold">Название</th>
                  <th class="font-weight-bold">Текст</th>
                  <th class="font-weight-bold">Фильтры</th>
                  <th class="font-weight-bold">Цепочка</th>
                  <th class="font-weight-bold">Статус рассылки</th>
                  <th class="font-weight-bold">Метрики отправки</th>
                  <th class="font-weight-bold text-center">Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="br in broadcasts" :key="br.id" class="hover-row">
                  <td class="font-weight-bold">{{ br.title }}</td>
                  <td>
                    <div class="text-truncate text-caption" style="max-width: 200px">
                      {{ br.template_text }}
                    </div>
                  </td>
                  <td>
                    <div class="d-flex flex-column gap-1 text-caption">
                      <span v-if="br.audience_filters?.days_inactive">Неактивность: {{ br.audience_filters.days_inactive }}+ дн.</span>
                      <span v-if="br.audience_filters?.total_orders_amount_min">LTV: {{ br.audience_filters.total_orders_amount_min }}+ ₽</span>
                      <span v-if="br.audience_filters?.total_orders_count_min">Заказов: {{ br.audience_filters.total_orders_count_min }}+</span>
                    </div>
                  </td>
                  <td>{{ br.cascade_name || 'Не указан' }}</td>
                  <td>
                    <VChip 
                      size="small" 
                      :color="br.status === 'completed' ? 'success' : br.status === 'processing' ? 'warning' : 'grey'"
                      class="font-weight-bold text-uppercase"
                    >
                      {{ br.status === 'draft' ? 'Черновик' : br.status === 'processing' ? 'В процессе' : br.status === 'completed' ? 'Завершена' : br.status }}
                    </VChip>
                  </td>
                  <td>
                    <div class="text-caption">
                      <div>Отправлено: <span class="font-weight-bold text-info">{{ br.sent_count }}</span></div>
                      <div>Ошибки: <span class="font-weight-bold text-error">{{ br.error_count }}</span></div>
                    </div>
                  </td>
                  <td class="text-center">
                    <VBtn 
                      v-if="br.status === 'draft' || br.status === 'scheduled'"
                      color="success" 
                      variant="elevated" 
                      size="small" 
                      class="me-1 shadow-sm"
                      @click="sendBroadcastNow(br.id)"
                    >
                      Отправить
                    </VBtn>
                    <VBtn icon variant="text" color="error" size="small" @click="deleteBroadcast(br.id)">
                      <VIcon icon="bx-trash" />
                    </VBtn>
                  </td>
                </tr>
                <tr v-if="broadcasts.length === 0">
                  <td colspan="7" class="text-center py-8 text-muted">
                    Создайте черновик вашей первой массовой рассылки
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </VWindowItem>

        <!-- ------------------- TAB 5: MESSAGE LOGS (СТАТУСЫ) ------------------- -->
        <VWindowItem value="status">
          <VCard class="mb-4">
            <VCardText class="d-flex align-center justify-space-between py-4 border-bottom flex-wrap gap-4">
              <div>
                <h3 class="text-h6 mb-1">Сквозной журнал отправки сообщений</h3>
                <span class="text-body-2 text-muted">Контроль доставки, прочтения и кликов по всем рассылкам и каналам</span>
              </div>
              <div class="d-flex align-center gap-3 flex-wrap">
                <VSelect 
                  v-model="logChannelFilter" 
                  :items="[{ title: 'Все каналы', value: null }, { title: 'VK', value: 'vk' }, { title: 'MAX', value: 'max' }, { title: 'Telegram', value: 'telegram' }, { title: 'SMS', value: 'sms' }]" 
                  label="Канал" 
                  density="compact"
                  style="width: 140px"
                  hide-details
                  @update:model-value="fetchMessageLogs"
                />
                <VSelect 
                  v-model="logStatusFilter" 
                  :items="[{ title: 'Все статусы', value: null }, { title: 'Доставлено', value: 'delivered' }, { title: 'Прочитано', value: 'read' }, { title: 'Переход', value: 'clicked' }, { title: 'Ошибки', value: 'failed' }]" 
                  label="Статус" 
                  density="compact"
                  style="width: 160px"
                  hide-details
                  @update:model-value="fetchMessageLogs"
                />
              </div>
            </VCardText>

            <VTable>
              <thead>
                <tr class="bg-light">
                  <th class="font-weight-bold">Дата</th>
                  <th class="font-weight-bold">Получатель</th>
                  <th class="font-weight-bold">Канал</th>
                  <th class="font-weight-bold">Содержание сообщения</th>
                  <th class="font-weight-bold">Статус доставки</th>
                  <th class="font-weight-bold">Источник рассылки</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in messageLogs" :key="log.id" class="hover-row">
                  <td class="text-caption">{{ new Date(log.sent_at || log.created_at).toLocaleString('ru-RU') }}</td>
                  <td>
                    <div>{{ log.customer_name }}</div>
                    <span class="text-caption text-muted">{{ log.recipient_address }}</span>
                  </td>
                  <td>
                    <span class="font-weight-bold text-uppercase">{{ log.channel }}</span>
                  </td>
                  <td>
                    <div class="text-caption font-mono py-1" style="max-width: 320px; white-space: normal">
                      {{ log.text }}
                    </div>
                  </td>
                  <td>
                    <VChip 
                      size="small" 
                      :color="getStatusColor(log.status)" 
                      class="font-weight-bold"
                    >
                      {{ getStatusText(log.status) }}
                    </VChip>
                    <div v-if="log.error_text" class="text-caption text-error mt-1" style="max-width: 150px">
                      {{ log.error_text }}
                    </div>
                  </td>
                  <td>
                    <span class="text-caption">
                      {{ log.broadcast_title ? `Рассылка: ${log.broadcast_title}` : log.reminder_name ? `Напоминание: ${log.reminder_name}` : 'Статус заказа' }}
                    </span>
                  </td>
                </tr>
                <tr v-if="messageLogs.length === 0">
                  <td colspan="6" class="text-center py-8 text-muted">
                    Записи логов отсутствуют
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </VWindowItem>

      </VWindow>
    </VCol>

    <!-- ----------------- DIALOG: CREATE/EDIT CASCADE ----------------- -->
    <VDialog v-model="isCascadeDialogOpen" max-width="1000px" scrollable>
      <VCard :title="currentCascade.id ? 'Редактировать каскад' : 'Создать каскадный сценарий'">
        <VCardText class="py-4">
          <VRow>
            <VCol cols="12" md="6">
              <VTextField v-model="currentCascade.name" label="Название каскада" placeholder="Напр: Доставка: Заказ доставлен" density="compact" />
            </VCol>
            <VCol cols="12" md="3">
              <VSelect 
                v-model="currentCascade.trigger_event" 
                :items="triggerEvents" 
                label="Событие-триггер" 
                density="compact"
              />
            </VCol>
            <VCol cols="12" md="3">
              <VSelect 
                v-model="currentCascade.order_type" 
                :items="orderTypes" 
                label="Тип заказа" 
                density="compact"
              />
            </VCol>
            <VCol cols="12" md="4" class="d-flex align-center">
              <VSwitch v-model="currentCascade.is_active" label="Активен каскад" color="success" hide-details />
            </VCol>
            <VCol cols="12" md="4" class="d-flex align-center">
              <VSwitch v-model="currentCascade.is_system" label="Системные статусы заказа" color="primary" hide-details />
            </VCol>
          </VRow>

          <!-- Step Builder inside Dialog -->
          <div class="mt-6">
            <div class="d-flex align-center justify-space-between mb-4 border-bottom pb-2">
              <h4 class="text-subtitle-1 font-weight-bold text-primary">Цепочка отправки (Шаги)</h4>
              <VBtn size="small" color="secondary" variant="outlined" @click="addStep">
                <VIcon start icon="bx-plus" /> Добавить канал
              </VBtn>
            </div>

            <div v-if="currentCascade.steps.length === 0" class="text-center py-10 border-dashed rounded text-muted">
              Добавьте хотя бы один канал отправки (например VK, MAX, Telegram)
            </div>

            <VCard 
              v-for="(step, index) in currentCascade.steps" 
              :key="index" 
              variant="outlined" 
              class="mb-4 bg-light"
            >
              <VCardText class="pa-4">
                <div class="d-flex align-center flex-wrap gap-2 mb-3">
                  <VChip color="primary" class="me-2 font-weight-bold">Шаг {{ index + 1 }}</VChip>
                  
                  <VSelect 
                    v-model="step.channel" 
                    :items="channels" 
                    label="Канал" 
                    density="compact"
                    style="width: 180px"
                    hide-details
                  />
                  
                  <VTextField 
                    v-model.number="step.delay_minutes" 
                    type="number" 
                    label="Задержка (мин)" 
                    density="compact"
                    style="width: 120px"
                    hide-details
                  />
                  
                  <VSelect 
                    v-model="step.condition" 
                    :items="conditions" 
                    label="Условие перехода" 
                    density="compact"
                    style="width: 250px"
                    hide-details
                  />

                  <VSpacer />

                  <VBtn icon variant="text" size="small" @click="moveStep(index, -1)" :disabled="index === 0">
                    <VIcon icon="bx-chevron-up" />
                  </VBtn>
                  <VBtn icon variant="text" size="small" @click="moveStep(index, 1)" :disabled="index === currentCascade.steps.length - 1">
                    <VIcon icon="bx-chevron-down" />
                  </VBtn>
                  <VBtn icon variant="text" color="error" size="small" @click="removeStep(index)">
                    <VIcon icon="bx-trash" />
                  </VBtn>
                </div>

                <!-- Настройки для канала MAX -->
                <div v-if="step.channel === 'max'" class="d-flex align-center flex-wrap gap-3 mb-3 pa-2 rounded border bg-purple-lighten-5">
                  <div class="d-flex align-center gap-2" style="min-width: 250px;">
                    <span class="text-caption font-weight-bold text-purple text-no-wrap">
                      <VIcon icon="bx-bot" size="16" class="me-1 text-purple" />
                      Бот MAX:
                    </span>
                    <VSelect
                      v-model="step.max_bot_id"
                      :items="[
                        { id: null, title: 'Основной бот MAX (по умолчанию)' },
                        ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name} (@${b.bot_username || b.id})${b.is_default_for_notifications ? ' ★' : ''}` }))
                      ]"
                      item-title="title"
                      item-value="id"
                      density="compact"
                      variant="outlined"
                      class="bg-white rounded"
                      hide-details
                      style="min-width: 230px;"
                    />
                  </div>

                  <div class="d-flex align-center gap-2" style="min-width: 250px;">
                    <span class="text-caption font-weight-bold text-purple text-no-wrap">
                      <VIcon icon="bx-git-branch" size="16" class="me-1 text-purple" />
                      Режим отправки MAX:
                    </span>
                    <VSelect
                      v-model="step.max_send_mode"
                      :items="[
                        { id: 'cascade', title: 'Каскад (Бот ➔ Личные по телефону)' },
                        { id: 'bot_only', title: 'Только Бот MAX' },
                        { id: 'bridge_only', title: 'Только Личный аккаунт (по номеру)' }
                      ]"
                      item-title="title"
                      item-value="id"
                      density="compact"
                      variant="outlined"
                      class="bg-white rounded"
                      hide-details
                      style="min-width: 250px;"
                    />
                  </div>
                </div>

                <VRow>
                  <VCol cols="12" md="8">
                    <VTextarea 
                      v-model="step.template" 
                      label="Шаблон текста сообщения" 
                      rows="3"
                      density="compact"
                      placeholder="Введите текст сообщения..."
                    />
                    
                    <div class="d-flex flex-wrap gap-1 mt-1">
                      <span class="text-caption text-muted me-2 align-self-center">Шорткоды:</span>
                      <VBtn 
                        v-for="v in variables" 
                        :key="v.name" 
                        size="x-small" 
                        variant="tonal"
                        color="secondary"
                        @click="insertVariable(index, v.name)"
                        :title="v.desc"
                      >
                        {{ v.name }}
                      </VBtn>
                    </div>
                  </VCol>
                  
                  <VCol cols="12" md="4" class="d-flex flex-column gap-2">
                    <VTextField 
                      v-model="step.image_path" 
                      label="Ссылка или путь к картинке" 
                      placeholder="media/img/... или http://" 
                      density="compact"
                    />

                    <!-- Button Builder for VK -->
                    <div class="d-flex flex-column gap-1">
                      <div class="d-flex align-center justify-space-between">
                        <span class="text-caption font-weight-bold">Клавиатура (JSON)</span>
                        <VBtn 
                          v-if="step.channel === 'vk'" 
                          size="x-small" 
                          color="success" 
                          variant="tonal"
                          @click="quickConfigureRatingButtons(index)"
                        >
                          Кнопки оценки (1-5)
                        </VBtn>
                      </div>
                      <VTextarea 
                        v-model="step.buttons_json" 
                        placeholder='{"inline": true, "buttons": [...]}' 
                        rows="2"
                        density="compact"
                        class="font-mono text-caption"
                      />
                    </div>
                  </VCol>
                </VRow>
              </VCardText>
            </VCard>
          </div>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn color="secondary" variant="text" @click="isCascadeDialogOpen = false">Отменить</VBtn>
          <VBtn color="primary" class="shadow-primary" :loading="isSaving" @click="saveCascade">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ----------------- DIALOG: CREATE/EDIT REMINDER ----------------- -->
    <VDialog v-model="isReminderDialogOpen" max-width="600px">
      <VCard :title="currentReminder.id ? 'Изменить автонапоминание' : 'Создать автонапоминание'">
        <VCardText class="py-4">
          <VRow>
            <VCol cols="12">
              <VTextField v-model="currentReminder.name" label="Название напоминания" placeholder="Напр: Скидка спящим 14 дней" density="compact" />
            </VCol>
            <VCol cols="12" sm="6">
              <VTextField v-model.number="currentReminder.days_inactive" type="number" label="Дней неактивности (без заказов)" density="compact" />
            </VCol>
            <VCol cols="12" sm="6">
              <VSelect 
                v-model="currentReminder.cascade_id" 
                :items="cascades" 
                item-title="name" 
                item-value="id"
                label="Цепочка каскада (каналы)" 
                placeholder="Использовать цепочку"
                density="compact"
                clearable
              />
            </VCol>
            <VCol cols="12">
              <VTextarea 
                v-model="currentReminder.template" 
                label="Шаблон сообщения ({customer_name} подставится автоматически)" 
                rows="4" 
                density="compact" 
              />
            </VCol>
            <VCol cols="12">
              <VSwitch v-model="currentReminder.is_active" label="Правило активно" color="success" hide-details />
            </VCol>
          </VRow>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn color="secondary" variant="text" @click="isReminderDialogOpen = false">Отмена</VBtn>
          <VBtn color="primary" class="shadow-primary" :loading="isSaving" @click="saveReminder">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- ----------------- DIALOG: CREATE BROADCAST ----------------- -->
    <VDialog v-model="isBroadcastDialogOpen" max-width="700px">
      <VCard title="Создать рекламную рассылку">
        <VCardText class="py-4">
          <VRow>
            <VCol cols="12">
              <VTextField v-model="currentBroadcast.title" label="Тема/Название рассылки" placeholder="Напр: Акция на сеты выходного дня" density="compact" />
            </VCol>
            <VCol cols="12" md="6">
              <VSelect 
                v-model="currentBroadcast.cascade_id" 
                :items="cascades" 
                item-title="name" 
                item-value="id"
                label="Цепочка каналов (Каскад)" 
                density="compact"
                clearable
              />
            </VCol>
            <VCol cols="12">
              <VTextarea 
                v-model="currentBroadcast.template_text" 
                label="Текст рассылки" 
                placeholder="Привет, {customer_name}! Только сегодня..."
                rows="4" 
                density="compact" 
              />
              <span class="text-caption text-muted">Если вставить ссылку, она автоматически сократится для трекинга переходов (кликов).</span>
            </VCol>

            <!-- Target Audience Filters -->
            <VCol cols="12">
              <h4 class="text-subtitle-2 font-weight-bold text-primary mb-3">Фильтры целевой аудитории (Оставьте пустыми для всех)</h4>
              <VRow>
                <VCol cols="12" sm="4">
                  <VTextField 
                    v-model.number="currentBroadcast.audience_filters.days_inactive" 
                    type="number" 
                    label="Не заказывали от (дней)" 
                    density="compact" 
                  />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField 
                    v-model.number="currentBroadcast.audience_filters.total_orders_amount_min" 
                    type="number" 
                    label="Мин. сумма покупок (₽)" 
                    density="compact" 
                  />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField 
                    v-model.number="currentBroadcast.audience_filters.total_orders_count_min" 
                    type="number" 
                    label="Мин. кол-во заказов" 
                    density="compact" 
                  />
                </VCol>
              </VRow>
            </VCol>
          </VRow>
        </VCardText>

        <VCardActions>
          <VSpacer />
          <VBtn color="secondary" variant="text" @click="isBroadcastDialogOpen = false">Отмена</VBtn>
          <VBtn color="primary" class="shadow-primary" :loading="isSaving" @click="saveBroadcast">Сохранить черновик</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VRow>
</template>

<style scoped>
.gradient-header {
  background: linear-gradient(135deg, #6200ea 0%, #311b92 100%);
}
.card-gradient-primary {
  background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%);
}
.card-gradient-success {
  background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%);
}
.border-dashed {
  border: 2px dashed rgba(var(--v-border-color), 0.6);
}
.hover-row:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
  transition: background-color 0.2s ease;
}
.cursor-pointer {
  cursor: pointer;
}
.hover-bg:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
.bg-primary-light {
  background-color: rgba(98, 0, 234, 0.08);
}
.font-mono {
  font-family: monospace;
}
.gap-1 {
  gap: 4px;
}
.gap-2 {
  gap: 8px;
}
.gap-3 {
  gap: 12px;
}
.gap-4 {
  gap: 16px;
}
.border-bottom {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
.shadow-sm {
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.shadow-primary {
  box-shadow: 0 4px 14px 0 rgba(98, 0, 234, 0.4);
}
</style>
