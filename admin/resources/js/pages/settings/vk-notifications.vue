<script setup>
import { ref, onMounted, computed } from 'vue'

const tab = ref('accounts')
const accounts = ref([])
const templates = ref([])
const variables = ref({})
const logs = ref([])
const loading = ref(false)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

// Диалоги
const addAccountDialog = ref(false)
const subscriptionDialog = ref(false)
const broadcastDialog = ref(false)
const templateDialog = ref(false)

const currentAccount = ref(null)
const accountSubscriptions = ref([])

const newAccount = ref({
  vkLink: '',
  name: '',
  phone: '',
  customerId: null,
  employeeId: null,
})

const customerSearchLoading = ref(false)
const foundCustomers = ref([])
const employeeSearchLoading = ref(false)
const foundEmployees = ref([])

const onCustomerSearch = async val => {
  if (!val || val.length < 2) return
  customerSearchLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/customers/search?q=${encodeURIComponent(val)}`, { headers: getAuthHeaders() })
    if (res.ok) foundCustomers.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    customerSearchLoading.value = false
  }
}

const onCustomerSelected = customerId => {
  const customer = foundCustomers.value.find(c => c.id === customerId)
  if (customer) {
    newAccount.value.phone = customer.phone
    newAccount.value.name = customer.name || ''
    newAccount.value.customerId = customer.id
  }
}

const onEmployeeSearch = async val => {
  if (!val || val.length < 2) return
  employeeSearchLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/employees/search?q=${encodeURIComponent(val)}`, { headers: getAuthHeaders() })
    if (res.ok) foundEmployees.value = await res.json()
  } catch (e) {
    console.error(e)
  } finally {
    employeeSearchLoading.value = false
  }
}

const onEmployeeSelected = employeeId => {
  const emp = foundEmployees.value.find(e => e.id === employeeId)
  if (emp) {
    newAccount.value.name = emp.name
    newAccount.value.phone = emp.phone
    newAccount.value.employeeId = emp.id
  }
}

const addingAccount = ref(false)

const broadcastData = ref({
  text: '',
  accountIds: [],
  templateId: null,
})

const currentTemplate = ref({
  name: '',
  text: '',
  keyboard_json: '',
})

// Конструктор клавиатуры
const kbRows = ref([])
const showKeyboardEditor = ref(false)

const addKbRow = () => {
  if (kbRows.value.length < 10) kbRows.value.push([])
}

const addKbButton = (rowIndex) => {
  if (kbRows.value[rowIndex].length < 4) {
    kbRows.value[rowIndex].push({
      label: 'Кнопка',
      color: 'primary',
      type: 'text',
      link: '',
    })
  }
}

const removeKbButton = (rowIndex, btnIndex) => {
  kbRows.value[rowIndex].splice(btnIndex, 1)
  if (kbRows.value[rowIndex].length === 0) kbRows.value.splice(rowIndex, 1)
}

const generateKbJson = () => {
  const buttons = kbRows.value.map(row => 
    row.map(btn => {
      const action = { type: btn.type, label: btn.label }
      if (btn.type === 'open_link' && btn.link) {
        action.link = btn.link
      }
      return {
        action: action,
        color: btn.type === 'open_link' ? undefined : btn.color
      }
    })
  )
  currentTemplate.value.keyboard_json = JSON.stringify({ one_time: false, buttons }, null, 2)
  showKeyboardEditor.value = false
}

const editKeyboard = () => {
  try {
    const data = JSON.parse(currentTemplate.value.keyboard_json || '{"buttons":[]}')
    kbRows.value = data.buttons.map(row => 
      row.map(btn => ({
        label: btn.action.label,
        color: btn.color || 'primary',
        type: btn.action.type,
        link: btn.action.link || '',
      }))
    )
  } catch (e) {
    kbRows.value = []
  }
  showKeyboardEditor.value = true
}

const sendingBroadcast = ref(false)
const searchQuery = ref('')

