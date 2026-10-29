<script setup>
import { ref, onMounted, computed } from 'vue'

const tab = ref('courier_chains')
const keyboardTab = ref('vk')
const accounts = ref([])
const templates = ref([])
const variables = ref({ variables: {}, events: [], bot_commands: [] })
const logs = ref([])
const bots = ref([])
const selectedBotId = ref(null)
const maxBots = ref([])
const settingTplMaxBot = ref({})
const loading = ref(false)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

// Диалоги
const addAccountDialog = ref(false)
const editAccountDialog = ref(false)
const subscriptionDialog = ref(false)
const broadcastDialog = ref(false)
const templateDialog = ref(false)
const previewQrDialog = ref(false)
const previewQrLoading = ref(false)
const previewQrResultUrl = ref('')
const previewQrData = ref({
  order_number: '104',
  amount: 1850,
  delivery_address: 'г. Тюмень, ул. Республики, д. 142, кв. 15'
})
const selectedTemplateStatuses = ref([])
const currentChainConfig = ref({
  require_courier_assigned: true,
  resend_on_courier_reassigned: false,
  require_cooking_time_set: true,
  require_cooking_time_changed: false,
  require_amount_changed: false,
  require_address_changed: false,
  require_time_changed: false,
  only_unpaid: false,
  attach_sbp_qr: false,
  check_status_in: []
})

const currentAccount = ref(null)
const accountSubscriptions = ref([])

const newAccount = ref({
  vkLink: '',
  name: '',
  phone: '',
  customerId: null,
  employeeId: null,
  userId: null,
  is_courier: false,
  tg_user_id: null,
  max_user_id: '',
  use_vk: true,
  use_tg: false,
  use_max: false,
  use_sms: false,
  max_bot_id: null,
  max_send_mode: 'cascade',
  send_payment_qr: false,
  payment_qr_mode: 'all',
})

const editingAccount = ref({
  id: null,
  name: '',
  phone: '',
  is_active: true,
  employee_id: null,
  user_id: null,
  is_courier: false,
  vk_user_id: null,
  tg_user_id: null,
  max_user_id: '',
  use_vk: true,
  use_tg: false,
  use_max: false,
  use_sms: false,
  max_bot_id: null,
  max_send_mode: 'cascade',
  send_payment_qr: false,
  payment_qr_mode: 'all',
})

const recipientType = ref('employee')
const customerSearchLoading = ref(false)
const foundCustomers = ref([])
const employeeSearchLoading = ref(false)
const foundEmployees = ref([])
const userSearchLoading = ref(false)
const foundUsers = ref([])

const fetchEmployees = async (searchVal = '') => {
  employeeSearchLoading.value = true
  try {
    const url = searchVal 
      ? `${API_BASE}/employees/search?q=${encodeURIComponent(searchVal)}`
      : `${API_BASE}/employees/search`
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (res.ok) {
      foundEmployees.value = await res.json()
    }
  } catch (e) {
    console.error('Ошибка загрузки сотрудников:', e)
  } finally {
    employeeSearchLoading.value = false
  }
}

const fetchUsers = async (searchVal = '') => {
  userSearchLoading.value = true
  try {
    const url = searchVal 
      ? `${API_BASE}/users/search?q=${encodeURIComponent(searchVal)}`
      : `${API_BASE}/users/search`
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (res.ok) {
      foundUsers.value = await res.json()
    }
  } catch (e) {
    console.error('Ошибка загрузки пользователей:', e)
  } finally {
    userSearchLoading.value = false
  }
}

const onUserSearch = async val => {
  if (val && val.length >= 2) {
    fetchUsers(val)
  } else if (!val) {
    fetchUsers()
  }
}

const onUserSelected = userId => {
  if (!userId) {
    newAccount.value.userId = null
    return
  }
  const u = foundUsers.value.find(item => item.id === userId)
  if (u) {
    newAccount.value.name = u.name || u.username || ''
    newAccount.value.phone = u.phone || ''
    newAccount.value.userId = u.id
    if (u.employee_id) {
      newAccount.value.employeeId = u.employee_id
      checkCourierStatus(u.employee_id)
    }
    if (u.vk_user_id && !newAccount.value.vkLink) {
      newAccount.value.vkLink = String(u.vk_user_id)
    }
  }
}

const getUserName = (userId) => {
  if (!userId) return null
  const u = foundUsers.value.find(item => item.id === userId)
  return u ? `${u.name || u.username}${u.role ? ' (' + u.role + ')' : ''}` : `Пользователь #${userId}`
}

const hasDuplicateVk = (account) => {
  if (!account || !account.vk_user_id) return false
  return accounts.value.filter(a => a.vk_user_id && String(a.vk_user_id) === String(account.vk_user_id)).length > 1
}

const getDuplicateVkNames = (account) => {
  if (!account || !account.vk_user_id) return ''
  const duplicates = accounts.value.filter(a => a.id !== account.id && a.vk_user_id && String(a.vk_user_id) === String(account.vk_user_id))
  return duplicates.map(d => d.name).join(', ')
}

const togglingChannel = ref({})

const toggleAccountChannel = async (account, channel) => {
  const key = `${account.id}_${channel}`
  if (togglingChannel.value[key]) return
  togglingChannel.value[key] = true
  
  const currentVal = Boolean(account[`use_${channel}`])
  const newVal = !currentVal
  
  // Оптимистичное обновление
  account[`use_${channel}`] = newVal
  
  try {
    const res = await fetch(`${API_BASE}/accounts/${account.id}/toggle-channel`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ channel, enabled: newVal })
    })
    if (res.ok) {
      const data = await res.json()
      if (data.account) {
        Object.assign(account, data.account)
      }
      showMessage(`Канал ${channel.toUpperCase()} для «${account.name}» ${newVal ? 'включен' : 'отключен'}`)
    } else {
      account[`use_${channel}`] = currentVal
      const err = await res.json().catch(() => ({}))
      showMessage(err.detail || 'Ошибка изменения канала', 'error')
    }
  } catch (e) {
    account[`use_${channel}`] = currentVal
    showMessage('Ошибка соединения с сервером', 'error')
  } finally {
    delete togglingChannel.value[key]
  }
}

const bulkSubLoading = ref(false)

const bulkToggleSubChannel = async (channel, enabled) => {
  if (!currentAccount.value) return
  bulkSubLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/accounts/${currentAccount.value.id}/bulk-toggle-subscriptions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ channel, enabled })
    })
    if (res.ok) {
      await fetchSubscriptions(currentAccount.value.id)
      await fetchAccounts()
      showMessage(`Канал ${channel.toUpperCase()} во всех событиях ${enabled ? 'включен' : 'отключен'}`)
    } else {
      const err = await res.json().catch(() => ({}))
      showMessage(err.detail || 'Ошибка массового обновления', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  } finally {
    bulkSubLoading.value = false
  }
}

const onCustomerSearch = async val => {
  if (!val || val.length < 2) {
    foundCustomers.value = []
    return
  }
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
  if (!customerId) {
    newAccount.value.customerId = null
    return
  }
  const customer = foundCustomers.value.find(c => c.id === customerId)
  if (customer) {
    newAccount.value.phone = customer.phone || ''
    newAccount.value.name = customer.name || ''
    newAccount.value.customerId = customer.id
  }
}

const onEmployeeSearch = async val => {
  if (val && val.length >= 2) {
    fetchEmployees(val)
  } else if (!val) {
    fetchEmployees()
  }
}

const courierValidationInfo = ref(null)

const checkCourierStatus = async (employeeId) => {
  if (!employeeId) {
    courierValidationInfo.value = null
    return
  }
  try {
    const res = await fetch(`${API_BASE}/accounts/check-courier/${employeeId}`, {
      headers: getAuthHeaders()
    })
    const data = await res.json()
    courierValidationInfo.value = data
    if (data.is_courier) {
      if (addAccountDialog.value) {
        newAccount.value.is_courier = true
      }
      if (editAccountDialog.value) {
        editingAccount.value.is_courier = true
      }
    }
  } catch (err) {
    console.error('Error checking courier status:', err)
  }
}

const onEmployeeSelected = employeeId => {
  if (!employeeId) {
    newAccount.value.employeeId = null
    courierValidationInfo.value = null
    return
  }
  const emp = foundEmployees.value.find(e => e.id === employeeId)
  if (emp) {
    newAccount.value.name = emp.name
    newAccount.value.phone = emp.phone || ''
    newAccount.value.employeeId = emp.id
    checkCourierStatus(emp.id)
  }
}

const onEditEmployeeSelected = employeeId => {
  if (!employeeId) {
    editingAccount.value.employee_id = null
    courierValidationInfo.value = null
    return
  }
  const emp = foundEmployees.value.find(e => e.id === employeeId)
  if (emp) {
    if (!editingAccount.value.name) editingAccount.value.name = emp.name
    if (!editingAccount.value.phone && emp.phone) editingAccount.value.phone = emp.phone
    editingAccount.value.employee_id = emp.id
    checkCourierStatus(emp.id)
  }
}

const getEmployeeName = (employeeId) => {
  if (!employeeId) return null
  const emp = foundEmployees.value.find(e => e.id === employeeId)
  return emp ? `${emp.name}${emp.role ? ' (' + emp.role + ')' : ''}` : null
}

const openAddAccountDialog = () => {
  recipientType.value = 'employee'
  newAccount.value = { 
    vkLink: '', name: '', phone: '', customerId: null, employeeId: null, userId: null,
    is_courier: false, tg_user_id: null, max_user_id: '', use_vk: true, use_tg: false, use_max: false, use_sms: false,
    send_payment_qr: false, payment_qr_mode: 'all'
  }
  fetchEmployees()
  fetchUsers()
  addAccountDialog.value = true
}

const addingAccount = ref(false)
const savingAccount = ref(false)

const broadcastData = ref({
  text: '',
  accountIds: [],
  templateId: null,
})

const currentTemplate = ref({
  name: '',
  text: '',
  keyboard_json: '',
  event_type: null,
  keyboard_telegram: '',
  keyboard_max: '',
  target_mode: 'all',
  is_active: true,
  include_statuses: null,
  attach_sbp_qr: false,
  chain_config: null,
  description: '',
  vk_bot_id: null,
  max_bot_id: null,
  max_send_mode: 'cascade',
  send_vk: true,
  send_tg: false,
  send_max: false,
  send_sms: false,
  edit_existing_message: true,
  collapse_on_delivered: true,
  show_courier_action_buttons: true,
})

// Конструктор клавиатуры
const kbRows = ref([])
const showKeyboardEditor = ref(false)
const activeKbPlatform = ref('vk')

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
  const platform = activeKbPlatform.value
  
  if (platform === 'vk') {
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
  } else if (platform === 'telegram') {
    const inline_keyboard = kbRows.value.map(row => 
      row.map(btn => {
        if (btn.type === 'open_link') {
          return { text: btn.label, url: btn.link }
        } else {
          return { text: btn.label, callback_data: `btn_${btn.label}` }
        }
      })
    )
    currentTemplate.value.keyboard_telegram = JSON.stringify({ inline_keyboard }, null, 2)
  } else if (platform === 'max') {
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
    currentTemplate.value.keyboard_max = JSON.stringify({ buttons }, null, 2)
  }
  showKeyboardEditor.value = false
}

const insertCourierTemplateButtons = (platform) => {
  if (platform === 'vk') {
    const vkKb = {
      inline: true,
      buttons: [
        [
          {
            action: {
              type: "open_link",
              link: "{{order.yandex_navigator}}",
              label: "🧭 Яндекс.Навигатор"
            }
          }
        ],
        [
          {
            action: {
              type: "callback",
              label: "📱 Доставлен (СБП QR)",
              payload: "{\"cmd\": \"courier_deliver\", \"order_id\": {{order.id}}, \"pay\": \"sbp\"}"
            },
            color: "positive"
          },
          {
            action: {
              type: "callback",
              label: "💵 Наличные",
              payload: "{\"cmd\": \"courier_deliver\", \"order_id\": {{order.id}}, \"pay\": \"cash\"}"
            },
            color: "primary"
          }
        ],
        [
          {
            action: {
              type: "callback",
              label: "💳 Терминал (Картой)",
              payload: "{\"cmd\": \"courier_deliver\", \"order_id\": {{order.id}}, \"pay\": \"card\"}"
            },
            color: "secondary"
          }
        ]
      ]
    }
    currentTemplate.value.keyboard_json = JSON.stringify(vkKb, null, 2)
  } else if (platform === 'telegram') {
    const tgKb = {
      inline_keyboard: [
        [
          { text: "🧭 Яндекс.Навигатор", url: "{{order.yandex_navigator}}" }
        ],
        [
          { text: "📱 Доставлен (СБП QR)", callback_data: "cdeliv:{{order.id}}:sbp" },
          { text: "💵 Наличные", callback_data: "cdeliv:{{order.id}}:cash" }
        ],
        [
          { text: "💳 Терминал (Картой)", callback_data: "cdeliv:{{order.id}}:card" }
        ]
      ]
    }
    currentTemplate.value.keyboard_telegram = JSON.stringify(tgKb, null, 2)
  } else if (platform === 'max') {
    const maxKb = {
      buttons: [
        [
          { type: "link", text: "🧭 Яндекс.Навигатор", url: "{{order.yandex_navigator}}" }
        ],
        [
          { type: "callback", text: "📱 Доставлен (СБП QR)", payload: "cdeliv:{{order.id}}:sbp" },
          { type: "callback", text: "💵 Наличные", payload: "cdeliv:{{order.id}}:cash" }
        ],
        [
          { type: "callback", text: "💳 Терминал (Картой)", payload: "cdeliv:{{order.id}}:card" }
        ]
      ]
    }
    currentTemplate.value.keyboard_max = JSON.stringify(maxKb, null, 2)
  }
}

const editKeyboard = (platform) => {
  activeKbPlatform.value = platform
  let rawJson = ''
  if (platform === 'vk') {
    rawJson = currentTemplate.value.keyboard_json
  } else if (platform === 'telegram') {
    rawJson = currentTemplate.value.keyboard_telegram
  } else if (platform === 'max') {
    rawJson = currentTemplate.value.keyboard_max
  }
  
  try {
    const data = JSON.parse(rawJson || '{}')
    let buttons = []
    if (platform === 'vk') {
      buttons = data.buttons || []
    } else if (platform === 'telegram') {
      buttons = data.inline_keyboard || []
    } else if (platform === 'max') {
      buttons = data.buttons || []
    }
    
    kbRows.value = buttons.map(row => 
      row.map(btn => {
        let label = ''
        let type = 'text'
        let link = ''
        let color = 'primary'
        
        if (platform === 'vk') {
          label = btn.action.label
          type = btn.action.type
          link = btn.action.link || ''
          color = btn.color || 'primary'
        } else if (platform === 'telegram') {
          label = btn.text
          type = btn.url ? 'open_link' : 'text'
          link = btn.url || ''
          color = 'primary'
        } else if (platform === 'max') {
          label = btn.action?.label || btn.label || ''
          type = btn.action?.type || btn.type || 'text'
          link = btn.action?.link || btn.link || ''
          color = btn.color || 'primary'
        }
        
        return { label, type, link, color }
      })
    )
  } catch (e) {
    kbRows.value = []
  }
  showKeyboardEditor.value = true
}

const sendingBroadcast = ref(false)
const searchQuery = ref('')

const availableEvents = [
  { id: 'order_new_all', name: 'Новый заказ (любой: доставка, самовывоз, зал)', icon: 'mdi-bell-ring' },
  { id: 'order_new', name: 'Новый заказ на доставку (курьер)', icon: 'mdi-bike-fast' },
  { id: 'courier_assigned', name: 'Назначение курьера', icon: 'mdi-account-check' },
  { id: 'change_cooking_time', name: 'Время готовности на кухне', icon: 'mdi-chef-hat' },
  { id: 'order_status_update', name: 'Статус заказа', icon: 'mdi-list-status' },
  { id: 'order_amount_changed', name: 'Изменение суммы', icon: 'mdi-cash-sync' },
  { id: 'order_address_changed', name: 'Изменение адреса', icon: 'mdi-map-marker-distance' },
  { id: 'order_time_changed', name: 'Изменение времени', icon: 'mdi-clock-fast' },
  { id: 'order_items_changed', name: 'Изменение состава', icon: 'mdi-basket' },
  { id: 'order_cancelled', name: 'Отмена заказа', icon: 'mdi-close-octagon' },
  { id: 'shift_open', name: 'Открытие смены', icon: 'mdi-account-clock' },
  { id: 'shift_close', name: 'Закрытие смены', icon: 'mdi-account-off' },
  { id: 'bonus_order', name: 'Заказ за баллы', icon: 'mdi-star-circle' },
  { id: 'system_alert', name: 'Системный алерт', icon: 'mdi-alert' },
  { id: 'purchase_list_sent', name: 'Отправка списка закупа', icon: 'mdi-package-variant-closed' },
]

const employeeRoles = ref([])

const fetchRoles = async () => {
  try {
    const res = await fetch(`${API_BASE}/roles`, { headers: getAuthHeaders() })
    if (res.ok) {
      employeeRoles.value = await res.json()
    }
  } catch (e) {
    console.error('Ошибка загрузки ролей', e)
  }
}

// Мультивыбор шаблонов и массовые операции
const templateCategoryFilter = ref('all') // 'all', 'system', 'courier', 'custom'
const templateViewMode = ref(typeof localStorage !== 'undefined' ? (localStorage.getItem('vk_template_view_mode') || 'list') : 'list')
watch(templateViewMode, (val) => {
  if (typeof localStorage !== 'undefined') localStorage.setItem('vk_template_view_mode', val)
})
const selectedTemplateIds = ref([])

const visibleTemplates = computed(() => {
  if (templateCategoryFilter.value === 'system') return systemTemplates.value
  if (templateCategoryFilter.value === 'courier') return courierTemplates.value
  if (templateCategoryFilter.value === 'custom') return customTemplates.value
  return [...systemTemplates.value, ...courierTemplates.value, ...customTemplates.value]
})

const isAllTemplatesSelected = computed(() => {
  return visibleTemplates.value.length > 0 && visibleTemplates.value.every(t => selectedTemplateIds.value.includes(t.id))
})

const toggleSelectAllTemplates = () => {
  if (isAllTemplatesSelected.value) {
    const visibleIds = new Set(visibleTemplates.value.map(t => t.id))
    selectedTemplateIds.value = selectedTemplateIds.value.filter(id => !visibleIds.has(id))
  } else {
    const set = new Set([...selectedTemplateIds.value, ...visibleTemplates.value.map(t => t.id)])
    selectedTemplateIds.value = Array.from(set)
  }
}

const bulkChannelsDialog = ref(false)
const bulkChannelsForm = ref({ send_vk: true, send_max: false, send_tg: false, send_sms: false })
const bulkBotDialog = ref(false)
const bulkSelectedBotId = ref(null)
const bulkLoading = ref(false)

const bulkDeleteTemplates = async () => {
  if (!selectedTemplateIds.value.length) return
  if (!confirm(`Вы действительно хотите удалить ${selectedTemplateIds.value.length} выбранных шаблонов?`)) return
  bulkLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/templates/bulk-delete`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ template_ids: selectedTemplateIds.value })
    })
    if (res.ok) {
      showMessage(`Успешно удалено шаблонов: ${selectedTemplateIds.value.length}`)
      selectedTemplateIds.value = []
      fetchTemplates()
    } else {
      showMessage('Ошибка массового удаления', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  } finally {
    bulkLoading.value = false
  }
}

const applyBulkChannels = async () => {
  if (!selectedTemplateIds.value.length) return
  bulkLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/templates/bulk-channels`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        template_ids: selectedTemplateIds.value,
        send_vk: bulkChannelsForm.value.send_vk,
        send_tg: bulkChannelsForm.value.send_tg,
        send_max: bulkChannelsForm.value.send_max,
        send_sms: bulkChannelsForm.value.send_sms,
      })
    })
    if (res.ok) {
      showMessage(`Каналы отправки обновлены для ${selectedTemplateIds.value.length} шаблонов`)
      bulkChannelsDialog.value = false
      fetchTemplates()
    } else {
      showMessage('Ошибка обновления каналов', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  } finally {
    bulkLoading.value = false
  }
}

const applyBulkBot = async () => {
  if (!selectedTemplateIds.value.length) return
  bulkLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/templates/bulk-bot`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        template_ids: selectedTemplateIds.value,
        vk_bot_id: bulkSelectedBotId.value
      })
    })
    if (res.ok) {
      showMessage(`Группа VK обновлена для ${selectedTemplateIds.value.length} шаблонов`)
      bulkBotDialog.value = false
      fetchTemplates()
    } else {
      showMessage('Ошибка смены группы', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  } finally {
    bulkLoading.value = false
  }
}

const bulkToggleStatus = async (status) => {
  if (!selectedTemplateIds.value.length) return
  bulkLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/templates/bulk-status`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        template_ids: selectedTemplateIds.value,
        is_active: status
      })
    })
    if (res.ok) {
      showMessage(`${status ? 'Включено' : 'Отключено'} шаблонов: ${selectedTemplateIds.value.length}`)
      fetchTemplates()
    } else {
      showMessage('Ошибка смены статуса', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  } finally {
    bulkLoading.value = false
  }
}

const testSendingTplId = ref(null)

const testSendTemplate = async (tpl) => {
  testSendingTplId.value = tpl.id
  try {
    const res = await fetch(`${API_BASE}/templates/${tpl.id}/test-send`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({})
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      showMessage(`Тестовое сообщение отправлено (${data.recipient || 'получателю'})`)
    } else {
      const msg = data.detail || data.rendered_text || 'Ошибка отправки тестового сообщения'
      showMessage(msg, 'warning')
    }
  } catch (e) {
    showMessage('Ошибка отправки теста', 'error')
  } finally {
    testSendingTplId.value = null
  }
}

const formatRoles = (targetRoles) => {
  if (!targetRoles) return 'Все'
  try {
    const parsed = typeof targetRoles === 'string' ? JSON.parse(targetRoles) : targetRoles
    if (Array.isArray(parsed)) {
      return parsed.length > 0 ? parsed.join(', ') : 'Не выбраны'
    }
    return String(parsed)
  } catch (e) {
    return String(targetRoles)
  }
}

const countAccounts = (targetAccounts) => {
  if (!targetAccounts) return 0
  try {
    const parsed = typeof targetAccounts === 'string' ? JSON.parse(targetAccounts) : targetAccounts
    return Array.isArray(parsed) ? parsed.length : 0
  } catch (e) {
    return 0
  }
}

const getTargetModeHint = (mode) => {
  switch (mode) {
    case 'roles': return 'Уведомление получат только сотрудники, имеющие одну из выбранных должностей'
    case 'specific': return 'Уведомление получат исключительно персонально выбранные сотрудники'
    case 'assigned_only': return 'Уведомление уйдет исключительно тому курьеру/сотруднику, который назначен на данный заказ'
    case 'assigned_and_admins': return 'Уведомление уйдет назначенному курьеру, а также управляющим/администраторам'
    default: return 'Уведомление получат все сотрудники с активной подпиской на это событие'
  }
}

const openCreateTemplate = () => {
  currentTemplate.value = {
    name: '',
    text: '',
    keyboard_json: '',
    event_type: null,
    keyboard_telegram: '',
    keyboard_max: '',
    target_mode: 'all',
    target_roles: [],
    target_accounts: [],
    is_active: true,
    include_statuses: null,
    attach_sbp_qr: false,
    chain_config: null,
    description: '',
    vk_bot_id: null,
    send_vk: true,
    send_tg: false,
    send_max: false,
    send_sms: false,
    edit_existing_message: true,
    collapse_on_delivered: true,
    show_courier_action_buttons: true,
  }
  selectedTemplateStatuses.value = []
  templateDialog.value = true
}

const orderStatusOptions = [
  { title: 'Готовится (cooking)', value: 'cooking', color: 'warning', icon: 'mdi-pot-steam' },
  { title: 'Готов к выдаче (ready_for_pickup)', value: 'ready_for_pickup', color: 'info', icon: 'mdi-package-variant-closed-check' },
  { title: 'В пути (delivering)', value: 'delivering', color: 'primary', icon: 'mdi-moped' },
  { title: 'Доставлен (delivered)', value: 'delivered', color: 'success', icon: 'mdi-check-all' },
  { title: 'Отменен (cancelled)', value: 'cancelled', color: 'error', icon: 'mdi-close-circle' },
  { title: 'Подтвержден (confirmed)', value: 'confirmed', color: 'secondary', icon: 'mdi-check' },
  { title: 'Новый / Ожидает (new/unconfirmed)', value: 'unconfirmed', color: 'grey', icon: 'mdi-help-circle' },
]

const courierEventTypes = [
  'order_new',
  'courier_assigned',
  'change_cooking_time',
  'order_status_update',
  'order_amount_changed',
  'order_items_changed',
  'order_address_changed',
  'order_time_changed',
  'order_cancelled'
]

const getEventName = (eventId) => {
  const ev = availableEvents.find(e => e.id === eventId)
  return ev ? ev.name : eventId
}
const getEventIcon = (eventId) => {
  const ev = availableEvents.find(e => e.id === eventId)
  return ev ? ev.icon : 'mdi-bell'
}

const getStageTitle = (eventType) => {
  switch (eventType) {
    case 'order_new': return 'Этап 1: Новый заказ'
    case 'courier_assigned': return 'Этап 1.1: Назначение курьера'
    case 'change_cooking_time': return 'Этап 2: Время приготовления на кухне'
    case 'order_status_update': return 'Этап 3: Смена статуса заказа'
    case 'order_amount_changed': return 'Этап 4: Изменение суммы к оплате'
    case 'order_address_changed': return 'Этап 5: Изменение адреса доставки'
    case 'order_time_changed': return 'Этап 6: Изменение времени доставки'
    case 'order_cancelled': return 'Экстренно: Отмена заказа'
    default: return 'Событие заказа'
  }
}

const getStageBadgeColor = (eventType) => {
  switch (eventType) {
    case 'order_new':
    case 'courier_assigned': return 'primary'
    case 'change_cooking_time': return 'warning'
    case 'order_status_update': return 'info'
    case 'order_amount_changed': return 'success'
    case 'order_address_changed': return 'purple'
    case 'order_time_changed': return 'cyan'
    case 'order_cancelled': return 'error'
    default: return 'grey'
  }
}

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

const hoursList = computed(() => {
  const list = []
  for (let i = 0; i < 24; i++) {
    const formatHour = i < 10 ? `0${i}:00` : `${i}:00`
    list.push({ title: formatHour, value: i })
  }
  return list
})

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
    (a.vk_user_id && a.vk_user_id.toString().includes(q)) ||
    (a.tg_user_id && a.tg_user_id.toString().includes(q))
  )
})

const systemTemplates = computed(() => {
  return templates.value.filter(t => t.event_type && !courierEventTypes.includes(t.event_type))
})

const customTemplates = computed(() => {
  return templates.value.filter(t => t.event_type === null || t.event_type === undefined)
})

const courierTemplates = computed(() => {
  const result = []
  for (const evType of courierEventTypes) {
    const found = templates.value.find(t => t.event_type === evType)
    if (found) {
      result.push(found)
    }
  }
  return result
})

