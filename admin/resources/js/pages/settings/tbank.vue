<script setup>
import { ref, computed, onMounted } from 'vue'
import { getAuthHeaders } from '@/utils/auth'

// Состояние формы
const terminalKey = ref('')
const token = ref('')
const certificateContent = ref('')
const selectedTerminalsList = ref([]) // массив выбранных TerminalKey
const terminalNames = ref({}) // кастомные названия терминалов: { terminalKey: customName }
const isActive = ref(false)
const terminalPickup = ref('')
const terminalDelivery = ref('')
const merchantId = ref('')
const sbpTerminalId = ref('42734785')
const sbpSecretKey = ref('')

// Интернет-эквайринг Т-Банка (Merchant API / онлайн-оплаты, СБП, T-Pay)
const acquiringTerminalKey = ref('')
const acquiringPassword = ref('')
const acquiringIsActive = ref(true)
const webhookSecret = ref('')

// Терминалы торгового эквайринга
const terminals = ref([])
const terminalsLoading = ref(false)

// Расчетные счета компании
const accounts = ref([])
const accountsLoading = ref(false)

// UI состояние
const loading = ref(false)
const saveLoading = ref(false)
const isTerminalKeyVisible = ref(false)
const isTokenVisible = ref(false)
const isSbpSecretKeyVisible = ref(false)
const isAcquiringPasswordVisible = ref(false)

// Уведомления (Snackbar)
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const showMessage = (text, color = 'success') => {
  snackbar.value.text = text
  snackbar.value.color = color
  snackbar.value.show = true
}

// Состояние проверки подключения
const testLoading = ref(false)
const testResult = ref(null)
const testDialog = ref({
  show: false,
  success: false,
  title: '',
  message: '',
  availableApis: []
})

const testConnection = async () => {
  testLoading.value = true
  try {
    const response = await fetch('/api/v1/settings/tbank/test-connection', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        terminal_key: terminalKey.value,
        token: token.value,
        certificate_content: certificateContent.value,
        is_active: isActive.value,
        terminal_pickup: terminalPickup.value,
        terminal_delivery: terminalDelivery.value,
        merchant_id: merchantId.value,
        sbp_terminal_id: sbpTerminalId.value,
        sbp_secret_key: sbpSecretKey.value,
        acquiring_terminal_key: acquiringTerminalKey.value,
        acquiring_password: acquiringPassword.value,
        acquiring_is_active: acquiringIsActive.value,
        webhook_secret: webhookSecret.value
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      testResult.value = data
      
      testDialog.value.success = data.success
      testDialog.value.title = data.success 
        ? 'Подключение успешно установлено!' 
        : 'Подключение не установлено'
      testDialog.value.message = data.error_message || 'Подключение успешно проверено.'
      testDialog.value.availableApis = data.available_apis || []
      testDialog.value.show = true
      
      // Выгружаем терминалы после успешного подключения
      if (data.success && token.value) {
        fetchTerminals()
        fetchAccounts()
      }
    } else {
      const err = await response.json()
      showMessage(`Ошибка проверки: ${err.detail || 'Не удалось выполнить запрос'}`, 'error')
    }
  } catch (error) {
    console.error('Ошибка при тестировании подключения:', error)
    showMessage('Сбой подключения к серверу при проверке', 'error')
  } finally {
    testLoading.value = false
  }
}

