<script setup>
import { ref, onMounted } from "vue"

const loading = ref(false)
const saving = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const settings = ref({
  telegram_bot_token: "",
  welcome_message: "",
})

const API_BASE = "/api/v1/bot"

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

onMounted(async () => {
  await loadSettings()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon icon="mdi-telegram" class="me-2" color="#24A1DE" />
          Настройки Telegram Бота
        </VCardTitle>
        <VCardText>
          <VRow>
            <VCol cols="12">
              <VTextField
                v-model.trim="settings.telegram_bot_token"
                label="Telegram Bot Token"
                hint="Токен, полученный от @BotFather"
                persistent-hint
                type="password"
                prepend-inner-icon="mdi-key"
              />
            </VCol>
            
            <VCol cols="12">
              <VTextarea
                v-model="settings.welcome_message"
                label="Приветственное сообщение"
                hint="Сообщение, которое увидит пользователь при первом запуске бота"
                persistent-hint
                rows="3"
                prepend-inner-icon="mdi-message-text-outline"
              />
            </VCol>

            <VCol cols="12" class="d-flex gap-4 mt-2">
              <VBtn
                color="primary"
                size="large"
                :loading="saving"
                prepend-icon="mdi-content-save"
                @click="saveSettings"
              >
                Сохранить настройки
              </VBtn>
            </VCol>
          </VRow>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- Snackbar -->
  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="3000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>
