<script setup>
import { ref, onMounted } from "vue";

const loading = ref(false);
const saving = ref(false);
const snackbar = ref(false);
const snackbarColor = ref("success");
const snackbarText = ref("");

const settings = ref({
  vk_bot_token: "",
  vk_confirmation_code: "",
  vk_secret_key: "",
});

const API_BASE = "/api/v1/vk";

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

onMounted(async () => {
  await loadSettings();
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
                type="password"
                prepend-inner-icon="mdi-key"
              />
            </VCol>
            
            <VCol cols="12" md="6">
              <VTextField
                v-model.trim="settings.vk_confirmation_code"
                label="Код подтверждения (Confirmation Code)"
                hint="Строка, которую возвращает сервер при подтверждении Webhook"
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
                type="password"
                prepend-inner-icon="mdi-shield-lock"
              />
            </VCol>
            
            <VCol cols="12">
              <VAlert
                type="info"
                variant="tonal"
                class="mt-4"
              >
                <strong>Webhook URL:</strong> <code>https://&lt;ваш_домен&gt;/api/v1/vk/webhook</code>
                <br />
                Укажите этот адрес в настройках Callback API вашего сообщества ВКонтакте.
              </VAlert>
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