// Получение настроек с сервера
const fetchSettings = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/settings/tbank/', {
      headers: getAuthHeaders()
    })
    
    if (response.ok) {
      const data = await response.json()
      // Если terminal_key случайно совпал с секретным ключом СБП из-за старого автозаполнения, не выводим его в OpenAPI терминал
      if (data.terminal_key && data.sbp_secret_key && data.terminal_key.trim() === data.sbp_secret_key.trim()) {
        terminalKey.value = ''
      } else {
        terminalKey.value = data.terminal_key || ''
      }
      token.value = data.token || ''
      certificateContent.value = data.certificate_content || ''
      isActive.value = data.is_active || false
      terminalPickup.value = data.terminal_pickup || ''
      terminalDelivery.value = data.terminal_delivery || ''
      merchantId.value = data.merchant_id || ''
      sbpTerminalId.value = data.sbp_terminal_id || '42734785'
      sbpSecretKey.value = data.sbp_secret_key || ''
      acquiringTerminalKey.value = data.acquiring_terminal_key || ''
      acquiringPassword.value = data.acquiring_password || ''
      acquiringIsActive.value = data.acquiring_is_active !== undefined ? data.acquiring_is_active : true
      webhookSecret.value = data.webhook_secret || ''
      
      // Восстановление списка выбранных терминалов
      try {
        selectedTerminalsList.value = data.selected_terminals ? JSON.parse(data.selected_terminals) : []
      } catch (e) {
        selectedTerminalsList.value = []
      }
      
      // Восстановление пользовательских названий терминалов
      try {
        terminalNames.value = data.terminal_names 
          ? (typeof data.terminal_names === 'string' ? JSON.parse(data.terminal_names) : data.terminal_names) 
          : {}
      } catch (e) {
        terminalNames.value = {}
      }
      
      // Если токен есть, выгружаем список терминалов
      if (token.value) {
        fetchTerminals()
        fetchAccounts()
      }
    } else {
      showMessage('Не удалось загрузить настройки Т-Банка', 'error')
    }
  } catch (error) {
    console.error('Ошибка при загрузке настроек:', error)
    showMessage('Сбой подключения при загрузке настроек', 'error')
  } finally {
    loading.value = false
  }
}

// Список терминалов с отображаемыми именами для селектов
const displayTerminals = computed(() => {
  return terminals.value.map(term => {
    const custom = terminalNames.value[term.terminalKey]
    return {
      ...term,
      name: custom && custom.trim() ? custom.trim() : (term.name || `Терминал ${term.terminalKey}`)
    }
  })
})

// Обновление названия терминала
const updateTerminalName = (key, val) => {
  if (val && val.trim()) {
    terminalNames.value[key] = val.trim()
  } else {
    delete terminalNames.value[key]
  }
}

// Сброс названия терминала к исходному
const resetTerminalName = (key) => {
  delete terminalNames.value[key]
  showMessage(`Название терминала ${key} сброшено к стандартному`)
}

// Сохранение настроек на сервере
const saveSettings = async () => {
  saveLoading.value = true
  try {
    const response = await fetch('/api/v1/settings/tbank/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        terminal_key: terminalKey.value,
        token: token.value,
        certificate_content: certificateContent.value,
        selected_terminals: JSON.stringify(selectedTerminalsList.value),
        is_active: isActive.value,
        terminal_pickup: terminalPickup.value,
        terminal_delivery: terminalDelivery.value,
        merchant_id: merchantId.value,
        sbp_terminal_id: sbpTerminalId.value,
        sbp_secret_key: sbpSecretKey.value,
        terminal_names: JSON.stringify(terminalNames.value),
        acquiring_terminal_key: acquiringTerminalKey.value,
        acquiring_password: acquiringPassword.value,
        acquiring_is_active: acquiringIsActive.value,
        webhook_secret: webhookSecret.value
      })
    })
    
    if (response.ok) {
      showMessage('Настройки интеграции и названия терминалов успешно сохранены')
      await fetchSettings()
    } else {
      const err = await response.json()
      showMessage(`Ошибка: ${err.detail || 'Не удалось сохранить настройки'}`, 'error')
    }
  } catch (error) {
    console.error('Ошибка при сохранении настроек:', error)
    showMessage('Сбой подключения при сохранении настроек', 'error')
  } finally {
    saveLoading.value = false
  }
}

