<script setup>
import { ref, onMounted, computed, watch } from "vue"
import YandexDeliveryMap from "@/components/YandexDeliveryMap.vue"
import { formatDateTime, appTimezone, appOffset } from "@/utils/date"

// =========================================================================
// Состояние формы
// =========================================================================

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")
const savingResto = ref(false)

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// Настройки iiko
const showPassword = ref(false)
const settings = ref({
  api_login: "",
  organization_id: "",
  external_menu_id: "",
  terminal_group_id: "",
  payment_type_cash: "",
  payment_type_card: "",
  payment_type_online: "",
  payment_type_bonus: "",
  bonus_limit_percent: 0,
  discount_id: "",
  no_pass_promo: false,
  no_use_bonus: false,
  no_use_iiko_promo: false,
  fallback_email: "",
  fallback_telegram_id: "",
  webhook_url: "",
  webhook_auth_token: "",
  resto_url: "",
  resto_login: "",
  resto_password: "",
  price_category_id: "",
  address_format: "components",
  city_name: "",
  manual_timezone: "",
  timezone_name: "",
  
  // Лояльность POS
  pos_loyalty_name: "",
  pos_loyalty_login: "",
  pos_loyalty_password: "",
  pos_loyalty_channel: "",

  // Гео
  delivery_zones_map_url: "",
})

// Справочники (загружаются из iiko)
const organizations = ref([])
const terminalGroups = ref([])
const paymentTypes = ref([])
const externalMenus = ref([])
const discountTypes = ref([])
const priceCategories = ref([])
const deliveryZones = ref([])
const iikoZonesOptions = ref([])

const paymentTypesOptions = computed(() => 
  paymentTypes.value.map(pt => ({
    title: pt.name,
    value: pt.id
  }))
)

const syncingZones = ref(false)
const syncingZonesMap = ref(false)
const syncingPayments = ref(false)
const savingZones = ref(false)
const savingPaymentMapping = ref(false)
const clearingZones = ref(false)

// Статус подключения
const connectionStatus = ref(null) // null, 'success', 'error'
const restoConnectionStatus = ref(null)
const loyaltyConnectionStatus = ref(null)
const testingResto = ref(false)
const testingLoyalty = ref(false)
const loyaltyPrograms = ref([])
const loyaltyCategories = ref([])
const loadingLoyaltyData = ref(false)

const activeTab = ref("general")
const webhookLogs = ref([])
const loadingLogs = ref(false)
const registeringWebhook = ref(false)
const syncingToken = ref(false)
const testingWebhook = ref(false)
const testingApi = ref(false)
const showWebhookToken = ref(false)

const API_BASE = "/api/v1/iiko"

// Настройки Яндекс
const yandexSettings = ref({
  api_key_js: '',
  api_key_suggest: '',
  api_key_matrix: '',
  api_key_monitoring: '',
  api_key_static: '',
  is_active: false
})
const savingYandex = ref(false)

// Мои компании (Отчетность)
const selectedOrgForReport = ref(null)
const reportData = ref(null)
const loadingReport = ref(false)
const reportDateFrom = ref(new Date().toISOString().split('T')[0])
const reportDateTo = ref(new Date().toISOString().split('T')[0])
const topTab = ref('qty')

const fetchOrganizationReport = async () => {
  if (!selectedOrgForReport.value) {
    showMessage("Выберите организацию", "warning")
    return
  }
  loadingReport.value = true
  reportData.value = null
  try {
    const from = `${reportDateFrom.value} 00:00:00.000`
    const to = `${reportDateTo.value} 23:59:59.999`
    const res = await fetch(`${API_BASE}/companies/report?organization_id=${selectedOrgForReport.value}&date_from=${from}&date_to=${to}`)
    const data = await res.json()
    if (res.ok) {
      reportData.value = data
      showMessage("Отчет сформирован")
    } else {
      showMessage(data.detail || "Ошибка при формировании отчета", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при получении отчета", "error")
  } finally {
    loadingReport.value = false
  }
}

// =========================================================================
// Методы
// =========================================================================

// Загрузка настроек Яндекс
const fetchYandexSettings = async () => {
  try {
    const res = await fetch('/api/v1/yandex/settings')
    if (res.ok) {
      yandexSettings.value = await res.json()
    }
  } catch (e) {
    console.error("Error fetching yandex settings:", e)
  }
}

const saveYandexSettings = async () => {
  savingYandex.value = true
  try {
    const res = await fetch('/api/v1/yandex/settings', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(yandexSettings.value),
    })
    if (res.ok) {
      showMessage("Настройки Яндекс.Карт сохранены")
      await fetchYandexSettings()
    } else {
      showMessage("Ошибка сохранения настроек Яндекс", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при сохранении Яндекс", "error")
  } finally {
    savingYandex.value = false
  }
}

const testYandexKey = async (type) => {
  let key = ""
  if (type === "geocoder") key = yandexSettings.value.api_key_js
  
  if (!key) {
    showMessage("Введите ключ для проверки", "warning")
    return
  }
  try {
    const res = await fetch(`/api/v1/yandex/test-key?key_type=${type}&api_key=${key}`, {
      method: "POST"
    })
    const data = await res.json()
    if (res.ok) {
      showMessage(data.message || "Ключ валиден")
    } else {
      showMessage(data.detail || "Ошибка проверки ключа", "error")
    }
  } catch (e) {
    showMessage("Ошибка при проверке ключа", "error")
  }
}

// Загрузка текущих настроек iiko
const loadSettings = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/settings`)
    if (res.ok) {
      const data = await res.json()
      settings.value = { ...settings.value, ...data }

      // Синхронизируем локальное состояние времени
      if (data.timezone_name) {
        appTimezone.value = data.timezone_name
        localStorage.setItem('app_timezone', data.timezone_name)
      }
      if (data.manual_timezone) {
        const offsetMatch = data.manual_timezone.match(/([+-])(\d+)/)
        if (offsetMatch) {
          const sign = offsetMatch[1] === '-' ? -1 : 1
          appOffset.value = sign * parseInt(offsetMatch[2])
          localStorage.setItem('app_offset', appOffset.value.toString())
        }
      }
    }
  } catch (e) {
    showMessage("Ошибка при загрузке настроек", "error")
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings.value),
    })
    if (res.ok) {
      showMessage("Настройки сохранены")
      
      // Обновляем глобальное смещение времени сразу после сохранения
      if (settings.value.timezone_name) {
        appTimezone.value = settings.value.timezone_name
        localStorage.setItem('app_timezone', settings.value.timezone_name)
      }
      if (settings.value.manual_timezone) {
        const offsetMatch = settings.value.manual_timezone.match(/([+-])(\d+)/)
        if (offsetMatch) {
          const sign = offsetMatch[1] === '-' ? -1 : 1
          appOffset.value = sign * parseInt(offsetMatch[2])
          localStorage.setItem('app_offset', appOffset.value.toString())
        }
      }
    } else {
      showMessage("Ошибка при сохранении", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    saving.value = false
  }
}

// Тест iiko Cloud API
const testConnection = async () => {
  testing.value = true
  connectionStatus.value = null
  try {
    const res = await fetch(`${API_BASE}/test-connection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings.value),
    })
    const data = await res.json()
    if (res.ok && data.success) {
      connectionStatus.value = "success"
      showMessage("Успешное подключение к iiko Cloud!")
    } else {
      connectionStatus.value = "error"
      showMessage(data.error || "Ошибка подключения", "error")
    }
  } catch (e) {
    connectionStatus.value = "error"
    showMessage("Не удалось подключиться к API iiko", "error")
  } finally {
    testing.value = false
  }
}

