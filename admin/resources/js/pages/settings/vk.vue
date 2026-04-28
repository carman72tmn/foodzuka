<script setup>
import { ref, onMounted, computed } from "vue";

const loading = ref(false);
const saving = ref(false);
const testingBot = ref(false);
const snackbar = ref(false);
const snackbarColor = ref("success");
const snackbarText = ref("");
const logs = ref([]);
const loadingLogs = ref(false);

const settings = ref({
  vk_bot_token: "",
  vk_confirmation_code: "",
  vk_group_id: "",
  vk_secret_key: "",
});

const API_BASE = "/api/v1/vk";

const webhookUrl = computed(() => {
  const origin = window.location.origin;
  return `${origin}/api/v1/vk/webhook`;
});

const showMessage = (text, color = "success") => {
  snackbarText.value = text;
  snackbarColor.value = color;
  snackbar.value = true;
};

// Загрузка текущих настроек
const loadSettings = async () => {
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/settings`);
    if (res.ok) {
      const data = await res.json();
      Object.keys(settings.value).forEach((key) => {
        if (data[key] !== undefined && data[key] !== null) {
          settings.value[key] = data[key];
        }
      });
    }
  } catch (e) {
    showMessage("Ошибка загрузки настроек", "error");
  } finally {
    loading.value = false;
  }
};

// Сохранение настроек
const saveSettings = async () => {
  saving.value = true;
  try {
    const res = await fetch(`${API_BASE}/settings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings.value),
    });

    if (res.ok) {
      showMessage("Настройки успешно сохранены");
      await loadLogs();
    } else {
      const err = await res.json();
      showMessage(err.detail || "Ошибка сохранения", "error");
    }
  } catch (e) {
    showMessage("Ошибка подключения к серверу", "error");
  } finally {
    saving.value = false;
  }
};

// Проверка соединения с ботом
const testBotConnection = async () => {
  testingBot.value = true;
  try {
    const res = await fetch(`${API_BASE}/test-connection`);
    const data = await res.json();
    
    if (data.status === "success") {
      showMessage(data.message, "success");
    } else {
      showMessage(data.message || "Ошибка проверки", "error");
    }
  } catch (e) {
    showMessage("Ошибка при проверке соединения", "error");
  } finally {
    testingBot.value = false;
  }
};

// Загрузка логов
const loadLogs = async () => {
  loadingLogs.value = true;
  try {
    const res = await fetch(`${API_BASE}/logs`);
    if (res.ok) {
      logs.value = await res.json();
    }
  } catch (e) {
    console.error("Ошибка загрузки логов VK:", e);
  } finally {
    loadingLogs.value = false;
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleString("ru-RU");
};

onMounted(async () => {
  await loadSettings();
  await loadLogs();
});
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon icon="mdi-vk" class="me-2" color="#0077FF" />
          Настройки интеграции VK Бота
        </VCardTitle>
        <VCardText>
          <VRow>
            <VCol cols="12" md="8">
              <VTextField
                v-model.trim="settings.vk_bot_token"
                label="VK Bot Token"
                hint="Токен доступа сообщества (с правами на сообщения)"
                persistent-hint
                type="text"
                prepend-inner-icon="mdi-key"
              />
            </VCol>
            
            <VCol cols="12" md="6">
              <VTextField
                v-model.trim="settings.vk_group_id"
                label="ID сообщества (Group ID)"
                hint="Числовой ID группы ВК (например, 186688777)"
                persistent-hint
                prepend-inner-icon="mdi-account-group"
              />
            </VCol>

            <VCol cols="12" md="6">
              <VTextField
                v-model.trim="settings.vk_confirmation_code"
                label="Строка, которую должен вернуть сервер"
                hint="Используется для подтверждения Callback API (событие confirmation)"
                persistent-hint
                prepend-inner-icon="mdi-check"
              />
            </VCol>

            <VCol cols="12" md="6">
              <VTextField
                v-model.trim="settings.vk_secret_key"
                label="Секретный ключ (Secret Key)"
                hint="Добавьте этот же секретный ключ в настройки Callback API ВКонтакте"
                persistent-hint
                type="text"
                prepend-inner-icon="mdi-shield-lock"
              />
            </VCol>
            
            <VCol cols="12">
              <VAlert
                type="info"
                variant="tonal"
                class="mt-4"
              >
                <strong>Webhook URL:</strong> <code>{{ webhookUrl }}</code>
                <br />
                Укажите этот адрес в настройках Callback API вашего сообщества ВКонтакте.
              </VAlert>
            </VCol>

            <VCol cols="12" class="d-flex flex-wrap gap-4 mt-2">
              <VBtn
                color="primary"
                :loading="saving"
                prepend-icon="mdi-content-save"
                @click="saveSettings"
              >
                Сохранить настройки
              </VBtn>

              <VBtn
                color="info"
                variant="outlined"
                :loading="testingBot"
                prepend-icon="mdi-robot"
                @click="testBotConnection"
              >
                Проверить бота
              </VBtn>

              <VBtn
                color="secondary"
                variant="tonal"
                prepend-icon="mdi-refresh"
                @click="loadLogs"
              >
                Обновить логи
              </VBtn>
            </VCol>
          </VRow>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Таблица логов -->
    <VCol cols="12">
      <VCard>
        <VCardTitle class="d-flex align-center">
          <VIcon icon="mdi-history" class="me-2" />
          Последние события VK API
        </VCardTitle>
        <VCardText>
          <VTable density="compact" class="text-no-wrap">
            <thead>
              <tr>
                <th class="text-uppercase">ID</th>
                <th class="text-uppercase">Тип события</th>
                <th class="text-uppercase">Дата</th>
                <th class="text-uppercase">Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loadingLogs">
                <td colspan="4" class="text-center py-4">Загрузка...</td>
              </tr>
              <tr v-else-if="logs.length === 0">
                <td colspan="4" class="text-center py-4">Событий пока нет</td>
              </tr>
              <tr v-for="log in logs" :key="log.id">
                <td>{{ log.id }}</td>
                <td>
                  <VChip size="small" :color="log.event_type === 'confirmation' ? 'info' : 'success'">
                    {{ log.event_type }}
                  </VChip>
                </td>
                <td>{{ formatDate(log.created_at) }}</td>
                <td>
                  <VBtn icon size="x-small" variant="text" @click="console.log(log.payload)">
                    <VIcon icon="mdi-eye" />
                    <VTooltip activator="parent">Посмотреть Payload в консоли</VTooltip>
                  </VBtn>
                </td>
              </tr>
            </tbody>
          </VTable>
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