// Получение списка терминалов
const fetchTerminals = async () => {
  terminalsLoading.value = true
  try {
    const response = await fetch('/api/v1/settings/tbank/terminals', {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      terminals.value = data
      
      // Синхронизируем кастомные названия, если они уже сохранены на сервере
      data.forEach(t => {
        if (t.custom_name && !terminalNames.value[t.terminalKey]) {
          terminalNames.value[t.terminalKey] = t.custom_name
        }
      })
    } else {
      const err = await response.json().catch(() => ({}))
      showMessage(`Не удалось загрузить терминалы: ${err.detail || 'Ошибка сервера'}`, 'error')
    }
  } catch (error) {
    console.error('Ошибка при загрузке терминалов:', error)
    showMessage('Сбой подключения при загрузке терминалов', 'error')
  } finally {
    terminalsLoading.value = false
  }
}

// Получение списка расчетных счетов компании
const fetchAccounts = async () => {
  accountsLoading.value = true
  try {
    const response = await fetch('/api/v1/settings/tbank/accounts', {
      headers: getAuthHeaders()
    })
    if (response.ok) {
      accounts.value = await response.json()
    } else {
      const err = await response.json().catch(() => ({}))
      showMessage(`Не удалось загрузить счета: ${err.detail || 'Ошибка сервера'}`, 'error')
    }
  } catch (error) {
    console.error('Ошибка при загрузке счетов:', error)
    showMessage('Сбой подключения при загрузке счетов', 'error')
  } finally {
    accountsLoading.value = false
  }
}

// Проверка корректности PEM-формата сертификата
const checkCertificateFormat = () => {
  const cert = certificateContent.value.trim()
  if (!cert) {
    showMessage('Поле сертификата пустое', 'warning')
    return
  }
  
  if (cert.startsWith('-----BEGIN CERTIFICATE-----') && cert.endsWith('-----END CERTIFICATE-----')) {
    showMessage('Формат SSL-сертификата (PEM) корректен')
  } else {
    showMessage('Внимание: неверные маркеры начала/конца PEM-сертификата!', 'error')
  }
}

// Копирование текста в буфер обмена
const copyToClipboard = async (text, label = 'Ссылка') => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = text
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      document.execCommand('copy')
      textArea.remove()
    }
    showMessage(`${label} успешно скопирована в буфер обмена`)
  } catch (err) {
    console.error('Ошибка копирования:', err)
    showMessage(`Не удалось скопировать: ${err.message}`, 'error')
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<template>
  <div>
    <!-- Шапка страницы -->
    <div class="mb-6">
      <h1 class="text-h4 font-weight-bold mb-1 d-flex align-center">
        <VIcon icon="bx-credit-card" color="primary" class="me-2" size="36" />
        Настройки T-API
      </h1>
      <p class="text-subtitle-1 text-muted">Конфигурация эквайринга и СБП Т-Банка для автоматического сопоставления оплат</p>
    </div>

    <!-- Основная карточка настроек -->
    <VCard class="glass-card mb-6" :loading="loading">
      <VCardTitle class="border-bottom py-4 px-6">
        <span class="text-h5 font-weight-bold">Параметры интеграции</span>
      </VCardTitle>

      <VCardText class="py-6 px-6">
        <VForm @submit.prevent="saveSettings" autocomplete="off">
          <!-- Скрытые фиктивные поля для блокировки агрессивного автозаполнения браузера (Chrome Password Manager) -->
          <input type="text" name="prevent_autofill_username" style="display:none" autocomplete="username" tabindex="-1">
          <input type="password" name="prevent_autofill_password" style="display:none" autocomplete="current-password" tabindex="-1">

          <VRow>
            <!-- Активация -->
            <VCol cols="12" class="pb-4">
              <div class="d-flex align-center justify-space-between p-4 rounded bg-light-gradient border-light">
                <div>
                  <span class="font-weight-bold d-block text-body-1">Включить интеграцию с Т-Банком</span>
                  <span class="text-caption text-muted">Если активно, система будет сверять поступающие платежи по данному терминалу</span>
                </div>
                <VSwitch
                  v-model="isActive"
                  color="success"
                  hide-details
                />
              </div>
            </VCol>

            <!-- Параметры СБП (QRPay) -->
            <VCol cols="12">
              <div class="p-3 mb-2 rounded bg-light border-light d-flex align-center">
                <VIcon icon="bx-qr-scan" color="primary" class="me-2" size="24" />
                <div>
                  <span class="font-weight-bold d-block text-body-2">Параметры сервиса СБП (QRPay / Динамические QR-коды)</span>
                  <span class="text-caption text-muted">Используются для генерации QR-кодов курьерами и на кассе</span>
                </div>
              </div>
            </VCol>

            <!-- Merchant ID -->
            <VCol cols="12" md="4">
              <VTextField
                v-model="merchantId"
                name="tbank_sbp_merchant_id"
                autocomplete="off"
                label="Идентификатор мерчанта СБП (Merchant ID)"
                placeholder="400000001164353"
                variant="outlined"
                density="comfortable"
                persistent-placeholder
              />
            </VCol>

            <!-- SBP Terminal ID (TID) -->
            <VCol cols="12" md="4">
              <VTextField
                v-model="sbpTerminalId"
                name="tbank_sbp_terminal_id"
                autocomplete="off"
                label="Идентификатор кассы СБП (Terminal ID / TID)"
                placeholder="42734785"
                variant="outlined"
                density="comfortable"
                persistent-placeholder
              />
            </VCol>

            <!-- SBP Secret Key -->
            <VCol cols="12" md="4">
              <VTextField
                v-model="sbpSecretKey"
                name="tbank_sbp_secret_key"
                autocomplete="new-password"
                label="Секретный ключ СБП (HMAC-SHA256)"
                placeholder="Секретный Base64 ключ"
                variant="outlined"
                density="comfortable"
                :type="isSbpSecretKeyVisible ? 'text' : 'password'"
                :append-inner-icon="isSbpSecretKeyVisible ? 'bx-hide' : 'bx-show'"
                @click:append-inner="isSbpSecretKeyVisible = !isSbpSecretKeyVisible"
                persistent-placeholder
              />
            </VCol>

            <!-- Разделитель для эквайринга и OpenAPI -->
            <VCol cols="12">
              <div class="p-3 mb-2 rounded bg-light border-light d-flex align-center">
                <VIcon icon="bx-server" color="primary" class="me-2" size="24" />
                <div>
                  <span class="font-weight-bold d-block text-body-2">Т-Бизнес OpenAPI и Торговый эквайринг (POS-терминалы)</span>
                  <span class="text-caption text-muted">Для выгрузки выписок по расчетному счету и сопоставления терминалов</span>
                </div>
              </div>
            </VCol>

            <!-- Terminal Key -->
            <VCol cols="12" md="6">
              <VTextField
                v-model="terminalKey"
                name="tbank_openapi_terminal_key"
                autocomplete="off"
                label="Терминальный ключ (Terminal Key)"
                placeholder="1234567890123DEMO"
                variant="outlined"
                density="comfortable"
                :type="isTerminalKeyVisible ? 'text' : 'password'"
                :append-inner-icon="isTerminalKeyVisible ? 'bx-hide' : 'bx-show'"
                @click:append-inner="isTerminalKeyVisible = !isTerminalKeyVisible"
                persistent-placeholder
              />
            </VCol>

            <!-- Token -->
            <VCol cols="12" md="6">
              <VTextField
                v-model="token"
                name="tbank_openapi_token"
                autocomplete="new-password"
                label="OpenAPI Токен Т-Банк Бизнес (Bearer t.xxx)"
                placeholder="t.HN..."
                variant="outlined"
                density="comfortable"
                :type="isTokenVisible ? 'text' : 'password'"
                :append-inner-icon="isTokenVisible ? 'bx-hide' : 'bx-show'"
                @click:append-inner="isTokenVisible = !isTokenVisible"
                persistent-placeholder
              />
            </VCol>

            <!-- Сопоставление терминалов с типами заказов -->
            <VCol cols="12" md="6">
              <VSelect
                v-model="terminalPickup"
                :items="displayTerminals"
                item-title="name"
                item-value="terminalKey"
                label="Терминал для заказов Самовывоз"
                placeholder="Выберите терминал"
                variant="outlined"
                density="comfortable"
                clearable
                persistent-placeholder
              >
                <template #prepend-inner>
                  <VIcon icon="bx-store-alt" color="primary" class="me-1" />
                </template>
              </VSelect>
            </VCol>

            <VCol cols="12" md="6">
              <VSelect
                v-model="terminalDelivery"
                :items="displayTerminals"
                item-title="name"
                item-value="terminalKey"
                label="Терминал для заказов Доставка"
                placeholder="Выберите терминал"
                variant="outlined"
                density="comfortable"
                clearable
                persistent-placeholder
              >
                <template #prepend-inner>
                  <VIcon icon="bx-cycling" color="primary" class="me-1" />
                </template>
              </VSelect>
            </VCol>

            <!-- Certificate PEM -->
            <VCol cols="12">
              <div class="d-flex justify-space-between align-center mb-1">
                <span class="text-body-2 font-weight-semibold text-muted">Содержимое SSL-сертификата (PEM-формат):</span>
                <VBtn 
                  size="x-small" 
                  variant="text" 
                  color="primary" 
                  @click="checkCertificateFormat"
                  :disabled="!certificateContent"
                >
                  Проверить формат
                </VBtn>
              </div>
              <VTextarea
                v-model="certificateContent"
                placeholder="-----BEGIN CERTIFICATE-----&#10;MIIFJDCCBAygAwIBAgIQDF6f...&#10;-----END CERTIFICATE-----"
                rows="10"
                variant="outlined"
                class="code-textarea font-mono"
                clearable
                persistent-placeholder
              />
              <span class="text-caption text-muted mt-1 d-block">
                Вставьте сюда содержимое вашего приватного ключа или сертификата для авторизации защищенных запросов к хосту Т-Банка.
              </span>
            </VCol>

            <!-- Разделитель для Интернет-эквайринга -->
            <VCol cols="12">
              <div class="p-3 mb-2 rounded bg-light border-light d-flex align-center justify-space-between flex-wrap gap-2">
                <div class="d-flex align-center">
                  <VIcon icon="bx-credit-card" color="primary" class="me-2" size="24" />
                  <div>
                    <span class="font-weight-bold d-block text-body-2">Интернет-эквайринг Т-Банк (Онлайн-оплаты картами, СБП и T-Pay)</span>
                    <span class="text-caption text-muted">Merchant API для приема оплат на сайте и в мобильном приложении со статусами в реальном времени</span>
                  </div>
                </div>
                <VSwitch
                  v-model="acquiringIsActive"
                  label="Интернет-эквайринг активен"
                  color="success"
                  density="compact"
                  hide-details
                />
              </div>
            </VCol>

            <!-- Acquiring Terminal Key -->
            <VCol cols="12" md="6">
              <VTextField
                v-model="acquiringTerminalKey"
                name="tbank_acq_terminal_key"
                autocomplete="off"
                label="Терминал интернет-эквайринга (TerminalKey)"
                placeholder="Например: 1729000000001DEMO"
                variant="outlined"
                density="comfortable"
                persistent-placeholder
                hint="TerminalKey из Личного кабинета интернет-эквайринга Т-Банка"
                persistent-hint
              />
            </VCol>

            <!-- Acquiring Password (Secret Key) -->
            <VCol cols="12" md="6">
              <VTextField
                v-model="acquiringPassword"
                name="tbank_acq_password"
                autocomplete="new-password"
                label="Пароль терминала интернет-эквайринга (Password)"
                placeholder="Секретный пароль терминала"
                variant="outlined"
                density="comfortable"
                :type="isAcquiringPasswordVisible ? 'text' : 'password'"
                :append-inner-icon="isAcquiringPasswordVisible ? 'bx-hide' : 'bx-show'"
                @click:append-inner="isAcquiringPasswordVisible = !isAcquiringPasswordVisible"
                persistent-placeholder
                hint="Используется для проверки цифровой подписи (Token) входящих вебхуков"
                persistent-hint
              />
            </VCol>

            <!-- Блок Webhook URL для Т-Банка -->
            <VCol cols="12">
              <VCard variant="tonal" color="primary" class="p-4 rounded border">
                <div class="d-flex align-center mb-2">
                  <VIcon icon="bx-link-external" class="me-2" size="20" />
                  <span class="font-weight-bold text-subtitle-2">URL для получения уведомлений об оплатах (Вебхуки)</span>
                </div>
                <p class="text-caption mb-3">
                  Скопируйте эти адреса и укажите их в Личном кабинете Т-Банка (раздел <b>Интернет-эквайринг → Настройки → Оповещения по HTTP</b>), чтобы платежи мгновенно подтверждались и отображались в мониторе в реальном времени:
                </p>

                <div class="mb-3 p-2 bg-white rounded border d-flex align-center justify-space-between flex-wrap gap-2">
                  <div>
                    <span class="text-caption font-weight-bold text-primary d-block">Основной Webhook (Эквайринг, СБП, T-Pay):</span>
                    <code class="text-body-2 text-dark font-mono">https://vezuroll.ru/api/v1/tbank/webhooks/payment-status</code>
                  </div>
                  <VBtn
                    size="small"
                    variant="tonal"
                    color="primary"
                    prepend-icon="bx-copy"
                    @click="copyToClipboard('https://vezuroll.ru/api/v1/tbank/webhooks/payment-status', 'URL вебхука оплаты')"
                  >
                    Скопировать URL
                  </VBtn>
                </div>

                <div class="p-2 bg-white rounded border d-flex align-center justify-space-between flex-wrap gap-2">
                  <div>
                    <span class="text-caption font-weight-bold text-primary d-block">Webhook для QR СБП (QRPay):</span>
                    <code class="text-body-2 text-dark font-mono">https://vezuroll.ru/api/v1/tbank/webhooks/sbp-qr</code>
                  </div>
                  <VBtn
                    size="small"
                    variant="tonal"
                    color="primary"
                    prepend-icon="bx-copy"
                    @click="copyToClipboard('https://vezuroll.ru/api/v1/tbank/webhooks/sbp-qr', 'URL вебхука СБП QR')"
                  >
                    Скопировать URL
                  </VBtn>
                </div>
              </VCard>
            </VCol>
          </VRow>
        </VForm>
      </VCardText>

      <VCardActions class="px-6 pb-6 border-top pt-4">
        <VBtn
          color="secondary"
          variant="outlined"
          size="large"
          class="font-weight-bold px-6 me-2"
          :loading="testLoading"
          :disabled="!terminalKey && !token && !certificateContent && !acquiringTerminalKey"
          @click="testConnection"
        >
          <VIcon icon="bx-plug" class="me-1" />
          Проверить подключение
        </VBtn>
        <VSpacer />
        <VBtn
          color="primary"
          size="large"
          class="gradient-btn font-weight-bold px-6"
          :loading="saveLoading"
          @click="saveSettings"
        >
          Сохранить настройки
        </VBtn>
      </VCardActions>
    </VCard>

    <!-- Карточка расчетных счетов компании -->
    <VCard class="glass-card mb-6" :loading="accountsLoading">
      <VCardTitle class="border-bottom py-4 px-6 d-flex align-center justify-space-between flex-wrap gap-2">
        <div>
          <span class="text-h5 font-weight-bold">Расчетные счета компании (T-API)</span>
          <span class="text-caption text-muted d-block mt-1">Список активных расчетных счетов организации в Т-Банке</span>
        </div>
        <VBtn
          color="primary"
          variant="tonal"
          size="small"
          :disabled="!token"
          @click="fetchAccounts"
        >
          <VIcon icon="bx-sync" class="me-1" />
          Обновить список счетов
        </VBtn>
      </VCardTitle>

      <VCardText class="py-6 px-6">
        <div v-if="accounts.length > 0">
          <VRow>
            <VCol 
              v-for="acc in accounts" 
              :key="acc.accountNumber" 
              cols="12" 
              md="6"
            >
              <VCard variant="outlined" class="p-4 bg-light-gradient border-light rounded d-flex flex-column h-100" style="background: rgba(var(--v-theme-surface), 0.4); border-color: rgba(var(--v-border-color), 0.08) !important;">
                <div class="d-flex align-center justify-space-between mb-3">
                  <div class="d-flex align-center">
                    <VIcon icon="bx-wallet" color="primary" class="me-2" size="24" />
                    <span class="font-weight-bold text-body-1">{{ acc.name || 'Расчетный счет' }}</span>
                  </div>
                  <VChip
                    :color="acc.status === 'ACTIVE' ? 'success' : 'warning'"
                    size="x-small"
                    class="font-weight-bold"
                  >
                    {{ acc.status === 'ACTIVE' ? 'АКТИВЕН' : acc.status }}
                  </VChip>
                </div>
                
                <div class="mb-4">
                  <span class="text-caption text-muted d-block">Номер счета</span>
                  <span class="font-mono text-body-2 font-weight-semibold">{{ acc.accountNumber }}</span>
                </div>
              </VCard>
            </VCol>
          </VRow>
        </div>
        
        <div v-else class="text-center py-6 text-muted">
          <VIcon icon="bx-wallet-alt" size="48" class="mb-2 text-muted" style="opacity: 0.5;" />
          <p class="text-body-2 mb-1">Список расчетных счетов пуст.</p>
          <p class="text-caption">Укажите API Токен и нажмите кнопку «Обновить список счетов» для загрузки расчетных счетов из банка.</p>
        </div>
      </VCardText>
    </VCard>

    <!-- Карточка выбора терминалов торгового эквайринга -->
    <VCard class="glass-card mb-6" :loading="terminalsLoading">
      <VCardTitle class="border-bottom py-4 px-6 d-flex align-center justify-space-between flex-wrap gap-2">
        <div>
          <span class="text-h5 font-weight-bold">Терминалы торгового эквайринга (POS)</span>
          <span class="text-caption text-muted d-block mt-1">Выберите терминалы, операции по которым необходимо получать и сверять с заказами</span>
        </div>
        <VBtn
          color="primary"
          variant="tonal"
          size="small"
          :disabled="!token"
          @click="fetchTerminals"
        >
          <VIcon icon="bx-download" class="me-1" />
          Выгрузить терминалы
        </VBtn>
      </VCardTitle>

      <VCardText class="py-6 px-6">
        <div v-if="terminals.length > 0">
          <VTable class="bg-transparent border-light rounded">
            <thead>
              <tr>
                <th class="text-left font-weight-bold" style="width: 60px;">Выбор</th>
                <th class="text-left font-weight-bold" style="width: 170px;">ID / Терминальный ключ</th>
                <th class="text-left font-weight-bold" style="min-width: 320px;">Название терминала (редактируемое)</th>
                <th class="text-left font-weight-bold">ИНН организации</th>
                <th class="text-left font-weight-bold" style="width: 120px;">Статус</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="term in terminals" :key="term.terminalKey">
                <td>
                  <VCheckbox
                    v-model="selectedTerminalsList"
                    :value="term.terminalKey"
                    hide-details
                    density="compact"
                  />
                </td>
                <td class="font-mono text-body-2 font-weight-semibold">{{ term.terminalKey }}</td>
                <td>
                  <div class="d-flex align-center gap-2 py-1">
                    <VTextField
                      :model-value="terminalNames[term.terminalKey] !== undefined ? terminalNames[term.terminalKey] : (term.custom_name || term.name)"
                      @update:model-value="val => updateTerminalName(term.terminalKey, val)"
                      placeholder="Введите понятное название"
                      variant="outlined"
                      density="compact"
                      hide-details
                      class="flex-grow-1"
                      style="max-width: 360px;"
                    >
                      <template #prepend-inner>
                        <VIcon icon="bx-edit-alt" size="18" color="primary" class="me-1" />
                      </template>
                      <template #append-inner v-if="terminalNames[term.terminalKey] && terminalNames[term.terminalKey] !== term.default_name">
                        <VTooltip text="Сбросить к стандартному названию">
                          <template #activator="{ props }">
                            <VBtn
                              v-bind="props"
                              icon="bx-undo"
                              size="x-small"
                              variant="text"
                              color="warning"
                              @click.stop="resetTerminalName(term.terminalKey)"
                            />
                          </template>
                        </VTooltip>
                      </template>
                    </VTextField>
                    <VChip
                      v-if="terminalNames[term.terminalKey] && terminalNames[term.terminalKey] !== term.default_name"
                      color="info"
                      size="x-small"
                      class="font-weight-medium"
                    >
                      Изменено
                    </VChip>
                  </div>
                  <span v-if="term.default_name && terminalNames[term.terminalKey] && terminalNames[term.terminalKey] !== term.default_name" class="text-caption text-muted d-block mt-1">
                    Стандартное: {{ term.default_name }}
                  </span>
                </td>
                <td class="text-caption text-muted">{{ term.inn || '-' }}</td>
                <td>
                  <VChip
                    :color="term.status === 'ACTIVE' ? 'success' : 'warning'"
                    size="x-small"
                    class="font-weight-bold"
                  >
                    {{ term.status === 'ACTIVE' ? 'АКТИВЕН' : 'НЕАКТИВЕН' }}
                  </VChip>
                </td>
              </tr>
            </tbody>
          </VTable>
          
          <div class="mt-4 d-flex align-center text-caption text-muted">
            <VIcon icon="bx-info-circle" class="me-1" size="16" />
            <span>Выбрано терминалов для сверки: <strong>{{ selectedTerminalsList.length }}</strong> из <strong>{{ terminals.length }}</strong></span>
          </div>
        </div>
        
        <div v-else class="text-center py-8 text-muted">
          <VIcon icon="bx-devices" size="48" class="mb-2 text-muted" style="opacity: 0.5;" />
          <p class="text-body-2 mb-1">Список терминалов торгового эквайринга пуст.</p>
          <p class="text-caption">Укажите API Токен и нажмите кнопку «Выгрузить терминалы» для загрузки устройств из банка.</p>
        </div>
      </VCardText>
    </VCard>

    <!-- Диалог результатов проверки -->
    <VDialog v-model="testDialog.show" max-width="600px">
      <VCard class="glass-card">
        <VCardTitle class="border-bottom py-4 px-6 d-flex align-center">
          <VIcon 
            :icon="testDialog.success ? 'bx-check-circle' : 'bx-error-circle'" 
            :color="testDialog.success ? 'success' : 'error'" 
            class="me-2" 
            size="28" 
          />
          <span class="text-h6 font-weight-bold">{{ testDialog.title }}</span>
        </VCardTitle>

        <VCardText class="py-6 px-6">
          <!-- Статус подключения -->
          <div class="mb-4 d-flex align-center">
            <span class="text-body-1 font-weight-semibold me-2">Статус транспорта TLS/SSL:</span>
            <VChip 
              :color="testResult?.tls_ok ? 'success' : 'error'" 
              size="small" 
              class="font-weight-bold"
            >
              {{ testResult?.tls_ok ? 'Успешно (TLS OK)' : 'Ошибка соединения/SSL' }}
            </VChip>
          </div>

          <!-- Детальное сообщение -->
          <div class="mb-6 rounded p-4 bg-light-gradient border-light" style="background: rgba(var(--v-theme-surface), 0.05);">
            <span class="text-body-2 font-weight-semibold d-block mb-1 text-muted">Детализация:</span>
            <p class="text-body-2 mb-0" :class="testDialog.success ? 'text-success' : 'text-error'">
              {{ testDialog.message }}
            </p>
          </div>

          <!-- Список доступных API -->
          <div v-if="testDialog.availableApis.length > 0">
            <span class="text-body-2 font-weight-bold text-muted d-block mb-3">Доступные API методы для текущей конфигурации:</span>
            <div 
              v-for="(api, index) in testDialog.availableApis" 
              :key="index" 
              class="mb-3 p-3 rounded border d-flex align-start"
              style="background: rgba(var(--v-theme-surface), 0.4); border-color: rgba(var(--v-border-color), 0.08) !important;"
            >
              <VIcon icon="bx-code-alt" color="primary" class="me-2 mt-1" size="20" />
              <div>
                <span class="font-weight-bold text-body-2 d-block">{{ api.name }}</span>
                <span class="text-caption text-muted d-block mb-1">{{ api.description }}</span>
                <VChip size="x-small" color="primary" variant="tonal" class="font-weight-semibold">
                  {{ api.status }}
                </VChip>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-4 text-muted text-body-2">
            Нет доступных API. Заполните терминальный ключ и токен для активации методов эквайринга.
          </div>
        </VCardText>

        <VCardActions class="px-6 pb-6 border-top pt-4">
          <VSpacer />
          <VBtn
            color="primary"
            variant="flat"
            class="px-6"
            @click="testDialog.show = false"
          >
            Понятно
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Всплывающее уведомление -->
    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="4000"
      location="top right"
    >
      {{ snackbar.text }}
      <template #actions>
        <VBtn
          variant="text"
          @click="snackbar.show = false"
        >
          Закрыть
        </VBtn>
      </template>
    </VSnackbar>
  </div>
</template>

<style scoped>
/* Стеклянный стиль карточки */
.glass-card {
  background: rgba(var(--v-theme-surface), 0.7) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(var(--v-border-color), 0.08) !important;
  border-radius: 12px !important;
}

/* Рамки и разделения */
.border-bottom {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.06);
}
.border-top {
  border-top: 1px solid rgba(var(--v-border-color), 0.06);
}

/* Градиентный фон */
.bg-light-gradient {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.04) 0%, rgba(var(--v-theme-secondary), 0.02) 100%);
}
.border-light {
  border: 1px solid rgba(var(--v-theme-primary), 0.06);
}

/* Кнопка с градиентом */
.gradient-btn {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 1) 0%, rgba(var(--v-theme-secondary), 0.9) 100%) !important;
  color: white !important;
  border: none !important;
}

/* Моноширинный шрифт для PEM-сертификата */
.code-textarea :deep(textarea) {
  font-family: 'Courier New', Courier, monospace !important;
  font-size: 13px !important;
  line-height: 1.5 !important;
}
</style>
