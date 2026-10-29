<script setup>
import { ref, onMounted } from "vue"

const loading = ref(false)
const saving = ref(false)
const testingBot = ref(false)
const testingChannel = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const activeTab = ref("bot")

const settings = ref({
  is_bot_active: false,
  telegram_bot_token: "",
  bot_username: "",
  system_channel_id: "",
  is_system_notifications_active: false,
  is_client_broadcast_active: false,
  is_user_client_active: false,
  user_phone: "",
  user_api_id: "",
  user_api_hash: "",
  user_account_status: "not_connected",
  welcome_message: "Добро пожаловать в службу доставки!",
})

const API_BASE = "/api/v1/bot"

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const getAuthHeaders = () => {
  const token = localStorage.getItem("accessToken")
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }
}

// Загрузка текущих настроек
const loadSettings = async () => {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/settings`, { headers: getAuthHeaders() })
    if (res.ok) {
      const data = await res.json()
      Object.keys(settings.value).forEach((key) => {
        if (data[key] !== undefined && data[key] !== null) {
          settings.value[key] = data[key]
        }
      })
    }
  } catch (e) {
    showMessage("Ошибка загрузки настроек", "error")
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
      headers: getAuthHeaders(),
      body: JSON.stringify(settings.value),
    })

    if (res.ok) {
      const saved = await res.json()
      showMessage("Настройки Telegram успешно сохранены")
      if (saved.bot_username) {
        settings.value.bot_username = saved.bot_username
      }
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

// Быстрое переключение свитча
const toggleChannelState = async (field, value) => {
  try {
    const res = await fetch(`${API_BASE}/toggle-channel`, {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify({ field, value })
    })
    if (res.ok) {
      showMessage(value ? "Канал успешно включен" : "Канал отключен (запросы остановлены)", "info")
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка переключения", "error")
      // откат в UI
      settings.value[field] = !value
    }
  } catch (e) {
    settings.value[field] = !value
    showMessage("Ошибка сети при переключении", "error")
  }
}

// Тестирование подключения бота
const testBotConnection = async () => {
  testingBot.value = true
  try {
    const res = await fetch(`${API_BASE}/test-connection`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ token: settings.value.telegram_bot_token })
    })

    if (res.ok) {
      const data = await res.json()
      showMessage(data.message, "success")
      if (data.bot?.username) {
        settings.value.bot_username = data.bot.username
      }
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка проверки бота", "error")
    }
  } catch (e) {
    showMessage("Сетевая ошибка при проверке", "error")
  } finally {
    testingBot.value = false
  }
}

// Тестирование системного канала
const testSystemChannel = async () => {
  if (!settings.value.system_channel_id) {
    showMessage("Укажите ID канала или чата для проверки", "warning")
    return
  }
  testingChannel.value = true
  try {
    const res = await fetch(`${API_BASE}/test-channel`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        chat_id: settings.value.system_channel_id,
        message: "🔔 <b>Тест уведомлений</b>: Канал успешно подключен к панели управления Vezuroll!"
      })
    })

    if (res.ok) {
      const data = await res.json()
      showMessage(data.message, "success")
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка отправки в канал", "error")
    }
  } catch (e) {
    showMessage("Сетевая ошибка при отправке в канал", "error")
  } finally {
    testingChannel.value = false
  }
}

onMounted(async () => {
  await loadSettings()
})
</script>

<template>
  <VRow>
    <!-- Заголовок страницы -->
    <VCol cols="12" class="d-flex align-center justify-space-between flex-wrap gap-4 pb-2">
      <div>
        <h4 class="text-h4 font-weight-bold d-flex align-center">
          <VIcon icon="ri-telegram-fill" color="#0088cc" class="me-2" size="32" />
          Интеграция Telegram
        </h4>
        <div class="text-caption text-medium-emphasis">
          Управление ботом, личным аккаунтом для рассылок по номеру и системными каналами оповещений
        </div>
      </div>

      <div class="d-flex align-center gap-2">
        <VBtn
          color="primary"
          prepend-icon="bx-save"
          :loading="saving"
          @click="saveSettings"
        >
          Сохранить настройки
        </VBtn>
      </div>
    </VCol>

    <!-- Сводные индикаторы активности -->
    <VCol cols="12" md="4">
      <VCard variant="outlined" :color="settings.is_bot_active ? 'success' : 'default'">
        <VCardText class="d-flex align-center justify-space-between py-3">
          <div class="d-flex align-center">
            <VAvatar size="40" :color="settings.is_bot_active ? 'success' : 'grey-lighten-2'" class="me-3">
              <VIcon icon="bx-bot" size="24" :color="settings.is_bot_active ? 'white' : 'grey'" />
            </VAvatar>
            <div>
              <div class="font-weight-medium">Telegram Бот</div>
              <div class="text-caption">
                {{ settings.is_bot_active ? (settings.bot_username ? '@' + settings.bot_username : 'Активен') : 'Отключен' }}
              </div>
            </div>
          </div>
          <VSwitch
            v-model="settings.is_bot_active"
            color="success"
            hide-details
            density="compact"
            @update:model-value="toggleChannelState('is_bot_active', $event)"
          />
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12" md="4">
      <VCard variant="outlined" :color="settings.is_system_notifications_active ? 'info' : 'default'">
        <VCardText class="d-flex align-center justify-space-between py-3">
          <div class="d-flex align-center">
            <VAvatar size="40" :color="settings.is_system_notifications_active ? 'info' : 'grey-lighten-2'" class="me-3">
              <VIcon icon="bx-broadcast" size="24" :color="settings.is_system_notifications_active ? 'white' : 'grey'" />
            </VAvatar>
            <div>
              <div class="font-weight-medium">Системный Канал</div>
              <div class="text-caption">
                {{ settings.is_system_notifications_active ? (settings.system_channel_id || 'Включен') : 'Оповещения выкл' }}
              </div>
            </div>
          </div>
          <VSwitch
            v-model="settings.is_system_notifications_active"
            color="info"
            hide-details
            density="compact"
            @update:model-value="toggleChannelState('is_system_notifications_active', $event)"
          />
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12" md="4">
      <VCard variant="outlined" :color="settings.is_user_client_active ? 'warning' : 'default'">
        <VCardText class="d-flex align-center justify-space-between py-3">
          <div class="d-flex align-center">
            <VAvatar size="40" :color="settings.is_user_client_active ? 'warning' : 'grey-lighten-2'" class="me-3">
              <VIcon icon="bx-user-voice" size="24" :color="settings.is_user_client_active ? 'white' : 'grey'" />
            </VAvatar>
            <div>
              <div class="font-weight-medium">Личный Номер</div>
              <div class="text-caption">
                {{ settings.is_user_client_active ? (settings.user_phone || 'Активен') : 'Отправка выкл' }}
              </div>
            </div>
          </div>
          <VSwitch
            v-model="settings.is_user_client_active"
            color="warning"
            hide-details
            density="compact"
            @update:model-value="toggleChannelState('is_user_client_active', $event)"
          />
        </VCardText>
      </VCard>
    </VCol>

    <!-- Основные разделы настроек -->
    <VCol cols="12">
      <VCard>
        <VTabs v-model="activeTab" bg-color="surface">
          <VTab value="bot">
            <VIcon icon="bx-bot" class="me-2" />
            Официальный Бот и Канал
          </VTab>
          <VTab value="user_client">
            <VIcon icon="bx-phone-call" class="me-2" />
            Рассылка с личного номера
          </VTab>
          <VTab value="policy">
            <VIcon icon="bx-slider-alt" class="me-2" />
            Управление нагрузкой
          </VTab>
        </VTabs>

        <VDivider />

        <VCardText>
          <VWindow v-model="activeTab">
            <!-- TAB 1: Telegram Bot -->
            <VWindowItem value="bot">
              <VRow>
                <VCol cols="12">
                  <VAlert
                    type="info"
                    variant="tonal"
                    icon="bx-info-circle"
                    class="mb-4"
                  >
                    Бот используется для служебных команд, регистрации гостей и отправки системных статусов заказов в ваш канал.
                    Пока бот отключен переключателем выше, система не делает фоновых запросов к Telegram.
                  </VAlert>
                </VCol>

                <VCol cols="12" md="8">
                  <VTextField
                    v-model.trim="settings.telegram_bot_token"
                    label="Telegram Bot Token"
                    hint="Токен, выданный @BotFather вида 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                    persistent-hint
                    type="password"
                    prepend-inner-icon="bx-key"
                  />
                </VCol>

                <VCol cols="12" md="4" class="d-flex align-center">
                  <VBtn
                    variant="tonal"
                    color="primary"
                    prepend-icon="bx-check-shield"
                    :loading="testingBot"
                    @click="testBotConnection"
                  >
                    Проверить соединение
                  </VBtn>
                </VCol>

                <VCol cols="12" md="6">
                  <VTextField
                    v-model.trim="settings.bot_username"
                    label="Юзернейм бота"
                    prefix="@"
                    placeholder="my_company_delivery_bot"
                    hint="Определяется автоматически при проверке токена"
                    persistent-hint
                    prepend-inner-icon="bx-at"
                  />
                </VCol>

                <VCol cols="12" md="6">
                  <VTextField
                    v-model.trim="settings.system_channel_id"
                    label="ID или @канал для системных рассылок"
                    placeholder="@delivery_orders_chat или -100123456789"
                    hint="Канал/чат для уведомлений сотрудников о новых заказах и статусах"
                    persistent-hint
                    prepend-inner-icon="bx-chat"
                  >
                    <template #append-inner>
                      <VBtn
                        size="x-small"
                        variant="text"
                        color="primary"
                        :loading="testingChannel"
                        @click="testSystemChannel"
                      >
                        Тест
                      </VBtn>
                    </template>
                  </VTextField>
                </VCol>

                <VCol cols="12">
                  <VTextarea
                    v-model="settings.welcome_message"
                    label="Приветственное сообщение для гостей"
                    hint="Текст, который увидит клиент при старте диалога с ботом"
                    persistent-hint
                    rows="3"
                    prepend-inner-icon="bx-message-detail"
                  />
                </VCol>
              </VRow>
            </VWindowItem>

            <!-- TAB 2: Личный аккаунт Telegram (Отправка с номера) -->
            <VWindowItem value="user_client">
              <VRow>
                <VCol cols="12">
                  <VAlert
                    type="warning"
                    variant="tonal"
                    icon="bx-shield-quarter"
                    class="mb-4"
                  >
                    <strong>Рассылка с личного номера Telegram</strong> позволяет отправлять сообщения напрямую клиентам от имени живого человека или номера службы заботы.
                    Для работы потребуются API ID и API Hash, полученные на официальном портале
                    <a href="https://my.telegram.org" target="_blank" rel="noopener noreferrer" class="text-decoration-underline font-weight-bold">my.telegram.org</a>.
                  </VAlert>
                </VCol>

                <VCol cols="12" md="4">
                  <VTextField
                    v-model.trim="settings.user_phone"
                    label="Номер телефона аккаунта"
                    placeholder="+79991234567"
                    hint="Номер, привязанный к аккаунту Telegram"
                    persistent-hint
                    prepend-inner-icon="bx-phone"
                  />
                </VCol>

                <VCol cols="12" md="4">
                  <VTextField
                    v-model.trim="settings.user_api_id"
                    label="API ID (App ID)"
                    placeholder="12345678"
                    hint="Получите на my.telegram.org -> API development tools"
                    persistent-hint
                    prepend-inner-icon="bx-code-alt"
                  />
                </VCol>

                <VCol cols="12" md="4">
                  <VTextField
                    v-model.trim="settings.user_api_hash"
                    label="API Hash"
                    placeholder="0123456789abcdef0123456789abcdef"
                    hint="Секретный хэш вашего приложения"
                    persistent-hint
                    type="password"
                    prepend-inner-icon="bx-lock-alt"
                  />
                </VCol>

                <VCol cols="12" class="pt-2">
                  <VCard variant="tonal" color="surface" class="pa-4">
                    <div class="d-flex align-center justify-space-between flex-wrap gap-4">
                      <div>
                        <div class="font-weight-bold mb-1">Статус авторизации личного номера</div>
                        <div class="text-caption text-medium-emphasis">
                          {{ settings.is_user_client_active ? 'Канал активен и готов к отправке' : 'Канал отключен — запросы не отправляются' }}
                        </div>
                      </div>

                      <div class="d-flex align-center gap-3">
                        <VChip
                          :color="settings.user_account_status === 'connected' ? 'success' : 'default'"
                          size="small"
                        >
                          {{ settings.user_account_status === 'connected' ? 'Подключен' : 'Не авторизован' }}
                        </VChip>

                        <VBtn
                          variant="tonal"
                          color="warning"
                          size="small"
                          prepend-icon="bx-log-in-circle"
                          :disabled="!settings.user_phone || !settings.user_api_id"
                          @click="showMessage('Параметры сохранены. Для первичного входа используйте код подтверждения в Telegram', 'info')"
                        >
                          Подключить сессию
                        </VBtn>
                      </div>
                    </div>
                  </VCard>
                </VCol>
              </VRow>
            </VWindowItem>

            <!-- TAB 3: Управление нагрузкой и политиками -->
            <VWindowItem value="policy">
              <VRow>
                <VCol cols="12">
                  <VAlert
                    type="success"
                    variant="tonal"
                    icon="bx-check-circle"
                    class="mb-4"
                  >
                    Здесь вы можете гибко включать и отключать типы рассылок. Если канал не заполнен или отключен — фоновые планировщики мгновенно пропускают отправку без таймаутов и задержек.
                  </VAlert>
                </VCol>

                <VCol cols="12" md="6">
                  <VCard variant="outlined" class="pa-4">
                    <div class="d-flex justify-space-between align-center mb-2">
                      <div class="font-weight-bold">Системные уведомления в Telegram</div>
                      <VSwitch
                        v-model="settings.is_system_notifications_active"
                        color="primary"
                        hide-details
                        density="compact"
                        @update:model-value="toggleChannelState('is_system_notifications_active', $event)"
                      />
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Автоматическая отправка новых заказов, статусов оплат и отчетов в системный канал.
                    </div>
                  </VCard>
                </VCol>

                <VCol cols="12" md="6">
                  <VCard variant="outlined" class="pa-4">
                    <div class="d-flex justify-space-between align-center mb-2">
                      <div class="font-weight-bold">Рассылки клиентам через Telegram</div>
                      <VSwitch
                        v-model="settings.is_client_broadcast_active"
                        color="success"
                        hide-details
                        density="compact"
                        @update:model-value="toggleChannelState('is_client_broadcast_active', $event)"
                      />
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Разрешить каскадным рассылкам и маркетинговым воронкам использовать Telegram в качестве канала доставки.
                    </div>
                  </VCard>
                </VCol>
              </VRow>
            </VWindowItem>
          </VWindow>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="3500"
    location="bottom end"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>
