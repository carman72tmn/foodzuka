<script setup>
import { ref, onMounted, computed } from "vue"

// =========================================================================
// Состояние формы
// =========================================================================

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

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
})

// Справочники (загружаются из iiko)
const organizations = ref([])
const terminalGroups = ref([])
const paymentTypes = ref([])
const externalMenus = ref([])
const discountTypes = ref([])

// Статус подключения
const connectionStatus = ref(null) // null, 'success', 'error'
const restoConnectionStatus = ref(null)
const testingResto = ref(false)

const activeTab = ref("general")
const webhookLogs = ref([])
const loadingLogs = ref(false)
const registeringWebhook = ref(false)

const API_BASE = "/api/v1/iiko"
const syncingPayments = ref(false)
const syncingZones = ref(false)
const deliveryZones = ref([])

// =========================================================================
// Методы
// =========================================================================

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

// Загрузка текущих настроек
const loadSettings = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/settings`)
    if (res.ok) {
      const data = await res.json()

      Object.keys(settings.value).forEach((key) => {
        if (data[key] !== undefined && data[key] !== null) {
          settings.value[key] = data[key]
        }
      })
    }
  } catch (e) {
    // Настройки ещё не созданы — это нормально
  } finally {
    loading.value = false
  }
}

// Сохранение настроек
const saveSettings = async () => {
  saving.value = true
  try {
    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings.value),
    })

    if (res.ok) {
      showMessage("Настройки успешно сохранены")
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка сохранения", "error")
    }
  } catch (e) {
    showMessage("Ошибка подключения к серверу", "error")
  } finally {
    saving.value = false
  }
}

// Тест подключения
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
    if (data.success) {
      connectionStatus.value = "success"
      showMessage("Подключение успешно!")

      // Загружаем справочники
      if (data.organizations?.length) {
        organizations.value = data.organizations.map((o) => ({
          title: o.name || o.id,
          value: o.id,
        }))
      }
    } else {
      connectionStatus.value = "error"
      showMessage(data.error || "Ошибка подключения", "error")
    }
  } catch (e) {
    connectionStatus.value = "error"
    showMessage("Не удалось подключиться к API iiko (port 8000)", "error")
  } finally {
    testing.value = false
  }
}

// Тест подключения к Resto API
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
      showMessage(data.message || "Успешное подключение к iiko Resto API!")
    } else {
      restoConnectionStatus.value = "error"
      showMessage(data.error || data.detail || "Ошибка подключения", "error")
    }
  } catch (e) {
    restoConnectionStatus.value = "error"
    showMessage("Не удалось подключиться к API iiko Resto", "error")
  } finally {
    testingResto.value = false
  }
}

// Загрузка справочников
const loadTerminalGroups = async () => {
  try {
    const res = await fetch(`${API_BASE}/terminal-groups`)
    if (res.ok) {
      const data = await res.json()
      terminalGroups.value = data.map((t) => ({
        title: t.name || t.id,
        value: t.id,
      }))
    }
  } catch (e) {
    console.error(e)
  }
}

const loadPaymentTypes = async () => {
  try {
    const res = await fetch(`${API_BASE}/payment-types`)
    if (res.ok) {
      const data = await res.json()
      paymentTypes.value = data.map((p) => ({
        title: `${p.name} (${p.paymentTypeKind || ""})`,
        value: p.id,
      }))
    }
  } catch (e) {
    console.error(e)
  }
}

const syncPaymentTypes = async () => {
  syncingPayments.value = true
  try {
    const res = await fetch(`${API_BASE}/sync-payment-types`, { method: "POST" })
    if (res.ok) {
      showMessage("Типы оплаты синхронизированы")
      await loadPaymentTypes()
    } else {
      showMessage("Ошибка синхронизации оплат", "error")
    }
  } catch (e) {
    showMessage("Ошибка соединения", "error")
  } finally {
    syncingPayments.value = false
  }
}

const loadExternalMenus = async () => {
  try {
    const res = await fetch(`${API_BASE}/external-menus`)
    if (res.ok) {
      const data = await res.json()
      externalMenus.value = data.map((m) => ({
        title: m.name || m.id,
        value: m.id,
      }))
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

const syncDeliveryZones = async () => {
  syncingZones.value = true
  try {
    const res = await fetch(`${API_BASE}/sync-delivery-zones`, { method: "POST" })
    if (res.ok) {
      showMessage("Зоны доставки синхронизированы")
      await loadDeliveryZones()
    } else {
      showMessage("Ошибка синхронизации зон", "error")
    }
  } catch (e) {
    showMessage("Ошибка соединения", "error")
  } finally {
    syncingZones.value = false
  }
}

const loadAllReferences = async () => {
  await Promise.all([
    loadTerminalGroups(),
    loadPaymentTypes(),
    loadExternalMenus(),
    loadDiscountTypes(),
    loadDeliveryZones(),
  ])
}

// Webhooks
const loadWebhookLogs = async () => {
  loadingLogs.value = true
  try {
    const res = await fetch(`${API_BASE}/webhooks/logs?limit=20`)
    if (res.ok) {
      webhookLogs.value = await res.json()
    }
  } finally {
    loadingLogs.value = false
  }
}

const registerWebhook = async () => {
  registeringWebhook.value = true
  try {
    const url = new URL(`${API_BASE}/webhooks/register`, window.location.origin)
    url.searchParams.append("webhook_url", settings.value.webhook_url)
    if (settings.value.webhook_auth_token) {
      url.searchParams.append("auth_token", settings.value.webhook_auth_token)
    }

    const res = await fetch(url, { method: "POST" })
    if (res.ok) {
      showMessage("Вебхук успешно зарегистрирован")
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка регистрации", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    registeringWebhook.value = false
  }
}

const autoRegisterWebhook = async () => {
  registeringWebhook.value = true
  try {
    const res = await fetch(`${API_BASE}/webhooks/register`, { method: "POST" })
    if (res.ok) {
      const data = await res.json()
      settings.value.webhook_url = data.webhook_url
      settings.value.webhook_auth_token = data.auth_token
      showMessage("Вебхук автоматически зарегистрирован!")
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка авто-регистрации", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    registeringWebhook.value = false
  }
}

// =========================================================================
// Инициализация
// =========================================================================

onMounted(async () => {
  await loadSettings()
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
        <VTab value="webhooks">Вебхуки</VTab>
      </VTabs>

      <VWindow v-model="activeTab" class="mt-4">
        <!-- ==================== Вкладка Основные настройки ==================== -->
        <VWindowItem value="general">
          <VRow>
            <!-- Подключение API -->
            <VCol cols="12">
              <VCard class="mb-6">
                <VCardTitle class="d-flex align-center">
                  <VIcon icon="mdi-connection" class="me-2" />
                  Подключение iiko Cloud
                  <VSpacer />
                  <VChip
                    v-if="connectionStatus"
                    :color="connectionStatus === 'success' ? 'success' : 'error'"
                    size="small"
                  >
                    {{ connectionStatus === 'success' ? 'Подключено' : 'Ошибка' }}
                  </VChip>
                </VCardTitle>
                <VCardText>
                  <VRow align="center">
                    <VCol cols="12" md="8">
                      <VTextField
                        v-model="settings.api_login"
                        label="API Login (API Key)"
                        type="password"
                        hide-details="auto"
                      />
                    </VCol>
                    <VCol cols="12" md="4">
                      <VBtn
                        color="primary"
                        block
                        :loading="testing"
                        @click="testConnection"
                      >
                        Тест связи
                      </VBtn>
                    </VCol>
                  </VRow>
                </VCardText>
              </VCard>
            </VCol>

            <!-- Конфигурация -->
            <VCol cols="12" md="6">
              <VCard class="h-100">
                <VCardTitle>Конфигурация iiko</VCardTitle>
                <VCardText>
                  <VSelect
                    v-model="settings.organization_id"
                    :items="organizations"
                    label="Организация"
                    class="mb-4"
                  />
                  <VSelect
                    v-model="settings.terminal_group_id"
                    :items="terminalGroups"
                    label="Касса (Терм. группа)"
                    class="mb-4"
                  />
                  <VSelect
                    v-model="settings.external_menu_id"
                    :items="externalMenus"
                    label="Внешнее меню"
                  />
                </VCardText>
              </VCard>
            </VCol>

            <VCol cols="12" md="6">
              <VCard class="h-100">
                <VCardTitle>Дополнительно</VCardTitle>
                <VCardText>
                  <VSelect
                    v-model="settings.discount_id"
                    :items="discountTypes"
                    label="Тип скидки для промокодов"
                    class="mb-4"
                  />
                  <VTextField
                    v-model="settings.fallback_email"
                    label="Резервный Email"
                    class="mb-4"
                  />
                  <VTextField
                    v-model="settings.fallback_telegram_id"
                    label="Резервный Telegram ID"
                  />
                </VCardText>
              </VCard>
            </VCol>

            <VCol cols="12" class="mt-4">
              <VBtn color="primary" :loading="saving" @click="saveSettings">
                Сохранить всё
              </VBtn>
            </VCol>
          </VRow>
        </VWindowItem>

        <!-- ==================== Вкладка Оплата ==================== -->
        <VWindowItem value="payment">
          <VCard>
            <VCardTitle class="d-flex align-center">
              Привязка оплат
              <VSpacer />
              <VBtn 
                size="small" 
                variant="outlined" 
                color="warning" 
                :loading="syncingPayments"
                prepend-icon="mdi-sync"
                @click="syncPaymentTypes"
              >
                Обновить список
              </VBtn>
            </VCardTitle>
            <VCardText>
              <VAlert type="info" variant="tonal" class="mb-4">
                Сопоставьте способы оплаты на сайте с типами оплат в iiko.
              </VAlert>
              <VRow>
                <VCol cols="12" md="6">
                  <VSelect v-model="settings.payment_type_cash" :items="paymentTypes" label="Наличные" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect v-model="settings.payment_type_card" :items="paymentTypes" label="Карта курьеру" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect v-model="settings.payment_type_online" :items="paymentTypes" label="Онлайн оплата" />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect v-model="settings.payment_type_bonus" :items="paymentTypes" label="Оплата баллами" />
                </VCol>
              </VRow>
              <VBtn color="primary" class="mt-4" @click="saveSettings">Сохранить</VBtn>
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
              <VTable density="compact">
                <thead>
                  <tr>
                    <th>Зона</th>
                    <th>Описание</th>
                    <th>Мин. заказ</th>
                    <th>Стоимость</th>
                    <th>Время</th>
                    <th>Статус</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="zone in deliveryZones" :key="zone.id">
                    <td>{{ zone.name }}</td>
                    <td class="text-caption" style="max-width: 200px; white-space: normal;">
                      {{ zone.description || '-' }}
                    </td>
                    <td>{{ zone.min_sum }} р.</td>
                    <td>{{ zone.delivery_cost }} р.</td>
                    <td>{{ zone.min_delivery_time }}-{{ zone.max_delivery_time }} мин.</td>
                    <td>
                      <VChip :color="zone.is_active ? 'success' : 'grey'" size="x-small">
                        {{ zone.is_active ? 'Да' : 'Нет' }}
                      </VChip>
                    </td>
                  </tr>
                  <tr v-if="!deliveryZones.length">
                    <td colspan="5" class="text-center py-4">Данных нет. Запустите синхронизацию.</td>
                  </tr>
                </tbody>
              </VTable>
            </VCardText>
          </VCard>
        </VWindowItem>

        <!-- ==================== Вкладка Вебхуки ==================== -->
        <VWindowItem value="webhooks">
          <VRow>
            <VCol cols="12" md="6">
              <VCard title="Настройка вебхука">
                <VCardText>
                  <VTextField v-model="settings.webhook_url" label="URL вебхука" class="mb-4" />
                  <VTextField v-model="settings.webhook_auth_token" label="Токен авторизации" class="mb-4" />
                  <div class="d-flex gap-2">
                    <VBtn color="primary" size="small" @click="registerWebhook">Manual</VBtn>
                    <VBtn color="success" size="small" @click="autoRegisterWebhook">Auto</VBtn>
                  </div>
                </VCardText>
              </VCard>
            </VCol>
            <VCol cols="12" md="6">
              <VCard title="Последние события" class="h-100">
                <VCardText>
                  <VBtn size="x-small" variant="text" @click="loadWebhookLogs" class="mb-2">Обновить логи</VBtn>
                  <div v-for="log in webhookLogs" :key="log.id" class="text-caption mb-1 border-bottom">
                    {{ new Date(log.created_at).toLocaleTimeString() }} - {{ log.event_type }}
                  </div>
                </VCardText>
              </VCard>
            </VCol>
          </VRow>
        </VWindowItem>
      </VWindow>
    </VCol>
  </VRow>

  <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
    {{ snackbarText }}
  </VSnackbar>
</template>