// Тест iiko Resto API (через backoffice)
const testRestoConnection = async () => {
  testingResto.value = true
  restoConnectionStatus.value = null
  try {
    const res = await fetch(`${API_BASE}/test-resto-connection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings.value),
    })
    const data = await res.json()
    if (res.ok && data.success) {
      restoConnectionStatus.value = "success"
      showMessage("Успешное подключение к iiko Resto!")
    } else {
      restoConnectionStatus.value = "error"
      showMessage(data.error || "Ошибка подключения к Resto", "error")
    }
  } catch (e) {
    restoConnectionStatus.value = "error"
    showMessage("Ошибка соединения с iiko Resto", "error")
  } finally {
    restoConnectionStatus.value = false
  }
}

const saveRestoSettings = async () => {
  savingResto.value = true
  try {
    const payload = {
      resto_url: settings.value.resto_url,
      resto_login: settings.value.resto_login,
      resto_password: settings.value.resto_password
    }
    const res = await fetch(`${API_BASE}/settings/resto`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    const data = await res.json()
    if (res.ok) {
      showMessage("Настройки iiko Server (Resto) успешно сохранены")
      await loadSettings()
    } else {
      showMessage(data.detail || "Ошибка при сохранении настроек Resto", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при сохранении настроек Resto", "error")
  } finally {
    savingResto.value = false
  }
}

// Тест iiko Loyalty API
const testLoyaltyConnection = async () => {
  testingLoyalty.value = true
  loyaltyConnectionStatus.value = null
  try {
    const res = await fetch(`${API_BASE}/test-loyalty-connection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings.value),
    })
    const data = await res.json()
    if (res.ok && data.success) {
      loyaltyConnectionStatus.value = "success"
      showMessage(data.message || "Успешное подключение к iiko Loyalty!")
    } else {
      loyaltyConnectionStatus.value = "error"
      showMessage(data.error || data.detail || "Ошибка подключения", "error")
    }
  } catch (e) {
    loyaltyConnectionStatus.value = "error"
    showMessage("Не удалось подключиться к API iiko Loyalty", "error")
  } finally {
    testingLoyalty.value = false
  }
}