const toggleTemplateActive = async (tpl) => {
  try {
    const newStatus = !tpl.is_active
    const res = await fetch(`${API_BASE}/templates/${tpl.id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ name: tpl.name, text: tpl.text, is_active: newStatus })
    })
    if (res.ok) {
      tpl.is_active = newStatus
      showMessage(newStatus ? `Уведомление «${tpl.name}» включено` : `Уведомление «${tpl.name}» выключено`)
    } else {
      const errorData = await res.json().catch(() => ({}))
      const detailMsg = Array.isArray(errorData.detail)
        ? errorData.detail.map(d => d.msg || JSON.stringify(d)).join(', ')
        : (errorData.detail || 'Ошибка изменения активности шаблона')
      showMessage(detailMsg, 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  }
}

const toggleTemplateQr = async (tpl) => {
  try {
    const newQr = !tpl.attach_sbp_qr
    const res = await fetch(`${API_BASE}/templates/${tpl.id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ name: tpl.name, text: tpl.text, attach_sbp_qr: newQr })
    })
    if (res.ok) {
      tpl.attach_sbp_qr = newQr
      showMessage(newQr ? 'Вложение QR-кода СБП с надписью включено' : 'Вложение QR-кода СБП выключено')
    } else {
      const errorData = await res.json().catch(() => ({}))
      const detailMsg = Array.isArray(errorData.detail)
        ? errorData.detail.map(d => d.msg || JSON.stringify(d)).join(', ')
        : (errorData.detail || 'Ошибка сохранения')
      showMessage(detailMsg, 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  }
}

const updateTemplateStatusFilter = async (tpl, statusValue) => {
  try {
    let currentStatuses = []
    if (tpl.include_statuses) {
      try {
        currentStatuses = JSON.parse(tpl.include_statuses)
        if (!Array.isArray(currentStatuses)) currentStatuses = []
      } catch (e) {
        currentStatuses = []
      }
    }
    
    if (currentStatuses.includes(statusValue)) {
      currentStatuses = currentStatuses.filter(s => s !== statusValue)
    } else {
      currentStatuses.push(statusValue)
    }
    
    const jsonVal = JSON.stringify(currentStatuses)
    const res = await fetch(`${API_BASE}/templates/${tpl.id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ name: tpl.name, text: tpl.text, include_statuses: jsonVal })
    })
    if (res.ok) {
      tpl.include_statuses = jsonVal
      showMessage('Фильтр статусов обновлен')
    } else {
      const errorData = await res.json().catch(() => ({}))
      const detailMsg = Array.isArray(errorData.detail)
        ? errorData.detail.map(d => d.msg || JSON.stringify(d)).join(', ')
        : (errorData.detail || 'Ошибка обновления статусов')
      showMessage(detailMsg, 'error')
    }
  } catch (e) {
    showMessage('Ошибка обновления статусов', 'error')
  }
}

const parseChainConfig = (tpl) => {
  if (!tpl) return {}
  if (!tpl.chain_config) {
    const isNewOrCourier = ['order_new', 'courier_assigned'].includes(tpl.event_type)
    return {
      require_courier_assigned: true,
      resend_on_courier_reassigned: isNewOrCourier,
      require_cooking_time_set: true,
      require_cooking_time_changed: tpl.event_type === 'change_cooking_time',
      require_amount_changed: tpl.event_type === 'order_amount_changed',
      require_address_changed: tpl.event_type === 'order_address_changed',
      require_time_changed: tpl.event_type === 'order_time_changed',
      only_unpaid: false,
      attach_sbp_qr: isNewOrCourier,
      check_status_in: tpl.event_type === 'order_status_update' ? ['cooking', 'ready_for_pickup', 'delivering', 'cancelled'] : []
    }
  }
  try {
    const parsed = typeof tpl.chain_config === 'string' ? JSON.parse(tpl.chain_config) : tpl.chain_config
    return {
      require_courier_assigned: parsed.require_courier_assigned !== undefined ? !!parsed.require_courier_assigned : true,
      resend_on_courier_reassigned: !!parsed.resend_on_courier_reassigned,
      require_cooking_time_set: parsed.require_cooking_time_set !== undefined ? !!parsed.require_cooking_time_set : true,
      require_cooking_time_changed: !!parsed.require_cooking_time_changed,
      require_amount_changed: !!parsed.require_amount_changed,
      require_address_changed: !!parsed.require_address_changed,
      require_time_changed: !!parsed.require_time_changed,
      only_unpaid: !!parsed.only_unpaid,
      attach_sbp_qr: !!parsed.attach_sbp_qr,
      check_status_in: Array.isArray(parsed.check_status_in) ? parsed.check_status_in : []
    }
  } catch (e) {
    return {}
  }
}

const toggleChainCondition = async (tpl, conditionKey) => {
  try {
    const config = parseChainConfig(tpl)
    config[conditionKey] = !config[conditionKey]
    
    const patchPayload = {
      name: tpl.name,
      text: tpl.text,
      chain_config: JSON.stringify(config)
    }
    if (conditionKey === 'attach_sbp_qr') {
      patchPayload.attach_sbp_qr = config.attach_sbp_qr
      tpl.attach_sbp_qr = config.attach_sbp_qr
    }
    
    const res = await fetch(`${API_BASE}/templates/${tpl.id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(patchPayload)
    })
    
    if (res.ok) {
      tpl.chain_config = JSON.stringify(config)
      const labels = {
        require_courier_assigned: 'Проверка «Курьер назначен»',
        resend_on_courier_reassigned: 'Повтор при переназначении курьера',
        require_cooking_time_set: 'Проверка «Время кухни задано»',
        require_cooking_time_changed: 'Только при повторном изменении времени готовки',
        require_amount_changed: 'Проверка «Сумма изменена»',
        require_address_changed: 'Проверка «Адрес изменен»',
        require_time_changed: 'Проверка «Время доставки изменено»',
        only_unpaid: 'Проверка «Только неоплаченные»',
        attach_sbp_qr: 'Вложение QR-кода СБП с надписью'
      }
      const label = labels[conditionKey] || conditionKey
      showMessage(`${label}: ${config[conditionKey] ? 'ВКЛЮЧЕНО' : 'ВЫКЛЮЧЕНО'}`)
    } else {
      const errData = await res.json().catch(() => ({}))
      const detailMsg = Array.isArray(errData.detail)
        ? errData.detail.map(d => d.msg || JSON.stringify(d)).join(', ')
        : (errData.detail || 'Ошибка сохранения условия цепочки')
      showMessage(detailMsg, 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  }
}

const isStatusSelected = (tpl, statusValue) => {
  if (!tpl || !tpl.include_statuses) return false
  try {
    const list = JSON.parse(tpl.include_statuses)
    return Array.isArray(list) && list.includes(statusValue)
  } catch (e) {
    return false
  }
}

const openPreviewQrDialog = (tpl) => {
  previewQrDialog.value = true
  generatePreviewQr()
}

const generatePreviewQr = async () => {
  previewQrLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/preview-sbp-qr`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(previewQrData.value)
    })
    if (res.ok) {
      const data = await res.json()
      previewQrResultUrl.value = data.url
    } else {
      showMessage('Ошибка генерации превью QR', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения при генерации QR', 'error')
  } finally {
    previewQrLoading.value = false
  }
}

const togglingTplChannel = ref({})

const toggleTemplateChannel = async (tpl, channel) => {
  const key = `${tpl.id}_${channel}`
  if (togglingTplChannel.value[key]) return
  togglingTplChannel.value[key] = true
  
  const currentVal = tpl[`send_${channel}`] !== false && tpl[`send_${channel}`] !== 0
  const newVal = !currentVal
  tpl[`send_${channel}`] = newVal
  
  try {
    const res = await fetch(`${API_BASE}/templates/${tpl.id}/toggle-channel`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ channel, enabled: newVal })
    })
    if (res.ok) {
      showMessage(`Канал ${channel.toUpperCase()} для «${tpl.name}» ${newVal ? 'включен' : 'отключен'}`)
    } else {
      tpl[`send_${channel}`] = currentVal
      const err = await res.json().catch(() => ({}))
      showMessage(err.detail || 'Ошибка переключения канала', 'error')
    }
  } catch (e) {
    tpl[`send_${channel}`] = currentVal
    showMessage('Ошибка соединения', 'error')
  } finally {
    delete togglingTplChannel.value[key]
  }
}

const settingTplBot = ref({})

const setTemplateBot = async (tpl, botId) => {
  const key = `${tpl.id}`
  if (settingTplBot.value[key]) return
  settingTplBot.value[key] = true
  
  const oldBotId = tpl.vk_bot_id
  tpl.vk_bot_id = botId
  
  try {
    const res = await fetch(`${API_BASE}/templates/${tpl.id}/set-bot`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ vk_bot_id: botId })
    })
    if (res.ok) {
      const bObj = bots.value.find(b => b.id === botId)
      const bName = bObj ? `${bObj.name} (${bObj.vk_group_id})` : 'Основной бот'
      showMessage(`Для «${tpl.name}» выбрано сообщество: ${bName}`)
    } else {
      tpl.vk_bot_id = oldBotId
      const err = await res.json().catch(() => ({}))
      showMessage(err.detail || 'Ошибка выбора бота', 'error')
    }
  } catch (e) {
    tpl.vk_bot_id = oldBotId
    showMessage('Ошибка соединения', 'error')
  } finally {
    delete settingTplBot.value[key]
  }
}

const setTemplateMaxBot = async (tpl, botId, mode) => {
  const key = `${tpl.id}_max`
  if (settingTplMaxBot.value[key]) return
  settingTplMaxBot.value[key] = true
  
  const oldBotId = tpl.max_bot_id
  const oldMode = tpl.max_send_mode
  tpl.max_bot_id = botId
  if (mode !== undefined) tpl.max_send_mode = mode
  
  try {
    const res = await fetch(`${API_BASE}/templates/${tpl.id}/set-max-bot`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ 
        max_bot_id: botId,
        max_send_mode: tpl.max_send_mode || 'cascade'
      })
    })
    if (res.ok) {
      const bObj = maxBots.value.find(b => b.id === botId)
      const bName = bObj ? `${bObj.bot_name} (@${bObj.bot_username || bObj.id})` : 'Основной бот'
      showMessage(`Для «${tpl.name}» сохранен MAX: ${bName}`)
    } else {
      tpl.max_bot_id = oldBotId
      tpl.max_send_mode = oldMode
      const err = await res.json().catch(() => ({}))
      showMessage(err.detail || 'Ошибка выбора бота MAX', 'error')
    }
  } catch (e) {
    tpl.max_bot_id = oldBotId
    tpl.max_send_mode = oldMode
    showMessage('Ошибка соединения', 'error')
  } finally {
    delete settingTplMaxBot.value[key]
  }
}

const bulkChainsLoading = ref(false)

const bulkToggleCourierChains = async (enable) => {
  bulkChainsLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/templates/bulk-toggle-chains`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ enabled: enable })
    })
    if (res.ok) {
      courierTemplates.value.forEach(t => {
        t.is_active = enable
      })
      showMessage(enable ? 'Все шаги цепочки курьера успешно активированы' : 'Все шаги цепочки курьера отключены')
    } else {
      const err = await res.json().catch(() => ({}))
      showMessage(err.detail || 'Ошибка массового переключения цепочек', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения', 'error')
  } finally {
    bulkChainsLoading.value = false
  }
}

const openEditTemplate = (tpl) => {
  let parsedRoles = []
  if (tpl && tpl.target_roles) {
    try {
      parsedRoles = typeof tpl.target_roles === 'string' ? JSON.parse(tpl.target_roles) : tpl.target_roles
      if (!Array.isArray(parsedRoles)) parsedRoles = [parsedRoles]
    } catch (e) {
      parsedRoles = [tpl.target_roles]
    }
  }
  let parsedAccounts = []
  if (tpl && tpl.target_accounts) {
    try {
      parsedAccounts = typeof tpl.target_accounts === 'string' ? JSON.parse(tpl.target_accounts) : tpl.target_accounts
      if (!Array.isArray(parsedAccounts)) parsedAccounts = [parsedAccounts]
    } catch (e) {
      parsedAccounts = []
    }
  }
  currentTemplate.value = {
    target_mode: 'all',
    is_active: true,
    attach_sbp_qr: false,
    include_statuses: null,
    chain_config: null,
    description: '',
    vk_bot_id: null,
    max_bot_id: null,
    max_send_mode: 'cascade',
    send_vk: true,
    send_tg: false,
    send_max: false,
    send_sms: false,
    ...tpl,
    max_bot_id: tpl?.max_bot_id || null,
    max_send_mode: tpl?.max_send_mode || 'cascade',
    target_roles: parsedRoles,
    target_accounts: parsedAccounts,
    edit_existing_message: tpl?.edit_existing_message !== undefined && tpl?.edit_existing_message !== null ? Boolean(tpl.edit_existing_message) : true,
    collapse_on_delivered: tpl?.collapse_on_delivered !== undefined && tpl?.collapse_on_delivered !== null ? Boolean(tpl.collapse_on_delivered) : true,
    show_courier_action_buttons: tpl?.show_courier_action_buttons !== undefined && tpl?.show_courier_action_buttons !== null ? Boolean(tpl.show_courier_action_buttons) : true,
  }
  currentChainConfig.value = parseChainConfig(tpl)
  if (tpl && tpl.include_statuses) {
    try {
      const parsed = JSON.parse(tpl.include_statuses)
      selectedTemplateStatuses.value = Array.isArray(parsed) ? parsed : []
    } catch (e) {
      selectedTemplateStatuses.value = []
    }
  } else if (currentChainConfig.value.check_status_in && currentChainConfig.value.check_status_in.length > 0) {
    selectedTemplateStatuses.value = [...currentChainConfig.value.check_status_in]
  } else {
    selectedTemplateStatuses.value = ['cooking', 'ready_for_pickup', 'delivering', 'delivered', 'cancelled']
  }
  templateDialog.value = true
}

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
    showMessage('Ошибка загрузки получателей', 'error')
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

const channelSettingsLoading = ref(false)
const channelSettings = ref(null)
const checkingVkBot = ref({})
const sendingTestVkBot = ref({})
const togglingCourierChainsLoading = ref(false)
const togglingTemplateLoading = ref({})
const bulkTemplatesLoading = ref(false)

const loadChannelSettings = async (accountId) => {
  channelSettingsLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/accounts/${accountId}/channel-settings`, { headers: getAuthHeaders() })
    if (res.ok) {
      channelSettings.value = await res.json()
    } else {
      showMessage('Ошибка загрузки настроек каналов получателя', 'error')
    }
  } catch (e) {
    console.error('Ошибка loadChannelSettings', e)
    showMessage('Ошибка соединения при загрузке настроек каналов', 'error')
  } finally {
    channelSettingsLoading.value = false
  }
}

const openSubscriptions = async account => {
  currentAccount.value = account
  subscriptionDialog.value = true
  await Promise.all([
    loadChannelSettings(account.id),
    fetchSubscriptions(account.id)
  ])
}

const checkVkGroupAuth = async (botId) => {
  if (!currentAccount.value) return
  checkingVkBot.value[botId] = true
  try {
    const res = await fetch(`${API_BASE}/accounts/${currentAccount.value.id}/check-vk-group/${botId}`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (res.ok) {
      if (data.is_messages_allowed) {
        showMessage(`Сообщения от «${data.name}» разрешены!`, 'success')
      } else {
        showMessage(`Сообщения от «${data.name}» не разрешены. Нажмите «Разрешить сообщения в ВК»`, 'warning')
      }
      if (channelSettings.value) {
        const grp = channelSettings.value.vk_groups?.find(g => g.id === botId)
        if (grp) {
          grp.is_messages_allowed = data.is_messages_allowed
          grp.error = data.is_messages_allowed ? null : 'Сообщения не разрешены'
        }
        if (channelSettings.value.courier_chains?.bot?.id === botId) {
          channelSettings.value.courier_chains.is_messages_allowed = data.is_messages_allowed
        }
        if (channelSettings.value.templates) {
          for (const t of channelSettings.value.templates) {
            if (t.vk_bot_id === botId) {
              t.bot_is_allowed = data.is_messages_allowed
            }
          }
        }
      }
    } else {
      showMessage(data.detail || 'Ошибка проверки авторизации сообщений', 'error')
    }
  } catch (e) {
    console.error('Ошибка checkVkGroupAuth', e)
    showMessage('Сетевая ошибка при проверке VK', 'error')
  } finally {
    checkingVkBot.value[botId] = false
  }
}

const sendTestVkGroup = async (botId) => {
  if (!currentAccount.value) return
  sendingTestVkBot.value[botId] = true
  try {
    const res = await fetch(`${API_BASE}/accounts/${currentAccount.value.id}/send-test-vk-group/${botId}`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      showMessage(data.message || 'Тестовое сообщение успешно отправлено в ВК!', 'success')
    } else {
      showMessage(data.detail || data.message || 'Ошибка отправки тестового сообщения', 'error')
    }
  } catch (e) {
    console.error('Ошибка sendTestVkGroup', e)
    showMessage('Сетевая ошибка при отправке теста', 'error')
  } finally {
    sendingTestVkBot.value[botId] = false
  }
}

const toggleCourierChains = async (val) => {
  if (!currentAccount.value) return
  togglingCourierChainsLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/accounts/${currentAccount.value.id}/toggle-courier-chains`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ allow_courier_chains: val })
    })
    const data = await res.json()
    if (res.ok) {
      if (channelSettings.value?.courier_chains) {
        channelSettings.value.courier_chains.allow_courier_chains = val
      }
      currentAccount.value.allow_courier_chains = val
      const acc = accounts.value.find(a => a.id === currentAccount.value.id)
      if (acc) acc.allow_courier_chains = val
      showMessage(val ? 'Цепочки курьера включены для сотрудника' : 'Цепочки курьера отключены для сотрудника', 'success')
      await fetchSubscriptions(currentAccount.value.id)
    } else {
      showMessage(data.detail || 'Ошибка изменения цепочек курьера', 'error')
    }
  } catch (e) {
    console.error('Ошибка toggleCourierChains', e)
    showMessage('Ошибка соединения', 'error')
  } finally {
    togglingCourierChainsLoading.value = false
  }
}

const toggleCourierChainChannel = async (channel, enabled) => {
  if (!currentAccount.value) return
  try {
    const res = await fetch(`${API_BASE}/accounts/${currentAccount.value.id}/toggle-courier-chains`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ channel: channel, enabled: enabled })
    })
    const data = await res.json()
    if (res.ok) {
      if (channelSettings.value?.courier_chains) {
        if (channel === 'vk') channelSettings.value.courier_chains.send_vk = enabled
        if (channel === 'tg') channelSettings.value.courier_chains.send_tg = enabled
        if (channel === 'max') channelSettings.value.courier_chains.send_max = enabled
        if (channel === 'sms') channelSettings.value.courier_chains.send_sms = enabled
      }
      showMessage(`Канал ${channel.toUpperCase()} для цепочек курьера ${enabled ? 'включен' : 'отключен'}`, 'success')
      await fetchSubscriptions(currentAccount.value.id)
    } else {
      showMessage(data.detail || 'Ошибка изменения канала курьера', 'error')
    }
  } catch (e) {
    console.error('Ошибка toggleCourierChainChannel', e)
    showMessage('Ошибка соединения', 'error')
  }
}

const toggleTemplateSubscription = async (tpl, isSubscribed) => {
  if (!currentAccount.value) return
  togglingTemplateLoading.value[tpl.event_type] = true
  try {
    const res = await fetch(`${API_BASE}/accounts/${currentAccount.value.id}/toggle-template-subscription`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ template_id: tpl.id, event_type: tpl.event_type, subscribed: isSubscribed })
    })
    const data = await res.json()
    if (res.ok) {
      tpl.subscribed = isSubscribed
      showMessage(isSubscribed ? `Подписка на «${tpl.name}» включена` : `Подписка на «${tpl.name}» отключена`, 'success')
      await fetchSubscriptions(currentAccount.value.id)
    } else {
      showMessage(data.detail || 'Ошибка изменения подписки', 'error')
    }
  } catch (e) {
    console.error('Ошибка toggleTemplateSubscription', e)
    showMessage('Ошибка соединения', 'error')
  } finally {
    togglingTemplateLoading.value[tpl.event_type] = false
  }
}

const toggleTemplateSubChannel = async (tpl, channel, enabled) => {
  if (!currentAccount.value) return
  try {
    const res = await fetch(`${API_BASE}/accounts/${currentAccount.value.id}/toggle-template-subscription`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ template_id: tpl.id, event_type: tpl.event_type, channel: channel, enabled: enabled, subscribed: true })
    })
    const data = await res.json()
    if (res.ok) {
      if (tpl.sub_channels) {
        tpl.sub_channels[channel] = enabled
      }
      showMessage(`Канал ${channel.toUpperCase()} для «${tpl.name}» ${enabled ? 'включен' : 'отключен'}`, 'success')
      await fetchSubscriptions(currentAccount.value.id)
    } else {
      showMessage(data.detail || 'Ошибка изменения канала', 'error')
    }
  } catch (e) {
    console.error('Ошибка toggleTemplateSubChannel', e)
    showMessage('Ошибка соединения', 'error')
  }
}

const bulkTemplatesAction = async (action, channel = null) => {
  if (!currentAccount.value) return
  bulkTemplatesLoading.value = true
  try {
    const res = await fetch(`${API_BASE}/accounts/${currentAccount.value.id}/bulk-toggle-templates`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ action: action, channel: channel })
    })
    const data = await res.json()
    if (res.ok) {
      showMessage('Настройки шаблонов успешно обновлены', 'success')
      await Promise.all([
        loadChannelSettings(currentAccount.value.id),
        fetchSubscriptions(currentAccount.value.id)
      ])
    } else {
      showMessage(data.detail || 'Ошибка массового обновления', 'error')
    }
  } catch (e) {
    console.error('Ошибка bulkTemplatesAction', e)
    showMessage('Ошибка соединения', 'error')
  } finally {
    bulkTemplatesLoading.value = false
  }
}

const getSub = (eventId) => accountSubscriptions.value.find(s => s.event_type === eventId)

const updateSubscription = async (eventType, mode, interval, startHour = 0, endHour = 23, sendVk = true, sendTg = false, sendMax = false, sendSms = false) => {
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
        send_vk: sendVk,
        send_tg: sendTg,
        send_max: sendMax,
        send_sms: sendSms
      }),
    })
    await fetchSubscriptions(currentAccount.value.id)
  } catch (e) {
    showMessage('Ошибка обновления подписки', 'error')
  }
}

const onChannelToggle = async (eventId, channel, val) => {
  const sub = getSub(eventId)
  let sendVk = sub ? sub.send_vk : false
  let sendTg = sub ? sub.send_tg : false
  let sendMax = sub ? sub.send_max : false
  let sendSms = sub ? sub.send_sms : false

  if (channel === 'vk') sendVk = val
  if (channel === 'tg') sendTg = val
  if (channel === 'max') sendMax = val
  if (channel === 'sms') sendSms = val

  if (sendVk || sendTg || sendMax || sendSms) {
    const mode = sub ? sub.delivery_mode : 'realtime'
    const interval = sub ? sub.interval_minutes : 0
    const startHour = sub ? sub.active_start_hour : 0
    const endHour = sub ? sub.active_end_hour : 23
    await updateSubscription(eventId, mode, interval, startHour, endHour, sendVk, sendTg, sendMax, sendSms)
  } else {
    if (sub) {
      try {
        const res = await fetch(`${API_BASE}/subscriptions/${sub.id}`, { 
          method: 'DELETE',
          headers: getAuthHeaders()
        })
        if (res.ok) fetchSubscriptions(currentAccount.value.id)
      } catch (e) {
        showMessage('Ошибка удаления подписки', 'error')
      }
    }
  }
}

