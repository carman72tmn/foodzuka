<script setup>
import { ref, onMounted } from "vue"

const loading = ref(false)
const saving = ref(false)
const snackbar = ref(false)
const snackbarColor = ref("success")
const snackbarText = ref("")

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const settings = ref({
  api_key: "",
  api_secret: "",
  base_url: "https://api.max-service.ru/v1",
  sender_name: "",
  default_template: "",
  is_active: false,
  bots: []
})

const botDialog = ref(false)
const editingBot = ref({
  id: null,
  bot_type: "Telegram",
  bot_name: "",
  bot_token: "",
  bot_external_id: "",
  is_active: true
})

const botTypes = ["MAX", "Telegram", "VK", "WhatsApp", "Viber"]

const loadSettings = async () => {
  loading.value = true
  try {
    const res = await fetch("/api/v1/max/settings")
    if (res.ok) {
      settings.value = await res.json()
    }
  } catch (e) {
    showMessage("Ошибка загрузки настроек", "error")
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    const res = await fetch("/api/v1/max/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings.value)
    })
    if (res.ok) {
      showMessage("Настройки сохранены")
      await loadSettings()
    } else {
      const data = await res.json()
      showMessage(data.detail || "Ошибка сохранения", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  } finally {
    saving.value = false
  }
}

const openBotDialog = (bot = null) => {
  if (bot) {
    editingBot.value = { ...bot }
  } else {
    editingBot.value = {
      id: null,
      bot_type: "Telegram",
      bot_name: "",
      bot_token: "",
      bot_external_id: "",
      is_active: true
    }
  }
  botDialog.value = true
}

const saveBot = async () => {
  const method = editingBot.value.id ? "PUT" : "POST"
  const url = editingBot.value.id 
    ? `/api/v1/max/bots/${editingBot.value.id}` 
    : "/api/v1/max/bots"
  
  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(editingBot.value)
    })
    if (res.ok) {
      showMessage(editingBot.value.id ? "Бот обновлен" : "Бот добавлен")
      botDialog.value = false
      await loadSettings()
    } else {
      const data = await res.json()
      showMessage(data.detail || "Ошибка сохранения бота", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  }
}

const deleteBot = async (botId) => {
  if (!confirm("Вы уверены, что хотите удалить этого бота?")) return
  
  try {
    const res = await fetch(`/api/v1/max/bots/${botId}`, { method: "DELETE" })
    if (res.ok) {
      showMessage("Бот удален")
      await loadSettings()
    } else {
      showMessage("Ошибка удаления бота", "error")
    }
  } catch (e) {
    showMessage("Ошибка сети", "error")
  }
}

onMounted(loadSettings)
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Настройка MAX (Интеграция)">
        <VCardText>
          <VForm @submit.prevent="saveSettings">
            <VRow>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.api_key"
                  label="API Key (MAX)"
                  placeholder="Введите ключ API"
                  persistent-placeholder
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.api_secret"
                  label="API Secret"
                  type="password"
                  placeholder="Введите секретный ключ"
                  persistent-placeholder
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.base_url"
                  label="Base URL API"
                  placeholder="https://api.max-service.ru/v1"
                />
              </VCol>
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.sender_name"
                  label="Имя отправителя"
                  placeholder="Напр. FOODTECH"
                />
              </VCol>
              <VCol cols="12">
                <VSwitch
                  v-model="settings.is_active"
                  label="Активировать интеграцию MAX"
                  color="success"
                />
              </VCol>
              <VCol cols="12">
                <VBtn
                  type="submit"
                  color="primary"
                  :loading="saving"
                >
                  Сохранить настройки
                </VBtn>
              </VCol>
            </VRow>
          </VForm>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12">
      <VCard>
        <VCardItem>
          <VCardTitle>Подключенные боты</VCardTitle>
          <template #append>
            <VBtn
              prepend-icon="bx-plus"
              size="small"
              @click="openBotDialog()"
            >
              Добавить бота
            </VBtn>
          </template>
        </VCardItem>

        <VCardText>
          <VTable v-if="settings.bots && settings.bots.length > 0">
            <thead>
              <tr>
                <th>Название</th>
                <th>Тип</th>
                <th>Статус</th>
                <th>Внешний ID</th>
                <th class="text-right">Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="bot in settings.bots" :key="bot.id">
                <td>{{ bot.bot_name }}</td>
                <td>
                  <VChip size="x-small" :color="bot.bot_type === 'Telegram' ? 'info' : 'primary'">
                    {{ bot.bot_type }}
                  </VChip>
                </td>
                <td>
                  <VIcon
                    :color="bot.is_active ? 'success' : 'error'"
                    :icon="bot.is_active ? 'bx-check-circle' : 'bx-x-circle'"
                  />
                </td>
                <td>{{ bot.bot_external_id || '-' }}</td>
                <td class="text-right">
                  <VBtn
                    icon="bx-edit"
                    variant="text"
                    size="small"
                    color="primary"
                    @click="openBotDialog(bot)"
                  />
                  <VBtn
                    icon="bx-trash"
                    variant="text"
                    size="small"
                    color="error"
                    @click="deleteBot(bot.id)"
                  />
                </td>
              </tr>
            </tbody>
          </VTable>
          <div v-else class="text-center py-4 text-muted">
            Боты еще не добавлены. Нажмите "Добавить бота", чтобы начать.
          </div>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Диалог добавления/редактирования бота -->
    <VDialog v-model="botDialog" max-width="600px">
      <VCard :title="editingBot.id ? 'Редактировать бота' : 'Добавить нового бота'">
        <VCardText>
          <VRow>
            <VCol cols="12" md="6">
              <VSelect
                v-model="editingBot.bot_type"
                :items="botTypes"
                label="Тип бота"
              />
            </VCol>
            <VCol cols="12" md="6">
              <VTextField
                v-model="editingBot.bot_name"
                label="Название бота"
                placeholder="Напр. Основной бот TG"
              />
            </VCol>
            <VCol cols="12">
              <VTextField
                v-model="editingBot.bot_token"
                label="Токен доступа"
                type="password"
              />
            </VCol>
            <VCol cols="12">
              <VTextField
                v-model="editingBot.bot_external_id"
                label="ID в системе MAX (опционально)"
              />
            </VCol>
            <VCol cols="12">
              <VSwitch
                v-model="editingBot.is_active"
                label="Бот активен"
                color="success"
              />
            </VCol>
          </VRow>
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn color="secondary" variant="tonal" @click="botDialog = false">Отмена</VBtn>
          <VBtn color="primary" @click="saveBot">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <VSnackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarText }}
    </VSnackbar>
  </VRow>
</template>