const availableEvents = [
  { id: 'order_new', name: 'Новый заказ', icon: 'mdi-plus-circle' },
  { id: 'order_status_update', name: 'Статус заказа', icon: 'mdi-refresh' },
  { id: 'order_amount_changed', name: 'Изменение суммы', icon: 'mdi-currency-rub' },
  { id: 'order_items_changed', name: 'Изменение состава', icon: 'mdi-basket' },
  { id: 'order_time_changed', name: 'Изменение времени', icon: 'mdi-clock-edit' },
  { id: 'order_address_changed', name: 'Изменение адреса', icon: 'mdi-map-marker-edit' },
  { id: 'order_cancelled', name: 'Отмена заказа', icon: 'mdi-close-circle' },
  { id: 'shift_open', name: 'Открытие смены', icon: 'mdi-account-clock' },
  { id: 'shift_close', name: 'Закрытие смены', icon: 'mdi-account-off' },
  { id: 'bonus_order', name: 'Заказ за баллы', icon: 'mdi-star-circle' },
  { id: 'system_alert', name: 'Системный алерт', icon: 'mdi-alert' },
  { id: 'courier_assigned', name: 'Назначен курьер', icon: 'mdi-bike' },
]

const intervalOptions = [
  { title: 'Мгновенно', value: 0 },
  { title: '5 минут', value: 5 },
  { title: '15 минут', value: 15 },
  { title: '30 минут', value: 30 },
  { title: '1 час', value: 60 },
  { title: '3 часа', value: 180 },
  { title: '6 часов', value: 360 },
  { title: '12 часов', value: 720 },
  { title: '24 часа', value: 1440 },
]

const API_BASE = '/api/v1/vk-bot'

const getAuthHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json'
})

const handleUnauthorized = () => {
  localStorage.removeItem('access_token')
  window.location.href = '/login'
}

const showMessage = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const filteredAccounts = computed(() => {
  if (!searchQuery.value) return accounts.value
  const q = searchQuery.value.toLowerCase()
  return accounts.value.filter(a => 
    a.name.toLowerCase().includes(q) || 
    (a.phone && a.phone.includes(q)) || 
    (a.vk_user_id && a.vk_user_id.toString().includes(q))
  )
})

const fetchAccounts = async () => {
  loading.value = true
  try {
    const url = searchQuery.value 
      ? `${API_BASE}/accounts?search=${encodeURIComponent(searchQuery.value)}`
      : `${API_BASE}/accounts`
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (res.ok) accounts.value = await res.json()
    else if (res.status === 401) handleUnauthorized()
  } catch (e) {
    showMessage('Ошибка загрузки аккаунтов', 'error')
  } finally {
    loading.value = false
  }
}

const fetchTemplates = async () => {
  try {
    const res = await fetch(`${API_BASE}/templates`, { headers: getAuthHeaders() })
    if (res.ok) templates.value = await res.json()
    else if (res.status === 401) handleUnauthorized()
  } catch (e) {
    console.error(e)
  }
}

const fetchVariables = async () => {
  try {
    const res = await fetch(`${API_BASE}/variables`, { headers: getAuthHeaders() })
    if (res.ok) variables.value = await res.json()
    else if (res.status === 401) handleUnauthorized()
  } catch (e) {
    console.error(e)
  }
}

const fetchLogs = async () => {
  try {
    const res = await fetch(`${API_BASE}/logs`, { headers: getAuthHeaders() })
    if (res.ok) logs.value = await res.json()
    else if (res.status === 401) handleUnauthorized()
  } catch (e) {
    console.error(e)
  }
}

const fetchSubscriptions = async accountId => {
  try {
    const res = await fetch(`${API_BASE}/accounts/${accountId}/subscriptions`, { headers: getAuthHeaders() })
    if (res.ok) accountSubscriptions.value = await res.json()
  } catch (e) {
    showMessage('Ошибка загрузки подписок', 'error')
  }
}