const addAccount = async () => {
  addingAccount.value = true
  try {
    const selectedEmpId = recipientType.value === 'employee' ? (newAccount.value.employeeId || null) : null
    const selectedUserId = recipientType.value === 'user' ? (newAccount.value.userId || null) : null
    const res = await fetch(`${API_BASE}/accounts`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: newAccount.value.name,
        vk_link: newAccount.value.vkLink || null,
        phone: newAccount.value.phone || null,
        employee_id: selectedEmpId,
        user_id: selectedUserId,
        is_courier: Boolean(newAccount.value.is_courier),
        tg_user_id: newAccount.value.tg_user_id ? parseInt(newAccount.value.tg_user_id) : null,
        max_user_id: newAccount.value.max_user_id || newAccount.value.phone || null,
        use_vk: newAccount.value.use_vk,
        use_tg: newAccount.value.use_tg,
        use_max: newAccount.value.use_max,
        use_sms: newAccount.value.use_sms,
        max_bot_id: newAccount.value.max_bot_id || null,
        max_send_mode: newAccount.value.max_send_mode || 'cascade',
        send_payment_qr: newAccount.value.send_payment_qr,
        payment_qr_mode: newAccount.value.payment_qr_mode,
      }),
    })

    const data = await res.json()
    if (res.ok) {
      showMessage('Получатель успешно добавлен')
      addAccountDialog.value = false
      newAccount.value = { 
        vkLink: '', name: '', phone: '', customerId: null, employeeId: null, userId: null, is_courier: false,
        tg_user_id: null, max_user_id: '', use_vk: true, use_tg: false, use_max: false, use_sms: false,
        max_bot_id: null, max_send_mode: 'cascade',
        send_payment_qr: false, payment_qr_mode: 'all'
      }
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

const openEditAccount = account => {
  fetchEmployees()
  fetchUsers()
  editingAccount.value = {
    id: account.id,
    name: account.name,
    phone: account.phone || '',
    is_active: account.is_active,
    employee_id: account.employee_id,
    user_id: account.user_id,
    is_courier: Boolean(account.is_courier),
    vk_user_id: account.vk_user_id,
    tg_user_id: account.tg_user_id,
    max_user_id: account.max_user_id || account.phone || '',
    use_vk: account.use_vk,
    use_tg: account.use_tg,
    use_max: account.use_max,
    use_sms: account.use_sms,
    max_bot_id: account.max_bot_id || null,
    max_send_mode: account.max_send_mode || 'cascade',
    send_payment_qr: account.send_payment_qr || false,
    payment_qr_mode: account.payment_qr_mode || 'all',
  }
  if (account.employee_id) {
    checkCourierStatus(account.employee_id)
  } else {
    courierValidationInfo.value = null
  }
  editAccountDialog.value = true
}

const saveAccount = async () => {
  savingAccount.value = true
  try {
    const res = await fetch(`${API_BASE}/accounts/${editingAccount.value.id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: editingAccount.value.name,
        phone: editingAccount.value.phone || null,
        is_active: editingAccount.value.is_active,
        employee_id: editingAccount.value.employee_id,
        user_id: editingAccount.value.user_id || null,
        is_courier: Boolean(editingAccount.value.is_courier),
        vk_user_id: editingAccount.value.vk_user_id || null,
        tg_user_id: editingAccount.value.tg_user_id ? parseInt(editingAccount.value.tg_user_id) : null,
        max_user_id: editingAccount.value.max_user_id || editingAccount.value.phone || null,
        use_vk: editingAccount.value.use_vk,
        use_tg: editingAccount.value.use_tg,
        use_max: editingAccount.value.use_max,
        use_sms: editingAccount.value.use_sms,
        max_bot_id: editingAccount.value.max_bot_id || null,
        max_send_mode: editingAccount.value.max_send_mode || 'cascade',
        send_payment_qr: editingAccount.value.send_payment_qr,
        payment_qr_mode: editingAccount.value.payment_qr_mode,
      })
    })
    if (res.ok) {
      showMessage('Данные получателя обновлены')
      editAccountDialog.value = false
      fetchAccounts()
    } else {
      const data = await res.json()
      showMessage(data.detail || 'Ошибка сохранения', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения с сервером', 'error')
  } finally {
    savingAccount.value = false
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
      showMessage(account.is_active ? 'Получатель деактивирован' : 'Получатель активирован')
      fetchAccounts()
    }
  } catch (e) {
    showMessage('Ошибка изменения статуса', 'error')
  }
}

const deleteAccount = async id => {
  if (!confirm('Удалить получателя? Все его подписки будут также удалены.')) return
  try {
    const res = await fetch(`${API_BASE}/accounts/${id}`, { 
      method: 'DELETE',
      headers: getAuthHeaders()
    })
    if (res.ok) {
      showMessage('Получатель удален')
      fetchAccounts()
    }
  } catch (e) {
    showMessage('Ошибка удаления получателя', 'error')
  }
}

const saveTemplate = async () => {
  try {
    const isEdit = !!currentTemplate.value.id
    const url = isEdit ? `${API_BASE}/templates/${currentTemplate.value.id}` : `${API_BASE}/templates`
    const method = isEdit ? 'PATCH' : 'POST'
    
    // Синхронизируем chain_config и статусы
    if (currentChainConfig.value) {
      if (currentTemplate.value.event_type === 'order_status_update') {
        currentChainConfig.value.check_status_in = [...selectedTemplateStatuses.value]
      }
      currentChainConfig.value.attach_sbp_qr = !!currentTemplate.value.attach_sbp_qr
      currentTemplate.value.chain_config = JSON.stringify(currentChainConfig.value)
    }
    if (currentTemplate.value.event_type === 'order_status_update') {
      currentTemplate.value.include_statuses = JSON.stringify(selectedTemplateStatuses.value)
    }

    // Сериализуем роли и аккаунты
    const rolesPayload = currentTemplate.value.target_roles && currentTemplate.value.target_roles.length > 0
      ? JSON.stringify(currentTemplate.value.target_roles)
      : null
    const accountsPayload = currentTemplate.value.target_accounts && currentTemplate.value.target_accounts.length > 0
      ? JSON.stringify(currentTemplate.value.target_accounts)
      : null

    // Очищаем пустые строки перед отправкой
    const payload = { 
      ...currentTemplate.value,
      target_roles: rolesPayload,
      target_accounts: accountsPayload
    }
    for (const key of ['keyboard_json', 'keyboard_telegram', 'keyboard_max', 'event_type', 'include_statuses', 'chain_config', 'description']) {
      if (payload[key] === '') {
        payload[key] = null
      }
    }
    if (payload.vk_bot_id === '' || payload.vk_bot_id === 0) {
      payload.vk_bot_id = null
    }
    if (payload.max_bot_id === '' || payload.max_bot_id === 0) {
      payload.max_bot_id = null
    }
    payload.max_send_mode = payload.max_send_mode || 'cascade'
    payload.edit_existing_message = Boolean(currentTemplate.value.edit_existing_message)
    payload.collapse_on_delivered = Boolean(currentTemplate.value.collapse_on_delivered)
    payload.show_courier_action_buttons = Boolean(currentTemplate.value.show_courier_action_buttons)

    const res = await fetch(url, {
      method: method,
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    if (res.ok) {
      showMessage(isEdit ? 'Шаблон обновлен' : 'Шаблон создан')
      templateDialog.value = false
      fetchTemplates()
    } else {
      const errorData = await res.json().catch(() => ({}))
      const detailMsg = Array.isArray(errorData.detail)
        ? errorData.detail.map(d => d.msg || JSON.stringify(d)).join(', ')
        : (errorData.detail || 'Ошибка сохранения шаблона')
      showMessage(detailMsg, 'error')
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
    showMessage('Ошибка верификации VK', 'error')
  }
}

const verifyAccountTg = async id => {
  try {
    const res = await fetch(`${API_BASE}/accounts/${id}/verify/tg`, { 
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
    showMessage('Ошибка верификации Telegram', 'error')
  }
}

const verifyAccountMax = async id => {
  try {
    const res = await fetch(`${API_BASE}/accounts/${id}/verify/max`, { 
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
    showMessage('Ошибка верификации MAX', 'error')
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

const savingMainBot = ref(false)

const fetchBots = async () => {
  try {
    const res = await fetch('/api/v1/vk/bots', { headers: getAuthHeaders() })
    if (res.ok) {
      const data = await res.json()
      bots.value = data
      const mainBot = data.find(b => b.is_main)
      if (mainBot) {
        selectedBotId.value = mainBot.id
      }
    }
  } catch (e) {
    console.error('Ошибка загрузки ботов VK', e)
  }
}

const saveMainBot = async () => {
  if (!selectedBotId.value) return
  savingMainBot.value = true
  try {
    const res = await fetch(`/api/v1/vk/bots/${selectedBotId.value}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify({ is_main: true }),
    })
    if (res.ok) {
      showMessage('Бот по умолчанию для системных рассылок успешно сохранен')
      await fetchBots()
    } else {
      const data = await res.json()
      showMessage(data.detail || 'Ошибка при сохранении настроек', 'error')
    }
  } catch (e) {
    showMessage('Ошибка соединения с сервером', 'error')
  } finally {
    savingMainBot.value = false
  }
}

const fetchMaxBots = async () => {
  try {
    const res = await fetch(`${API_BASE}/max-bots`, { headers: getAuthHeaders() })
    if (res.ok) {
      maxBots.value = await res.json()
    }
  } catch (e) {
    console.error('Ошибка загрузки ботов MAX', e)
  }
}

onMounted(() => {
  fetchAccounts()
  fetchEmployees()
  fetchUsers()
  fetchLogs()
  fetchTemplates()
  fetchVariables()
  fetchBots()
  fetchMaxBots()
  fetchRoles()
})
</script>