// Загрузка данных для импорта по лояльности
const fetchLoyaltyData = async () => {
  loadingLoyaltyData.value = true
  try {
    const res = await fetch(`${API_BASE}/loyalty/importable-data`)
    const data = await res.json()
    if (res.ok && data.success) {
      loyaltyPrograms.value = data.programs
      loyaltyCategories.value = data.categories
      showMessage("Данные лояльности успешно загружены")
    } else {
      showMessage(data.detail || "Ошибка при получении данных лояльности", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    loadingLoyaltyData.value = false
  }
}

// Загрузка справочников
const loadOrganizations = async () => {
  try {
    const res = await fetch(`${API_BASE}/organizations`)
    if (res.ok) {
      organizations.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  }
}

const loadTerminalGroups = async () => {
  try {
    const res = await fetch(`${API_BASE}/terminal-groups`)
    if (res.ok) {
      terminalGroups.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  }
}

const loadPaymentTypes = async () => {
  try {
    const res = await fetch(`${API_BASE}/payment-types`)
    if (res.ok) {
      paymentTypes.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  }
}

const loadExternalMenus = async () => {
  try {
    const res = await fetch(`${API_BASE}/external-menus`)
    if (res.ok) {
      externalMenus.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  }
}

const loadDiscountTypes = async () => {
  try {
    const res = await fetch(`${API_BASE}/discount-types`)
    if (res.ok) {
      const data = await res.json()
      discountTypes.value = data.map((d) => ({
        title: d.name || d.id,
        value: d.id,
      }))
    }
  } catch (e) {
    console.error(e)
  }
}

const loadPriceCategories = async () => {
  try {
    const res = await fetch(`${API_BASE}/price-categories`)
    if (res.ok) {
      const data = await res.json()
      priceCategories.value = data.map((pc) => ({
        title: pc.name || pc.id,
        value: pc.id,
      }))
    }
  } catch (e) {
    console.error(e)
  }
}

const loadDeliveryZones = async () => {
  try {
    const res = await fetch(`${API_BASE}/delivery-zones`)
    if (res.ok) {
      deliveryZones.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  }
}

const fetchIikoZonesOptions = async () => {
  try {
    const res = await fetch(`${API_BASE}/iiko-zones-list`)
    if (res.ok) {
      iikoZonesOptions.value = await res.json()
    }
  } catch (e) {
    console.error("Error fetching iiko zones list:", e)
  }
}

const loadAllReferences = async () => {
  await Promise.all([
    loadOrganizations(),
    loadTerminalGroups(),
    loadPaymentTypes(),
    loadExternalMenus(),
    loadDiscountTypes(),
    loadPriceCategories(),
    loadDeliveryZones(),
    fetchIikoZonesOptions(),
  ])
}

// Синхронизация данных
const syncPaymentTypes = async () => {
  syncingPayments.value = true
  try {
    const res = await fetch(`${API_BASE}/sync-payment-types`, { method: "POST" })
    const data = await res.json()
    if (res.ok && !data.error) {
      showMessage(`Типы оплаты синхронизированы (обработано: ${data.synced_count})`)
      await loadPaymentTypes()
    } else {
      showMessage(data.error || "Ошибка синхронизации оплат", "error")
    }
  } catch (e) {
    showMessage("Ошибка соединения", "error")
  } finally {
    syncingPayments.value = false
  }
}

const savePaymentMapping = async () => {
  savingPaymentMapping.value = true
  try {
    const res = await fetch(`${API_BASE}/save-payment-types-mapping`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(paymentTypes.value),
    })
    if (res.ok) {
      showMessage("Сопоставление оплат сохранено")
      await saveSettings() 
    } else {
      showMessage("Ошибка сохранения сопоставления", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    savingPaymentMapping.value = false
  }
}

const syncDeliveryZones = async () => {
  syncingZones.value = true
  try {
    const res = await fetch(`${API_BASE}/sync-delivery-zones`, { method: "POST" })
    const data = await res.json()
    if (res.ok && !data.error) {
      showMessage(`Зоны доставки синхронизированы (зон: ${data.synced_zones}, полигонов: ${data.polygons_found})`)
      await loadDeliveryZones()
    } else {
      showMessage(data.error || "Ошибка синхронизации зон", "error")
    }
  } catch (e) {
    showMessage("Ошибка соединения", "error")
  } finally {
    syncingZones.value = false
  }
}

const syncZonesFromMap = async () => {
  if (!settings.value.delivery_zones_map_url) {
    showMessage("Укажите ссылку на карту", "warning")
    return
  }
  syncingZonesMap.value = true
  try {
    const res = await fetch(`${API_BASE}/sync-zones-from-map`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: settings.value.delivery_zones_map_url })
    })
    const data = await res.json()
    if (res.ok && !data.error) {
      showMessage(`Геометрия зон обновлена (обновлено: ${data.updated_count})`)
      await loadDeliveryZones()
    } else {
      showMessage(data.error || "Ошибка синхронизации геометрии", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при импорте из карт", "error")
  } finally {
    syncingZonesMap.value = false
  }
}

const saveDeliveryZones = async () => {
  savingZones.value = true
  try {
    const res = await fetch(`${API_BASE}/save-delivery-zones`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(deliveryZones.value),
    })
    const data = await res.json()
    if (res.ok) {
      showMessage("Параметры зон доставки сохранены")
      await loadDeliveryZones()
    } else {
      showMessage(data.detail || data.error || "Ошибка сохранения зон", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при сохранении зон", "error")
  } finally {
    savingZones.value = false
  }
}

const uploadingKml = ref(false)

const registerWebhook = async () => {
  registeringWebhook.value = true
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 60000) // 60s timeout

  try {
    const res = await fetch(`${API_BASE}/webhooks/register`, { 
      method: "POST",
      signal: controller.signal
    })
    const data = await res.json()
    if (res.ok && data.success) {
      showMessage("Вебхук успешно зарегистрирован в iiko Cloud")
      if (data.webhook_url) settings.value.webhook_url = data.webhook_url
      if (data.auth_token) settings.value.webhook_auth_token = data.auth_token
    } else {
      showMessage(data.error || "Ошибка регистрации вебхука", "error")
    }
  } catch (e) {
    if (e.name === 'AbortError') {
      showMessage("Таймаут запроса. Проверьте соединение с iiko Cloud API на сервере.", "error")
    } else {
      showMessage("Ошибка сети или сервера", "error")
    }
    console.error(e)
  } finally {
    clearTimeout(timeoutId)
    registeringWebhook.value = false
  }
}

const syncWebhookToken = async () => {
  syncingToken.value = true
  try {
    const res = await fetch(`${API_BASE}/webhooks/sync-token`, { method: "POST" })
    const data = await res.json()
    if (res.ok && data.success) {
      showMessage("Токен успешно синхронизирован из iiko Cloud")
      if (data.webhook_url) settings.value.webhook_url = data.webhook_url
      if (data.auth_token) settings.value.webhook_auth_token = data.auth_token
      // Сбрасываем результат теста после исправления
      webhookTestResult.value = null
    } else {
      showMessage(data.detail || data.error || "Ошибка синхронизации токена", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети или сервера", "error")
    console.error(e)
  } finally {
    syncingToken.value = false
  }
}

const testWebhook = async () => {
  testingWebhook.value = true
  try {
    const res = await fetch(`${API_BASE}/webhooks/test`, { method: "POST" })
    const data = await res.json()
    if (res.ok) {
      if (data.success) {
        showMessage("РўРµСЃС‚ РІРµР±С…СѓРєР° РїСЂРѕР№РґРµРЅ: РЅР°СЃС‚СЂРѕР№РєРё РІ iiko Cloud Рё Р‘Р” СЃРѕРІРїР°РґР°СЋС‚")
      } else {
        let msg = "Р Р°СЃСЃРёРЅС…СЂРѕРЅРёР·Р°С†РёСЏ: "
        if (!data.url_match) msg += "URL РЅРµ СЃРѕРІРїР°РґР°РµС‚. "
        if (!data.token_match) msg += "РўРѕРєРµРЅ РЅРµ СЃРѕРІРїР°РґР°РµС‚. "
        showMessage(msg, "warning")
      }
    } else {
      showMessage(data.detail || data.error || "РћС€РёР±РєР° РїСЂРё С‚РµСЃС‚РёСЂРѕРІР°РЅРёРё", "error")
    }
  } catch (e) {
    showMessage("РћС€РёР±РєР° СЃРµС‚Рё РїСЂРё С‚РµСЃС‚РёСЂРѕРІР°РЅРёРё РІРµР±С…СѓРєР°", "error")
  } finally {
    testingWebhook.value = false
  }
}

const testIikoApi = async () => {
  testingApi.value = true
  try {
    const res = await fetch(`${API_BASE}/test-connection`, { method: "POST" })
    const data = await res.json()
    if (res.ok && data.success) {
      showMessage(data.message || "Соединение с iiko Cloud API успешно")
    } else {
      showMessage(data.error || "Ошибка соединения с API", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при проверке API", "error")
  } finally {
    testingApi.value = false
  }
}

const uploadKmlFile = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const formData = new FormData()
  formData.append("file", file)
  
  uploadingKml.value = true
  try {
    const res = await fetch(`${API_BASE}/upload-kml`, {
      method: "POST",
      body: formData
    })
    const data = await res.json()
    if (res.ok) {
      showMessage(data.message || "Зоны успешно обновлены из файла")
      await loadDeliveryZones()
    } else {
      showMessage(data.detail || data.error || "Ошибка обработки KML файла", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети при загрузке файла", "error")
  } finally {
    uploadingKml.value = false
    if (kmlFileInput.value) kmlFileInput.value.value = ""
  }
}

const loadWebhookLogs = async () => {
  loadingLogs.value = true
  try {
    const res = await fetch(`${API_BASE}/webhooks/logs`)
    if (res.ok) {
      webhookLogs.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  } finally {
    loadingLogs.value = false
  }
}

const clearDeliveryZones = async () => {
  if (!confirm("Вы уверены, что хотите удалить ВСЕ зоны доставки? Это действие нельзя отменить.")) return
  
  clearingZones.value = true
  try {
    const res = await fetch(`${API_BASE}/clear-delivery-zones`, {
      method: "POST"
    })
    const data = await res.json()
    if (res.ok) {
      showMessage("Зоны доставки успешно очищены")
      deliveryZones.value = []
    } else {
      showMessage(data.detail || "Ошибка при очистке зон", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    clearingZones.value = false
  }
}

// Часовые пояса
const timezoneOptions = [
  { title: "Калининград (UTC+2)", value: "Europe/Kaliningrad" },
  { title: "Москва, С-Петербург (UTC+3)", value: "Europe/Moscow" },
  { title: "Самара, Ижевск (UTC+4)", value: "Europe/Samara" },
  { title: "Екатеринбург, Тюмень (UTC+5)", value: "Asia/Yekaterinburg" },
  { title: "Омск (UTC+6)", value: "Asia/Omsk" },
  { title: "Новосибирск, Томск (UTC+7)", value: "Asia/Novosibirsk" },
  { title: "Красноярск (UTC+7)", value: "Asia/Krasnoyarsk" },
  { title: "Иркутск (UTC+8)", value: "Asia/Irkutsk" },
  { title: "Якутск (UTC+9)", value: "Asia/Yakutsk" },
  { title: "Владивосток (UTC+10)", value: "Asia/Vladivostok" },
  { title: "Магадан, Сахалин (UTC+11)", value: "Asia/Magadan" },
  { title: "Камчатка, Чукотка (UTC+12)", value: "Asia/Kamchatka" },
]

const updateTimezoneOffset = (tzName) => {
  if (!tzName) return
  try {
    const date = new Date()
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: tzName,
      timeZoneName: 'longOffset'
    })
    const parts = formatter.formatToParts(date)
    const tzPart = parts.find(p => p.type === 'timeZoneName')
    if (tzPart) {
      const offset = tzPart.value === 'GMT' ? '+00:00' : tzPart.value.replace('GMT', '')
      settings.value.manual_timezone = offset
    }
  } catch (e) {
    console.error("Error calculating offset:", e)
  }
}

onMounted(async () => {
  await loadSettings()
  await fetchYandexSettings()
  if (settings.value.api_login) {
    loadAllReferences()
  }
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VTabs v-model="activeTab" class="mb-4">
        <VTab value="general">Основные настройки</VTab>
        <VTab value="payment">Оплата</VTab>
        <VTab value="zones">Зоны доставки</VTab>
        <VTab value="companies">Мои компании</VTab>
        <VTab value="loyalty">Лояльность (POS)</VTab>
        <VTab value="management">Управление</VTab>
        <VTab value="webhooks">Вебхуки</VTab>
        <VTab value="yandex">Яндекс Карты</VTab>
      </VTabs>

      <VWindow v-model="activeTab" class="mt-4">
        <!-- ==================== Вкладка Общие ==================== -->
        <VWindowItem value="general">
          <VCard title="Параметры iiko Cloud API" class="mb-6">
            <VCardText>
              <VRow>
                <VCol cols="12">
                  <VTextField
                    v-model="settings.api_login"
                    label="API Login"
                    :type="showPassword ? 'text' : 'password'"
                    :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="showPassword = !showPassword"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect
                    v-model="settings.organization_id"
                    :items="organizations"
                    item-title="name"
                    item-value="id"
                    label="Организация"
                    @update:model-value="loadAllReferences"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect
                    v-model="settings.external_menu_id"
                    :items="externalMenus"
                    item-title="name"
                    item-value="id"
                    label="Внешнее меню"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect
                    v-model="settings.terminal_group_id"
                    :items="terminalGroups"
                    item-title="name"
                    item-value="id"
                    label="Группа терминалов"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect
                    v-model="settings.price_category_id"
                    :items="priceCategories"
                    label="Категория цен"
                    hint="Используется для фильтрации цен в меню"
                    persistent-hint
                  />
                </VCol>
              </VRow>

              <div class="d-flex gap-4 mt-6">
                <VBtn
                  color="primary"
                  :loading="saving"
                  prepend-icon="mdi-content-save"
                  @click="saveSettings"
                >
                  Сохранить настройки
                </VBtn>
                <VBtn
                  variant="outlined"
                  :color="connectionStatus === 'success' ? 'success' : connectionStatus === 'error' ? 'error' : 'secondary'"
                  :loading="testing"
                  prepend-icon="mdi-api"
                  @click="testConnection"
                >
                  Проверить Cloud API
                </VBtn>
              </div>
            </VCardText>
          </VCard>

          <VCard title="Параметры iiko Resto (Backoffice)">
            <VCardText>
              <VRow>
                <VCol cols="12">
                  <VTextField
                    v-model="settings.resto_url"
                    label="URL iiko Resto"
                    placeholder="https://your-server.iiko.it:443"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField v-model="settings.resto_login" label="Логин Resto" />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField
                    v-model="settings.resto_password"
                    label="Пароль Resto"
                    type="password"
                  />
                </VCol>
              </VRow>
              <div class="d-flex gap-4 mt-6">
                <VBtn
                  color="success"
                  :loading="savingResto"
                  prepend-icon="mdi-content-save"
                  @click="saveRestoSettings"
                >
                  Сохранить параметры Resto
                </VBtn>
                <VBtn
                  variant="outlined"
                  :color="restoConnectionStatus === 'success' ? 'success' : restoConnectionStatus === 'error' ? 'error' : 'secondary'"
                  :loading="testingResto"
                  prepend-icon="mdi-server"
                  @click="testRestoConnection"
                >
                  Проверить связь с Resto
                </VBtn>
              </div>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- ==================== Вкладка Оплата ==================== -->
        <VWindowItem value="payment">
          <VCard class="mb-6">
            <VCardTitle>Основные типы оплат</VCardTitle>
            <VCardText>
              <VRow>
                <VCol cols="12" md="6">
                  <VSelect v-model="settings.payment_type_cash" :items="paymentTypesOptions" label="Наличные" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect v-model="settings.payment_type_card" :items="paymentTypesOptions" label="Карта курьеру" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect v-model="settings.payment_type_online" :items="paymentTypesOptions" label="Онлайн оплата" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect v-model="settings.payment_type_bonus" :items="paymentTypesOptions" label="Оплата баллами" />
                </VCol>
              </VRow>
            </VCardText>
          </VCard>

          <VCard>
            <VCardTitle class="d-flex align-center">
              Привязка оплат (Mapping)
              <VSpacer />
              <VBtn 
                size="small" 
                variant="outlined" 
                color="warning" 
                class="me-2"
                :loading="syncingPayments"
                prepend-icon="mdi-sync"
                @click="syncPaymentTypes"
              >
                Обновить список из iiko
              </VBtn>
              <VBtn
                color="success"
                size="small"
                :loading="savingPaymentMapping"
                prepend-icon="mdi-content-save"
                @click="savePaymentMapping"
              >
                Сохранить сопоставление
              </VBtn>
            </VCardTitle>
            <VCardText>
              <VAlert type="info" variant="tonal" class="mb-4">
                Сопоставьте способы оплаты на сайте с типами оплат в iiko.
              </VAlert>
              <VTable density="compact">
                <thead>
                  <tr>
                    <th>Название iiko</th>
                    <th>Тип (Kind)</th>
                    <th>Внутренний тип (Mapping)</th>
                    <th>Внешняя обработка</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="pt in paymentTypes" :key="pt.id">
                    <td>{{ pt.name }}</td>
                    <td><VChip size="x-small">{{ pt.paymentTypeKind || '-' }}</VChip></td>
                    <td>
                      <VSelect
                        v-model="pt.mapping_type"
                        :items="[
                          {title: 'Наличные', value: 'cash'},
                          {title: 'Карта курьеру', value: 'card_courier'},
                          {title: 'Онлайн', value: 'online'},
                          {title: 'Бонусы', value: 'bonus'},
                          {title: 'Прочее', value: 'other'}
                        ]"
                        density="compact"
                        hide-details
                        style="width: 200px"
                      />
                    </td>
                    <td>
                      <VSwitch v-model="pt.is_processed_externally" hide-details density="compact" />
                    </td>
                  </tr>
                </tbody>
              </VTable>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- ==================== Вкладка Зоны доставки ==================== -->
        <VWindowItem value="zones">
          <VCard>
            <VCardTitle class="d-flex align-center">
              Зоны доставки (iiko)
              <VSpacer />
              <VBtn 
                size="small" 
                color="primary" 
                :loading="syncingZones"
                prepend-icon="mdi-refresh"
                @click="syncDeliveryZones"
              >
                Синхронизировать
              </VBtn>
            </VCardTitle>
            <VCardText>
              <!-- Визуализация (только если есть ключи Яндекса) -->
              <div v-if="yandexSettings.is_active" class="mb-6" style="height: 400px; border-radius: 8px; overflow: hidden; border: 1px solid #ddd;">
                <YandexDeliveryMap :zones="deliveryZones" :apiKey="yandexSettings.api_key_js" />
              </div>

              <VRow class="mb-4">
                <VCol cols="12" md="8">
                  <VTextField
                    v-model="settings.delivery_zones_map_url"
                    label="URL карты (Google My Maps KML)"
                    hint="Ссылка на карту для импорта геометрии зон"
                    persistent-hint
                  />
                </VCol>
                <VCol cols="12" md="4" class="d-flex align-center">
                  <VBtn color="secondary" variant="outlined" block :loading="syncingZonesMap" @click="syncZonesFromMap">
                    Импорт по ссылке
                  </VBtn>
                </VCol>
              </VRow>

              <div class="mb-4 d-flex align-center gap-2">
                  <VBtn
                    color="primary"
                    size="small"
                    :loading="uploadingKml"
                    prepend-icon="mdi-file-upload"
                    @click="$refs.kmlFileInput.click()"
                  >
                    Загрузить KML файл
                  </VBtn>
                  <VBtn color="error" :loading="clearingZones" @click="clearDeliveryZones" class="mr-2">
                    Очистить зоны
                  </VBtn>
                  <VBtn color="info" size="small" :loading="syncingZones" @click="syncDeliveryZones">
                    Синхронизировать с iiko Web
                  </VBtn>
                  <input
                    ref="kmlFileInput"
                    type="file"
                    accept=".kml"
                    class="d-none"
                    @change="uploadKmlFile"
                  >
                  <VSpacer />
                  <span class="text-caption text-grey">Имена фигур должны совпадать с зонами iiko</span>
              </div>

              <VTable density="compact">
                <thead>
                  <tr>
                    <th>Зона (на сайте)</th>
                    <th>Привязка к iiko</th>
                    <th>Мин. заказ</th>
                    <th>Доставка</th>
                    <th>Бесплатно от</th>
                    <th>Время (мин)</th>
                    <th>Статус</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="zone in deliveryZones" :key="zone.id">
                    <td>
                        <VTextField v-model="zone.name" density="compact" hide-details class="mb-1" />
                        <div class="d-flex align-center mt-1">
                            <VIcon 
                                :icon="zone.polygon_coordinates && zone.polygon_coordinates !== '[]' ? 'mdi-map-marker-check' : 'mdi-map-marker-alert'" 
                                :color="zone.polygon_coordinates && zone.polygon_coordinates !== '[]' ? 'success' : 'warning'"
                                size="x-small"
                                class="me-1"
                            />
                            <span class="text-caption" :class="zone.polygon_coordinates && zone.polygon_coordinates !== '[]' ? 'text-success' : 'text-warning'">
                                {{ zone.polygon_coordinates && zone.polygon_coordinates !== '[]' ? 'Геометрия ок' : 'Нет полигона' }}
                            </span>
                        </div>
                    </td>
                    <td>
                      <VSelect
                        v-model="zone.iiko_id"
                        :items="iikoZonesOptions"
                        item-title="name"
                        item-value="iiko_id"
                        placeholder="Не привязана"
                        density="compact"
                        hide-details
                        clearable
                        style="min-width: 150px"
                      />
                    </td>
                    <td>
                      <VTextField v-model="zone.min_order_amount" density="compact" hide-details type="number" style="width: 80px" />
                    </td>
                    <td>
                      <VTextField v-model="zone.delivery_cost" density="compact" hide-details type="number" style="width: 80px" />
                    </td>
                    <td>
                      <VTextField v-model="zone.free_delivery_sum" density="compact" hide-details type="number" style="width: 80px" />
                    </td>
                    <td class="d-flex align-center pt-2">
                      <VTextField v-model="zone.min_delivery_time" density="compact" hide-details type="number" style="width: 50px" class="me-1" />
                      -
                      <VTextField v-model="zone.max_delivery_time" density="compact" hide-details type="number" style="width: 50px" class="ms-1" />
                    </td>
                    <td>
                      <VSwitch v-model="zone.is_active" density="compact" hide-details color="success" />
                    </td>
                  </tr>
                </tbody>
              </VTable>
              <div class="mt-4 d-flex justify-end">
                <VBtn color="success" :loading="savingZones" @click="saveDeliveryZones">
                  Сохранить параметры зон
                </VBtn>
              </div>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- ==================== Вкладка Лояльность ==================== -->
        <!-- ==================== Вкладка Мои компании ==================== -->
        <VWindowItem value="companies">
          <VCard class="mb-6">
            <VCardTitle>Панель управления организацией</VCardTitle>
            <VCardText>
              <VRow align="center">
                <VCol cols="12" md="4">
                  <VSelect
                    v-model="selectedOrgForReport"
                    :items="organizations"
                    item-title="name"
                    item-value="id"
                    label="Выберите организацию"
                    density="compact"
                    hide-details
                  />
                </VCol>
                <VCol cols="12" md="3">
                  <VTextField
                    v-model="reportDateFrom"
                    type="date"
                    label="От"
                    density="compact"
                    hide-details
                  />
                </VCol>
                <VCol cols="12" md="3">
                  <VTextField
                    v-model="reportDateTo"
                    type="date"
                    label="До"
                    density="compact"
                    hide-details
                  />
                </VCol>
                <VCol cols="12" md="2">
                  <VBtn 
                    block 
                    color="primary" 
                    :loading="loadingReport"
                    @click="fetchOrganizationReport"
                  >
                    Сформировать
                  </VBtn>
                </VCol>
              </VRow>
            </VCardText>
          </VCard>

          <template v-if="reportData">
            <!-- KPI Карточки -->
            <VRow class="mb-6">
              <VCol cols="12" md="3">
                <VCard color="primary" theme="dark">
                  <VCardText class="text-center">
                    <div class="text-h4 font-weight-bold">{{ reportData.kpi.ordersTotal }}</div>
                    <div class="text-caption">Всего заказов</div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol cols="12" md="3">
                <VCard color="success" theme="dark">
                  <VCardText class="text-center">
                    <div class="text-h4 font-weight-bold">{{ reportData.kpi.kitchenAvgMin }} мин</div>
                    <div class="text-caption">Средняя кухня</div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol cols="12" md="3">
                <VCard color="info" theme="dark">
                  <VCardText class="text-center">
                    <div class="text-h4 font-weight-bold">{{ reportData.kpi.travelAvgMin }} мин</div>
                    <div class="text-caption">Средняя доставка</div>
                  </VCardText>
                </VCard>
              </VCol>
              <VCol cols="12" md="3">
                <VCard color="warning" theme="dark">
                  <VCardText class="text-center">
                    <div class="text-h4 font-weight-bold">{{ reportData.kpi.couriersTotal }}</div>
                    <div class="text-caption">Курьеров в штате</div>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>

            <VRow>
              <!-- Терминалы -->
              <VCol cols="12" md="6">
                <VCard title="Статус терминалов" class="fill-height">
                  <VTable density="compact">
                    <thead>
                      <tr>
                        <th>Название</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="t in reportData.terminals.groups.terminalGroups" :key="t.id">
                        <td>{{ t.items[0]?.name || 'Группа '+t.id.slice(0,8) }}</td>
                        <td>
                          <VChip 
                            :color="reportData.terminals.status.isAliveStatus.find(s => s.terminalGroupId === t.id)?.isAlive ? 'success' : 'error'" 
                            size="x-small"
                          >
                            {{ reportData.terminals.status.isAliveStatus.find(s => s.terminalGroupId === t.id)?.isAlive ? 'В сети' : 'Оффлайн' }}
                          </VChip>
                        </td>
                      </tr>
                    </tbody>
                  </VTable>
                </VCard>
              </VCol>

              <!-- Топ товаров -->
              <VCol cols="12" md="6">
                <VCard title="Популярные товары" class="fill-height">
                  <VTabs density="compact">
                    <VTab @click="topTab = 'qty'">По количеству</VTab>
                    <VTab @click="topTab = 'sum'">По сумме</VTab>
                  </VTabs>
                  <VCardText>
                    <VList density="compact">
                      <VListItem 
                        v-for="item in (topTab === 'sum' ? reportData.analytics.topItems.bySum : reportData.analytics.topItems.byQty)" 
                        :key="item.name"
                      >
                        <template #prepend>
                          <VIcon icon="mdi-food" size="small" />
                        </template>
                        <VListItemTitle>{{ item.name }}</VListItemTitle>
                        <template #append>
                          <span class="font-weight-bold">{{ topTab === 'sum' ? item.value + ' ₽' : item.value + ' шт.' }}</span>
                        </template>
                      </VListItem>
                    </VList>
                  </VCardText>
                </VCard>
              </VCol>

              <!-- Последние заказы -->
              <VCol cols="12">
                <VCard title="Последние заказы">
                  <VTable density="compact">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Клиент</th>
                        <th>Статус</th>
                        <th>Сумма</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="order in reportData.analytics.ordersShort" :key="order.id">
                        <td>{{ order.number }}</td>
                        <td>{{ order.customer }}</td>
                        <td>
                          <VChip size="x-small" label>{{ order.status }}</VChip>
                        </td>
                        <td>{{ order.sum }} ₽</td>
                      </tr>
                    </tbody>
                  </VTable>
                </VCard>
              </VCol>
            </VRow>
          </template>

          <VCard v-else-if="!loadingReport" class="text-center py-12" variant="tonal">
            <VIcon icon="mdi-chart-line" size="64" color="grey-lighten-1" class="mb-4" />
            <div class="text-h6 text-grey">Выберите организацию и нажмите "Сформировать"</div>
          </VCard>
        </VWindowItem>

        <VWindowItem value="loyalty">
          <VCard>
            <VCardTitle class="d-flex align-center">
              <VIcon icon="mdi-star-circle" class="me-2" />
              Настройки iiko POS Loyalty
              <VSpacer />
              <VChip
                v-if="loyaltyConnectionStatus"
                :color="loyaltyConnectionStatus === 'success' ? 'success' : 'error'"
                size="small"
              >
                {{ loyaltyConnectionStatus === 'success' ? 'Связь есть' : 'Ошибка' }}
              </VChip>
            </VCardTitle>
            <VCardText>
              <VAlert type="warning" variant="tonal" class="mb-4 text-caption">
                Эти настройки используются для интеграции с внешним сервером лояльности iiko POS.
              </VAlert>
              <VRow>
                <VCol cols="12" md="6">
                  <VTextField
                    v-model="settings.pos_loyalty_name"
                    label="Наименование (pos_login)"
                    placeholder="Напр. 72roll_pos"
                    class="mb-4"
                  />
                  <VTextField
                    v-model="settings.pos_loyalty_login"
                    label="Логин API"
                    class="mb-4"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField
                    v-model="settings.pos_loyalty_password"
                    label="Пароль API"
                    type="password"
                    class="mb-4"
                  />
                  <VTextField
                    v-model="settings.pos_loyalty_channel"
                    label="Канал (Channel ID)"
                    placeholder="Введите UUID канала"
                  />
                </VCol>
              </VRow>
              <div class="d-flex gap-4 mt-6">
                <VBtn color="primary" :loading="saving" @click="saveSettings">
                  Сохранить настройки
                </VBtn>
                <VBtn
                  variant="outlined"
                  color="info"
                  :loading="testingLoyalty"
                  @click="testLoyaltyConnection"
                >
                  Проверить соединение
                </VBtn>
                <VBtn
                  variant="tonal"
                  color="secondary"
                  :loading="loadingLoyaltyData"
                  @click="fetchLoyaltyData"
                >
                  Отобразить данные для импорта
                </VBtn>
              </div>

              <!-- Список доступных программ и категорий -->
              <VDivider class="my-6" />
              
              <VRow v-if="loyaltyPrograms.length || loyaltyCategories.length">
                <VCol cols="12" md="6">
                  <VCard variant="outlined" class="h-100">
                    <VCardTitle class="text-subtitle-1">Бонусные программы</VCardTitle>
                    <VDivider />
                    <VList density="compact">
                      <VListItem v-for="program in loyaltyPrograms" :key="program.id">
                        <VListItemTitle>{{ program.name }}</VListItemTitle>
                        <template #append>
                          <VChip size="x-small" :color="program.isActive ? 'success' : 'grey'">
                            {{ program.isActive ? 'Активна' : 'Неактивна' }}
                          </VChip>
                        </template>
                      </VListItem>
                    </VList>
                  </VCard>
                </VCol>
                
                <VCol cols="12" md="6">
                  <VCard variant="outlined" class="h-100">
                    <VCardTitle class="text-subtitle-1">Категории клиентов</VCardTitle>
                    <VDivider />
                    <VList density="compact">
                      <VListItem v-for="category in loyaltyCategories" :key="category.id">
                        <VListItemTitle>{{ category.name }}</VListItemTitle>
                        <template #append>
                          <VChip size="x-small" color="info" v-if="category.isDeleted === false">
                            Действует
                          </VChip>
                        </template>
                      </VListItem>
                    </VList>
                  </VCard>
                </VCol>
              </VRow>
              
              <VAlert v-else-if="!loadingLoyaltyData" type="info" variant="tonal" class="mt-4">
                Нажмите «Отобразить данные для импорта», чтобы увидеть доступные программы и категории из iiko.
              </VAlert>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- ==================== Вкладка Управление ==================== -->
        <VWindowItem value="management">
          <VRow>
            <VCol cols="12" md="6">
              <VCard title="Системные настройки">
                <VCardText>
                  <VSelect
                    v-model="settings.address_format"
                    label="Формат адреса"
                    :items="[
                      {title: 'По компонентам (Город, Улица, Дом)', value: 'components'},
                      {title: 'Строка (Одной строкой)', value: 'line1'}
                    ]"
                    class="mb-4"
                  />
                  <VTextField
                    v-model="settings.city_name"
                    label="Город по умолчанию"
                    class="mb-4"
                  />
                  <VTextField
                    v-model="settings.manual_timezone"
                    label="Смещение времени (напр. +05:00)"
                    class="mb-4"
                    hint="Вычисляется автоматически при выборе пояса"
                    persistent-hint
                  />
                  <VSelect
                    v-model="settings.timezone_name"
                    :items="timezoneOptions"
                    label="Часовой пояс"
                    placeholder="Выберите часовой пояс"
                    clearable
                    @update:model-value="updateTimezoneOffset"
                  />
                  <VBtn color="primary" class="mt-4" @click="saveSettings">Сохранить</VBtn>
                </VCardText>
              </VCard>
            </VCol>

            <VCol cols="12" md="6">
              <VCard title="Настройки бонусов и промо">
                <VCardText>
                  <VTextField
                    v-model.number="settings.bonus_limit_percent"
                    label="Лимит оплаты баллами (%)"
                    type="number"
                    class="mb-4"
                  />
                  <VSelect
                    v-model="settings.discount_id"
                    :items="discountTypes"
                    label="Тип скидки по умолчанию"
                    class="mb-4"
                  />
                  <VSwitch v-model="settings.no_pass_promo" label="Не передавать промокоды в iiko" density="compact" />
                  <VSwitch v-model="settings.no_use_bonus" label="Отключить списание баллов" density="compact" />
                  <VSwitch v-model="settings.no_use_iiko_promo" label="Отключить акции iiko (промокоды)" density="compact" />
                  <VBtn color="primary" class="mt-4" @click="saveSettings">Сохранить</VBtn>
                </VCardText>
              </VCard>
            </VCol>
          </VRow>
        </VWindowItem>

        <!-- ==================== Вкладка Вебхуки ==================== -->
        <VWindowItem value="webhooks">
          <VCard title="Настройки вебхуков iiko Cloud">
            <VCardText>
              <VRow class="mb-4">
                <VCol cols="12">
                  <VTextField
                    v-model="settings.webhook_url"
                    label="URL вебхука"
                    placeholder="Автоматически определится при регистрации"
                    hint="URL, на который iiko Cloud будет отправлять уведомления"
                    persistent-hint
                    class="mb-2"
                  />
                </VCol>
                <VCol cols="12">
                  <VTextField
                    v-model="settings.webhook_auth_token"
                    label="Ключ авторизации (Token)"
                    placeholder="Генерируется автоматически"
                    hint="Секретный ключ для проверки подлинности запросов от iiko"
                    persistent-hint
                    type="text"
                  />
                </VCol>
              </VRow>
              <div class="d-flex mb-4 gap-2 flex-wrap">
                <VBtn size="small" variant="outlined" :loading="loadingLogs" @click="loadWebhookLogs">Обновить логи</VBtn>
                <VBtn size="small" color="secondary" :loading="registeringWebhook" @click="registerWebhook">Перерегистрировать вебхук</VBtn>
                <VBtn size="small" color="info" :loading="testingWebhook" @click="testWebhook">Тестировать вебхук</VBtn>
                <VBtn size="small" color="warning" :loading="syncingToken" @click="syncWebhookToken">Синхронизировать токен из iiko</VBtn>
                <VBtn size="small" color="primary" :loading="saving" @click="saveSettings">Сохранить настройки</VBtn>
              </div>
              <VTable density="compact">
                <thead>
                  <tr>
                    <th>Время</th>
                    <th>Тип</th>
                    <th>Статус</th>
                    <th>Заказ</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in webhookLogs" :key="log.id">
                    <td>{{ formatDateTime(log.created_at) }}</td>
                    <td>{{ log.event_type }}</td>
                    <td>
                      <VChip :color="log.processed ? 'success' : 'error'" size="x-small">
                        {{ log.status }}
                      </VChip>
                    </td>
                    <td>{{ log.order_id || '-' }}</td>
                  </tr>
                </tbody>
              </VTable>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- ==================== Вкладка Яндекс Карты ==================== -->
        <VWindowItem value="yandex">
          <VCard>
            <VCardTitle class="d-flex align-center">
              <VIcon icon="mdi-map-search-outline" class="me-2" />
              Настройки Яндекс.Карт
              <VSpacer />
              <VSwitch
                v-model="yandexSettings.is_active"
                label="Интеграция активна"
                hide-details
                color="success"
              />
            </VCardTitle>
            <VCardText>
              <VRow>
                <VCol cols="12" md="6">
                  <VTextField
                    v-model="yandexSettings.api_key_js"
                    label="JavaScript API и HTTP Геокодер"
                    placeholder="Введите ключ"
                    hint="Используется для отображения карт и поиска координат по адресу"
                    persistent-hint
                    class="mb-4"
                    type="password"
                  >
                    <template #append-inner>
                      <VBtn size="x-small" color="info" variant="text" @click="testYandexKey('geocoder')">Тест</VBtn>
                    </template>
                  </VTextField>
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField
                    v-model="yandexSettings.api_key_suggest"
                    label="API Геосаджеста"
                    placeholder="Введите ключ"
                    hint="Для выпадающих подсказок при вводе адреса"
                    persistent-hint
                    class="mb-4"
                    type="password"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField
                    v-model="yandexSettings.api_key_matrix"
                    label="Матрица расстояний"
                    placeholder="Введите ключ"
                    hint="Для расчета времени и стоимости доставки по расстоянию"
                    persistent-hint
                    class="mb-4"
                    type="password"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VTextField
                    v-model="yandexSettings.api_key_monitoring"
                    label="Маршрутизация (Планирование)"
                    placeholder="Введите ключ"
                    hint="Для функций мониторинга"
                    persistent-hint
                    class="mb-4"
                    type="password"
                  />
                </VCol>
              </VRow>
              
              <VAlert type="info" variant="tonal" class="mt-6">
                <div><strong>Какие ключи нужны?</strong></div>
                <ul class="text-caption mt-1">
                  <li><strong>JavaScript API:</strong> Основной ключ для работы карт.</li>
                  <li><strong>Матрица расстояний:</strong> Нужен для расчета времени.</li>
                  <li><strong>Геосаджест:</strong> Улучшает ввод адреса.</li>
                </ul>
              </VAlert>
              <VBtn color="primary" class="mt-4" :loading="savingYandex" @click="saveYandexSettings">
                Сохранить настройки Яндекс
              </VBtn>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- ==================== Вкладка KML (DELETED) ==================== -->
      </VWindow>
    </VCol>
  </VRow>

  <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
    {{ snackbarText }}
  </VSnackbar>
</template>

<style scoped>
.gap-4 { gap: 16px; }
.gap-2 { gap: 8px; }
</style>