const openSubscriptions = async account => {
  currentAccount.value = account
  subscriptionDialog.value = true
  await fetchSubscriptions(account.id)
}

const updateSubscription = async (eventType, mode, interval, startHour = 0, endHour = 23) => {
  try {
    await fetch(`${API_BASE}/subscriptions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        account_id: currentAccount.value.id,
        event_type: eventType,
        delivery_mode: mode,
        interval_minutes: interval,
        active_start_hour: startHour,
        active_end_hour: endHour,
      }),
    })
    await fetchSubscriptions(currentAccount.value.id)
  } catch (e) {
    showMessage('Ошибка обновления подписки', 'error')
  }
}

const toggleSubscription = async eventType => {
  const existing = accountSubscriptions.value.find(s => s.event_type === eventType)
  if (existing) {
    try {
      const res = await fetch(`${API_BASE}/subscriptions/${existing.id}`, { 
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      if (res.ok) fetchSubscriptions(currentAccount.value.id)
    } catch (e) {
      showMessage('Ошибка удаления подписки', 'error')
    }
  } else {
    await updateSubscription(eventType, 'realtime', 0)
  }
}

const addAccount = async () => {
  addingAccount.value = true
  try {
    const res = await fetch(`${API_BASE}/accounts`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: newAccount.value.name,
        vk_link: newAccount.value.vkLink,
        phone: newAccount.value.phone,
        employee_id: newAccount.value.employeeId,
      }),
    })

    const data = await res.json()
    if (res.ok) {
      showMessage('Аккаунт успешно добавлен')
      addAccountDialog.value = false
      newAccount.value = { vkLink: '', name: '', phone: '' }
      fetchAccounts()
    } else {
      showMessage(data.detail || 'Ошибка добавления', 'error')
    }
  } catch (e) {
    showMessage('Ошибка сети', 'error')
  } finally {
    addingAccount.value = false
  }
}

const toggleAccountStatus = async account => {
  try {
    const res = await fetch(`${API_BASE}/accounts/${account.id}`, { 
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ is_active: !account.is_active })
    })
    if (res.ok) {
      showMessage(account.is_active ? 'Аккаунт деактивирован' : 'Аккаунт активирован')
      fetchAccounts()
    }
  } catch (e) {
    showMessage('Ошибка изменения статуса', 'error')
  }
}

const deleteAccount = async id => {
  if (!confirm('Удалить аккаунт?')) return
  try {
    const res = await fetch(`${API_BASE}/accounts/${id}`, { 
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    if (res.ok) {
      showMessage('Аккаунт удален')
      fetchAccounts()
    }
  } catch (e) {
    showMessage('Ошибка удаления', 'error')
  }
}

const saveTemplate = async () => {
  try {
    const isEdit = !!currentTemplate.value.id
    const url = isEdit ? `${API_BASE}/templates/${currentTemplate.value.id}` : `${API_BASE}/templates`
    const method = isEdit ? 'PATCH' : 'POST'
    
    const res = await fetch(url, {
      method: method,
      headers: getAuthHeaders(),
      body: JSON.stringify(currentTemplate.value),
    })
    if (res.ok) {
      showMessage(isEdit ? 'Шаблон обновлен' : 'Шаблон создан')
      templateDialog.value = false
      fetchTemplates()
    }
  } catch (e) {
    showMessage('Ошибка сохранения', 'error')
  }
}

const deleteTemplate = async id => {
  if (!confirm('Удалить шаблон?')) return
  try {
    await fetch(`${API_BASE}/templates/${id}`, { 
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    fetchTemplates()
  } catch (e) {
    showMessage('Ошибка удаления', 'error')
  }
}

const verifyAccount = async id => {
  try {
    const res = await fetch(`${API_BASE}/accounts/${id}/verify`, { 
      method: 'POST',
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (data.status === 'success') {
      showMessage(data.message)
      fetchAccounts()
    } else {
      showMessage(data.message, 'error')
    }
  } catch (e) {
    showMessage('Ошибка верификации', 'error')
  }
}

const sendBroadcast = async () => {
  sendingBroadcast.value = true
  try {
    const res = await fetch(`${API_BASE}/broadcast`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        text: broadcastData.value.text,
        account_ids: broadcastData.value.accountIds,
        template_id: broadcastData.value.templateId,
      }),
    })

    if (res.ok) {
      showMessage('Рассылка отправлена')
      broadcastDialog.value = false
      broadcastData.value.text = ''
      broadcastData.value.templateId = null
      fetchLogs()
    }
  } catch (e) {
    showMessage('Ошибка рассылки', 'error')
  } finally {
    sendingBroadcast.value = false
  }
}

const insertVariable = (variable, target = 'template') => {
  if (target === 'template') {
    currentTemplate.value.text += `{{${variable}}}`
  } else {
    broadcastData.value.text += `{{${variable}}}`
  }
}

const formatDate = date => {
  if (!date) return '-'
  return new Date(date).toLocaleString('ru-RU')
}

onMounted(() => {
  fetchAccounts()
  fetchLogs()
  fetchTemplates()
  fetchVariables()
})
</script>

<template>
  <div class="vk-notifications-container">
    <VRow>
      <VCol cols="12">
        <VCard elevation="10" class="glass-card">
          <VCardTitle class="d-flex justify-space-between align-center pa-6">
            <div class="d-flex align-center">
              <VIcon icon="mdi-vk" color="#4C75A3" size="32" class="me-3" />
              <span class="text-h5 font-weight-bold">Уведомления VK Бота</span>
            </div>
            <div class="d-flex gap-2">
              <VBtn color="primary" prepend-icon="mdi-plus" rounded="lg" @click="addAccountDialog = true">
                Добавить получателя
              </VBtn>
              <VBtn color="secondary" variant="tonal" prepend-icon="mdi-bullhorn" rounded="lg" @click="broadcastDialog = true">
                Рассылка
              </VBtn>
            </div>
          </VCardTitle>

          <VTabs v-model="tab" class="px-6">
            <VTab value="accounts">Аккаунты ({{ accounts.length }})</VTab>
            <VTab value="templates">Шаблоны</VTab>
            <VTab value="logs">История</VTab>
          </VTabs>

          <VDivider />

          <VWindow v-model="tab" class="pa-6">
            <VWindowItem value="accounts">
              <div class="d-flex mb-4">
                <VTextField
                  v-model="searchQuery"
                  label="Поиск по имени, телефону или ID"
                  variant="outlined"
                  density="compact"
                  prepend-inner-icon="mdi-magnify"
                  clearable
                  hide-details
                  @update:model-value="fetchAccounts"
                />
              </div>

              <div v-if="loading && accounts.length === 0" class="d-flex justify-center py-10">
                <VProgressCircular indeterminate color="primary" />
              </div>
              <VRow v-else>
                <VCol v-for="account in filteredAccounts" :key="account.id" cols="12" md="6" lg="4">
                  <VCard variant="outlined" rounded="xl" class="account-card">
                    <VCardText class="pa-5">
                      <div class="d-flex align-center mb-4">
                        <VAvatar color="#4C75A3" size="48" class="me-4">
                          <VIcon icon="mdi-account" color="white" />
                        </VAvatar>
                        <div class="overflow-hidden">
                          <div class="text-h6 text-truncate">{{ account.name }}</div>
                          <div class="text-caption text-grey text-truncate d-flex align-center">
                            <VIcon icon="mdi-phone" size="12" class="me-1" />
                            {{ account.phone || 'Нет телефона' }}
                          </div>
                          <div v-if="account.employee_id" class="text-caption text-primary d-flex align-center">
                            <VIcon icon="mdi-account-tie" size="12" class="me-1" />
                            Сотрудник ID: {{ account.employee_id }}
                          </div>
                        </div>
                        <VSpacer />
                        <div class="d-flex flex-column align-end gap-1">
                          <VChip :color="account.is_verified ? 'success' : 'warning'" size="x-small" label variant="tonal">
                            {{ account.is_verified ? 'Проверен' : 'Не проверен' }}
                          </VChip>
                          <VChip :color="account.is_active ? 'success' : 'error'" size="x-small" label variant="tonal">
                            {{ account.is_active ? 'Активен' : 'Отключен' }}
                          </VChip>
                        </div>
                      </div>
                      <div class="d-flex gap-2 mt-2">
                        <VBtn size="small" variant="tonal" color="primary" prepend-icon="mdi-cog" class="flex-grow-1" @click="openSubscriptions(account)">Настроить</VBtn>
                        <VBtn size="small" variant="tonal" :color="account.is_active ? 'warning' : 'success'" :icon="account.is_active ? 'mdi-pause' : 'mdi-play'" @click="toggleAccountStatus(account)" />
                        <VBtn size="small" variant="tonal" color="info" icon="mdi-test-tube" @click="verifyAccount(account.id)" />
                        <VBtn size="small" variant="tonal" color="error" icon="mdi-delete" @click="deleteAccount(account.id)" />
                      </div>
                    </VCardText>
                  </VCard>
                </VCol>
              </VRow>
            </VWindowItem>

            <VWindowItem value="templates">
              <VBtn color="primary" class="mb-4" prepend-icon="mdi-plus" @click="templateDialog = true; currentTemplate = { name: '', text: '', keyboard_json: '' }">
                Создать шаблон
              </VBtn>
              <VRow>
                <VCol v-for="tpl in templates" :key="tpl.id" cols="12" md="4">
                  <VCard variant="outlined" class="pa-4 rounded-xl">
                    <div class="text-h6 mb-2">{{ tpl.name }}</div>
                    <div class="text-body-2 text-grey mb-4 text-truncate">{{ tpl.text }}</div>
                    <div class="d-flex gap-2">
                      <VBtn size="small" variant="tonal" color="primary" icon="mdi-pencil" @click="currentTemplate = { ...tpl }; templateDialog = true" />
                      <VBtn size="small" variant="tonal" color="error" icon="mdi-delete" @click="deleteTemplate(tpl.id)" />
                    </div>
                  </VCard>
                </VCol>
              </VRow>
            </VWindowItem>

            <VWindowItem value="logs">
              <VTable density="compact">
                <thead>
                  <tr>
                    <th>Время</th>
                    <th>Событие</th>
                    <th>Текст</th>
                    <th class="text-center">Статус</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in logs" :key="log.id">
                    <td class="text-caption">{{ formatDate(log.created_at) }}</td>
                    <td><VChip size="x-small" variant="outlined" label>{{ log.event_type }}</VChip></td>
                    <td class="text-truncate text-body-2" style="max-width: 400px">{{ log.text }}</td>
                    <td class="text-center">
                      <VIcon :icon="log.status === 'sent' ? 'mdi-check-circle' : 'mdi-alert-circle'" :color="log.status === 'sent' ? 'success' : 'error'" size="18" />
                    </td>
                  </tr>
                </tbody>
              </VTable>
            </VWindowItem>
          </VWindow>
        </VCard>
      </VCol>
    </VRow>

    <!-- Диалог управления подписками -->
    <VDialog v-model="subscriptionDialog" max-width="700px" scrollable>
      <VCard rounded="xl" class="glass-card">
        <VCardTitle class="pa-6 d-flex align-center">
          <VIcon icon="mdi-cog" class="me-3" color="primary" />
          <div>
            <div class="text-h6">Настройка уведомлений</div>
            <div class="text-caption text-grey">{{ currentAccount?.name }}</div>
          </div>
          <VSpacer />
          <VBtn icon="mdi-close" variant="text" @click="subscriptionDialog = false" />
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-0">
          <VList lines="three" class="py-0">
            <template v-for="event in availableEvents" :key="event.id">
              <VListItem class="px-6 py-3">
                <template #prepend>
                  <VAvatar color="primary" variant="tonal" size="40"><VIcon :icon="event.icon" /></VAvatar>
                </template>
                <VListItemTitle class="font-weight-bold">{{ event.name }}</VListItemTitle>
                <VListItemSubtitle>{{ event.id }}</VListItemSubtitle>
                <template #append>
                  <div class="d-flex flex-column align-end gap-2">
                    <template v-if="accountSubscriptions.find(s => s.event_type === event.id)">
                      <VSelect
                        :model-value="accountSubscriptions.find(s => s.event_type === event.id).interval_minutes"
                        :items="intervalOptions"
                        density="compact"
                        variant="outlined"
                        hide-details
                        style="width: 140px"
                        label="Интервал"
                        @update:model-value="(val) => updateSubscription(event.id, val === 0 ? 'realtime' : 'interval', val, accountSubscriptions.find(s => s.event_type === event.id).active_start_hour, accountSubscriptions.find(s => s.event_type === event.id).active_end_hour)"
                      />
                      <div class="d-flex align-center gap-2 mt-2">
                        <span class="text-caption">Активно:</span>
                        <VTextField :model-value="accountSubscriptions.find(s => s.event_type === event.id).active_start_hour" type="number" min="0" max="23" density="compact" variant="outlined" hide-details style="width: 60px" suffix="ч" @update:model-value="(val) => updateSubscription(event.id, 'interval', accountSubscriptions.find(s => s.event_type === event.id).interval_minutes, parseInt(val), accountSubscriptions.find(s => s.event_type === event.id).active_end_hour)" />
                        <span>-</span>
                        <VTextField :model-value="accountSubscriptions.find(s => s.event_type === event.id).active_end_hour" type="number" min="0" max="23" density="compact" variant="outlined" hide-details style="width: 60px" suffix="ч" @update:model-value="(val) => updateSubscription(event.id, 'interval', accountSubscriptions.find(s => s.event_type === event.id).interval_minutes, accountSubscriptions.find(s => s.event_type === event.id).active_start_hour, parseInt(val))" />
                      </div>
                    </template>
                    <VBtn v-else prepend-icon="mdi-bell-plus" variant="tonal" color="primary" size="small" @click="toggleSubscription(event.id)">Подписаться</VBtn>
                  </div>
                </template>
              </VListItem>
              <VDivider />
            </template>
          </VList>
        </VCardText>
        <VCardActions class="pa-6">
          <VBtn color="primary" block variant="flat" size="large" @click="subscriptionDialog = false">Готово</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог шаблона -->
    <VDialog v-model="templateDialog" max-width="900px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6">Редактор шаблона</VCardTitle>
        <VCardText class="px-6">
          <VRow>
            <VCol cols="12" md="8">
              <VTextField v-model="currentTemplate.name" label="Название шаблона" variant="outlined" class="mb-4" />
              <VTextarea v-model="currentTemplate.text" label="Текст шаблона" rows="10" variant="outlined" />
              <div class="d-flex align-center mt-4">
                <VTextarea v-model="currentTemplate.keyboard_json" label="JSON Клавиатуры (опционально)" rows="3" variant="outlined" hide-details />
                <VBtn color="primary" class="ms-4" variant="tonal" prepend-icon="mdi-keyboard-outline" @click="editKeyboard">Конструктор</VBtn>
              </div>
            </VCol>
            <VCol cols="12" md="4">
              <div class="text-subtitle-2 mb-2">Переменные (нажмите для вставки)</div>
              <VExpansionPanels variant="accordion">
                <VExpansionPanel v-for="(vars, category) in variables.variables" :key="category" :title="category">
                  <VExpansionPanelText class="pa-0">
                    <VList density="compact">
                      <VListItem v-for="(desc, code) in vars" :key="code" @click="insertVariable(code, 'template')">
                        <VListItemTitle class="text-caption font-weight-bold" style="cursor: pointer">{{ code }}</VListItemTitle>
                        <VListItemSubtitle class="text-caption">{{ desc }}</VListItemSubtitle>
                      </VListItem>
                    </VList>
                  </VExpansionPanelText>
                </VExpansionPanel>
              </VExpansionPanels>
            </VCol>
          </VRow>
        </VCardText>
        <VCardActions class="pa-6">
          <VBtn variant="text" color="grey" @click="templateDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="primary" variant="flat" rounded="lg" @click="saveTemplate">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Визуальный редактор клавиатуры -->
    <VDialog v-model="showKeyboardEditor" max-width="600px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6">Конструктор клавиатуры VK</VCardTitle>
        <VCardText class="px-6">
            <div v-for="(row, rIdx) in kbRows" :key="rIdx" class="mb-4 pa-3 border rounded-lg shadow-sm">
              <div class="d-flex justify-space-between align-center mb-2">
                <span class="text-caption font-weight-bold">Ряд {{ rIdx + 1 }}</span>
                <VBtn size="x-small" color="error" variant="text" @click="kbRows.splice(rIdx, 1)">Удалить ряд</VBtn>
              </div>
              <div class="d-flex flex-wrap gap-3">
                <div v-for="(btn, bIdx) in row" :key="bIdx" class="border pa-3 rounded-lg bg-grey-lighten-4 position-relative" style="width: 160px">
                  <VTextField v-model="btn.label" label="Текст кнопки" density="compact" hide-details class="mb-2" />
                  <VSelect 
                    v-model="btn.type" 
                    :items="[
                      {title: 'Текст', value: 'text'}, 
                      {title: 'Ссылка', value: 'open_link'}
                    ]" 
                    label="Действие" 
                    density="compact" 
                    hide-details 
                    class="mb-2" 
                  />
                  
                  <VTextField 
                    v-if="btn.type === 'open_link'" 
                    v-model="btn.link" 
                    label="URL (https://...)" 
                    density="compact" 
                    hide-details 
                    class="mb-2" 
                  />
                  <VSelect 
                    v-else
                    v-model="btn.color" 
                    :items="[
                      {title: 'Синий', value: 'primary'}, 
                      {title: 'Белый', value: 'secondary'}, 
                      {title: 'Зеленый', value: 'positive'}, 
                      {title: 'Красный', value: 'negative'}
                    ]" 
                    label="Цвет" 
                    density="compact" 
                    hide-details 
                    class="mb-2" 
                  />
                  
                  <VBtn size="x-small" block color="error" variant="tonal" class="mt-1" @click="removeKbButton(rIdx, bIdx)">Удалить</VBtn>
                </div>
                <VBtn v-if="row.length < 4" variant="dashed" border color="primary" style="height: 140px; width: 60px" @click="addKbButton(rIdx)">
                  <VIcon icon="mdi-plus" />
                </VBtn>
              </div>
            </div>
          <VBtn v-if="kbRows.length < 10" block variant="outlined" color="primary" class="mt-4" prepend-icon="mdi-plus" @click="addKbRow">Добавить ряд кнопок</VBtn>
          
          <div class="mt-6 text-caption text-grey">
            💡 <b>Инструкция:</b>
            <ul>
              <li>В одном ряду может быть до 4 кнопок. Всего до 10 рядов.</li>
              <li><b>Текст:</b> кнопка просто отправляет свой текст сообщением от пользователя.</li>
              <li><b>Ссылка:</b> кнопка открывает указанный URL (обязательно с https://).</li>
              <li>Цвета доступны только для текстовых кнопок.</li>
            </ul>
          </div>
        </VCardText>
        <VCardActions class="pa-6">
          <VBtn variant="text" @click="showKeyboardEditor = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="primary" variant="flat" @click="generateKbJson">Применить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог добавления аккаунта -->
    <VDialog v-model="addAccountDialog" max-width="500px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6">Новый получатель</VCardTitle>
        <VCardText class="px-6">
          <VTabs density="compact" class="mb-4">
            <VTab @click="newAccount.employeeId = null">Обычный</VTab>
            <VTab @click="newAccount.employeeId = -1">Сотрудник</VTab>
          </VTabs>

          <VAutocomplete
            v-if="newAccount.employeeId !== null"
            v-model="newAccount.employeeId"
            :items="foundEmployees"
            item-title="name"
            item-value="id"
            label="Поиск сотрудника"
            variant="outlined"
            class="mb-4"
            :loading="employeeSearchLoading"
            placeholder="Имя или телефон..."
            @update:search="onEmployeeSearch"
            @update:model-value="onEmployeeSelected"
          >
            <template #item="{ props, item }">
              <VListItem v-bind="props" :subtitle="item.raw.phone" />
            </template>
          </VAutocomplete>

          <VAutocomplete
            v-else
            v-model="newAccount.customerId"
            :items="foundCustomers"
            item-title="phone"
            item-value="id"
            label="Поиск по номеру телефона или имени клиента"
            variant="outlined"
            class="mb-4"
            :loading="customerSearchLoading"
            placeholder="Начните вводить +7..."
            @update:search="onCustomerSearch"
            @update:model-value="onCustomerSelected"
          >
            <template #item="{ props, item }">
              <VListItem v-bind="props" :subtitle="item.raw.name" />
            </template>
          </VAutocomplete>

          <VTextField v-model="newAccount.name" label="Имя отображения" variant="outlined" class="mb-4" hint="Заполнится автоматически при выборе" persistent-hint />
          <VTextField v-model="newAccount.phone" label="Номер телефона" placeholder="+7999..." variant="outlined" class="mb-4" />
          <VTextField v-model="newAccount.vkLink" label="Ссылка на профиль или ID" placeholder="durov или 1" variant="outlined" persistent-hint hint="Мы сами определим ID из ссылки" />
        </VCardText>
        <VCardActions class="pa-6">
          <VBtn variant="text" @click="addAccountDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="primary" variant="flat" :loading="addingAccount" @click="addAccount">Добавить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог рассылки -->
    <VDialog v-model="broadcastDialog" max-width="600px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6">Глобальная рассылка</VCardTitle>
        <VCardText class="px-6">
          <VSelect v-model="broadcastData.accountIds" :items="accounts" item-title="name" item-value="id" label="Выберите получателей" multiple chips variant="outlined" class="mb-4" />
          <VSelect v-model="broadcastData.templateId" :items="templates" item-title="name" item-value="id" label="Использовать шаблон (опционально)" variant="outlined" clearable class="mb-4" />
          
          <template v-if="!broadcastData.templateId">
            <VTextarea v-model="broadcastData.text" label="Текст сообщения" variant="outlined" rows="5" class="mb-4" />
            
            <div class="text-subtitle-2 mb-2">Вставить переменную:</div>
            <div class="d-flex flex-wrap gap-2">
              <VChip v-for="(vars, category) in variables.variables" :key="category" size="small" @click="insertVariable(Object.keys(vars)[0], 'broadcast')">
                {{ category }}
              </VChip>
            </div>
          </template>
        </VCardText>
        <VCardActions class="pa-6">
          <VBtn variant="text" @click="broadcastDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="secondary" variant="flat" :loading="sendingBroadcast" @click="sendBroadcast">Отправить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <VSnackbar v-model="snackbar" :color="snackbarColor" timeout="3000" rounded="pill">{{ snackbarText }}</VSnackbar>
  </div>
</template>

<style scoped>
.glass-card { background: rgba(255, 255, 255, 0.9) !important; backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
.account-card { transition: all 0.3s ease; }
.account-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1) !important; border-color: var(--v-primary-base) !important; }
.gap-2 { gap: 8px; }
</style>