<template>
  <div class="vk-notifications-container">
    <VRow>
      <VCol cols="12">
        <VCard elevation="10" class="glass-card">
          <VCardTitle class="d-flex justify-space-between align-center pa-6">
            <div class="d-flex align-center">
              <VIcon icon="mdi-bullhorn-variant" color="primary" size="32" class="me-3 animate-vk" />
              <span class="text-h5 font-weight-bold gradient-text">Системные рассылки</span>
            </div>
            <div class="d-flex gap-2">
              <VBtn color="primary" prepend-icon="mdi-plus" rounded="lg" class="action-btn" @click="openAddAccountDialog">
                Добавить получателя
              </VBtn>
              <VBtn color="secondary" variant="tonal" prepend-icon="mdi-bullhorn" rounded="lg" class="action-btn" @click="broadcastDialog = true">
                Рассылка
              </VBtn>
            </div>
          </VCardTitle>

          <VTabs v-model="tab" class="px-6" color="primary">
            <VTab value="courier_chains">
              <VIcon icon="mdi-source-branch" class="me-2" />
              Цепочки курьера
            </VTab>
            <VTab value="accounts">Получатели ({{ accounts.length }})</VTab>
            <VTab value="templates">Шаблоны уведомлений</VTab>
            <VTab value="logs">История логов</VTab>
            <VTab value="settings">Настройки каналов</VTab>
          </VTabs>

          <VDivider />

          <VWindow v-model="tab" class="pa-6">
            <!-- Вкладка: Логические цепочки уведомлений курьера -->
            <VWindowItem value="courier_chains">
              <!-- Информационный баннер логической цепочки доставки -->
              <VCard variant="tonal" color="primary" rounded="xl" class="mb-6 pa-5 border-primary">
                <div class="d-flex flex-wrap align-center justify-space-between gap-4">
                    <div class="d-flex align-center gap-2 mb-1">
                      <VIcon icon="mdi-source-branch" size="24" class="text-primary" />
                      <h3 class="text-h6 font-weight-bold text-primary">Цепочки уведомлений курьера</h3>
                      <VChip color="indigo" size="small" label variant="flat" class="font-weight-black text-white ms-2">
                        <VIcon icon="mdi-moped" size="16" class="me-1" />
                        СТРОГО ДЛЯ КУРЬЕРОВ
                      </VChip>
                    </div>
                    <p class="text-body-2 text-medium-emphasis mb-0">
                      Управление правилами и условиями отправки уведомлений назначенному курьеру по всему жизненному циклу заказа:
                      поступление, готовность кухни, смена статусов, изменение сумм, адресов и времени, а также QR-код СБП с надписью.
                      <b>Отправка выполняется строго назначенному курьеру в iiko (с активным статусом курьера и включенными цепочками).</b>
                    </p>
                  <div class="d-flex flex-wrap gap-2">
                    <VBtn
                      color="success"
                      variant="flat"
                      prepend-icon="mdi-play-circle-outline"
                      rounded="lg"
                      :loading="bulkChainsLoading"
                      @click="bulkToggleCourierChains(true)"
                    >
                      Активировать все шаги
                    </VBtn>
                    <VBtn
                      color="error"
                      variant="tonal"
                      prepend-icon="mdi-stop-circle-outline"
                      rounded="lg"
                      :loading="bulkChainsLoading"
                      @click="bulkToggleCourierChains(false)"
                    >
                      Отключить все
                    </VBtn>
                    <VBtn
                      color="primary"
                      variant="tonal"
                      prepend-icon="mdi-qrcode-scan"
                      rounded="lg"
                      @click="openPreviewQrDialog(null)"
                    >
                      Образец QR СБП с надписью
                    </VBtn>
                  </div>
                </div>

                <VDivider class="my-4" />

                <!-- Визуальная схема шагов -->
                <div class="d-flex flex-wrap align-center gap-2 text-caption font-weight-medium mb-3">
                  <VChip size="small" color="primary" variant="flat">1. Назначение / Новый заказ</VChip>
                  <VIcon icon="mdi-arrow-right" size="14" class="text-grey" />
                  <VChip size="small" color="warning" variant="flat">2. Готовность кухни</VChip>
                  <VIcon icon="mdi-arrow-right" size="14" class="text-grey" />
                  <VChip size="small" color="info" variant="flat">3. Смена статусов</VChip>
                  <VIcon icon="mdi-arrow-right" size="14" class="text-grey" />
                  <VChip size="small" color="success" variant="flat">4. Корректировка сумм/адреса</VChip>
                  <VIcon icon="mdi-arrow-right" size="14" class="text-grey" />
                  <VChip size="small" color="grey-darken-2" variant="flat">5. Вручение / Завершение</VChip>
                </div>

                <!-- Подсказка курьерам: разрешение сообщений от бота сообщества -->
                <div class="d-flex flex-wrap align-center justify-space-between pt-3 border-t text-caption">
                  <div class="d-flex align-center text-medium-emphasis">
                    <VIcon icon="mdi-information-outline" size="16" class="me-1 text-primary" />
                    <span>Для получения заказов в VK курьер должен разрешить сообщения в диалоге с ботом:</span>
                  </div>
                  <div class="d-flex flex-wrap gap-2">
                    <VBtn
                      v-for="b in bots"
                      :key="b.id"
                      size="x-small"
                      variant="tonal"
                      color="primary"
                      prepend-icon="mdi-vk"
                      :href="`https://vk.com/im?sel=-${b.vk_group_id}`"
                      target="_blank"
                    >
                      Открыть диалог: {{ b.name }} ({{ b.vk_group_id }})
                    </VBtn>
                  </div>
                </div>
              </VCard>

              <!-- Список шагов / цепочек курьера -->
              <VRow>
                <VCol
                  v-for="(tpl, idx) in courierTemplates"
                  :key="tpl.id"
                  cols="12"
                >
                  <VCard
                    variant="outlined"
                    rounded="xl"
                    class="pa-5 transition-swing"
                    :class="{ 'border-primary border-opacity-75 bg-surface': tpl.is_active, 'opacity-70 bg-grey-lighten-5': !tpl.is_active }"
                  >
                    <div class="d-flex flex-wrap align-start justify-space-between gap-3 mb-3">
                      <div class="d-flex align-center gap-3">
                        <VAvatar :color="getStageBadgeColor(tpl.event_type)" variant="flat" size="38" class="text-white font-weight-bold">
                          {{ idx + 1 }}
                        </VAvatar>
                        <div>
                          <div class="d-flex align-center gap-2">
                            <span class="text-subtitle-1 font-weight-bold">{{ tpl.name }}</span>
                            <VChip size="x-small" :color="getStageBadgeColor(tpl.event_type)" variant="tonal" class="font-weight-bold">
                              {{ getStageTitle(tpl.event_type) }}
                            </VChip>
                            <VChip size="x-small" color="secondary" variant="flat">
                              🎯 Только курьеру заказа
                            </VChip>
                          </div>
                          <div class="text-caption text-grey mt-1">
                            {{ tpl.description || getEventName(tpl.event_type) }}
                          </div>
                        </div>
                      </div>

                      <!-- Тумблер включения шага -->
                      <div class="d-flex align-center gap-4">
                        <div class="d-flex align-center">
                          <span class="text-caption me-2 font-weight-medium" :class="tpl.is_active ? 'text-success' : 'text-grey'">
                            {{ tpl.is_active ? 'Шаг активен' : 'Отключен' }}
                          </span>
                          <VSwitch
                            :model-value="tpl.is_active"
                            color="success"
                            hide-details
                            density="compact"
                            @update:model-value="toggleTemplateActive(tpl)"
                          />
                        </div>
                        <VBtn
                          size="small"
                          variant="tonal"
                          color="primary"
                          prepend-icon="mdi-pencil"
                          rounded="lg"
                          @click="openEditTemplate(tpl)"
                        >
                          Настроить
                        </VBtn>
                      </div>
                    </div>

                    <!-- Блок каналов отправки и выбора бота ВК для шага -->
                    <div class="d-flex flex-wrap align-center justify-space-between gap-3 mb-3 pa-3 rounded-lg bg-grey-lighten-4 border">
                      <!-- Каналы отправки -->
                      <div class="d-flex align-center flex-wrap gap-2">
                        <span class="text-caption font-weight-bold text-uppercase text-grey-darken-2 me-1 d-flex align-center">
                          <VIcon icon="mdi-broadcast" size="14" class="me-1 text-primary" />
                          Каналы:
                        </span>
                        <!-- VK -->
                        <VChip
                          size="small"
                          :color="tpl.send_vk !== false ? 'primary' : 'grey'"
                          :variant="tpl.send_vk !== false ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-bold"
                          :disabled="togglingTplChannel[`${tpl.id}_vk`]"
                          @click="toggleTemplateChannel(tpl, 'vk')"
                        >
                          <VIcon icon="mdi-vk" size="14" class="me-1" />
                          VK {{ tpl.send_vk !== false ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>
                        <!-- MAX -->
                        <VChip
                          size="small"
                          :color="tpl.send_max ? 'purple' : 'grey'"
                          :variant="tpl.send_max ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-bold"
                          :disabled="togglingTplChannel[`${tpl.id}_max`]"
                          @click="toggleTemplateChannel(tpl, 'max')"
                        >
                          <VIcon icon="mdi-message-flash" size="14" class="me-1" />
                          MAX {{ tpl.send_max ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>
                        <!-- Telegram -->
                        <VChip
                          size="small"
                          :color="tpl.send_tg ? 'info' : 'grey'"
                          :variant="tpl.send_tg ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-bold"
                          :disabled="togglingTplChannel[`${tpl.id}_tg`]"
                          @click="toggleTemplateChannel(tpl, 'tg')"
                        >
                          <VIcon icon="mdi-send" size="14" class="me-1" />
                          TG {{ tpl.send_tg ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>
                        <!-- SMS -->
                        <VChip
                          size="small"
                          :color="tpl.send_sms ? 'success' : 'grey'"
                          :variant="tpl.send_sms ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-bold"
                          :disabled="togglingTplChannel[`${tpl.id}_sms`]"
                          @click="toggleTemplateChannel(tpl, 'sms')"
                        >
                          <VIcon icon="mdi-cellphone-message" size="14" class="me-1" />
                          SMS {{ tpl.send_sms ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>
                      </div>

                      <!-- Выбор сообщества / бота ВК -->
                      <div class="d-flex align-center gap-2" style="min-width: 230px;">
                        <span class="text-caption text-grey-darken-2 font-weight-medium text-no-wrap">
                          <VIcon icon="mdi-robot-outline" size="14" class="me-1 text-primary" />
                          Бот ВК:
                        </span>
                        <VSelect
                          :model-value="tpl.vk_bot_id || null"
                          :items="[
                            { id: null, title: 'Основной бот по умолчанию' },
                            ...bots.map(b => ({ id: b.id, title: `${b.name} (${b.vk_group_id})${b.is_main ? ' ★' : ''}` }))
                          ]"
                          item-title="title"
                          item-value="id"
                          density="compact"
                          variant="outlined"
                          hide-details
                          class="bg-surface rounded"
                          style="max-width: 230px;"
                          @update:model-value="val => setTemplateBot(tpl, val)"
                        />
                      </div>

                      <!-- Выбор бота MAX -->
                      <div class="d-flex align-center gap-2" style="min-width: 230px;">
                        <span class="text-caption text-grey-darken-2 font-weight-medium text-no-wrap">
                          <VIcon icon="mdi-message-badge-outline" size="14" class="me-1 text-purple" />
                          Бот MAX:
                        </span>
                        <VSelect
                          :model-value="tpl.max_bot_id || null"
                          :items="[
                            { id: null, title: 'Основной бот MAX' },
                            ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name} (@${b.bot_username || b.id})${b.is_default_for_notifications ? ' ★' : ''}` }))
                          ]"
                          item-title="title"
                          item-value="id"
                          density="compact"
                          variant="outlined"
                          hide-details
                          class="bg-surface rounded"
                          style="max-width: 230px;"
                          :loading="settingTplMaxBot[`${tpl.id}_max`]"
                          @update:model-value="val => setTemplateMaxBot(tpl, val, tpl.max_send_mode)"
                        />
                      </div>

                      <!-- Выбор режима отправки MAX -->
                      <div class="d-flex align-center gap-2" style="min-width: 210px;">
                        <span class="text-caption text-grey-darken-2 font-weight-medium text-no-wrap">
                          <VIcon icon="mdi-call-split" size="14" class="me-1 text-purple" />
                          Режим MAX:
                        </span>
                        <VSelect
                          :model-value="tpl.max_send_mode || 'cascade'"
                          :items="[
                            { id: 'cascade', title: 'Каскад (Бот ➔ Личные)' },
                            { id: 'bot_only', title: 'Только Бот MAX' },
                            { id: 'bridge_only', title: 'Только Личный аккаунт' }
                          ]"
                          item-title="title"
                          item-value="id"
                          density="compact"
                          variant="outlined"
                          hide-details
                          class="bg-surface rounded"
                          style="max-width: 210px;"
                          :loading="settingTplMaxBot[`${tpl.id}_max`]"
                          @update:model-value="mode => setTemplateMaxBot(tpl, tpl.max_bot_id, mode)"
                        />
                      </div>
                    </div>

                    <!-- Блок логической цепочки проверок (Decision Chain) -->
                    <div class="chain-decision-box pa-4 rounded-lg bg-grey-lighten-4 mb-4 border">
                      <div class="d-flex flex-wrap align-center justify-space-between mb-2">
                        <div class="text-caption font-weight-bold text-uppercase text-grey-darken-2 d-flex align-center">
                          <VIcon icon="mdi-shield-check-outline" size="16" class="me-1 text-primary" />
                          Логическая цепочка проверок перед отправкой (нажмите для переключения):
                        </div>
                        <VBtn
                          size="x-small"
                          variant="text"
                          color="primary"
                          prepend-icon="mdi-tune-vertical"
                          @click="openEditTemplate(tpl)"
                        >
                          Редактор условий
                        </VBtn>
                      </div>
                      
                      <div class="d-flex flex-wrap gap-2 align-center">
                        <!-- 1. Назначен курьер -->
                        <VChip
                          size="small"
                          :color="parseChainConfig(tpl).require_courier_assigned ? 'primary' : 'grey'"
                          :variant="parseChainConfig(tpl).require_courier_assigned ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-medium"
                          @click="toggleChainCondition(tpl, 'require_courier_assigned')"
                        >
                          <VIcon :icon="parseChainConfig(tpl).require_courier_assigned ? 'mdi-account-check' : 'mdi-account-off-outline'" size="14" class="me-1" />
                          Курьер назначен: {{ parseChainConfig(tpl).require_courier_assigned ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>

                        <!-- 2. Повторять при переназначении курьера -->
                        <VChip
                          size="small"
                          :color="parseChainConfig(tpl).resend_on_courier_reassigned ? 'success' : 'grey'"
                          :variant="parseChainConfig(tpl).resend_on_courier_reassigned ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-medium"
                          @click="toggleChainCondition(tpl, 'resend_on_courier_reassigned')"
                        >
                          <VIcon :icon="parseChainConfig(tpl).resend_on_courier_reassigned ? 'mdi-account-switch' : 'mdi-account-switch-outline'" size="14" class="me-1" />
                          Повтор при переназначении: {{ parseChainConfig(tpl).resend_on_courier_reassigned ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>

                        <!-- 3. Установлено время готовности на кухне -->
                        <VChip
                          size="small"
                          :color="parseChainConfig(tpl).require_cooking_time_set ? 'warning' : 'grey'"
                          :variant="parseChainConfig(tpl).require_cooking_time_set ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-medium"
                          @click="toggleChainCondition(tpl, 'require_cooking_time_set')"
                        >
                          <VIcon :icon="parseChainConfig(tpl).require_cooking_time_set ? 'mdi-clock-check-outline' : 'mdi-clock-outline'" size="14" class="me-1" />
                          Время кухни задано (>0): {{ parseChainConfig(tpl).require_cooking_time_set ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>

                        <!-- 4. Изменено время кухни -->
                        <VChip
                          v-if="tpl.event_type === 'change_cooking_time'"
                          size="small"
                          :color="parseChainConfig(tpl).require_cooking_time_changed ? 'warning' : 'grey'"
                          :variant="parseChainConfig(tpl).require_cooking_time_changed ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-medium"
                          @click="toggleChainCondition(tpl, 'require_cooking_time_changed')"
                        >
                          <VIcon icon="mdi-timer-sync-outline" size="14" class="me-1" />
                          Только при повторном изменении времени: {{ parseChainConfig(tpl).require_cooking_time_changed ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>

                        <!-- 5. Изменение суммы -->
                        <VChip
                          v-if="tpl.event_type === 'order_amount_changed'"
                          size="small"
                          :color="parseChainConfig(tpl).require_amount_changed ? 'success' : 'grey'"
                          :variant="parseChainConfig(tpl).require_amount_changed ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-medium"
                          @click="toggleChainCondition(tpl, 'require_amount_changed')"
                        >
                          <VIcon icon="mdi-cash-sync" size="14" class="me-1" />
                          Сумма изменена: {{ parseChainConfig(tpl).require_amount_changed ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>

                        <!-- 6. Изменение адреса -->
                        <VChip
                          v-if="tpl.event_type === 'order_address_changed'"
                          size="small"
                          :color="parseChainConfig(tpl).require_address_changed ? 'purple' : 'grey'"
                          :variant="parseChainConfig(tpl).require_address_changed ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-medium"
                          @click="toggleChainCondition(tpl, 'require_address_changed')"
                        >
                          <VIcon icon="mdi-map-marker-distance" size="14" class="me-1" />
                          Адрес изменен: {{ parseChainConfig(tpl).require_address_changed ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>

                        <!-- 7. Изменение времени доставки -->
                        <VChip
                          v-if="tpl.event_type === 'order_time_changed'"
                          size="small"
                          :color="parseChainConfig(tpl).require_time_changed ? 'cyan' : 'grey'"
                          :variant="parseChainConfig(tpl).require_time_changed ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-medium"
                          @click="toggleChainCondition(tpl, 'require_time_changed')"
                        >
                          <VIcon icon="mdi-calendar-clock" size="14" class="me-1" />
                          Время доставки изменено: {{ parseChainConfig(tpl).require_time_changed ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>

                        <!-- 8. Только неоплаченные -->
                        <VChip
                          size="small"
                          :color="parseChainConfig(tpl).only_unpaid ? 'amber-darken-3' : 'grey'"
                          :variant="parseChainConfig(tpl).only_unpaid ? 'flat' : 'outlined'"
                          class="cursor-pointer font-weight-medium"
                          @click="toggleChainCondition(tpl, 'only_unpaid')"
                        >
                          <VIcon icon="mdi-credit-card-remove-outline" size="14" class="me-1" />
                          Только неоплаченные: {{ parseChainConfig(tpl).only_unpaid ? 'ВКЛ' : 'ВЫКЛ' }}
                        </VChip>

                        <!-- 9. QR СБП с надписью -->
                        <div class="d-inline-flex align-center">
                          <VChip
                            size="small"
                            :color="tpl.attach_sbp_qr ? 'success' : 'grey'"
                            :variant="tpl.attach_sbp_qr ? 'flat' : 'outlined'"
                            class="cursor-pointer font-weight-medium"
                            @click="toggleTemplateQr(tpl)"
                          >
                            <VIcon :icon="tpl.attach_sbp_qr ? 'mdi-qrcode-scan' : 'mdi-qrcode-remove'" size="14" class="me-1" />
                            QR СБП: {{ tpl.attach_sbp_qr ? 'ВКЛ' : 'ВЫКЛ' }}
                          </VChip>
                          <VBtn
                            v-if="tpl.attach_sbp_qr"
                            size="x-small"
                            variant="text"
                            color="primary"
                            icon="mdi-eye"
                            class="ms-1"
                            title="Предпросмотр карточки QR"
                            @click="openPreviewQrDialog(tpl)"
                          />
                        </div>

                        <!-- 10. Для смены статуса (интерактивный выбор статусов прямо на карточке) -->
                        <div v-if="tpl.event_type === 'order_status_update'" class="w-100 mt-2 pt-2 border-t">
                          <div class="text-caption text-grey-darken-2 mb-1 font-weight-bold">
                            Отправлять курьеру при переходе в статусы (нажмите на статус для переключения):
                          </div>
                          <div class="d-flex flex-wrap gap-1">
                            <VChip
                              v-for="st in orderStatusOptions"
                              :key="st.value"
                              size="small"
                              :color="isStatusSelected(tpl, st.value) ? st.color : 'grey-lighten-2'"
                              :variant="isStatusSelected(tpl, st.value) ? 'flat' : 'outlined'"
                              class="cursor-pointer"
                              @click="updateTemplateStatusFilter(tpl, st.value)"
                            >
                              <VIcon :icon="st.icon" size="14" class="me-1" />
                              {{ st.title }}
                              <VIcon
                                :icon="isStatusSelected(tpl, st.value) ? 'mdi-check' : 'mdi-plus'"
                                size="12"
                                class="ms-1"
                              />
                            </VChip>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Предпросмотр текста шаблона -->
                    <div class="bg-surface pa-3 rounded-lg border text-caption font-monospace text-grey-darken-3 whitespace-pre-wrap" style="max-height: 140px; overflow-y: auto;">
                      {{ tpl.text }}
                    </div>
                  </VCard>
                </VCol>
              </VRow>
            </VWindowItem>

            <VWindowItem value="accounts">
              <div class="d-flex mb-6">
                <VTextField
                  v-model="searchQuery"
                  label="Поиск получателя по имени, телефону или ID (VK / Telegram)"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-magnify"
                  clearable
                  hide-details
                  class="rounded-xl search-field"
                  @update:model-value="fetchAccounts"
                />
              </div>

              <div v-if="loading && accounts.length === 0" class="d-flex justify-center py-10">
                <VProgressCircular indeterminate color="primary" size="64" />
              </div>
              <VRow v-else>
                <VCol v-for="account in filteredAccounts" :key="account.id" cols="12" md="6" lg="4">
                  <VCard variant="outlined" rounded="xl" class="account-card bg-surface elevation-1">
                    <VCardText class="pa-5">
                      <div class="d-flex align-center mb-4">
                        <VAvatar color="primary" size="52" class="me-4 shadow-sm border-2">
                          <VIcon icon="mdi-account" color="white" size="28" />
                        </VAvatar>
                        <div class="overflow-hidden flex-grow-1">
                          <div class="text-h6 text-truncate font-weight-bold">{{ account.name }}</div>
                          <div class="text-caption text-grey text-truncate d-flex align-center mt-1">
                            <VIcon icon="mdi-phone" size="12" class="me-1 text-primary" />
                            {{ account.phone || 'Нет телефона' }}
                          </div>
                          <div v-if="account.employee_id && getEmployeeName(account.employee_id)" class="text-caption text-primary text-truncate d-flex align-center mt-1 font-weight-medium">
                            <VIcon icon="mdi-badge-account-horizontal-outline" size="12" class="me-1" />
                            {{ getEmployeeName(account.employee_id) }}
                          </div>
                          <div v-if="account.user_id" class="text-caption text-deep-purple text-truncate d-flex align-center mt-1 font-weight-medium">
                            <VIcon icon="mdi-shield-account-outline" size="12" class="me-1" />
                            {{ getUserName(account.user_id) }}
                          </div>
                          <div v-if="hasDuplicateVk(account)" class="text-caption text-warning text-truncate d-flex align-center mt-1" :title="'Общая VK страница с: ' + getDuplicateVkNames(account)">
                            <VIcon icon="mdi-account-multiple" size="12" class="me-1" />
                            Общая VK страница (ID: {{ account.vk_user_id }})
                          </div>
                          
                          <!-- Каналы доставки с быстрым переключением в 1 клик -->
                          <div class="mt-3">
                            <div class="text-caption text-grey mb-1 d-flex align-center justify-space-between">
                              <span class="font-weight-medium">Каналы уведомлений:</span>
                              <span style="font-size: 10px; color: #888;">(клик переключает)</span>
                            </div>
                            <div class="d-flex flex-wrap gap-1 align-center">
                              <!-- VK -->
                              <VChip
                                size="small"
                                :color="account.use_vk ? '#4C75A3' : 'grey'"
                                :variant="account.use_vk ? 'flat' : 'outlined'"
                                class="cursor-pointer font-weight-medium"
                                :disabled="togglingChannel[`${account.id}_vk`]"
                                title="Кликните, чтобы включить/отключить отправку в VK"
                                @click="toggleAccountChannel(account, 'vk')"
                              >
                                <VIcon start icon="mdi-vk" size="15" />
                                VK
                                <VIcon end :icon="account.use_vk ? 'mdi-check' : 'mdi-close'" size="13" />
                              </VChip>
                              <VTooltip location="top" text="Проверить доставку в VK">
                                <template #activator="{ props }">
                                  <VBtn
                                    v-if="account.vk_user_id && account.use_vk"
                                    v-bind="props"
                                    icon="mdi-send-check-outline"
                                    size="x-small"
                                    variant="text"
                                    :color="account.is_verified ? 'success' : 'warning'"
                                    class="ms-n1"
                                    @click.stop="verifyAccount(account.id)"
                                  />
                                </template>
                              </VTooltip>

                              <!-- Telegram -->
                              <VChip
                                size="small"
                                :color="account.use_tg ? '#0088cc' : 'grey'"
                                :variant="account.use_tg ? 'flat' : 'outlined'"
                                class="cursor-pointer font-weight-medium"
                                :disabled="togglingChannel[`${account.id}_tg`]"
                                title="Кликните, чтобы включить/отключить отправку в Telegram"
                                @click="toggleAccountChannel(account, 'tg')"
                              >
                                <VIcon start icon="mdi-telegram" size="15" />
                                TG
                                <VIcon end :icon="account.use_tg ? 'mdi-check' : 'mdi-close'" size="13" />
                              </VChip>
                              <VTooltip location="top" text="Проверить доставку в Telegram">
                                <template #activator="{ props }">
                                  <VBtn
                                    v-if="account.tg_user_id && account.use_tg"
                                    v-bind="props"
                                    icon="mdi-send-check-outline"
                                    size="x-small"
                                    variant="text"
                                    :color="account.is_tg_verified ? 'success' : 'warning'"
                                    class="ms-n1"
                                    @click.stop="verifyAccountTg(account.id)"
                                  />
                                </template>
                              </VTooltip>

                              <!-- MAX -->
                              <VChip
                                size="small"
                                :color="account.use_max ? 'teal-darken-1' : 'grey'"
                                :variant="account.use_max ? 'flat' : 'outlined'"
                                class="cursor-pointer font-weight-medium"
                                :disabled="togglingChannel[`${account.id}_max`]"
                                title="Кликните, чтобы включить/отключить отправку в MAX"
                                @click="toggleAccountChannel(account, 'max')"
                              >
                                <VIcon start icon="mdi-message-text" size="15" />
                                MAX
                                <VIcon end :icon="account.use_max ? 'mdi-check' : 'mdi-close'" size="13" />
                              </VChip>
                              <VTooltip location="top" text="Проверить доставку в MAX">
                                <template #activator="{ props }">
                                  <VBtn
                                    v-if="(account.max_user_id || account.phone) && account.use_max"
                                    v-bind="props"
                                    icon="mdi-send-check-outline"
                                    size="x-small"
                                    variant="text"
                                    :color="account.is_max_verified ? 'success' : 'warning'"
                                    class="ms-n1"
                                    @click.stop="verifyAccountMax(account.id)"
                                  />
                                </template>
                              </VTooltip>

                              <!-- SMS -->
                              <VChip
                                size="small"
                                :color="account.use_sms ? 'primary' : 'grey'"
                                :variant="account.use_sms ? 'flat' : 'outlined'"
                                class="cursor-pointer font-weight-medium"
                                :disabled="togglingChannel[`${account.id}_sms`]"
                                title="Кликните, чтобы включить/отключить отправку через SMS"
                                @click="toggleAccountChannel(account, 'sms')"
                              >
                                <VIcon start icon="mdi-cellphone-message" size="15" />
                                SMS
                                <VIcon end :icon="account.use_sms ? 'mdi-check' : 'mdi-close'" size="13" />
                              </VChip>
                            </div>
                          </div>
                        </div>
                        <div class="d-flex flex-column align-end gap-1 ms-2">
                          <VChip :color="account.is_active ? 'success' : 'error'" size="x-small" label variant="tonal" class="font-weight-bold">
                            {{ account.is_active ? 'Активен' : 'Отключен' }}
                          </VChip>
                          <VChip v-if="account.is_courier" color="indigo" size="x-small" label variant="flat" class="font-weight-black text-white mt-1">
                            <VIcon icon="mdi-moped" size="14" class="me-1" />
                            Курьер iiko
                          </VChip>
                          <VChip v-if="account.is_courier && account.allow_courier_chains !== false" color="teal" size="x-small" label variant="tonal" class="font-weight-bold mt-1">
                            Цепочки: Вкл
                          </VChip>
                          <VChip v-else-if="account.is_courier && account.allow_courier_chains === false" color="grey" size="x-small" label variant="tonal" class="font-weight-bold mt-1">
                            Цепочки: Выкл
                          </VChip>
                          <VChip v-if="account.send_payment_qr" :color="account.payment_qr_mode === 'all' ? 'primary' : 'info'" size="x-small" label variant="tonal" class="font-weight-bold mt-1">
                            {{ account.payment_qr_mode === 'all' ? 'QR: Все' : 'QR: Курьер' }}
                          </VChip>
                        </div>
                      </div>
                      <VDivider class="my-3" />
                      <div class="d-flex gap-2">
                        <VBtn size="small" variant="tonal" color="primary" prepend-icon="mdi-cog" class="flex-grow-1 rounded-lg" @click="openSubscriptions(account)">Настроить каналы рассылок</VBtn>
                        <VBtn size="small" variant="tonal" color="secondary" icon="mdi-pencil" class="rounded-lg" title="Редактировать получателя" @click="openEditAccount(account)" />
                        <VBtn size="small" variant="tonal" :color="account.is_active ? 'warning' : 'success'" :icon="account.is_active ? 'mdi-pause' : 'mdi-play'" class="rounded-lg" title="Вкл/Выкл получателя" @click="toggleAccountStatus(account)" />
                        <VBtn size="small" variant="tonal" color="error" icon="mdi-delete" class="rounded-lg" title="Удалить" @click="deleteAccount(account.id)" />
                      </div>
                    </VCardText>
                  </VCard>
                </VCol>
              </VRow>
            </VWindowItem>

            <VWindowItem value="templates">
              <!-- Заголовок вкладки -->
              <div class="d-flex flex-wrap justify-space-between align-center mb-4 gap-3">
                <div>
                  <h3 class="text-h6 font-weight-bold text-primary d-flex align-center">
                    <VIcon icon="mdi-file-document-multiple-outline" class="me-2" />
                    Системные шаблоны уведомлений
                  </h3>
                  <div class="text-caption text-grey">Управление шаблонами, каналами связи, сообществами ВК и адресацией сотрудникам</div>
                </div>
                <div class="d-flex align-center gap-2">
                  <VBtnToggle
                    v-model="templateViewMode"
                    density="compact"
                    rounded="lg"
                    color="primary"
                    mandatory
                    class="border"
                  >
                    <VBtn value="list" size="small" title="Построчный компактный список">
                      <VIcon icon="mdi-view-headline" size="18" class="me-1" />
                      Строки
                    </VBtn>
                    <VBtn value="grid" size="small" title="Сетка карточек">
                      <VIcon icon="mdi-view-grid-outline" size="18" class="me-1" />
                      Плитка
                    </VBtn>
                  </VBtnToggle>

                  <VBtn color="primary" prepend-icon="mdi-plus" rounded="lg" class="action-btn" @click="openCreateTemplate">
                    Создать шаблон
                  </VBtn>
                </div>
              </div>

              <!-- Фильтры категорий шаблонов -->
              <div class="d-flex flex-wrap align-center gap-2 mb-4">
                <VBtn
                  size="small"
                  :variant="templateCategoryFilter === 'all' ? 'flat' : 'tonal'"
                  :color="templateCategoryFilter === 'all' ? 'primary' : 'default'"
                  rounded="lg"
                  @click="templateCategoryFilter = 'all'"
                >
                  <VIcon start icon="mdi-view-grid-outline" />
                  Все шаблоны ({{ templates.length }})
                </VBtn>
                <VBtn
                  size="small"
                  :variant="templateCategoryFilter === 'system' ? 'flat' : 'tonal'"
                  :color="templateCategoryFilter === 'system' ? 'primary' : 'default'"
                  rounded="lg"
                  @click="templateCategoryFilter = 'system'"
                >
                  <VIcon start icon="mdi-cog-sync-outline" />
                  Общие системные ({{ systemTemplates.length }})
                </VBtn>
                <VBtn
                  size="small"
                  :variant="templateCategoryFilter === 'courier' ? 'flat' : 'tonal'"
                  :color="templateCategoryFilter === 'courier' ? 'indigo' : 'default'"
                  rounded="lg"
                  @click="templateCategoryFilter = 'courier'"
                >
                  <VIcon start icon="mdi-moped" />
                  Цепочки курьера ({{ courierTemplates.length }})
                </VBtn>
                <VBtn
                  size="small"
                  :variant="templateCategoryFilter === 'custom' ? 'flat' : 'tonal'"
                  :color="templateCategoryFilter === 'custom' ? 'secondary' : 'default'"
                  rounded="lg"
                  @click="templateCategoryFilter = 'custom'"
                >
                  <VIcon start icon="mdi-bullhorn-outline" />
                  Ручные рассылки ({{ customTemplates.length }})
                </VBtn>
              </div>

              <!-- Панель мультивыбора и массовых действий -->
              <VCard variant="tonal" color="primary" class="pa-3 mb-6 rounded-xl border d-flex flex-wrap align-center justify-space-between gap-3">
                <div class="d-flex align-center gap-3">
                  <VCheckbox
                    :model-value="isAllTemplatesSelected"
                    :indeterminate="selectedTemplateIds.length > 0 && !isAllTemplatesSelected"
                    color="primary"
                    density="compact"
                    hide-details
                    @update:model-value="toggleSelectAllTemplates"
                    :label="`Выбрать все (${selectedTemplateIds.length} / ${visibleTemplates.length})`"
                    class="font-weight-medium"
                  />
                  <VChip v-if="selectedTemplateIds.length > 0" size="small" color="primary" variant="flat" class="font-weight-bold">
                    Выбрано: {{ selectedTemplateIds.length }}
                  </VChip>
                </div>

                <div v-if="selectedTemplateIds.length > 0" class="d-flex flex-wrap align-center gap-2">
                  <VBtn size="small" variant="flat" color="primary" prepend-icon="mdi-broadcast" rounded="lg" @click="bulkChannelsDialog = true" :loading="bulkLoading">
                    Каналы ({{ selectedTemplateIds.length }})
                  </VBtn>
                  <VBtn size="small" variant="flat" color="secondary" prepend-icon="mdi-robot" rounded="lg" @click="bulkBotDialog = true" :loading="bulkLoading">
                    Бот VK ({{ selectedTemplateIds.length }})
                  </VBtn>
                  <VBtn size="small" variant="tonal" color="success" prepend-icon="mdi-check" rounded="lg" @click="bulkToggleStatus(true)" :loading="bulkLoading">
                    Включить
                  </VBtn>
                  <VBtn size="small" variant="tonal" color="warning" prepend-icon="mdi-pause" rounded="lg" @click="bulkToggleStatus(false)" :loading="bulkLoading">
                    Выключить
                  </VBtn>
                  <VBtn size="small" variant="flat" color="error" prepend-icon="mdi-delete" rounded="lg" @click="bulkDeleteTemplates" :loading="bulkLoading">
                    Удалить
                  </VBtn>
                </div>
              </VCard>

              <!-- Раздел: Системные автоматические шаблоны -->
              <div v-if="templateCategoryFilter === 'all' || templateCategoryFilter === 'system'">
                <h4 class="text-subtitle-1 font-weight-bold text-primary mb-3 d-flex align-center">
                  <VIcon icon="mdi-cog-sync-outline" class="me-2 text-primary" />
                  Автоматические системные уведомления ({{ systemTemplates.length }})
                </h4>

                <!-- Построчный упорядоченный список (по умолчанию) -->
                <div v-if="templateViewMode === 'list'" class="d-flex flex-column gap-2 mb-6">
                  <VCard 
                    v-for="tpl in systemTemplates" 
                    :key="tpl.id"
                    variant="outlined" 
                    class="template-row-item px-3 py-2 rounded-xl border d-flex flex-wrap align-center justify-space-between gap-2" 
                    :class="{ 'template-row-inactive': !tpl.is_active }"
                    :style="{ borderColor: tpl.is_active ? 'var(--v-primary-base)' : '#e0e0e0' }"
                  >
                    <!-- Левая часть: Чекбокс, Иконка, Название, Тип, Адресация -->
                    <div class="d-flex align-center gap-2 template-row-left" style="min-width: 280px; max-width: 380px;">
                      <VCheckbox
                        v-model="selectedTemplateIds"
                        :value="tpl.id"
                        density="compact"
                        hide-details
                        color="primary"
                        class="pa-0 ma-0 flex-shrink-0"
                      />
                      <VAvatar :color="tpl.is_active ? 'primary' : 'grey'" variant="tonal" size="34" class="flex-shrink-0">
                        <VIcon :icon="getEventIcon(tpl.event_type)" size="18" />
                      </VAvatar>
                      <div class="min-width-0">
                        <div class="d-flex align-center gap-1">
                          <span class="text-body-2 font-weight-bold text-truncate cursor-pointer" :title="tpl.name" @click="openEditTemplate(tpl)">
                            {{ tpl.name }}
                          </span>
                          <VChip v-if="!tpl.is_active" size="x-small" color="error" variant="tonal" class="px-1" style="height: 18px; font-size: 10px;">
                            Выкл
                          </VChip>
                        </div>
                        <div class="d-flex align-center flex-wrap gap-1 mt-0">
                          <span class="text-caption text-grey text-truncate" style="font-size: 11px;">{{ getEventName(tpl.event_type) }}</span>
                          
                          <!-- Чип адресации -->
                          <VChip
                            v-if="tpl.target_mode === 'roles'"
                            size="x-small"
                            color="purple"
                            variant="flat"
                            class="font-weight-medium px-1"
                            style="height: 18px; font-size: 10px;"
                            :title="`Роли: ${formatRoles(tpl.target_roles)}`"
                          >
                            👔 {{ formatRoles(tpl.target_roles) }}
                          </VChip>
                          <VChip
                            v-else-if="tpl.target_mode === 'specific'"
                            size="x-small"
                            color="teal"
                            variant="flat"
                            class="font-weight-medium px-1"
                            style="height: 18px; font-size: 10px;"
                            :title="`Получателей: ${countAccounts(tpl.target_accounts)}`"
                          >
                            👤 {{ countAccounts(tpl.target_accounts) }} чел.
                          </VChip>
                          <VChip
                            v-else-if="tpl.target_mode === 'assigned_only'"
                            size="x-small"
                            color="info"
                            variant="flat"
                            class="font-weight-medium px-1"
                            style="height: 18px; font-size: 10px;"
                            title="Только назначенному курьеру"
                          >
                            🎯 Курьеру
                          </VChip>
                          <VChip
                            v-else-if="tpl.target_mode === 'assigned_and_admins'"
                            size="x-small"
                            color="primary"
                            variant="flat"
                            class="font-weight-medium px-1"
                            style="height: 18px; font-size: 10px;"
                            title="Курьеру и администраторам"
                          >
                            👥🎯 Курьер+Админ
                          </VChip>
                          <VChip
                            v-else
                            size="x-small"
                            color="secondary"
                            variant="tonal"
                            class="font-weight-medium px-1"
                            style="height: 18px; font-size: 10px;"
                            title="Всем подписчикам"
                          >
                            👥 Всем
                          </VChip>

                          <VChip
                            v-if="tpl.attach_sbp_qr"
                            size="x-small"
                            color="primary"
                            variant="outlined"
                            class="px-1"
                            style="height: 18px; font-size: 10px;"
                            title="QR-код СБП"
                          >
                            QR СБП
                          </VChip>
                        </div>
                      </div>
                    </div>

                    <!-- Центральная часть: Превью сообщения и описание -->
                    <div class="template-row-center flex-grow-1 min-width-0 mx-2" style="min-width: 200px;">
                      <div v-if="tpl.description" class="text-caption text-primary font-weight-medium text-truncate mb-0" style="font-size: 11px;">
                        {{ tpl.description }}
                      </div>
                      <div
                        class="text-caption text-grey-darken-1 text-truncate-2 cursor-pointer"
                        style="line-height: 1.3; max-height: 2.6em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;"
                        :title="tpl.text"
                        @click="openEditTemplate(tpl)"
                      >
                        {{ tpl.text }}
                      </div>
                    </div>

                    <!-- Каналы отправки -->
                    <div class="template-row-channels d-flex align-center gap-1 flex-shrink-0">
                      <VChip
                        size="x-small"
                        :color="tpl.send_vk ? '#4C75A3' : 'grey-lighten-2'"
                        :variant="tpl.send_vk ? 'flat' : 'tonal'"
                        class="font-weight-bold cursor-pointer"
                        :class="tpl.send_vk ? 'text-white' : 'text-grey'"
                        @click="toggleTemplateChannel(tpl, 'vk')"
                        :disabled="togglingTplChannel[`${tpl.id}_vk`]"
                        title="Клик переключает канал VK"
                      >
                        <VIcon start :icon="tpl.send_vk ? 'mdi-check' : 'mdi-close'" size="12" />
                        VK
                      </VChip>
                      <VChip
                        size="x-small"
                        :color="tpl.send_max ? 'purple' : 'grey-lighten-2'"
                        :variant="tpl.send_max ? 'flat' : 'tonal'"
                        class="font-weight-bold cursor-pointer"
                        :class="tpl.send_max ? 'text-white' : 'text-grey'"
                        @click="toggleTemplateChannel(tpl, 'max')"
                        :disabled="togglingTplChannel[`${tpl.id}_max`]"
                        title="Клик переключает канал MAX"
                      >
                        <VIcon start :icon="tpl.send_max ? 'mdi-check' : 'mdi-close'" size="12" />
                        MAX
                      </VChip>
                      <VChip
                        size="x-small"
                        :color="tpl.send_tg ? '#0088cc' : 'grey-lighten-2'"
                        :variant="tpl.send_tg ? 'flat' : 'tonal'"
                        class="font-weight-bold cursor-pointer"
                        :class="tpl.send_tg ? 'text-white' : 'text-grey'"
                        @click="toggleTemplateChannel(tpl, 'tg')"
                        :disabled="togglingTplChannel[`${tpl.id}_tg`]"
                        title="Клик переключает канал Telegram"
                      >
                        <VIcon start :icon="tpl.send_tg ? 'mdi-check' : 'mdi-close'" size="12" />
                        TG
                      </VChip>
                      <VChip
                        size="x-small"
                        :color="tpl.send_sms ? 'success' : 'grey-lighten-2'"
                        :variant="tpl.send_sms ? 'flat' : 'tonal'"
                        class="font-weight-bold cursor-pointer"
                        :class="tpl.send_sms ? 'text-white' : 'text-grey'"
                        @click="toggleTemplateChannel(tpl, 'sms')"
                        :disabled="togglingTplChannel[`${tpl.id}_sms`]"
                        title="Клик переключает канал SMS"
                      >
                        <VIcon start :icon="tpl.send_sms ? 'mdi-check' : 'mdi-close'" size="12" />
                        SMS
                      </VChip>
                    </div>

                    <!-- Выбор сообщества / бота -->
                    <div class="template-row-bots d-flex align-center gap-1 flex-shrink-0" style="min-width: 250px; max-width: 320px;">
                      <VSelect
                        :model-value="tpl.vk_bot_id"
                        @update:model-value="val => setTemplateBot(tpl, val)"
                        :items="[
                          { id: null, title: 'Основное VK' },
                          ...bots.map(b => ({ id: b.id, title: `${b.name} (${b.vk_group_id})${b.is_main ? ' ★' : ''}` }))
                        ]"
                        item-title="title"
                        item-value="id"
                        density="compact"
                        variant="underlined"
                        hide-details
                        prepend-inner-icon="mdi-robot"
                        class="text-caption tpl-bot-select flex-grow-1"
                        style="font-size: 11px; max-width: 140px;"
                        :loading="settingTplBot[`${tpl.id}`]"
                        title="Сообщество VK для отправки"
                      />
                      <VSelect
                        :model-value="tpl.max_bot_id || null"
                        @update:model-value="val => setTemplateMaxBot(tpl, val, tpl.max_send_mode)"
                        :items="[
                          { id: null, title: 'Основной MAX' },
                          ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name}${b.is_default_for_notifications ? ' ★' : ''}` }))
                        ]"
                        item-title="title"
                        item-value="id"
                        density="compact"
                        variant="underlined"
                        hide-details
                        prepend-inner-icon="mdi-message-badge-outline"
                        class="text-caption tpl-bot-select flex-grow-1"
                        style="font-size: 11px; max-width: 130px;"
                        :loading="settingTplMaxBot[`${tpl.id}_max`]"
                        title="Бот MAX для отправки"
                      />
                    </div>

                    <!-- Переключатель активности -->
                    <div class="template-row-switch d-flex align-center flex-shrink-0">
                      <VSwitch
                        :model-value="tpl.is_active"
                        @update:model-value="toggleTemplateActive(tpl)"
                        color="success"
                        density="compact"
                        hide-details
                        title="Включить / выключить шаблон"
                      />
                    </div>

                    <!-- Кнопки действий -->
                    <div class="template-row-actions d-flex align-center gap-1 flex-shrink-0">
                      <VBtn
                        size="small"
                        variant="tonal"
                        color="info"
                        icon="mdi-send-check"
                        class="rounded-lg"
                        @click="testSendTemplate(tpl)"
                        :loading="testSendingTplId === tpl.id"
                        title="Отправить тестовое сообщение"
                      />
                      <VBtn
                        size="small"
                        variant="tonal"
                        color="primary"
                        icon="mdi-pencil"
                        class="rounded-lg"
                        @click="openEditTemplate(tpl)"
                        title="Изменить шаблон"
                      />
                      <VBtn
                        size="small"
                        variant="text"
                        color="error"
                        icon="mdi-delete"
                        class="rounded-lg"
                        @click="deleteTemplate(tpl.id)"
                        title="Удалить шаблон"
                      />
                    </div>
                  </VCard>
                </div>

                <!-- Плиточный вид (сетка) -->
                <VRow v-else class="mb-6">
                <VCol v-for="tpl in systemTemplates" :key="tpl.id" cols="12" md="6" lg="4">
                  <VCard 
                    variant="outlined" 
                    class="pa-4 rounded-xl border-dashed relative-card d-flex flex-column h-100" 
                    :style="{ borderColor: tpl.is_active ? 'var(--v-primary-base)' : '#e0e0e0', opacity: tpl.is_active ? 1 : 0.75 }"
                  >
                    <!-- Верхняя строка карточки -->
                    <div class="d-flex align-start justify-space-between mb-2">
                      <div class="d-flex align-center">
                        <VCheckbox
                          v-model="selectedTemplateIds"
                          :value="tpl.id"
                          density="compact"
                          hide-details
                          color="primary"
                          class="me-2 pa-0"
                        />
                        <VAvatar :color="tpl.is_active ? 'primary' : 'grey'" variant="tonal" size="36" class="me-2">
                          <VIcon :icon="getEventIcon(tpl.event_type)" size="20" />
                        </VAvatar>
                        <div>
                          <div class="text-subtitle-1 font-weight-bold d-flex align-center">
                            {{ tpl.name }}
                            <span v-if="!tpl.is_active" class="text-caption text-error ms-2">(Выкл)</span>
                          </div>
                          <div class="text-caption text-grey">{{ getEventName(tpl.event_type) }}</div>
                        </div>
                      </div>
                      
                      <VSwitch
                        :model-value="tpl.is_active"
                        @update:model-value="toggleTemplateActive(tpl)"
                        color="success"
                        density="compact"
                        hide-details
                        title="Включить / выключить шаблон"
                      />
                    </div>

                    <!-- Бейджи адресации и опций -->
                    <div class="d-flex flex-wrap gap-1 mb-2">
                      <VChip
                        v-if="tpl.target_mode === 'roles'"
                        size="x-small"
                        color="purple"
                        variant="flat"
                        prepend-icon="mdi-account-tie"
                        class="font-weight-bold"
                        :title="`Роли: ${formatRoles(tpl.target_roles)}`"
                      >
                        👔 Роли: {{ formatRoles(tpl.target_roles) }}
                      </VChip>
                      <VChip
                        v-else-if="tpl.target_mode === 'specific'"
                        size="x-small"
                        color="teal"
                        variant="flat"
                        prepend-icon="mdi-account-multiple"
                        class="font-weight-bold"
                        :title="`Получателей: ${countAccounts(tpl.target_accounts)}`"
                      >
                        👤 Получатели ({{ countAccounts(tpl.target_accounts) }})
                      </VChip>
                      <VChip
                        v-else-if="tpl.target_mode === 'assigned_only'"
                        size="x-small"
                        color="info"
                        variant="flat"
                        prepend-icon="mdi-account-arrow-right"
                        class="font-weight-bold"
                        title="Только назначенному курьеру"
                      >
                        🎯 Адресно курьеру
                      </VChip>
                      <VChip
                        v-else-if="tpl.target_mode === 'assigned_and_admins'"
                        size="x-small"
                        color="primary"
                        variant="flat"
                        prepend-icon="mdi-account-group"
                        class="font-weight-bold"
                        title="Курьеру и администраторам"
                      >
                        👥🎯 Курьеру + Админам
                      </VChip>
                      <VChip
                        v-else
                        size="x-small"
                        color="secondary"
                        variant="tonal"
                        prepend-icon="mdi-bullhorn"
                        title="Всем подписчикам"
                      >
                        👥 Всем
                      </VChip>

                      <VChip
                        v-if="tpl.attach_sbp_qr"
                        size="x-small"
                        color="primary"
                        variant="outlined"
                        prepend-icon="mdi-qrcode"
                        title="QR-код СБП с надписью"
                      >
                        QR СБП
                      </VChip>
                    </div>

                    <!-- Описание или пояснение -->
                    <div v-if="tpl.description" class="text-caption text-primary mb-2 font-weight-medium">
                      {{ tpl.description }}
                    </div>

                    <!-- Текст шаблона -->
                    <div class="text-body-2 text-grey mb-3 text-truncate-3 flex-grow-1" style="min-height: 50px; white-space: pre-line;">{{ tpl.text }}</div>

                    <!-- Интерактивная полоска каналов отправки -->
                    <div class="pa-2 rounded-lg bg-grey-lighten-4 mb-3 border">
                      <div class="text-caption text-grey font-weight-bold mb-1 d-flex align-center justify-space-between">
                        <span>Каналы отправки:</span>
                        <span class="text-caption" style="font-size: 10px;">(клик переключает)</span>
                      </div>
                      <div class="d-flex flex-wrap gap-1">
                        <VChip
                          size="x-small"
                          :color="tpl.send_vk ? '#4C75A3' : 'grey-lighten-1'"
                          :variant="tpl.send_vk ? 'flat' : 'tonal'"
                          class="font-weight-bold cursor-pointer"
                          :prepend-icon="tpl.send_vk ? 'mdi-check-circle' : 'mdi-circle-outline'"
                          @click="toggleTemplateChannel(tpl, 'vk')"
                          :disabled="togglingTplChannel[`${tpl.id}_vk`]"
                        >
                          VK
                        </VChip>
                        <VChip
                          size="x-small"
                          :color="tpl.send_max ? 'purple' : 'grey-lighten-1'"
                          :variant="tpl.send_max ? 'flat' : 'tonal'"
                          class="font-weight-bold cursor-pointer"
                          :prepend-icon="tpl.send_max ? 'mdi-check-circle' : 'mdi-circle-outline'"
                          @click="toggleTemplateChannel(tpl, 'max')"
                          :disabled="togglingTplChannel[`${tpl.id}_max`]"
                        >
                          MAX
                        </VChip>
                        <VChip
                          size="x-small"
                          :color="tpl.send_tg ? '#0088cc' : 'grey-lighten-1'"
                          :variant="tpl.send_tg ? 'flat' : 'tonal'"
                          class="font-weight-bold cursor-pointer"
                          :prepend-icon="tpl.send_tg ? 'mdi-check-circle' : 'mdi-circle-outline'"
                          @click="toggleTemplateChannel(tpl, 'tg')"
                          :disabled="togglingTplChannel[`${tpl.id}_tg`]"
                        >
                          TG
                        </VChip>
                        <VChip
                          size="x-small"
                          :color="tpl.send_sms ? 'success' : 'grey-lighten-1'"
                          :variant="tpl.send_sms ? 'flat' : 'tonal'"
                          class="font-weight-bold cursor-pointer"
                          :prepend-icon="tpl.send_sms ? 'mdi-check-circle' : 'mdi-circle-outline'"
                          @click="toggleTemplateChannel(tpl, 'sms')"
                          :disabled="togglingTplChannel[`${tpl.id}_sms`]"
                        >
                          SMS
                        </VChip>
                      </div>
                    </div>

                    <!-- Выбор сообщества / бота прямо на карточке -->
                    <div class="mb-3 d-flex flex-wrap gap-2">
                      <VSelect
                        :model-value="tpl.vk_bot_id"
                        @update:model-value="val => setTemplateBot(tpl, val)"
                        :items="[
                          { id: null, title: 'Основное сообщество VK' },
                          ...bots.map(b => ({ id: b.id, title: `${b.name} (${b.vk_group_id})${b.is_main ? ' ★' : ''}` }))
                        ]"
                        item-title="title"
                        item-value="id"
                        density="compact"
                        variant="underlined"
                        hide-details
                        prepend-inner-icon="mdi-robot"
                        class="text-caption flex-grow-1"
                        style="min-width: 180px;"
                        :loading="settingTplBot[`${tpl.id}`]"
                      />
                      <VSelect
                        :model-value="tpl.max_bot_id || null"
                        @update:model-value="val => setTemplateMaxBot(tpl, val, tpl.max_send_mode)"
                        :items="[
                          { id: null, title: 'Основной бот MAX' },
                          ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name}${b.is_default_for_notifications ? ' ★' : ''}` }))
                        ]"
                        item-title="title"
                        item-value="id"
                        density="compact"
                        variant="underlined"
                        hide-details
                        prepend-inner-icon="mdi-message-badge-outline"
                        class="text-caption flex-grow-1"
                        style="min-width: 180px;"
                        :loading="settingTplMaxBot[`${tpl.id}_max`]"
                      />
                      <VSelect
                        :model-value="tpl.max_send_mode || 'cascade'"
                        @update:model-value="mode => setTemplateMaxBot(tpl, tpl.max_bot_id, mode)"
                        :items="[
                          { id: 'cascade', title: 'MAX: Каскад' },
                          { id: 'bot_only', title: 'MAX: Только бот' },
                          { id: 'bridge_only', title: 'MAX: Только личные' }
                        ]"
                        item-title="title"
                        item-value="id"
                        density="compact"
                        variant="underlined"
                        hide-details
                        prepend-inner-icon="mdi-call-split"
                        class="text-caption"
                        style="width: 160px;"
                        :loading="settingTplMaxBot[`${tpl.id}_max`]"
                      />
                    </div>

                    <VDivider class="my-2" />

                    <!-- Кнопки действий -->
                    <div class="d-flex align-center gap-2">
                      <VBtn
                        size="small"
                        variant="tonal"
                        color="info"
                        prepend-icon="mdi-send-check"
                        class="flex-grow-1 rounded-lg"
                        @click="testSendTemplate(tpl)"
                        :loading="testSendingTplId === tpl.id"
                        title="Отправить тестовое сообщение"
                      >
                        Тест
                      </VBtn>
                      <VBtn
                        size="small"
                        variant="flat"
                        color="primary"
                        prepend-icon="mdi-pencil"
                        class="flex-grow-1 rounded-lg"
                        @click="openEditTemplate(tpl)"
                      >
                        Изменить
                      </VBtn>
                      <VBtn
                        size="small"
                        variant="tonal"
                        color="error"
                        icon="mdi-delete"
                        class="rounded-lg"
                        @click="deleteTemplate(tpl.id)"
                        title="Удалить шаблон"
                      />
                    </div>
                  </VCard>
                </VCol>
              </VRow>
              </div>

              <!-- Раздел: Шаблоны логистических цепочек курьера -->
              <div v-if="templateCategoryFilter === 'all' || templateCategoryFilter === 'courier'">
                <VDivider v-if="templateCategoryFilter === 'all'" class="my-6" />
                <div class="d-flex flex-wrap align-center justify-space-between mb-3 gap-2">
                  <h4 class="text-subtitle-1 font-weight-bold text-indigo d-flex align-center mb-0">
                    <VIcon icon="mdi-moped" class="me-2 text-indigo" />
                    Шаблоны логистических цепочек курьера ({{ courierTemplates.length }})
                  </h4>
                  <VChip color="indigo" size="small" variant="tonal" class="font-weight-medium">
                    <VIcon start icon="mdi-source-branch" size="16" />
                    Условия доставки настраиваются во вкладке «Цепочки курьера»
                  </VChip>
                </div>
                <!-- Построчный список логистических цепочек курьера -->
                <div v-if="templateViewMode === 'list'" class="d-flex flex-column gap-2 mb-6">
                  <VCard 
                    v-for="tpl in courierTemplates" 
                    :key="tpl.id"
                    variant="outlined" 
                    class="template-row-item px-3 py-2 rounded-xl border d-flex flex-wrap align-center justify-space-between gap-2" 
                    :class="{ 'template-row-inactive': !tpl.is_active }"
                    :style="{ borderColor: tpl.is_active ? '#3F51B5' : '#e0e0e0', backgroundColor: tpl.is_active ? '#F8F9FE' : '' }"
                  >
                    <!-- Левая часть: Чекбокс, Иконка, Название, Тип, Адресация -->
                    <div class="d-flex align-center gap-2 template-row-left" style="min-width: 280px; max-width: 380px;">
                      <VCheckbox
                        v-model="selectedTemplateIds"
                        :value="tpl.id"
                        density="compact"
                        hide-details
                        color="indigo"
                        class="pa-0 ma-0 flex-shrink-0"
                      />
                      <VAvatar :color="tpl.is_active ? 'indigo' : 'grey'" variant="tonal" size="34" class="flex-shrink-0">
                        <VIcon :icon="getEventIcon(tpl.event_type)" size="18" />
                      </VAvatar>
                      <div class="min-width-0">
                        <div class="d-flex align-center gap-1">
                          <span class="text-body-2 font-weight-bold text-truncate text-indigo-darken-2 cursor-pointer" :title="tpl.name" @click="openEditTemplate(tpl)">
                            {{ tpl.name }}
                          </span>
                          <VChip v-if="!tpl.is_active" size="x-small" color="error" variant="tonal" class="px-1" style="height: 18px; font-size: 10px;">
                            Выкл
                          </VChip>
                        </div>
                        <div class="d-flex align-center flex-wrap gap-1 mt-0">
                          <span class="text-caption text-grey text-truncate" style="font-size: 11px;">{{ getEventName(tpl.event_type) }}</span>
                          
                          <VChip
                            size="x-small"
                            color="indigo"
                            variant="flat"
                            class="font-weight-medium text-white px-1"
                            style="height: 18px; font-size: 10px;"
                            title="Адресно назначенному курьеру заказа"
                          >
                            🛵 Курьеру
                          </VChip>
                          <VChip
                            size="x-small"
                            :color="getStageBadgeColor(tpl.event_type)"
                            variant="tonal"
                            class="font-weight-bold px-1"
                            style="height: 18px; font-size: 10px;"
                          >
                            {{ getStageTitle(tpl.event_type) }}
                          </VChip>
                          <VChip
                            v-if="tpl.attach_sbp_qr"
                            size="x-small"
                            color="primary"
                            variant="outlined"
                            class="px-1"
                            style="height: 18px; font-size: 10px;"
                            title="QR-код СБП"
                          >
                            QR СБП
                          </VChip>
                        </div>
                      </div>
                    </div>

                    <!-- Центральная часть: Превью сообщения и описание -->
                    <div class="template-row-center flex-grow-1 min-width-0 mx-2" style="min-width: 200px;">
                      <div v-if="tpl.description" class="text-caption text-indigo font-weight-medium text-truncate mb-0" style="font-size: 11px;">
                        {{ tpl.description }}
                      </div>
                      <div
                        class="text-caption text-grey-darken-1 text-truncate-2 cursor-pointer"
                        style="line-height: 1.3; max-height: 2.6em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;"
                        :title="tpl.text"
                        @click="openEditTemplate(tpl)"
                      >
                        {{ tpl.text }}
                      </div>
                    </div>

                    <!-- Каналы отправки -->
                    <div class="template-row-channels d-flex align-center gap-1 flex-shrink-0">
                      <VChip
                        size="x-small"
                        :color="tpl.send_vk ? '#4C75A3' : 'grey-lighten-2'"
                        :variant="tpl.send_vk ? 'flat' : 'tonal'"
                        class="font-weight-bold cursor-pointer"
                        :class="tpl.send_vk ? 'text-white' : 'text-grey'"
                        @click="toggleTemplateChannel(tpl, 'vk')"
                        :disabled="togglingTplChannel[`${tpl.id}_vk`]"
                        title="Клик переключает канал VK"
                      >
                        <VIcon start :icon="tpl.send_vk ? 'mdi-check' : 'mdi-close'" size="12" />
                        VK
                      </VChip>
                      <VChip
                        size="x-small"
                        :color="tpl.send_max ? 'purple' : 'grey-lighten-2'"
                        :variant="tpl.send_max ? 'flat' : 'tonal'"
                        class="font-weight-bold cursor-pointer"
                        :class="tpl.send_max ? 'text-white' : 'text-grey'"
                        @click="toggleTemplateChannel(tpl, 'max')"
                        :disabled="togglingTplChannel[`${tpl.id}_max`]"
                        title="Клик переключает канал MAX"
                      >
                        <VIcon start :icon="tpl.send_max ? 'mdi-check' : 'mdi-close'" size="12" />
                        MAX
                      </VChip>
                      <VChip
                        size="x-small"
                        :color="tpl.send_tg ? '#0088cc' : 'grey-lighten-2'"
                        :variant="tpl.send_tg ? 'flat' : 'tonal'"
                        class="font-weight-bold cursor-pointer"
                        :class="tpl.send_tg ? 'text-white' : 'text-grey'"
                        @click="toggleTemplateChannel(tpl, 'tg')"
                        :disabled="togglingTplChannel[`${tpl.id}_tg`]"
                        title="Клик переключает канал Telegram"
                      >
                        <VIcon start :icon="tpl.send_tg ? 'mdi-check' : 'mdi-close'" size="12" />
                        TG
                      </VChip>
                      <VChip
                        size="x-small"
                        :color="tpl.send_sms ? 'success' : 'grey-lighten-2'"
                        :variant="tpl.send_sms ? 'flat' : 'tonal'"
                        class="font-weight-bold cursor-pointer"
                        :class="tpl.send_sms ? 'text-white' : 'text-grey'"
                        @click="toggleTemplateChannel(tpl, 'sms')"
                        :disabled="togglingTplChannel[`${tpl.id}_sms`]"
                        title="Клик переключает канал SMS"
                      >
                        <VIcon start :icon="tpl.send_sms ? 'mdi-check' : 'mdi-close'" size="12" />
                        SMS
                      </VChip>
                    </div>

                    <!-- Выбор сообщества / бота -->
                    <div class="template-row-bots d-flex align-center gap-1 flex-shrink-0" style="min-width: 250px; max-width: 320px;">
                      <VSelect
                        :model-value="tpl.vk_bot_id"
                        @update:model-value="val => setTemplateBot(tpl, val)"
                        :items="[
                          { id: null, title: 'Основное VK' },
                          ...bots.map(b => ({ id: b.id, title: `${b.name} (${b.vk_group_id})${b.is_main ? ' ★' : ''}` }))
                        ]"
                        item-title="title"
                        item-value="id"
                        density="compact"
                        variant="underlined"
                        hide-details
                        prepend-inner-icon="mdi-robot"
                        class="text-caption tpl-bot-select flex-grow-1"
                        style="font-size: 11px; max-width: 140px;"
                        :loading="settingTplBot[`${tpl.id}`]"
                        title="Сообщество VK для отправки"
                      />
                      <VSelect
                        :model-value="tpl.max_bot_id || null"
                        @update:model-value="val => setTemplateMaxBot(tpl, val, tpl.max_send_mode)"
                        :items="[
                          { id: null, title: 'Основной MAX' },
                          ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name}${b.is_default_for_notifications ? ' ★' : ''}` }))
                        ]"
                        item-title="title"
                        item-value="id"
                        density="compact"
                        variant="underlined"
                        hide-details
                        prepend-inner-icon="mdi-message-badge-outline"
                        class="text-caption tpl-bot-select flex-grow-1"
                        style="font-size: 11px; max-width: 130px;"
                        :loading="settingTplMaxBot[`${tpl.id}_max`]"
                        title="Бот MAX для отправки"
                      />
                    </div>

                    <!-- Переключатель активности -->
                    <div class="template-row-switch d-flex align-center flex-shrink-0">
                      <VSwitch
                        :model-value="tpl.is_active"
                        @update:model-value="toggleTemplateActive(tpl)"
                        color="success"
                        density="compact"
                        hide-details
                        title="Включить / выключить шаблон"
                      />
                    </div>

                    <!-- Кнопки действий -->
                    <div class="template-row-actions d-flex align-center gap-1 flex-shrink-0">
                      <VBtn
                        size="small"
                        variant="tonal"
                        color="info"
                        icon="mdi-send-check"
                        class="rounded-lg"
                        @click="testSendTemplate(tpl)"
                        :loading="testSendingTplId === tpl.id"
                        title="Отправить тестовое сообщение"
                      />
                      <VBtn
                        size="small"
                        variant="flat"
                        color="indigo"
                        prepend-icon="mdi-pencil"
                        class="rounded-lg"
                        @click="openEditTemplate(tpl)"
                      >
                        Изменить
                      </VBtn>
                    </div>
                  </VCard>
                </div>

                <!-- Плиточный вид (сетка) -->
                <VRow v-else class="mb-6">
                  <VCol v-for="tpl in courierTemplates" :key="tpl.id" cols="12" md="6" lg="4">
                    <VCard 
                      variant="outlined" 
                      class="pa-4 rounded-xl border-dashed relative-card d-flex flex-column h-100" 
                      :style="{ borderColor: tpl.is_active ? '#3F51B5' : '#e0e0e0', opacity: tpl.is_active ? 1 : 0.75, backgroundColor: tpl.is_active ? '#F8F9FE' : '' }"
                    >
                      <!-- Верхняя строка карточки -->
                      <div class="d-flex align-start justify-space-between mb-2">
                        <div class="d-flex align-center">
                          <VCheckbox
                            v-model="selectedTemplateIds"
                            :value="tpl.id"
                            density="compact"
                            hide-details
                            color="indigo"
                            class="me-2 pa-0"
                          />
                          <VAvatar :color="tpl.is_active ? 'indigo' : 'grey'" variant="tonal" size="36" class="me-2">
                            <VIcon :icon="getEventIcon(tpl.event_type)" size="20" />
                          </VAvatar>
                          <div>
                            <div class="text-subtitle-1 font-weight-bold d-flex align-center text-indigo-darken-2">
                              {{ tpl.name }}
                              <span v-if="!tpl.is_active" class="text-caption text-error ms-2">(Выкл)</span>
                            </div>
                            <div class="text-caption text-grey">{{ getEventName(tpl.event_type) }}</div>
                          </div>
                        </div>
                        
                        <VSwitch
                          :model-value="tpl.is_active"
                          @update:model-value="toggleTemplateActive(tpl)"
                          color="success"
                          density="compact"
                          hide-details
                          title="Включить / выключить шаблон"
                        />
                      </div>

                      <!-- Бейджи адресации и опций -->
                      <div class="d-flex flex-wrap gap-1 mb-2">
                        <VChip
                          size="x-small"
                          color="indigo"
                          variant="flat"
                          prepend-icon="mdi-moped"
                          class="font-weight-bold text-white"
                          title="Адресно назначенному курьеру заказа"
                        >
                          🛵 Курьеру iiko
                        </VChip>
                        <VChip
                          size="x-small"
                          :color="getStageBadgeColor(tpl.event_type)"
                          variant="tonal"
                          class="font-weight-bold"
                        >
                          {{ getStageTitle(tpl.event_type) }}
                        </VChip>
                        <VChip
                          v-if="tpl.attach_sbp_qr"
                          size="x-small"
                          color="primary"
                          variant="outlined"
                          prepend-icon="mdi-qrcode"
                          title="QR-код СБП с надписью"
                        >
                          QR СБП
                        </VChip>
                      </div>

                      <!-- Описание или пояснение -->
                      <div v-if="tpl.description" class="text-caption text-indigo mb-2 font-weight-medium">
                        {{ tpl.description }}
                      </div>

                      <!-- Текст шаблона -->
                      <div class="text-body-2 text-grey mb-3 text-truncate-3 flex-grow-1" style="min-height: 50px; white-space: pre-line;">{{ tpl.text }}</div>

                      <!-- Интерактивная полоска каналов отправки -->
                      <div class="pa-2 rounded-lg bg-grey-lighten-4 mb-3 border">
                        <div class="text-caption text-grey font-weight-bold mb-1 d-flex align-center justify-space-between">
                          <span>Каналы отправки:</span>
                          <span class="text-caption" style="font-size: 10px;">(клик переключает)</span>
                        </div>
                        <div class="d-flex flex-wrap gap-1">
                          <VChip
                            size="x-small"
                            :color="tpl.send_vk ? '#4C75A3' : 'grey-lighten-1'"
                            :variant="tpl.send_vk ? 'flat' : 'tonal'"
                            class="font-weight-bold cursor-pointer"
                            :prepend-icon="tpl.send_vk ? 'mdi-check-circle' : 'mdi-circle-outline'"
                            @click="toggleTemplateChannel(tpl, 'vk')"
                            :disabled="togglingTplChannel[`${tpl.id}_vk`]"
                          >
                            VK
                          </VChip>
                          <VChip
                            size="x-small"
                            :color="tpl.send_max ? 'purple' : 'grey-lighten-1'"
                            :variant="tpl.send_max ? 'flat' : 'tonal'"
                            class="font-weight-bold cursor-pointer"
                            :prepend-icon="tpl.send_max ? 'mdi-check-circle' : 'mdi-circle-outline'"
                            @click="toggleTemplateChannel(tpl, 'max')"
                            :disabled="togglingTplChannel[`${tpl.id}_max`]"
                          >
                            MAX
                          </VChip>
                          <VChip
                            size="x-small"
                            :color="tpl.send_tg ? '#0088cc' : 'grey-lighten-1'"
                            :variant="tpl.send_tg ? 'flat' : 'tonal'"
                            class="font-weight-bold cursor-pointer"
                            :prepend-icon="tpl.send_tg ? 'mdi-check-circle' : 'mdi-circle-outline'"
                            @click="toggleTemplateChannel(tpl, 'tg')"
                            :disabled="togglingTplChannel[`${tpl.id}_tg`]"
                          >
                            TG
                          </VChip>
                          <VChip
                            size="x-small"
                            :color="tpl.send_sms ? 'success' : 'grey-lighten-1'"
                            :variant="tpl.send_sms ? 'flat' : 'tonal'"
                            class="font-weight-bold cursor-pointer"
                            :prepend-icon="tpl.send_sms ? 'mdi-check-circle' : 'mdi-circle-outline'"
                            @click="toggleTemplateChannel(tpl, 'sms')"
                            :disabled="togglingTplChannel[`${tpl.id}_sms`]"
                          >
                            SMS
                          </VChip>
                        </div>
                      </div>

                      <!-- Выбор сообщества / бота прямо на карточке -->
                      <div class="mb-3 d-flex flex-wrap gap-2">
                        <VSelect
                          :model-value="tpl.vk_bot_id"
                          @update:model-value="val => setTemplateBot(tpl, val)"
                          :items="[
                            { id: null, title: 'Основное сообщество VK' },
                            ...bots.map(b => ({ id: b.id, title: `${b.name} (${b.vk_group_id})${b.is_main ? ' ★' : ''}` }))
                          ]"
                          item-title="title"
                          item-value="id"
                          density="compact"
                          variant="underlined"
                          hide-details
                          prepend-inner-icon="mdi-robot"
                          class="text-caption flex-grow-1"
                          style="min-width: 180px;"
                          :loading="settingTplBot[`${tpl.id}`]"
                        />
                        <VSelect
                          :model-value="tpl.max_bot_id || null"
                          @update:model-value="val => setTemplateMaxBot(tpl, val, tpl.max_send_mode)"
                          :items="[
                            { id: null, title: 'Основной бот MAX' },
                            ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name}${b.is_default_for_notifications ? ' ★' : ''}` }))
                          ]"
                          item-title="title"
                          item-value="id"
                          density="compact"
                          variant="underlined"
                          hide-details
                          prepend-inner-icon="mdi-message-badge-outline"
                          class="text-caption flex-grow-1"
                          style="min-width: 180px;"
                          :loading="settingTplMaxBot[`${tpl.id}_max`]"
                        />
                        <VSelect
                          :model-value="tpl.max_send_mode || 'cascade'"
                          @update:model-value="mode => setTemplateMaxBot(tpl, tpl.max_bot_id, mode)"
                          :items="[
                            { id: 'cascade', title: 'MAX: Каскад' },
                            { id: 'bot_only', title: 'MAX: Только бот' },
                            { id: 'bridge_only', title: 'MAX: Только личные' }
                          ]"
                          item-title="title"
                          item-value="id"
                          density="compact"
                          variant="underlined"
                          hide-details
                          prepend-inner-icon="mdi-call-split"
                          class="text-caption"
                          style="width: 160px;"
                          :loading="settingTplMaxBot[`${tpl.id}_max`]"
                        />
                      </div>

                      <VDivider class="my-2" />

                      <!-- Кнопки действий -->
                      <div class="d-flex align-center gap-2">
                        <VBtn
                          size="small"
                          variant="tonal"
                          color="info"
                          prepend-icon="mdi-send-check"
                          class="flex-grow-1 rounded-lg"
                          @click="testSendTemplate(tpl)"
                          :loading="testSendingTplId === tpl.id"
                          title="Отправить тестовое сообщение"
                        >
                          Тест
                        </VBtn>
                        <VBtn
                          size="small"
                          variant="flat"
                          color="indigo"
                          prepend-icon="mdi-pencil"
                          class="flex-grow-1 rounded-lg"
                          @click="openEditTemplate(tpl)"
                        >
                          Изменить
                        </VBtn>
                      </div>
                    </VCard>
                  </VCol>
                </VRow>
              </div>

              <!-- Раздел: Шаблоны для ручной рассылки -->
              <div v-if="templateCategoryFilter === 'all' || templateCategoryFilter === 'custom'">
                <VDivider v-if="templateCategoryFilter === 'all'" class="my-6" />
                <h4 class="text-subtitle-1 font-weight-bold text-secondary mb-3 d-flex align-center">
                  <VIcon icon="mdi-bullhorn-outline" class="me-2 text-secondary" />
                  Шаблоны для ручной рассылки ({{ customTemplates.length }})
                </h4>
                <!-- Построчный список шаблонов ручной рассылки -->
                <div v-if="templateViewMode === 'list'">
                  <div v-if="customTemplates.length > 0" class="d-flex flex-column gap-2 mb-6">
                    <VCard 
                      v-for="tpl in customTemplates" 
                      :key="tpl.id"
                      variant="outlined" 
                      class="template-row-item px-3 py-2 rounded-xl border d-flex flex-wrap align-center justify-space-between gap-2" 
                      :class="{ 'template-row-inactive': !tpl.is_active }"
                    >
                      <!-- Левая часть: Чекбокс, Иконка, Название, Тип -->
                      <div class="d-flex align-center gap-2 template-row-left" style="min-width: 280px; max-width: 380px;">
                        <VCheckbox
                          v-model="selectedTemplateIds"
                          :value="tpl.id"
                          density="compact"
                          hide-details
                          color="secondary"
                          class="pa-0 ma-0 flex-shrink-0"
                        />
                        <VAvatar :color="tpl.is_active ? 'secondary' : 'grey'" variant="tonal" size="34" class="flex-shrink-0">
                          <VIcon icon="mdi-bullhorn-outline" size="18" />
                        </VAvatar>
                        <div class="min-width-0">
                          <div class="d-flex align-center gap-1">
                            <span class="text-body-2 font-weight-bold text-truncate cursor-pointer" :title="tpl.name" @click="openEditTemplate(tpl)">
                              {{ tpl.name }}
                            </span>
                            <VChip v-if="!tpl.is_active" size="x-small" color="error" variant="tonal" class="px-1" style="height: 18px; font-size: 10px;">
                              Выкл
                            </VChip>
                          </div>
                          <div class="d-flex align-center flex-wrap gap-1 mt-0">
                            <span class="text-caption text-grey text-truncate" style="font-size: 11px;">Ручная рассылка</span>
                          </div>
                        </div>
                      </div>

                      <!-- Центральная часть: Превью сообщения -->
                      <div class="template-row-center flex-grow-1 min-width-0 mx-2" style="min-width: 200px;">
                        <div
                          class="text-caption text-grey-darken-1 text-truncate-2 cursor-pointer"
                          style="line-height: 1.3; max-height: 2.6em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;"
                          :title="tpl.text"
                          @click="openEditTemplate(tpl)"
                        >
                          {{ tpl.text }}
                        </div>
                      </div>

                      <!-- Каналы отправки -->
                      <div class="template-row-channels d-flex align-center gap-1 flex-shrink-0">
                        <VChip
                          size="x-small"
                          :color="tpl.send_vk ? '#4C75A3' : 'grey-lighten-2'"
                          :variant="tpl.send_vk ? 'flat' : 'tonal'"
                          class="font-weight-bold cursor-pointer"
                          :class="tpl.send_vk ? 'text-white' : 'text-grey'"
                          @click="toggleTemplateChannel(tpl, 'vk')"
                          title="Клик переключает канал VK"
                        >
                          <VIcon start :icon="tpl.send_vk ? 'mdi-check' : 'mdi-close'" size="12" />
                          VK
                        </VChip>
                        <VChip
                          size="x-small"
                          :color="tpl.send_max ? 'purple' : 'grey-lighten-2'"
                          :variant="tpl.send_max ? 'flat' : 'tonal'"
                          class="font-weight-bold cursor-pointer"
                          :class="tpl.send_max ? 'text-white' : 'text-grey'"
                          @click="toggleTemplateChannel(tpl, 'max')"
                          title="Клик переключает канал MAX"
                        >
                          <VIcon start :icon="tpl.send_max ? 'mdi-check' : 'mdi-close'" size="12" />
                          MAX
                        </VChip>
                        <VChip
                          size="x-small"
                          :color="tpl.send_tg ? '#0088cc' : 'grey-lighten-2'"
                          :variant="tpl.send_tg ? 'flat' : 'tonal'"
                          class="font-weight-bold cursor-pointer"
                          :class="tpl.send_tg ? 'text-white' : 'text-grey'"
                          @click="toggleTemplateChannel(tpl, 'tg')"
                          title="Клик переключает канал Telegram"
                        >
                          <VIcon start :icon="tpl.send_tg ? 'mdi-check' : 'mdi-close'" size="12" />
                          TG
                        </VChip>
                        <VChip
                          size="x-small"
                          :color="tpl.send_sms ? 'success' : 'grey-lighten-2'"
                          :variant="tpl.send_sms ? 'flat' : 'tonal'"
                          class="font-weight-bold cursor-pointer"
                          :class="tpl.send_sms ? 'text-white' : 'text-grey'"
                          @click="toggleTemplateChannel(tpl, 'sms')"
                          title="Клик переключает канал SMS"
                        >
                          <VIcon start :icon="tpl.send_sms ? 'mdi-check' : 'mdi-close'" size="12" />
                          SMS
                        </VChip>
                      </div>

                      <!-- Переключатель активности -->
                      <div class="template-row-switch d-flex align-center flex-shrink-0">
                        <VSwitch
                          :model-value="tpl.is_active"
                          @update:model-value="toggleTemplateActive(tpl)"
                          color="success"
                          density="compact"
                          hide-details
                          title="Включить / выключить шаблон"
                        />
                      </div>

                      <!-- Кнопки действий -->
                      <div class="template-row-actions d-flex align-center gap-1 flex-shrink-0">
                        <VBtn
                          size="small"
                          variant="tonal"
                          color="info"
                          icon="mdi-send-check"
                          class="rounded-lg"
                          @click="testSendTemplate(tpl)"
                          :loading="testSendingTplId === tpl.id"
                          title="Отправить тестовое сообщение"
                        />
                        <VBtn
                          size="small"
                          variant="tonal"
                          color="secondary"
                          icon="mdi-pencil"
                          class="rounded-lg"
                          @click="openEditTemplate(tpl)"
                          title="Изменить шаблон"
                        />
                        <VBtn
                          size="small"
                          variant="text"
                          color="error"
                          icon="mdi-delete"
                          class="rounded-lg"
                          @click="deleteTemplate(tpl.id)"
                          title="Удалить шаблон"
                        />
                      </div>
                    </VCard>
                  </div>
                  <div v-else class="text-caption text-grey py-4">Нет шаблонов для ручной рассылки. Создайте шаблон и выберите тип события "Ручная рассылка".</div>
                </div>

                <!-- Плиточный вид (сетка) -->
                <div v-else>
                  <VRow v-if="customTemplates.length > 0">
                  <VCol v-for="tpl in customTemplates" :key="tpl.id" cols="12" md="6" lg="4">
                    <VCard 
                      variant="outlined" 
                      class="pa-4 rounded-xl bg-surface-variant relative-card d-flex flex-column h-100"
                      :style="{ opacity: tpl.is_active ? 1 : 0.75 }"
                    >
                      <div class="d-flex align-start justify-space-between mb-2">
                        <div class="d-flex align-center">
                          <VCheckbox
                            v-model="selectedTemplateIds"
                            :value="tpl.id"
                            density="compact"
                            hide-details
                            color="secondary"
                            class="me-2 pa-0"
                          />
                          <VAvatar color="secondary" variant="tonal" size="36" class="me-2">
                            <VIcon icon="mdi-bullhorn-outline" size="20" />
                          </VAvatar>
                          <div>
                            <div class="text-subtitle-1 font-weight-bold">{{ tpl.name }}</div>
                            <div class="text-caption text-grey">Ручная рассылка</div>
                          </div>
                        </div>

                        <VSwitch
                          :model-value="tpl.is_active"
                          @update:model-value="toggleTemplateActive(tpl)"
                          color="success"
                          density="compact"
                          hide-details
                        />
                      </div>

                      <!-- Текст шаблона -->
                      <div class="text-body-2 text-grey mb-3 text-truncate-3 flex-grow-1" style="min-height: 50px; white-space: pre-line;">{{ tpl.text }}</div>

                      <!-- Интерактивная полоска каналов отправки -->
                      <div class="pa-2 rounded-lg bg-grey-lighten-4 mb-3 border">
                        <div class="d-flex flex-wrap gap-1">
                          <VChip
                            size="x-small"
                            :color="tpl.send_vk ? '#4C75A3' : 'grey-lighten-1'"
                            :variant="tpl.send_vk ? 'flat' : 'tonal'"
                            class="font-weight-bold cursor-pointer"
                            @click="toggleTemplateChannel(tpl, 'vk')"
                          >
                            VK
                          </VChip>
                          <VChip
                            size="x-small"
                            :color="tpl.send_max ? 'purple' : 'grey-lighten-1'"
                            :variant="tpl.send_max ? 'flat' : 'tonal'"
                            class="font-weight-bold cursor-pointer"
                            @click="toggleTemplateChannel(tpl, 'max')"
                          >
                            MAX
                          </VChip>
                          <VChip
                            size="x-small"
                            :color="tpl.send_tg ? '#0088cc' : 'grey-lighten-1'"
                            :variant="tpl.send_tg ? 'flat' : 'tonal'"
                            class="font-weight-bold cursor-pointer"
                            @click="toggleTemplateChannel(tpl, 'tg')"
                          >
                            TG
                          </VChip>
                          <VChip
                            size="x-small"
                            :color="tpl.send_sms ? 'success' : 'grey-lighten-1'"
                            :variant="tpl.send_sms ? 'flat' : 'tonal'"
                            class="font-weight-bold cursor-pointer"
                            @click="toggleTemplateChannel(tpl, 'sms')"
                          >
                            SMS
                          </VChip>
                        </div>
                      </div>

                      <VDivider class="my-2" />

                      <div class="d-flex align-center gap-2">
                        <VBtn
                          size="small"
                          variant="tonal"
                          color="info"
                          prepend-icon="mdi-send-check"
                          class="flex-grow-1 rounded-lg"
                          @click="testSendTemplate(tpl)"
                          :loading="testSendingTplId === tpl.id"
                        >
                          Тест
                        </VBtn>
                        <VBtn size="small" variant="flat" color="secondary" prepend-icon="mdi-pencil" class="flex-grow-1 rounded-lg" @click="openEditTemplate(tpl)">
                          Изменить
                        </VBtn>
                        <VBtn size="small" variant="tonal" color="error" icon="mdi-delete" class="rounded-lg" @click="deleteTemplate(tpl.id)" />
                      </div>
                    </VCard>
                  </VCol>
                </VRow>
                <div v-else class="text-caption text-grey py-4">Нет шаблонов для ручной рассылки. Создайте шаблон и выберите тип события "Ручная рассылка".</div>
                </div>
              </div>
            </VWindowItem>

            <VWindowItem value="logs">
              <VTable density="comfortable" class="border rounded-xl">
                <thead>
                  <tr class="bg-grey-lighten-4">
                    <th class="font-weight-bold">Время</th>
                    <th class="font-weight-bold">Событие</th>
                    <th class="font-weight-bold">Текст сообщения</th>
                    <th class="text-center font-weight-bold">Статус отправки</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in logs" :key="log.id" class="hover-row">
                    <td class="text-caption font-weight-medium" style="white-space: nowrap;">{{ formatDate(log.created_at) }}</td>
                    <td><VChip size="small" variant="outlined" color="primary" label class="font-weight-bold">{{ getEventName(log.event_type) }}</VChip></td>
                    <td class="text-truncate text-body-2" style="max-width: 500px">{{ log.text }}</td>
                    <td class="text-center">
                      <VChip :color="log.status === 'sent' ? 'success' : (log.status === 'failed' ? 'error' : 'warning')" size="small" label variant="tonal">
                        <VIcon :icon="log.status === 'sent' ? 'mdi-check-circle' : (log.status === 'failed' ? 'mdi-alert-circle' : 'mdi-clock-outline')" size="14" class="me-1" />
                        {{ log.status === 'sent' ? 'Отправлено' : (log.status === 'failed' ? 'Ошибка' : 'В очереди') }}
                      </VChip>
                    </td>
                  </tr>
                </tbody>
              </VTable>
            </VWindowItem>

            <VWindowItem value="settings">
              <div class="py-4" style="max-width: 600px;">
                <h3 class="text-h6 font-weight-bold mb-4 text-primary">Настройки каналов системных рассылок</h3>
                <VCard variant="outlined" rounded="xl" class="pa-6 mb-6">
                  <div class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
                    <VIcon icon="mdi-vk" color="#4C75A3" class="me-2" />
                    Канал ВКонтакте (VK)
                  </div>
                  <div class="text-body-2 text-grey mb-4">
                    Выберите подключение (группу VK), через которое будут отправляться системные уведомления сотрудникам.
                  </div>
                  
                  <VSelect
                    v-model="selectedBotId"
                    :items="bots"
                    item-title="name"
                    item-value="id"
                    label="Выберите бота для системных уведомлений"
                    variant="outlined"
                    class="mb-4"
                  >
                    <template #item="{ props, item }">
                      <VListItem v-bind="props" :subtitle="`ID группы: ${item.raw.vk_group_id}`">
                        <template #append>
                          <VChip v-if="item.raw.is_main" size="x-small" color="primary" class="font-weight-bold">Текущий</VChip>
                        </template>
                      </VListItem>
                    </template>
                  </VSelect>
                  
                  <div v-if="bots.length === 0" class="text-caption text-error mb-4">
                    ⚠️ Нет подключенных VK-ботов. Сначала добавьте подключение в разделе "Настройки VK Бота".
                  </div>
                  
                  <VBtn 
                    color="primary" 
                    rounded="lg" 
                    :loading="savingMainBot" 
                    :disabled="bots.length === 0"
                    @click="saveMainBot"
                  >
                    Сохранить настройки
                  </VBtn>
                </VCard>
              </div>
            </VWindowItem>
          </VWindow>
        </VCard>
      </VCol>
    </VRow>

    <!-- Диалог настройки каналов и подписок -->
    <VDialog v-model="subscriptionDialog" max-width="880px" scrollable>
      <VCard rounded="xl" class="glass-card">
        <VCardTitle class="pa-6 d-flex align-center">
          <VIcon icon="mdi-tune-vertical" class="me-3" color="primary" size="28" />
          <div>
            <div class="text-h6 font-weight-bold">Каналы рассылок и подписки получателя</div>
            <div class="text-caption text-grey d-flex align-center gap-2 mt-0.5">
              <span class="font-weight-medium">{{ currentAccount?.name }}</span>
              <span v-if="currentAccount?.phone">({{ currentAccount.phone }})</span>
              <VChip v-if="currentAccount?.is_courier" color="indigo" size="x-small" label variant="flat" class="font-weight-black text-white">
                <VIcon icon="mdi-moped" size="12" class="me-1" /> Курьер iiko
              </VChip>
            </div>
          </div>
          <VSpacer />
          <VBtn icon="mdi-close" variant="text" @click="subscriptionDialog = false" />
        </VCardTitle>
        <VDivider />

        <VProgressLinear v-if="channelSettingsLoading" indeterminate color="primary" />

        <VCardText class="pa-6">
          <div class="d-flex flex-column gap-6">

            <!-- БЛОК 1: Проверка связи и разрешение сообщений ВКонтакте -->
            <VCard variant="outlined" rounded="lg" class="border-grey-lighten-2 overflow-hidden">
              <div class="px-5 py-3 bg-grey-lighten-4 d-flex align-center justify-space-between border-bottom">
                <div class="d-flex align-center">
                  <VIcon icon="mdi-vk" color="#4C75A3" class="me-2" size="22" />
                  <span class="font-weight-bold text-subtitle-2">Авторизация и проверка сообщений ВКонтакте</span>
                </div>
                <div class="text-caption text-grey">
                  VK ID: <span class="font-weight-bold">{{ currentAccount?.vk_user_id || 'Не привязан' }}</span>
                </div>
              </div>
              <div class="pa-5">
                <div v-if="!currentAccount?.vk_user_id" class="d-flex align-center gap-2 text-warning mb-2">
                  <VIcon icon="mdi-alert" color="warning" />
                  <span class="text-body-2">У получателя не привязан VK ID! Сообщения ВКонтакте отправляться не будут.</span>
                </div>
                <div v-else class="text-caption text-grey-darken-1 mb-4">
                  ⚠️ <b>Важно:</b> По правилам ВКонтакте бот сообщества не может отправить сообщение пользователю первым, пока получатель не разрешит сообщения сообществу или не напишет ему диалог.
                </div>

                <!-- Список подключенных групп VK -->
                <div class="d-flex flex-column gap-3">
                  <div
                    v-for="bot in channelSettings?.vk_groups || []"
                    :key="bot.id"
                    class="pa-3 rounded-lg border d-flex flex-wrap align-center justify-space-between gap-3"
                    :class="bot.is_messages_allowed ? 'bg-green-lighten-5 border-success' : 'bg-orange-lighten-5 border-warning'"
                  >
                    <div class="d-flex align-center gap-3">
                      <VAvatar :color="bot.is_messages_allowed ? 'success' : 'warning'" variant="tonal" size="36">
                        <VIcon :icon="bot.is_messages_allowed ? 'mdi-check-circle' : 'mdi-alert-circle'" />
                      </VAvatar>
                      <div>
                        <div class="d-flex align-center gap-2">
                          <span class="font-weight-bold text-body-2">{{ bot.name }}</span>
                          <VChip v-if="bot.is_main" size="x-small" color="primary" variant="tonal">Основной</VChip>
                          <VChip v-if="bot.is_courier_bot" size="x-small" color="indigo" variant="tonal">Бот курьеров</VChip>
                          <span class="text-caption text-grey">ID: {{ bot.vk_group_id }}</span>
                        </div>
                        <div class="text-caption mt-0.5" :class="bot.is_messages_allowed ? 'text-success' : 'text-deep-orange-darken-2'">
                          {{ bot.is_messages_allowed ? '✓ Сообщения разрешены (связь активна)' : '✕ Сообщения не разрешены пользователем' }}
                        </div>
                      </div>
                    </div>

                    <div class="d-flex align-center gap-2">
                      <VBtn
                        v-if="!bot.is_messages_allowed"
                        :href="bot.allow_url"
                        target="_blank"
                        size="small"
                        color="#4C75A3"
                        variant="flat"
                        prepend-icon="mdi-open-in-new"
                      >
                        Разрешить в ВК
                      </VBtn>
                      <VBtn
                        size="small"
                        variant="outlined"
                        color="secondary"
                        prepend-icon="mdi-refresh"
                        :loading="checkingVkBot[bot.id]"
                        @click="checkVkGroupAuth(bot.id)"
                      >
                        Проверить
                      </VBtn>
                      <VBtn
                        v-if="bot.is_messages_allowed"
                        size="small"
                        variant="tonal"
                        color="success"
                        prepend-icon="mdi-send-check"
                        :loading="sendingTestVkBot[bot.id]"
                        @click="sendTestVkGroup(bot.id)"
                      >
                        Тест
                      </VBtn>
                    </div>
                  </div>
                </div>
              </div>
            </VCard>

            <!-- БЛОК 2: Рассылка «Цепочки курьера» (СТРОГО ДЛЯ КУРЬЕРОВ) -->
            <VCard
              variant="outlined"
              rounded="lg"
              class="overflow-hidden border-2"
              :class="channelSettings?.courier_chains?.allow_courier_chains ? 'border-indigo' : 'border-grey-lighten-1'"
            >
              <div class="px-5 py-4 d-flex flex-wrap align-center justify-space-between gap-3" :class="channelSettings?.courier_chains?.allow_courier_chains ? 'bg-indigo-lighten-5' : 'bg-grey-lighten-4'">
                <div class="d-flex align-center gap-3">
                  <VAvatar color="indigo" variant="flat" size="40">
                    <VIcon icon="mdi-moped" color="white" />
                  </VAvatar>
                  <div>
                    <div class="d-flex align-center gap-2">
                      <span class="text-subtitle-1 font-weight-black text-indigo-darken-3">Рассылка: Цепочки курьера</span>
                      <VChip color="indigo" size="x-small" label variant="flat" class="font-weight-black text-white">
                        СТРОГО ДЛЯ КУРЬЕРОВ
                      </VChip>
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Пошаговые уведомления по этапам заказа: новый заказ, кухня, статус, адрес, состав, время, отмена
                    </div>
                  </div>
                </div>

                <div class="d-flex align-center gap-3">
                  <VSwitch
                    :model-value="channelSettings?.courier_chains?.allow_courier_chains || false"
                    color="indigo"
                    inset
                    hide-details
                    :loading="togglingCourierChainsLoading"
                    @update:model-value="toggleCourierChains"
                  />
                </div>
              </div>

              <VDivider />

              <div class="pa-5">
                <div v-if="channelSettings?.courier_chains?.allow_courier_chains">
                  <div class="text-caption font-weight-bold text-grey-darken-2 mb-3">
                    Каналы отправки курьерских цепочек для данного сотрудника:
                  </div>
                  <div class="d-flex flex-wrap align-center gap-3">
                    <!-- VK канал курьера -->
                    <VChip
                      size="default"
                      :color="channelSettings?.courier_chains?.send_vk ? '#4C75A3' : 'grey'"
                      :variant="channelSettings?.courier_chains?.send_vk ? 'flat' : 'outlined'"
                      class="cursor-pointer font-weight-bold"
                      @click="toggleCourierChainChannel('vk', !channelSettings?.courier_chains?.send_vk)"
                    >
                      <VIcon start icon="mdi-vk" />
                      ВКонтакте
                      <VIcon end :icon="channelSettings?.courier_chains?.send_vk ? 'mdi-check' : 'mdi-close'" />
                    </VChip>

                    <!-- TG канал курьера -->
                    <VChip
                      size="default"
                      :color="channelSettings?.courier_chains?.send_tg ? '#0088cc' : 'grey'"
                      :variant="channelSettings?.courier_chains?.send_tg ? 'flat' : 'outlined'"
                      class="cursor-pointer font-weight-bold"
                      @click="toggleCourierChainChannel('tg', !channelSettings?.courier_chains?.send_tg)"
                    >
                      <VIcon start icon="mdi-telegram" />
                      Telegram
                      <VIcon end :icon="channelSettings?.courier_chains?.send_tg ? 'mdi-check' : 'mdi-close'" />
                    </VChip>

                    <!-- MAX канал курьера -->
                    <VChip
                      size="default"
                      :color="channelSettings?.courier_chains?.send_max ? 'teal-darken-1' : 'grey'"
                      :variant="channelSettings?.courier_chains?.send_max ? 'flat' : 'outlined'"
                      class="cursor-pointer font-weight-bold"
                      @click="toggleCourierChainChannel('max', !channelSettings?.courier_chains?.send_max)"
                    >
                      <VIcon start icon="mdi-message-text" />
                      MAX Messenger
                      <VIcon end :icon="channelSettings?.courier_chains?.send_max ? 'mdi-check' : 'mdi-close'" />
                    </VChip>

                    <!-- SMS канал курьера -->
                    <VChip
                      size="default"
                      :color="channelSettings?.courier_chains?.send_sms ? 'primary' : 'grey'"
                      :variant="channelSettings?.courier_chains?.send_sms ? 'flat' : 'outlined'"
                      class="cursor-pointer font-weight-bold"
                      @click="toggleCourierChainChannel('sms', !channelSettings?.courier_chains?.send_sms)"
                    >
                      <VIcon start icon="mdi-cellphone-message" />
                      SMS
                      <VIcon end :icon="channelSettings?.courier_chains?.send_sms ? 'mdi-check' : 'mdi-close'" />
                    </VChip>

                    <!-- Быстрая проверка связи TG и MAX -->
                    <VBtn
                      v-if="currentAccount?.tg_user_id"
                      size="small"
                      variant="tonal"
                      color="#0088cc"
                      prepend-icon="mdi-send-check-outline"
                      rounded="lg"
                      class="font-weight-bold ms-2"
                      title="Отправить проверочное сообщение в Telegram"
                      @click="verifyAccountTg(currentAccount.id)"
                    >
                      Тест TG
                    </VBtn>
                    <VBtn
                      v-if="currentAccount && (currentAccount.max_user_id || currentAccount.phone)"
                      size="small"
                      variant="tonal"
                      color="teal-darken-1"
                      prepend-icon="mdi-send-check-outline"
                      rounded="lg"
                      class="font-weight-bold"
                      title="Отправить проверочное сообщение в MAX Messenger"
                      @click="verifyAccountMax(currentAccount.id)"
                    >
                      Тест MAX
                    </VBtn>
                  </div>

                  <div v-if="!currentAccount?.is_courier" class="mt-4 pa-3 rounded bg-amber-lighten-5 border-warning d-flex align-center gap-2">
                    <VIcon icon="mdi-alert-circle" color="warning" size="20" />
                    <span class="text-caption text-amber-darken-4">
                      <b>Внимание:</b> Получатель не отмечен как курьер iiko. Курьерские цепочки отправляются <b>СТРОГО</b> курьеру, назначенному на заказ в iiko!
                    </span>
                  </div>
                </div>
                <div v-else class="text-caption text-grey">
                  Цепочки курьера для данного получателя выключены. Он не будет получать пошаговые уведомления по заказам курьера.
                </div>
              </div>
            </VCard>

            <!-- БЛОК 3: Динамические системные шаблоны сотрудников -->
            <VCard variant="outlined" rounded="lg" class="border-grey-lighten-2 overflow-hidden">
              <div class="px-5 py-4 bg-grey-lighten-4 border-bottom d-flex flex-wrap align-center justify-space-between gap-3">
                <div>
                  <div class="d-flex align-center gap-2">
                    <VIcon icon="mdi-file-document-multiple-outline" color="primary" size="22" />
                    <span class="text-subtitle-1 font-weight-bold">Системные шаблоны сотрудников (из вкладки «Шаблоны»)</span>
                  </div>
                  <div class="text-caption text-grey">
                    Управление подписками на информационные рассылки. Список формируется динамически из базы данных.
                  </div>
                </div>

                <div class="d-flex flex-wrap gap-2 align-center">
                  <VBtn
                    size="small"
                    variant="tonal"
                    color="success"
                    :loading="bulkTemplatesLoading"
                    @click="bulkTemplatesAction('enable_all')"
                  >
                    Включить все
                  </VBtn>
                  <VBtn
                    size="small"
                    variant="tonal"
                    color="grey"
                    :loading="bulkTemplatesLoading"
                    @click="bulkTemplatesAction('disable_all')"
                  >
                    Отключить все
                  </VBtn>

                  <VBtnGroup density="compact" variant="outlined" class="ms-2">
                    <VBtn size="x-small" color="#4C75A3" :loading="bulkTemplatesLoading" title="Включить VK для всех шаблонов" @click="bulkTemplatesAction('channel', 'vk')">
                      <VIcon start icon="mdi-vk" size="14" /> +VK
                    </VBtn>
                    <VBtn size="x-small" color="#0088cc" :loading="bulkTemplatesLoading" title="Включить TG для всех шаблонов" @click="bulkTemplatesAction('channel', 'tg')">
                      <VIcon start icon="mdi-telegram" size="14" /> +TG
                    </VBtn>
                    <VBtn size="x-small" color="teal-darken-1" :loading="bulkTemplatesLoading" title="Включить MAX для всех шаблонов" @click="bulkTemplatesAction('channel', 'max')">
                      <VIcon start icon="mdi-message-text" size="14" /> +MAX
                    </VBtn>
                    <VBtn size="x-small" color="primary" :loading="bulkTemplatesLoading" title="Включить SMS для всех шаблонов" @click="bulkTemplatesAction('channel', 'sms')">
                      <VIcon start icon="mdi-cellphone-message" size="14" /> +SMS
                    </VBtn>
                  </VBtnGroup>
                </div>
              </div>

              <VList lines="two" class="pa-0">
                <template v-for="(tpl, idx) in channelSettings?.templates || []" :key="tpl.id">
                  <VListItem class="px-5 py-4" :class="{ 'bg-grey-lighten-5': !tpl.subscribed }">
                    <template #prepend>
                      <VAvatar :color="tpl.subscribed ? 'primary' : 'grey'" variant="tonal" size="40">
                        <VIcon :icon="getEventIcon(tpl.event_type)" />
                      </VAvatar>
                    </template>

                    <VListItemTitle class="font-weight-bold text-subtitle-2 d-flex flex-wrap align-center gap-2">
                      <span>{{ tpl.name }}</span>
                      <VChip size="x-small" color="secondary" variant="outlined">{{ tpl.event_type }}</VChip>
                      <VChip v-if="!tpl.is_active" size="x-small" color="error" variant="tonal">Выключен в системе</VChip>
                      <VChip v-if="tpl.bot_name" size="x-small" color="#4C75A3" variant="tonal">Бот: {{ tpl.bot_name }}</VChip>
                    </VListItemTitle>

                    <VListItemSubtitle class="text-caption text-grey mt-1">
                      <div v-if="tpl.description" class="mb-1">{{ tpl.description }}</div>
                      
                      <!-- Замечания по доступности -->
                      <div v-if="tpl.availability_notes && tpl.availability_notes.length > 0" class="d-flex flex-wrap gap-1 text-deep-orange-darken-2">
                        <span v-for="(note, nIdx) in tpl.availability_notes" :key="nIdx" class="d-inline-flex align-center me-2">
                          ⚠️ {{ note }}
                        </span>
                      </div>
                    </VListItemSubtitle>

                    <template #append>
                      <div class="d-flex align-center gap-4">
                        <!-- Каналы шаблона (доступны если подписан) -->
                        <div v-if="tpl.subscribed" class="d-flex align-center gap-1">
                          <VCheckboxBtn
                            :model-value="tpl.sub_channels?.vk || false"
                            color="#4C75A3"
                            title="Отправлять в ВКонтакте"
                            @update:model-value="(val) => toggleTemplateSubChannel(tpl, 'vk', val)"
                          >
                            <template #label><VIcon icon="mdi-vk" color="#4C75A3" size="18" /></template>
                          </VCheckboxBtn>

                          <VCheckboxBtn
                            :model-value="tpl.sub_channels?.tg || false"
                            color="#0088cc"
                            title="Отправлять в Telegram"
                            @update:model-value="(val) => toggleTemplateSubChannel(tpl, 'tg', val)"
                          >
                            <template #label><VIcon icon="mdi-telegram" color="#0088cc" size="18" /></template>
                          </VCheckboxBtn>

                          <VCheckboxBtn
                            :model-value="tpl.sub_channels?.max || false"
                            color="teal-darken-1"
                            title="Отправлять в MAX"
                            @update:model-value="(val) => toggleTemplateSubChannel(tpl, 'max', val)"
                          >
                            <template #label><VIcon icon="mdi-message-text" color="teal-darken-1" size="18" /></template>
                          </VCheckboxBtn>

                          <VCheckboxBtn
                            :model-value="tpl.sub_channels?.sms || false"
                            color="primary"
                            title="Отправлять по SMS"
                            @update:model-value="(val) => toggleTemplateSubChannel(tpl, 'sms', val)"
                          >
                            <template #label><VIcon icon="mdi-cellphone-message" color="primary" size="18" /></template>
                          </VCheckboxBtn>
                        </div>

                        <!-- Тумблер подписки на шаблон -->
                        <VSwitch
                          :model-value="tpl.subscribed"
                          color="primary"
                          inset
                          hide-details
                          :loading="togglingTemplateLoading[tpl.event_type]"
                          @update:model-value="(val) => toggleTemplateSubscription(tpl, val)"
                        />
                      </div>
                    </template>
                  </VListItem>
                  <VDivider v-if="idx < (channelSettings?.templates?.length - 1)" />
                </template>
              </VList>
            </VCard>

          </div>
        </VCardText>

        <VDivider />
        <VCardActions class="pa-5 bg-grey-lighten-5">
          <VSpacer />
          <VBtn color="primary" variant="flat" size="large" rounded="lg" class="px-8" @click="subscriptionDialog = false">
            Готово
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог добавления получателя -->
    <VDialog v-model="addAccountDialog" max-width="540px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6 font-weight-bold d-flex align-center">
          <VIcon icon="mdi-account-plus-outline" color="primary" class="me-2" />
          Добавить получателя
        </VCardTitle>
        <VCardText class="px-6 py-2">
          <VTabs v-model="recipientType" density="compact" class="mb-4" color="primary">
            <VTab value="employee">
              <VIcon start icon="mdi-badge-account-horizontal" size="18" />
              Сотрудник iiko
            </VTab>
            <VTab value="user">
              <VIcon start icon="mdi-shield-account" size="18" />
              Пользователь системы
            </VTab>
            <VTab value="customer">
              <VIcon start icon="mdi-account" size="18" />
              Клиент
            </VTab>
          </VTabs>

          <!-- Выбор сотрудника -->
          <template v-if="recipientType === 'employee'">
            <VAutocomplete
              v-model="newAccount.employeeId"
              :items="foundEmployees"
              item-title="name"
              item-value="id"
              label="Поиск и выбор сотрудника iiko"
              variant="outlined"
              class="mb-4"
              :loading="employeeSearchLoading"
              placeholder="Начните вводить имя сотрудника..."
              clearable
              no-data-text="Сотрудники не найдены"
              hint="Данные имени и телефона подтянутся автоматически"
              persistent-hint
              @update:search="onEmployeeSearch"
              @update:model-value="onEmployeeSelected"
            >
              <template #item="{ props, item }">
                <VListItem v-bind="props" :title="item.raw.name" :subtitle="`${item.raw.role || 'Сотрудник'}${item.raw.phone ? ' • ' + item.raw.phone : ''}`">
                  <template #prepend>
                    <VAvatar size="32" color="primary" variant="tonal" class="me-2">
                      <VIcon size="18" :icon="item.raw.is_courier ? 'mdi-moped' : (item.raw.is_admin ? 'mdi-shield-account' : 'mdi-account-tie')" />
                    </VAvatar>
                  </template>
                </VListItem>
              </template>
            </VAutocomplete>
          </template>

          <!-- Выбор пользователя системы -->
          <template v-else-if="recipientType === 'user'">
            <VAutocomplete
              v-model="newAccount.userId"
              :items="foundUsers"
              item-title="name"
              item-value="id"
              label="Поиск пользователя системы (админки)"
              variant="outlined"
              class="mb-4"
              :loading="userSearchLoading"
              placeholder="Начните вводить имя или логин..."
              clearable
              no-data-text="Пользователи не найдены"
              hint="Имя, телефон и привязанные соцсети подтянутся автоматически"
              persistent-hint
              @update:search="onUserSearch"
              @update:model-value="onUserSelected"
            >
              <template #item="{ props, item }">
                <VListItem v-bind="props" :title="item.raw.name" :subtitle="`${item.raw.role || 'Пользователь'}${item.raw.phone ? ' • ' + item.raw.phone : (item.raw.email ? ' • ' + item.raw.email : '')}`">
                  <template #prepend>
                    <VAvatar size="32" color="deep-purple" variant="tonal" class="me-2">
                      <VIcon size="18" icon="mdi-shield-account" />
                    </VAvatar>
                  </template>
                </VListItem>
              </template>
            </VAutocomplete>
          </template>

          <!-- Поиск клиента -->
          <template v-else>
            <VAutocomplete
              v-model="newAccount.customerId"
              :items="foundCustomers"
              item-title="phone"
              item-value="id"
              label="Поиск по телефону или имени клиента"
              variant="outlined"
              class="mb-4"
              :loading="customerSearchLoading"
              placeholder="Начните вводить телефон или имя..."
              clearable
              no-data-text="Клиенты не найдены"
              hint="Данные имени и телефона подтянутся автоматически"
              persistent-hint
              @update:search="onCustomerSearch"
              @update:model-value="onCustomerSelected"
            >
              <template #item="{ props, item }">
                <VListItem v-bind="props" :title="item.raw.name || 'Без имени'" :subtitle="item.raw.phone" />
              </template>
            </VAutocomplete>
          </template>

          <VTextField v-model="newAccount.name" label="Имя отображения" variant="outlined" class="mb-4" hint="Заполнится автоматически при выборе" persistent-hint />
          <VTextField v-model="newAccount.phone" label="Номер телефона" placeholder="+7999..." variant="outlined" class="mb-4" />
          
          <!-- Переключатель роли курьера с проверкой в iiko (п. 1 ТЗ) -->
          <div v-if="recipientType === 'employee'" class="mb-4 pa-3 rounded-lg border bg-grey-lighten-5">
            <VSwitch
              v-model="newAccount.is_courier"
              label="Сотрудник является курьером"
              color="indigo"
              density="compact"
              hide-details
            />
            <div v-if="courierValidationInfo" class="text-caption d-flex align-center ga-1 mt-2" :class="courierValidationInfo.is_courier ? 'text-success' : 'text-warning'">
              <VIcon size="16" :icon="courierValidationInfo.is_courier ? 'mdi-check-decagram' : 'mdi-alert-circle-outline'" />
              <span>{{ courierValidationInfo.is_courier ? `Сотрудник подтвержден как курьер в iiko (${courierValidationInfo.employee_name})` : 'Внимание: сотрудник не найден среди курьеров в iiko' }}</span>
            </div>
          </div>

          <VDivider class="my-4" />
          <div class="text-subtitle-2 mb-2 font-weight-bold">Социальные сети получателя</div>
          
          <VTextField v-model="newAccount.vkLink" label="Ссылка на профиль VK или ID" placeholder="durov или id1" variant="outlined" class="mb-4" hint="Будет найден цифровой ID VK" />
          <VTextField v-model="newAccount.tg_user_id" label="Telegram ID пользователя" placeholder="Напр. 12345678" variant="outlined" class="mb-4" />
          <VTextField 
            v-model="newAccount.max_user_id" 
            label="Телефон для привязки в MAX Messenger" 
            placeholder="+79991234567" 
            variant="outlined" 
            class="mb-4" 
            hint="Если не указан, используется основной номер телефона" 
            persistent-hint 
          />

          <VDivider class="my-4" />
          <div class="text-subtitle-2 mb-2 font-weight-bold">Каналы по умолчанию</div>
          <div class="d-flex flex-wrap gap-2">
            <VSwitch v-model="newAccount.use_vk" label="VK" density="compact" color="#4C75A3" />
            <VSwitch v-model="newAccount.use_tg" label="Telegram" density="compact" color="#0088cc" />
            <VSwitch v-model="newAccount.use_max" label="MAX" density="compact" color="success" />
            <VSwitch v-model="newAccount.use_sms" label="SMS" density="compact" color="primary" />
          </div>

          <!-- Параметры MAX -->
          <div v-if="newAccount.use_max" class="mt-3 pa-3 rounded-lg border bg-grey-lighten-5">
            <div class="text-caption font-weight-bold mb-2 text-purple d-flex align-center">
              <VIcon icon="mdi-message-badge-outline" size="16" class="me-1" />
              Параметры отправки в MAX Messenger
            </div>
            <VSelect
              v-model="newAccount.max_bot_id"
              :items="[
                { id: null, title: 'Основной бот по умолчанию' },
                ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name} (@${b.bot_username || b.id})${b.is_default_for_notifications ? ' ★' : ''}` }))
              ]"
              item-title="title"
              item-value="id"
              label="Предпочитаемый бот MAX"
              variant="outlined"
              density="compact"
              class="mb-2"
              hide-details
            />
            <VSelect
              v-model="newAccount.max_send_mode"
              :items="[
                { id: 'cascade', title: 'Каскад (Сначала бот ➔ Личные сообщения)' },
                { id: 'bot_only', title: 'Только выбранный бот MAX' },
                { id: 'bridge_only', title: 'Только личный аккаунт (по телефону)' }
              ]"
              item-title="title"
              item-value="id"
              label="Режим отправки MAX"
              variant="outlined"
              density="compact"
              hide-details
            />
          </div>

          <VDivider class="my-4" />
          <div class="text-subtitle-2 mb-2 font-weight-bold">Оплата по СБП</div>
          <VSwitch v-model="newAccount.send_payment_qr" label="Отправлять QR на оплату" density="compact" color="primary" />
          <VRadioGroup v-if="newAccount.send_payment_qr" v-model="newAccount.payment_qr_mode" inline class="mt-0">
            <VRadio label="Все заказы" value="all" />
            <VRadio label="Только назначенному курьеру" value="assigned_only" />
          </VRadioGroup>
        </VCardText>
        <VCardActions class="pa-6 bg-grey-lighten-5">
          <VBtn variant="text" @click="addAccountDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="primary" variant="flat" rounded="lg" :loading="addingAccount" @click="addAccount">Добавить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог редактирования получателя -->
    <VDialog v-model="editAccountDialog" max-width="540px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6 font-weight-bold d-flex align-center">
          <VIcon icon="mdi-account-edit-outline" color="primary" class="me-2" />
          Редактирование получателя
        </VCardTitle>
        <VCardText class="px-6 py-2">
          <!-- Привязка сотрудника iiko -->
          <VAutocomplete
            v-model="editingAccount.employee_id"
            :items="foundEmployees"
            item-title="name"
            item-value="id"
            label="Привязанный сотрудник iiko"
            variant="outlined"
            class="mb-4"
            :loading="employeeSearchLoading"
            placeholder="Выберите или начните вводить имя сотрудника..."
            clearable
            no-data-text="Сотрудники не найдены"
            hint="Служит для адресной отправки заказов назначенному курьеру"
            persistent-hint
            @update:search="onEmployeeSearch"
            @update:model-value="onEditEmployeeSelected"
          >
            <template #item="{ props, item }">
              <VListItem v-bind="props" :title="item.raw.name" :subtitle="`${item.raw.role || 'Сотрудник'}${item.raw.phone ? ' • ' + item.raw.phone : ''}`">
                <template #prepend>
                  <VAvatar size="32" color="primary" variant="tonal" class="me-2">
                    <VIcon size="18" :icon="item.raw.is_courier ? 'mdi-moped' : (item.raw.is_admin ? 'mdi-shield-account' : 'mdi-account-tie')" />
                  </VAvatar>
                </template>
              </VListItem>
            </template>
          </VAutocomplete>

          <!-- Привязка пользователя системы (админки) -->
          <VAutocomplete
            v-model="editingAccount.user_id"
            :items="foundUsers"
            item-title="name"
            item-value="id"
            label="Привязанный пользователь админки"
            variant="outlined"
            class="mb-4"
            :loading="userSearchLoading"
            placeholder="Выберите пользователя..."
            clearable
            no-data-text="Пользователи не найдены"
            hint="Служит для авторизации и идентификации системного пользователя"
            persistent-hint
            @update:search="onUserSearch"
          >
            <template #item="{ props, item }">
              <VListItem v-bind="props" :title="item.raw.name" :subtitle="`${item.raw.role || 'Пользователь'}${item.raw.phone ? ' • ' + item.raw.phone : ''}`">
                <template #prepend>
                  <VAvatar size="32" color="deep-purple" variant="tonal" class="me-2">
                    <VIcon size="18" icon="mdi-shield-account" />
                  </VAvatar>
                </template>
              </VListItem>
            </template>
          </VAutocomplete>

          <VTextField v-model="editingAccount.name" label="Имя отображения" variant="outlined" class="mb-4" />
          <VTextField v-model="editingAccount.phone" label="Номер телефона" variant="outlined" class="mb-4" />
          
          <!-- Переключатель роли курьера с проверкой в iiko (п. 1 ТЗ) -->
          <div class="mb-4 pa-3 rounded-lg border bg-grey-lighten-5">
            <VSwitch
              v-model="editingAccount.is_courier"
              label="Сотрудник является курьером"
              color="indigo"
              density="compact"
              hide-details
            />
            <div v-if="courierValidationInfo" class="text-caption d-flex align-center ga-1 mt-2" :class="courierValidationInfo.is_courier ? 'text-success' : 'text-warning'">
              <VIcon size="16" :icon="courierValidationInfo.is_courier ? 'mdi-check-decagram' : 'mdi-alert-circle-outline'" />
              <span>{{ courierValidationInfo.is_courier ? `Сотрудник подтвержден как курьер в iiko (${courierValidationInfo.employee_name})` : 'Внимание: сотрудник не найден среди курьеров в iiko' }}</span>
            </div>
          </div>

          <VDivider class="my-4" />
          <div class="text-subtitle-2 mb-2 font-weight-bold">Социальные сети получателя</div>
          
          <VTextField v-model="editingAccount.vk_user_id" label="Цифровой ID VK" variant="outlined" class="mb-4" />
          <VTextField v-model="editingAccount.tg_user_id" label="Telegram ID пользователя" variant="outlined" class="mb-4" />
          <VTextField 
            v-model="editingAccount.max_user_id" 
            label="Телефон для привязки в MAX Messenger" 
            placeholder="+79991234567" 
            variant="outlined" 
            class="mb-4" 
            hint="Если не указан, используется основной номер телефона" 
            persistent-hint 
          />

          <VDivider class="my-4" />
          <div class="text-subtitle-2 mb-2 font-weight-bold">Каналы по умолчанию</div>
          <div class="d-flex flex-wrap gap-2 mb-4">
            <VSwitch v-model="editingAccount.use_vk" label="VK" density="compact" color="#4C75A3" />
            <VSwitch v-model="editingAccount.use_tg" label="Telegram" density="compact" color="#0088cc" />
            <VSwitch v-model="editingAccount.use_max" label="MAX" density="compact" color="success" />
            <VSwitch v-model="editingAccount.use_sms" label="SMS" density="compact" color="primary" />
          </div>

          <!-- Параметры MAX -->
          <div v-if="editingAccount.use_max" class="mb-4 pa-3 rounded-lg border bg-grey-lighten-5">
            <div class="text-caption font-weight-bold mb-2 text-purple d-flex align-center">
              <VIcon icon="mdi-message-badge-outline" size="16" class="me-1" />
              Параметры отправки в MAX Messenger
            </div>
            <VSelect
              v-model="editingAccount.max_bot_id"
              :items="[
                { id: null, title: 'Основной бот по умолчанию' },
                ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name} (@${b.bot_username || b.id})${b.is_default_for_notifications ? ' ★' : ''}` }))
              ]"
              item-title="title"
              item-value="id"
              label="Предпочитаемый бот MAX"
              variant="outlined"
              density="compact"
              class="mb-2"
              hide-details
            />
            <VSelect
              v-model="editingAccount.max_send_mode"
              :items="[
                { id: 'cascade', title: 'Каскад (Сначала бот ➔ Личные сообщения)' },
                { id: 'bot_only', title: 'Только выбранный бот MAX' },
                { id: 'bridge_only', title: 'Только личный аккаунт (по телефону)' }
              ]"
              item-title="title"
              item-value="id"
              label="Режим отправки MAX"
              variant="outlined"
              density="compact"
              hide-details
            />
          </div>

          <VDivider class="my-4" />
          <div class="text-subtitle-2 mb-2 font-weight-bold">Оплата по СБП</div>
          <VSwitch v-model="editingAccount.send_payment_qr" label="Отправлять QR на оплату" density="compact" color="primary" />
          <VRadioGroup v-if="editingAccount.send_payment_qr" v-model="editingAccount.payment_qr_mode" inline class="mt-0">
            <VRadio label="Все заказы" value="all" />
            <VRadio label="Только назначенному курьеру" value="assigned_only" />
          </VRadioGroup>

          <VDivider class="my-4" />
          <VSwitch v-model="editingAccount.is_active" label="Активен" color="success" />
        </VCardText>
        <VCardActions class="pa-6 bg-grey-lighten-5">
          <VBtn variant="text" @click="editAccountDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="primary" variant="flat" :loading="savingAccount" @click="saveAccount">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог шаблона -->
    <VDialog v-model="templateDialog" max-width="950px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6 font-weight-bold d-flex align-center">
          <VIcon icon="mdi-file-document-edit-outline" color="primary" class="me-3" />
          Редактор шаблона
        </VCardTitle>
        <VDivider />
        <VCardText class="px-6 py-6">
          <VRow>
            <VCol cols="12" md="7">
              <div class="d-flex align-center justify-space-between mb-4 pa-3 rounded-lg bg-grey-lighten-4 border">
                <div>
                  <div class="font-weight-bold text-subtitle-2">Активность шаблона</div>
                  <div class="text-caption text-grey">Включить или выключить автоматическую отправку</div>
                </div>
                <VSwitch v-model="currentTemplate.is_active" color="success" hide-details />
              </div>

              <VTextField v-model="currentTemplate.name" label="Название шаблона" variant="outlined" class="mb-4" />

              <VTextField 
                v-model="currentTemplate.description" 
                label="Пояснение / Описание назначения" 
                variant="outlined" 
                class="mb-4" 
                placeholder="Например: Уведомление курьеру при смене статуса на «Готов к выдаче»" 
              />
              
              <VSelect
                v-model="currentTemplate.event_type"
                :items="[
                  { title: 'Ручная рассылка (без события)', value: null },
                  ...availableEvents.map(e => ({ title: `Автоматическое событие: ${e.name}`, value: e.id }))
                ]"
                label="Связать с системным событием"
                variant="outlined"
                class="mb-4"
              />

              <!-- Мультивыбор целевых статусов заказа для события order_status_update -->
              <VSelect
                v-if="currentTemplate.event_type === 'order_status_update'"
                v-model="selectedTemplateStatuses"
                :items="orderStatusOptions"
                item-title="title"
                item-value="value"
                multiple
                chips
                closable-chips
                label="Отправлять только при переходе в указанные статусы"
                variant="outlined"
                class="mb-4"
                hint="Курьер получит уведомление только при переходе заказа в один из выбранных статусов"
                persistent-hint
              />

              <VSelect
                v-model="currentTemplate.target_mode"
                :items="[
                  { title: '👥 Всем сотрудникам (Массовая рассылка)', value: 'all' },
                  { title: '👔 По ролям сотрудников (Курьеры, Повара, Администраторы...)', value: 'roles' },
                  { title: '👤 Конкретным сотрудникам (Индивидуальный выбор)', value: 'specific' },
                  { title: '🎯 Только назначенному курьеру (Адресная: курьер заказа)', value: 'assigned_only' },
                  { title: '👥🎯 Назначенному курьеру + Администраторам', value: 'assigned_and_admins' },
                ]"
                label="Режим адресации получателей"
                variant="outlined"
                class="mb-4"
                :hint="getTargetModeHint(currentTemplate.target_mode)"
                persistent-hint
              />

              <!-- Мультивыбор ролей сотрудников -->
              <VCombobox
                v-if="currentTemplate.target_mode === 'roles'"
                v-model="currentTemplate.target_roles"
                :items="employeeRoles"
                label="Выберите роли / должности сотрудников"
                multiple
                chips
                closable-chips
                variant="outlined"
                class="mb-4"
                hint="Уведомление получат только сотрудники, имеющие одну из выбранных ролей (можно выбрать или ввести свою)"
                persistent-hint
              />

              <!-- Мультивыбор конкретных сотрудников -->
              <VAutocomplete
                v-if="currentTemplate.target_mode === 'specific'"
                v-model="currentTemplate.target_accounts"
                :items="accounts"
                :item-title="item => `${item.name}${item.phone ? ' (' + item.phone + ')' : ''}`"
                item-value="id"
                label="Выберите конкретных сотрудников-получателей"
                multiple
                chips
                closable-chips
                variant="outlined"
                class="mb-4"
                hint="Уведомление уйдет только персонально выбранным сотрудникам"
                persistent-hint
              />

              <!-- Каналы отправки для этого шаблона -->
              <div class="pa-4 border rounded-lg bg-grey-lighten-5 mb-4">
                <div class="font-weight-bold text-subtitle-2 d-flex align-center mb-1">
                  <VIcon icon="mdi-broadcast" class="me-2 text-primary" />
                  Каналы отправки шаблона
                </div>
                <div class="text-caption text-grey mb-3">
                  В какие каналы связи разрешена отправка данного уведомления
                </div>
                <div class="d-flex flex-wrap gap-4">
                  <VSwitch v-model="currentTemplate.send_vk" label="ВКонтакте (VK)" density="compact" color="#4C75A3" hide-details />
                  <VSwitch v-model="currentTemplate.send_max" label="MAX Messenger" density="compact" color="purple" hide-details />
                  <VSwitch v-model="currentTemplate.send_tg" label="Telegram" density="compact" color="#0088cc" hide-details />
                  <VSwitch v-model="currentTemplate.send_sms" label="SMS" density="compact" color="success" hide-details />
                </div>
              </div>

              <!-- Выбор сообщества / бота ВКонтакте для отправки -->
              <VSelect
                v-model="currentTemplate.vk_bot_id"
                :items="[
                  { id: null, title: 'Основной бот по умолчанию' },
                  ...bots.map(b => ({ id: b.id, title: `${b.name} (${b.vk_group_id})${b.is_main ? ' ★' : ''}` }))
                ]"
                item-title="title"
                item-value="id"
                label="Сообщество / Бот ВКонтакте для отправки"
                variant="outlined"
                class="mb-4"
                hint="Выберите группу, от имени которой получатель получит уведомление в VK"
                persistent-hint
              />

              <!-- Выбор бота MAX Messenger для отправки -->
              <VSelect
                v-model="currentTemplate.max_bot_id"
                :items="[
                  { id: null, title: 'Основной бот MAX по умолчанию' },
                  ...maxBots.map(b => ({ id: b.id, title: `${b.bot_name} (@${b.bot_username || b.id})${b.is_default_for_notifications ? ' ★' : ''}` }))
                ]"
                item-title="title"
                item-value="id"
                label="Бот MAX Messenger для отправки"
                variant="outlined"
                class="mb-4"
                hint="Выберите бота MAX для отправки уведомления"
                persistent-hint
              />

              <!-- Выбор режима отправки MAX -->
              <VSelect
                v-model="currentTemplate.max_send_mode"
                :items="[
                  { id: 'cascade', title: 'Каскад (Сначала бот ➔ если не доставлено, то личный аккаунт)' },
                  { id: 'bot_only', title: 'Только Бот MAX (без отправки от личного аккаунта)' },
                  { id: 'bridge_only', title: 'Только Личный аккаунт (по номеру телефона)' }
                ]"
                item-title="title"
                item-value="id"
                label="Режим отправки MAX"
                variant="outlined"
                class="mb-4"
                hint="Каскадный режим гарантирует доставку: если у пользователя нет диалога с ботом, сообщение будет отправлено через личные сообщения"
                persistent-hint
              />

              <!-- Блок прикрепления фирменного QR-кода оплаты СБП с надписью -->
              <div class="pa-4 border rounded-lg bg-grey-lighten-5 mb-4">
                <div class="d-flex align-center justify-space-between">
                  <div>
                    <div class="font-weight-bold text-subtitle-2 d-flex align-center">
                      <VIcon icon="mdi-qrcode-scan" class="me-2 text-primary" />
                      Прикреплять QR-код СБП с надписью
                    </div>
                    <div class="text-caption text-grey">
                      Генерирует фирменное изображение с суммой, номером заказа и адресом для оплаты по СБП
                    </div>
                  </div>
                  <VSwitch
                    v-model="currentTemplate.attach_sbp_qr"
                    color="primary"
                    hide-details
                  />
                </div>
                <div v-if="currentTemplate.attach_sbp_qr" class="mt-3 d-flex justify-end">
                  <VBtn
                    size="small"
                    variant="tonal"
                    color="primary"
                    prepend-icon="mdi-eye"
                    @click="openPreviewQrDialog(currentTemplate)"
                  >
                    Предпросмотр образца карточки СБП
                  </VBtn>
                </div>

                <!-- Умные опции рассылки курьерам: Редактирование, Кнопки, Сжатие -->
                <div class="d-flex align-center justify-space-between p-3 border rounded mt-3">
                  <div>
                    <div class="font-weight-medium">Режим одного сообщения (редактировать вместо новых)</div>
                    <div class="text-caption text-medium-emphasis">
                      При смене времени готовности или статуса заказа бот обновит уже отправленное сообщение в чате курьера вместо отправки нового
                    </div>
                  </div>
                  <VSwitch
                    v-model="currentTemplate.edit_existing_message"
                    color="primary"
                    hide-details
                  />
                </div>

                <div class="d-flex align-center justify-space-between p-3 border rounded mt-3">
                  <div>
                    <div class="font-weight-medium">Кнопки действий курьера в соцсетях</div>
                    <div class="text-caption text-medium-emphasis">
                      Добавляет курьеру кнопки в VK, MAX и Telegram: «Заказ доставлен», выбор способа оплаты (СБП / Наличные / Терминал) и Навигатор по полному адресу
                    </div>
                  </div>
                  <VSwitch
                    v-model="currentTemplate.show_courier_action_buttons"
                    color="primary"
                    hide-details
                  />
                </div>

                <div class="d-flex align-center justify-space-between p-3 border rounded mt-3">
                  <div>
                    <div class="font-weight-medium">Сжимать сообщение и скрывать QR-код после доставки</div>
                    <div class="text-caption text-medium-emphasis">
                      После закрытия заказа автоматически удаляет картинку QR-кода на оплату, оставляя только данные о доставке, ссылки на навигатор и статус «Заказ доставлен»
                    </div>
                  </div>
                  <VSwitch
                    v-model="currentTemplate.collapse_on_delivered"
                    color="primary"
                    hide-details
                  />
                </div>
              </div>

              <!-- Блок Конструктор логической цепочки проверок -->
              <div class="pa-4 border rounded-lg bg-grey-lighten-5 mb-4">
                <div class="d-flex align-center justify-space-between mb-2">
                  <div class="font-weight-bold text-subtitle-2 d-flex align-center">
                    <VIcon icon="mdi-shield-check-outline" class="me-2 text-primary" />
                    Конструктор логической цепочки проверок перед отправкой
                  </div>
                  <VChip size="x-small" color="primary" variant="tonal">
                    Условия срабатывания
                  </VChip>
                </div>
                <div class="text-caption text-grey mb-3">
                  Настройте логические условия: система проверит каждое условие по цепочке перед отправкой уведомления курьеру.
                </div>

                <div class="d-flex flex-column gap-3">
                  <!-- 1. Назначен курьер -->
                  <div class="d-flex align-center justify-space-between pa-3 rounded bg-white border">
                    <div>
                      <div class="text-body-2 font-weight-bold d-flex align-center">
                        <VIcon icon="mdi-account-check" size="16" class="me-1 text-primary" />
                        Обязательно назначен курьер
                      </div>
                      <div class="text-caption text-grey">Отправлять только если на заказ назначен курьер в iiko или админке</div>
                    </div>
                    <VSwitch v-model="currentChainConfig.require_courier_assigned" color="primary" hide-details density="compact" />
                  </div>

                  <!-- 2. Повтор при переназначении курьера -->
                  <div class="d-flex align-center justify-space-between pa-3 rounded bg-white border">
                    <div>
                      <div class="text-body-2 font-weight-bold d-flex align-center">
                        <VIcon icon="mdi-account-switch" size="16" class="me-1 text-success" />
                        Повторять отправку при переназначении курьера
                      </div>
                      <div class="text-caption text-grey">Если заказ передан другому курьеру, автоматически отправить ему уведомление со всеми данными</div>
                    </div>
                    <VSwitch v-model="currentChainConfig.resend_on_courier_reassigned" color="success" hide-details density="compact" />
                  </div>

                  <!-- 3. Установлено время кухни -->
                  <div class="d-flex align-center justify-space-between pa-3 rounded bg-white border">
                    <div>
                      <div class="text-body-2 font-weight-bold d-flex align-center">
                        <VIcon icon="mdi-clock-check-outline" size="16" class="me-1 text-warning" />
                        Установлено время приготовления кухни
                      </div>
                      <div class="text-caption text-grey">Отправлять только если на кухне задано время готовности (> 0 мин)</div>
                    </div>
                    <VSwitch v-model="currentChainConfig.require_cooking_time_set" color="warning" hide-details density="compact" />
                  </div>

                  <!-- 4. Изменение времени кухни -->
                  <div class="d-flex align-center justify-space-between pa-3 rounded bg-white border">
                    <div>
                      <div class="text-body-2 font-weight-bold d-flex align-center">
                        <VIcon icon="mdi-timer-sync-outline" size="16" class="me-1 text-warning" />
                        Только при повторном изменении времени готовки
                      </div>
                      <div class="text-caption text-grey">Первичная установка времени кухни не отправляется курьеру. Отправка только если время уже было задано и изменилось повторно</div>
                    </div>
                    <VSwitch v-model="currentChainConfig.require_cooking_time_changed" color="warning" hide-details density="compact" />
                  </div>

                  <!-- 5. Изменение суммы заказа -->
                  <div class="d-flex align-center justify-space-between pa-3 rounded bg-white border">
                    <div>
                      <div class="text-body-2 font-weight-bold d-flex align-center">
                        <VIcon icon="mdi-cash-sync" size="16" class="me-1 text-success" />
                        Проверять изменение суммы заказа
                      </div>
                      <div class="text-caption text-grey">Срабатывать при изменении состава, скидок или суммы к оплате</div>
                    </div>
                    <VSwitch v-model="currentChainConfig.require_amount_changed" color="success" hide-details density="compact" />
                  </div>

                  <!-- 6. Изменение адреса доставки -->
                  <div class="d-flex align-center justify-space-between pa-3 rounded bg-white border">
                    <div>
                      <div class="text-body-2 font-weight-bold d-flex align-center">
                        <VIcon icon="mdi-map-marker-distance" size="16" class="me-1 text-purple" />
                        Проверять изменение адреса доставки
                      </div>
                      <div class="text-caption text-grey">Срабатывать при изменении улицы, дома, подъезда, этажа или домофона</div>
                    </div>
                    <VSwitch v-model="currentChainConfig.require_address_changed" color="purple" hide-details density="compact" />
                  </div>

                  <!-- 7. Изменение времени доставки -->
                  <div class="d-flex align-center justify-space-between pa-3 rounded bg-white border">
                    <div>
                      <div class="text-body-2 font-weight-bold d-flex align-center">
                        <VIcon icon="mdi-calendar-clock" size="16" class="me-1 text-cyan" />
                        Проверять изменение времени доставки
                      </div>
                      <div class="text-caption text-grey">Срабатывать при переносе ожидаемого времени прибытия к гостю</div>
                    </div>
                    <VSwitch v-model="currentChainConfig.require_time_changed" color="cyan" hide-details density="compact" />
                  </div>

                  <!-- 8. Только неоплаченные заказы -->
                  <div class="d-flex align-center justify-space-between pa-3 rounded bg-white border">
                    <div>
                      <div class="text-body-2 font-weight-bold d-flex align-center">
                        <VIcon icon="mdi-credit-card-remove-outline" size="16" class="me-1 text-amber-darken-3" />
                        Только для неоплаченных заказов
                      </div>
                      <div class="text-caption text-grey">Не отправлять счет или QR-код, если заказ уже полностью оплачен</div>
                    </div>
                    <VSwitch v-model="currentChainConfig.only_unpaid" color="amber-darken-3" hide-details density="compact" />
                  </div>
                </div>
              </div>

              <VTextarea v-model="currentTemplate.text" label="Текст шаблона" rows="8" variant="outlined" class="mb-4 mt-2" placeholder="Введите текст шаблона..." />
              
              <VDivider class="my-4" />
              
              <div class="d-flex align-center justify-space-between mb-3">
                <h4 class="text-subtitle-1 font-weight-bold d-flex align-center">
                  <VIcon icon="mdi-keyboard-outline" class="me-2" color="primary" />
                  Интерактивные кнопки для соцсетей
                </h4>
                <VChip v-if="currentTemplate.show_courier_action_buttons" color="success" size="small" variant="tonal" prepend-icon="mdi-check-decagram">
                  Смарт-кнопки курьера включены
                </VChip>
              </div>

              <!-- Информационная плашка активных смарт-кнопок курьера -->
              <div v-if="currentTemplate.show_courier_action_buttons" class="pa-4 mb-4 border rounded-lg bg-primary-lighten-5">
                <div class="d-flex align-center justify-space-between mb-2">
                  <div class="font-weight-bold text-subtitle-2 text-primary d-flex align-center">
                    <VIcon icon="mdi-auto-fix" class="me-2" size="20" />
                    Автоматические динамические кнопки для каждого заказа
                  </div>
                  <VChip size="x-small" color="primary" variant="flat">ГЕНЕРИРУЮТСЯ НА ЛЕТУ</VChip>
                </div>
                <div class="text-caption text-medium-emphasis mb-3">
                  Для каждого заказа бэкенд формирует в чатах <b>VK, MAX и Telegram</b> точную ссылку на навигатор по адресу клиента и кнопки отчета о вручении с фиксацией способа оплаты:
                </div>
                <div class="d-flex flex-wrap gap-2 mb-3">
                  <VChip size="small" variant="flat" color="blue-lighten-4" class="text-primary font-weight-medium" prepend-icon="mdi-navigation">
                    🧭 Яндекс.Навигатор (по точному адресу)
                  </VChip>
                  <VChip size="small" variant="flat" color="green-lighten-4" class="text-success font-weight-medium" prepend-icon="mdi-qrcode-scan">
                    📱 Доставлен (СБП QR)
                  </VChip>
                  <VChip size="small" variant="flat" color="teal-lighten-4" class="text-teal font-weight-medium" prepend-icon="mdi-cash">
                    💵 Наличные
                  </VChip>
                  <VChip size="small" variant="flat" color="deep-purple-lighten-4" class="text-deep-purple font-weight-medium" prepend-icon="mdi-credit-card">
                    💳 Терминал (Картой)
                  </VChip>
                  <VChip size="small" variant="flat" color="indigo-lighten-4" class="text-indigo font-weight-medium" prepend-icon="mdi-check-all">
                    ✅ Заказ доставлен (если оплачен онлайн)
                  </VChip>
                </div>
                <div class="text-caption text-grey-darken-1">
                  💡 <b>Поля ниже можно оставить пустыми</b> — эти кнопки прикрепляются автоматически при включенном тумблере «Показывать интерактивные кнопки курьера». Если хотите переопределить кнопки своим кастомным набором, используйте кнопки быстрой вставки или конструктор ниже.
                </div>
              </div>
              
              <VTabs v-model="keyboardTab" class="mb-4" color="primary" density="compact">
                <VTab value="vk"><VIcon icon="mdi-vk" class="me-1" /> ВКонтакте</VTab>
                <VTab value="telegram"><VIcon icon="mdi-telegram" class="me-1" /> Telegram</VTab>
                <VTab value="max"><VIcon icon="mdi-message-text" class="me-1" /> MAX Messenger</VTab>
              </VTabs>
              
              <VWindow v-model="keyboardTab" class="border rounded-lg pa-4 bg-grey-lighten-5">
                <VWindowItem value="vk">
                  <div class="d-flex align-center justify-between mb-2">
                    <span class="text-caption text-grey">Структура клавиатуры VK в формате JSON</span>
                    <VSpacer />
                    <VBtn color="success" size="small" variant="tonal" class="me-2" prepend-icon="mdi-content-paste" @click="insertCourierTemplateButtons('vk')">
                      Вставить кнопки курьера
                    </VBtn>
                    <VBtn color="primary" size="small" variant="tonal" prepend-icon="mdi-gamepad-variant" @click="editKeyboard('vk')">Конструктор VK</VBtn>
                  </div>
                  <VTextarea v-model="currentTemplate.keyboard_json" placeholder="Ничего не настроено (используются авто-кнопки курьера)" rows="3" variant="outlined" hide-details class="bg-white" />
                </VWindowItem>
                <VWindowItem value="telegram">
                  <div class="d-flex align-center justify-between mb-2">
                    <span class="text-caption text-grey">Кнопки inline_keyboard для Telegram</span>
                    <VSpacer />
                    <VBtn color="success" size="small" variant="tonal" class="me-2" prepend-icon="mdi-content-paste" @click="insertCourierTemplateButtons('telegram')">
                      Вставить кнопки курьера
                    </VBtn>
                    <VBtn color="primary" size="small" variant="tonal" prepend-icon="mdi-gamepad-variant" @click="editKeyboard('telegram')">Конструктор TG</VBtn>
                  </div>
                  <VTextarea v-model="currentTemplate.keyboard_telegram" placeholder="Ничего не настроено (используются авто-кнопки курьера)" rows="3" variant="outlined" hide-details class="bg-white" />
                </VWindowItem>
                <VWindowItem value="max">
                  <div class="d-flex align-center justify-between mb-2">
                    <span class="text-caption text-grey">Кнопки для мессенджера MAX</span>
                    <VSpacer />
                    <VBtn color="success" size="small" variant="tonal" class="me-2" prepend-icon="mdi-content-paste" @click="insertCourierTemplateButtons('max')">
                      Вставить кнопки курьера
                    </VBtn>
                    <VBtn color="primary" size="small" variant="tonal" prepend-icon="mdi-gamepad-variant" @click="editKeyboard('max')">Конструктор MAX</VBtn>
                  </div>
                  <VTextarea v-model="currentTemplate.keyboard_max" placeholder="Ничего не настроено (используются авто-кнопки курьера)" rows="3" variant="outlined" hide-details class="bg-white" />
                </VWindowItem>
              </VWindow>
            </VCol>
            
            <VCol cols="12" md="5">
              <div class="sticky-panel-variables">
                <h4 class="text-subtitle-2 font-weight-bold mb-3 d-flex align-center">
                  <VIcon icon="mdi-variable" class="me-1 text-primary" />
                  Доступные шорткоды (кликните для вставки)
                </h4>
                <VExpansionPanels variant="accordion" class="border rounded-lg mb-4">
                  <VExpansionPanel v-for="(vars, category) in variables.variables" :key="category" :title="category">
                    <VExpansionPanelText class="pa-0">
                      <VList density="compact" class="py-0">
                        <VListItem v-for="(desc, code) in vars" :key="code" class="px-2" @click="insertVariable(code, 'template')">
                          <div class="d-flex justify-space-between align-center">
                            <span class="text-caption font-weight-bold text-primary" style="cursor: pointer; font-family: monospace;" v-text="'{{' + code + '}}'"></span>
                            <span class="text-caption text-grey text-right ms-2">{{ desc }}</span>
                          </div>
                        </VListItem>
                      </VList>
                    </VExpansionPanelText>
                  </VExpansionPanel>
                </VExpansionPanels>

                <h4 class="text-subtitle-2 font-weight-bold mb-2 d-flex align-center">
                  <VIcon icon="mdi-robot" class="me-1 text-info" />
                  Команды ВК Бота (в сообщениях гостя)
                </h4>
                <VList density="compact" class="border rounded-lg pa-2 bg-grey-lighten-5" style="max-height: 200px; overflow-y: auto;">
                  <VListItem v-for="cmd in variables.bot_commands" :key="cmd.trigger" class="px-2">
                    <div class="d-flex align-center justify-between">
                      <VChip size="small" color="info" label class="font-weight-bold text-monospace">{{ cmd.trigger }}</VChip>
                      <span class="text-caption text-grey ms-2">{{ cmd.name }}</span>
                    </div>
                  </VListItem>
                  <VListItem v-if="!variables.bot_commands || variables.bot_commands.length === 0" class="text-caption text-grey">Нет активных команд ботов.</VListItem>
                </VList>
              </div>
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6 bg-grey-lighten-5">
          <VBtn variant="text" color="grey" rounded="lg" @click="templateDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="primary" variant="flat" rounded="lg" class="px-6" @click="saveTemplate">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог массового изменения каналов отправки -->
    <VDialog v-model="bulkChannelsDialog" max-width="500px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6 font-weight-bold d-flex align-center">
          <VIcon icon="mdi-broadcast" color="primary" class="me-3" />
          Каналы отправки для {{ selectedTemplateIds.length }} шаблонов
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <div class="text-body-2 text-grey mb-4">
            Выберите, какие каналы связи будут включены для всех отмеченных шаблонов ({{ selectedTemplateIds.length }} шт.):
          </div>
          <div class="d-flex flex-column gap-3 pa-3 rounded-lg border bg-grey-lighten-5">
            <VSwitch v-model="bulkChannelsForm.send_vk" label="ВКонтакте (VK)" color="#4C75A3" hide-details />
            <VSwitch v-model="bulkChannelsForm.send_max" label="MAX Messenger" color="purple" hide-details />
            <VSwitch v-model="bulkChannelsForm.send_tg" label="Telegram" color="#0088cc" hide-details />
            <VSwitch v-model="bulkChannelsForm.send_sms" label="SMS" color="success" hide-details />
          </div>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6 bg-grey-lighten-5">
          <VBtn variant="text" color="grey" rounded="lg" @click="bulkChannelsDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="primary" variant="flat" rounded="lg" class="px-6" @click="applyBulkChannels" :loading="bulkLoading">
            Применить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог массовой смены сообщества / бота ВКонтакте -->
    <VDialog v-model="bulkBotDialog" max-width="500px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6 font-weight-bold d-flex align-center">
          <VIcon icon="mdi-robot" color="secondary" class="me-3" />
          Смена сообщества / бота ВК
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <div class="text-body-2 text-grey mb-4">
            Выберите сообщество ВКонтакте, через которое будут отправляться выбранные шаблоны ({{ selectedTemplateIds.length }} шт.):
          </div>
          <VSelect
            v-model="bulkSelectedBotId"
            :items="[
              { id: null, title: 'Основной бот по умолчанию' },
              ...bots.map(b => ({ id: b.id, title: `${b.name} (${b.vk_group_id})${b.is_main ? ' ★' : ''}` }))
            ]"
            item-title="title"
            item-value="id"
            label="Сообщество / Бот ВКонтакте"
            variant="outlined"
          />
        </VCardText>
        <VDivider />
        <VCardActions class="pa-6 bg-grey-lighten-5">
          <VBtn variant="text" color="grey" rounded="lg" @click="bulkBotDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="secondary" variant="flat" rounded="lg" class="px-6" @click="applyBulkBot" :loading="bulkLoading">
            Применить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог предпросмотра фирменного QR-кода СБП с надписями -->
    <VDialog v-model="previewQrDialog" max-width="560px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6 font-weight-bold d-flex align-center">
          <VIcon icon="mdi-qrcode-scan" color="primary" class="me-3" />
          Фирменный QR-код оплаты СБП с надписью
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-6">
          <p class="text-caption text-grey mb-4">
            Карточка генерируется бэкендом на основе шрифтов Roboto-Bold и содержит номер заказа, сумму к оплате и адрес доставки.
          </p>

          <VRow class="mb-4">
            <VCol cols="12" sm="4">
              <VTextField
                v-model="previewQrData.order_number"
                label="Номер заказа"
                density="compact"
                variant="outlined"
                hide-details
              />
            </VCol>
            <VCol cols="12" sm="4">
              <VTextField
                v-model.number="previewQrData.amount"
                label="Сумма (₽)"
                type="number"
                density="compact"
                variant="outlined"
                hide-details
              />
            </VCol>
            <VCol cols="12" sm="4" class="d-flex align-center">
              <VBtn
                color="primary"
                variant="tonal"
                block
                :loading="previewQrLoading"
                prepend-icon="mdi-refresh"
                @click="generatePreviewQr"
              >
                Обновить
              </VBtn>
            </VCol>
            <VCol cols="12">
              <VTextField
                v-model="previewQrData.delivery_address"
                label="Адрес доставки"
                density="compact"
                variant="outlined"
                hide-details
              />
            </VCol>
          </VRow>

          <div class="d-flex justify-center align-center pa-4 bg-grey-lighten-4 rounded-xl border" style="min-height: 380px;">
            <VProgressCircular v-if="previewQrLoading" indeterminate color="primary" size="48" />
            <div v-else-if="previewQrResultUrl" class="text-center">
              <img
                :src="previewQrResultUrl"
                alt="SBP QR Card"
                class="rounded-lg shadow elevation-3"
                style="max-width: 100%; max-height: 480px; object-fit: contain;"
              />
              <div class="text-caption text-grey mt-2">
                Файл сохранен: <code>{{ previewQrResultUrl }}</code>
              </div>
            </div>
            <div v-else class="text-grey text-caption">Нажмите «Обновить» для формирования карточки</div>
          </div>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4 bg-grey-lighten-5">
          <VSpacer />
          <VBtn color="primary" variant="flat" rounded="lg" @click="previewQrDialog = false">Закрыть</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Визуальный редактор клавиатуры -->
    <VDialog v-model="showKeyboardEditor" max-width="600px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6 font-weight-bold d-flex align-center">
          <VIcon icon="mdi-gamepad-variant" class="me-3" color="primary" />
          Конструктор кнопок: {{ activeKbPlatform.toUpperCase() }}
        </VCardTitle>
        <VDivider />
        <VCardText class="px-6 py-6">
            <div v-for="(row, rIdx) in kbRows" :key="rIdx" class="mb-4 pa-4 border rounded-xl shadow-sm bg-white relative-row">
              <div class="d-flex justify-space-between align-center mb-3">
                <span class="text-subtitle-2 font-weight-bold text-primary">Ряд {{ rIdx + 1 }}</span>
                <VBtn size="x-small" color="error" variant="tonal" class="rounded-lg" @click="kbRows.splice(rIdx, 1)">Удалить ряд</VBtn>
              </div>
              <div class="d-flex flex-wrap gap-3">
                <div v-for="(btn, bIdx) in row" :key="bIdx" class="border pa-3 rounded-lg bg-grey-lighten-4 position-relative card-button-editor">
                  <VTextField v-model="btn.label" label="Текст кнопки" density="compact" hide-details class="mb-2" />
                  <VSelect 
                    v-model="btn.type" 
                    :items="[
                      {title: 'Текст (сообщение)', value: 'text'}, 
                      {title: 'Ссылка (URL)', value: 'open_link'}
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
                    v-else-if="activeKbPlatform === 'vk'"
                    v-model="btn.color" 
                    :items="[
                      {title: 'Синий', value: 'primary'}, 
                      {title: 'Белый', value: 'secondary'}, 
                      {title: 'Зеленый', value: 'positive'}, 
                      {title: 'Красный', value: 'negative'}
                    ]" 
                    label="Цвет кнопки" 
                    density="compact" 
                    hide-details 
                    class="mb-2" 
                  />
                  
                  <VBtn size="x-small" block color="error" variant="tonal" class="mt-2" @click="removeKbButton(rIdx, bIdx)">Удалить кнопку</VBtn>
                </div>
                <VBtn v-if="row.length < 4" variant="dashed" border color="primary" style="height: 146px; width: 70px" class="rounded-lg d-flex align-center justify-center" @click="addKbButton(rIdx)">
                  <VIcon icon="mdi-plus" size="24" />
                </VBtn>
              </div>
            </div>
          <VBtn v-if="kbRows.length < 10" block variant="outlined" color="primary" class="mt-4 rounded-lg py-3" prepend-icon="mdi-plus" @click="addKbRow">Добавить ряд кнопок</VBtn>
          
          <div class="mt-6 text-caption text-grey bg-grey-lighten-4 pa-3 rounded-lg">
            💡 <b>Ограничения платформ:</b>
            <ul class="ps-4 mt-1">
              <li>В одном ряду может быть до 4 кнопок. Всего до 10 рядов.</li>
              <li><b>VK:</b> поддерживает цвета для кнопок-текста.</li>
              <li><b>Telegram:</b> все кнопки отображаются как Inline (под сообщением).</li>
              <li><b>MAX:</b> поддерживает текстовые кнопки и ссылки.</li>
            </ul>
          </div>
        </VCardText>
        <VCardActions class="pa-6 bg-grey-lighten-5">
          <VBtn variant="text" @click="showKeyboardEditor = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="primary" variant="flat" rounded="lg" class="px-6" @click="generateKbJson">Применить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог рассылки -->
    <VDialog v-model="broadcastDialog" max-width="600px">
      <VCard rounded="xl">
        <VCardTitle class="pa-6 font-weight-bold">Глобальная ручная рассылка</VCardTitle>
        <VCardText class="px-6 py-4">
          <VSelect v-model="broadcastData.accountIds" :items="accounts" item-title="name" item-value="id" label="Выберите получателей" multiple chips variant="outlined" class="mb-4" />
          <VSelect v-model="broadcastData.templateId" :items="templates" item-title="name" item-value="id" label="Использовать шаблон (опционально)" variant="outlined" clearable class="mb-4" />
          
          <template v-if="!broadcastData.templateId">
            <VTextarea v-model="broadcastData.text" label="Текст сообщения" variant="outlined" rows="5" class="mb-4" />
            
            <div class="text-subtitle-2 mb-2 font-weight-bold">Вставить переменную:</div>
            <div class="d-flex flex-wrap gap-2">
              <VChip v-for="(vars, category) in variables.variables" :key="category" size="small" class="rounded-lg" @click="insertVariable(Object.keys(vars)[0], 'broadcast')">
                {{ category }}
              </VChip>
            </div>
            <div class="text-caption mt-2 text-grey">Нажмите на категорию, чтобы вставить первую переменную. Для детального редактирования используйте Редактор Шаблонов.</div>
          </template>
        </VCardText>
        <VCardActions class="pa-6 bg-grey-lighten-5">
          <VBtn variant="text" @click="broadcastDialog = false">Отмена</VBtn>
          <VSpacer />
          <VBtn color="secondary" variant="flat" rounded="lg" :loading="sendingBroadcast" @click="sendBroadcast">Отправить рассылку</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <VSnackbar v-model="snackbar" :color="snackbarColor" timeout="3000" rounded="pill">{{ snackbarText }}</VSnackbar>
  </div>
</template>

<style scoped>
.glass-card { background: rgba(255, 255, 255, 0.9) !important; backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2); }
.account-card { transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); border-color: rgba(0,0,0,0.08) !important; }
.account-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.08) !important; border-color: var(--v-primary-base) !important; }
.gap-3 { gap: 12px; }
.gap-2 { gap: 8px; }
.gap-1 { gap: 4px; }
.sticky-panel-variables { position: sticky; top: 20px; }
.relative-card { transition: all 0.3s ease; }
.relative-card:hover { box-shadow: 0 8px 16px rgba(0,0,0,0.05); transform: translateY(-2px); border-color: var(--v-primary-base); }
.animate-vk { transition: transform 0.5s ease; }
.animate-vk:hover { transform: rotate(15deg) scale(1.1); }
.gradient-text { background: linear-gradient(45deg, #3f51b5, #5c6bc0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.card-button-editor { width: 168px; }
.hover-row:hover { background-color: rgba(0,0,0,0.01); }
.text-truncate-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}
.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;  
  overflow: hidden;
}
.cursor-pointer { cursor: pointer; }
.template-row-item {
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  background-color: #ffffff;
}
.template-row-item:hover {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
  border-color: var(--v-primary-base) !important;
}
.template-row-inactive {
  opacity: 0.72;
  background-color: #fbfbfb !important;
}
.tpl-bot-select :deep(.v-field__input) {
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  min-height: 26px !important;
  font-size: 11px !important;
}
.tpl-bot-select :deep(.v-field) {
  font-size: 11px !important;
}
</style>
