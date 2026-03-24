<script setup>
import { ref, onMounted, computed } from "vue";

// =========================================================================
// Состояние формы
// =========================================================================

const loading = ref(false)
const saving = ref(false);
const testing = ref(false);
const snackbar = ref(false);
const snackbarColor = ref("success");
const snackbarText = ref("");

// Настройки iiko
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
});

// Справочники (загружаются из iiko)
const organizations = ref([]);
const terminalGroups = ref([]);
const paymentTypes = ref([]);
const externalMenus = ref([]);
const discountTypes = ref([]);

// Статус подключения
const connectionStatus = ref(null); // null, 'success', 'error'

const activeTab = ref("general");
const webhookLogs = ref([]);
const loadingLogs = ref(false);
const registeringWebhook = ref(false);

const API_BASE = "/api/v1/iiko";

// =========================================================================
// Методы
// =========================================================================

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
    // Настройки ещё не созданы — это нормально
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

// Тест подключения
const testConnection = async () => {
  testing.value = true;
  connectionStatus.value = null;
  try {
    const res = await fetch(`${API_BASE}/test-connection`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings.value),
    });
    const data = await res.json();
    if (data.success) {
      connectionStatus.value = "success";
      showMessage("Подключение успешно!");

      // Загружаем справочники
      if (data.organizations?.length) {
        organizations.value = data.organizations.map((o) => ({
          title: o.name || o.id,
          value: o.id,
        }));
      }
    } else {
      connectionStatus.value = "error";
      showMessage(data.error || "Ошибка подключения", "error");
    }
  } catch (e) {
    connectionStatus.value = "error";
    showMessage("Не удалось подключиться к API iiko (port 8000)", "error");
  } finally {
    testing.value = false;
  }
};

// Загрузка справочников
const loadTerminalGroups = async () => {
  try {
    const res = await fetch(`${API_BASE}/terminal-groups`);
    if (res.ok) {
      const data = await res.json();

      terminalGroups.value = data.map((t) => ({
        title: t.name || t.id,
        value: t.id,
      }));
    }
  } catch (e) {
    /* Справочник недоступен */
  }
};

const loadPaymentTypes = async () => {
  try {
    const res = await fetch(`${API_BASE}/payment-types`);
    if (res.ok) {
      const data = await res.json();

      paymentTypes.value = data.map((p) => ({
        title: `${p.name} (${p.paymentTypeKind || ""})`,
        value: p.id,
      }));
    }
  } catch (e) {
    /* Справочник недоступен */
  }
};

const loadExternalMenus = async () => {
  try {
    const res = await fetch(`${API_BASE}/external-menus`);
    if (res.ok) {
      const data = await res.json();

      externalMenus.value = data.map((m) => ({
        title: m.name || m.id,
        value: m.id,
      }));
    }
  } catch (e) {
    /* Справочник недоступен */
  }
};

const loadDiscountTypes = async () => {
  try {
    const res = await fetch(`${API_BASE}/discount-types`);
    if (res.ok) {
      const data = await res.json();

      discountTypes.value = data.map((d) => ({
        title: d.name || d.id,
        value: d.id,
      }));
    }
  } catch (e) {
    /* Справочник недоступен */
  }
};

const loadAllReferences = async () => {
  await Promise.all([
    loadTerminalGroups(),
    loadPaymentTypes(),
    loadExternalMenus(),
    loadDiscountTypes(),
  ]);
};

// Webhooks
const loadWebhookLogs = async () => {
  loadingLogs.value = true;
  try {
    const res = await fetch(`${API_BASE}/webhooks/logs?limit=20`);
    if (res.ok) {
      webhookLogs.value = await res.json();
    }
  } finally {
    loadingLogs.value = false;
  }
};

const registerWebhook = async () => {
  registeringWebhook.value = true;
  try {
    const url = new URL(`${API_BASE}/webhooks/register`);

    url.searchParams.append("webhook_url", settings.value.webhook_url);
    if (settings.value.webhook_auth_token) {
      url.searchParams.append("auth_token", settings.value.webhook_auth_token);
    }

    const res = await fetch(url, { method: "POST" });

    if (res.ok) {
      showMessage("Вебхук успешно зарегистрирован");
    } else {
      const err = await res.json();
      showMessage(err.detail || "Ошибка регистрации", "error");
    }
  } catch (e) {
    showMessage("Ошибка сети", "error");
  } finally {
    registeringWebhook.value = false;
  }
};

const autoRegisterWebhook = async () => {
  registeringWebhook.value = true;
  try {
    const res = await fetch(`${API_BASE}/webhooks/register`, { method: "POST" });

    if (res.ok) {
      const data = await res.json();
      settings.value.webhook_url = data.webhook_url;
      settings.value.webhook_auth_token = data.auth_token;
      showMessage("Вебхук автоматически зарегистрирован!");
    } else {
      const err = await res.json();
      showMessage(err.detail || "Ошибка авто-регистрации", "error");
    }
  } catch (e) {
    showMessage("Ошибка сети", "error");
  } finally {
    registeringWebhook.value = false;
  }
};

// =========================================================================
// Инициализация
// =========================================================================

onMounted(async () => {
  await loadSettings();
  if (settings.value.api_login) {
    loadAllReferences();
  }
});
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VTabs v-model="activeTab"
class="mb-4">
        <VTab value="general"> Основные настройки </VTab>
        <VTab value="webhooks"> Вебхуки </VTab>
      </VTabs>

      <VWindow v-model="activeTab">
        <VWindowItem value="general">
          <VRow>
            <!-- ==================== Подключение ==================== -->
            <VCol cols="12">
              <VCard>
                <VCardTitle class="d-flex align-center">
                  <VIcon icon="mdi-connection"
class="me-2" />
                  Подключение к iiko Cloud API
                  <VSpacer />
                  <VChip
                    v-if="connectionStatus === 'success'"
                    color="success"
                    variant="tonal"
                    prepend-icon="mdi-check-circle"
                  >
                    Подключено
                  </VChip>
                  <VChip
                    v-if="connectionStatus === 'error'"
                    color="error"
                    variant="tonal"
                    prepend-icon="mdi-alert-circle"
                  >
                    Ошибка
                  </VChip>
                </VCardTitle>
                <VCardText>
                  <VRow>
                    <VCol cols="12"
md="8">
                      <VTextField
                        v-model.trim="settings.api_login"
                        label="API Login (Cloud API Key)"
                        hint="Ключ из iiko Cloud → Интеграции → API"
                        persistent-hint
                        type="password"
                        prepend-inner-icon="mdi-key"
                      />
                    </VCol>
                    <VCol cols="12"
md="4" class="d-flex align-center">
                      <VBtn
                        color="primary"
                        variant="elevated"
                        :loading="testing"
                        :disabled="!settings.api_login"
                        prepend-icon="mdi-lan-check"
                        @click="testConnection"
                      >
                        Проверить подключение
                      </VBtn>
                    </VCol>
                  </VRow>
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Организация ==================== -->
            <VCol cols="12"
md="6">
              <VCard>
                <VCardTitle>
                  <VIcon icon="mdi-office-building"
class="me-2" />
                  Организация
                </VCardTitle>
                <VCardText>
                  <VSelect
                    v-model="settings.organization_id"
                    :items="organizations"
                    label="Организация"
                    hint="Выберите организацию после проверки подключения"
                    persistent-hint
                    clearable
                  />
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Терминальная группа ==================== -->
            <VCol cols="12"
md="6">
              <VCard>
                <VCardTitle>
                  <VIcon icon="mdi-monitor"
class="me-2" />
                  Терминальная группа
                </VCardTitle>
                <VCardText>
                  <VSelect
                    v-model="settings.terminal_group_id"
                    :items="terminalGroups"
                    label="Терминальная группа"
                    hint="Группа касс для приёма заказов"
                    persistent-hint
                    clearable
                  />
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Внешнее меню ==================== -->
            <VCol cols="12"
md="6">
              <VCard>
                <VCardTitle>
                  <VIcon icon="mdi-food"
class="me-2" />
                  Внешнее меню
                </VCardTitle>
                <VCardText>
                  <VSelect
                    v-model="settings.external_menu_id"
                    :items="externalMenus"
                    label="Источник меню"
                    hint="Настраивается в iiko Web → Внешние меню"
                    persistent-hint
                    clearable
                  />
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Скидки ==================== -->
            <VCol cols="12"
md="6">
              <VCard>
                <VCardTitle>
                  <VIcon icon="mdi-percent"
class="me-2" />
                  Скидка
                </VCardTitle>
                <VCardText>
                  <VSelect
                    v-model="settings.discount_id"
                    :items="discountTypes"
                    label="Универсальная скидка"
                    hint="Скидка для передачи промокодов в iiko"
                    persistent-hint
                    clearable
                  />
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Типы оплаты ==================== -->
            <VCol cols="12">
              <VCard>
                <VCardTitle>
                  <VIcon icon="mdi-credit-card"
class="me-2" />
                  Типы оплаты
                </VCardTitle>
                <VCardText>
                  <VRow>
                    <VCol cols="12"
md="3">
                      <VSelect
                        v-model="settings.payment_type_cash"
                        :items="paymentTypes"
                        label="Наличные"
                        clearable
                      />
                    </VCol>
                    <VCol cols="12"
md="3">
                      <VSelect
                        v-model="settings.payment_type_card"
                        :items="paymentTypes"
                        label="Карта"
                        clearable
                      />
                    </VCol>
                    <VCol cols="12"
md="3">
                      <VSelect
                        v-model="settings.payment_type_online"
                        :items="paymentTypes"
                        label="Онлайн оплата"
                        clearable
                      />
                    </VCol>
                    <VCol cols="12"
md="3">
                      <VSelect
                        v-model="settings.payment_type_bonus"
                        :items="paymentTypes"
                        label="Бонусы / баллы"
                        clearable
                      />
                    </VCol>
                  </VRow>
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Бонусная программа ==================== -->
            <VCol cols="12"
md="6">
              <VCard>
                <VCardTitle>
                  <VIcon icon="mdi-star"
class="me-2" />
                  Бонусная программа
                </VCardTitle>
                <VCardText>
                  <VSlider
                    v-model="settings.bonus_limit_percent"
                    label="Лимит списания баллов (%)"
                    :min="0"
                    :max="100"
                    :step="5"
                    thumb-label="always"
                    class="mb-4"
                  />
                  <p class="text-caption text-medium-emphasis">
                    Максимальный процент от суммы заказа, который можно оплатить
                    бонусными баллами. 0 = без ограничений.
                  </p>
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Флаги ==================== -->
            <VCol cols="12"
md="6">
              <VCard>
                <VCardTitle>
                  <VIcon icon="mdi-toggle-switch"
class="me-2" />
                  Опции
                </VCardTitle>
                <VCardText>
                  <VSwitch
                    v-model="settings.no_pass_promo"
                    label="Не передавать промокоды в iiko"
                    color="primary"
                    class="mb-2"
                  />
                  <VSwitch
                    v-model="settings.no_use_bonus"
                    label="Не использовать оплату бонусами"
                    color="primary"
                    class="mb-2"
                  />
                  <VSwitch
                    v-model="settings.no_use_iiko_promo"
                    label="Не использовать промокоды из iiko"
                    color="primary"
                  />
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Резервные каналы ==================== -->
            <VCol cols="12">
              <VCard>
                <VCardTitle>
                  <VIcon icon="mdi-alert"
class="me-2" />
                  Резервные каналы при ошибке отправки заказа
                </VCardTitle>
                <VCardText>
                  <VRow>
                    <VCol cols="12"
md="6">
                      <VTextField
                        v-model="settings.fallback_email"
                        label="Email для уведомлений"
                        prepend-inner-icon="mdi-email"
                        type="email"
                      />
                    </VCol>
                    <VCol cols="12"
md="6">
                      <VTextField
                        v-model="settings.fallback_telegram_id"
                        label="Telegram ID для уведомлений"
                        prepend-inner-icon="mdi-send"
                      />
                    </VCol>
                  </VRow>
                </VCardText>
              </VCard>
            </VCol>

            <!-- ==================== Кнопки ==================== -->
            <VCol cols="12"
class="d-flex gap-4">
              <VBtn
                color="primary"
                size="large"
                :loading="saving"
                prepend-icon="mdi-content-save"
                @click="saveSettings"
              >
                Сохранить настройки
              </VBtn>
              <VBtn
                color="secondary"
                size="large"
                variant="outlined"
                prepend-icon="mdi-refresh"
                @click="loadAllReferences"
              >
                Обновить справочники
              </VBtn>
            </VCol>
          </VRow>
        </VWindowItem>

        <VWindowItem value="webhooks">
          <VCard class="mb-4">
            <VCardTitle>Настройки Webhook</VCardTitle>
            <VCardText>
              <VRow>
                <VCol cols="12"
md="8">
                  <VTextField
                    v-model="settings.webhook_url"
                    label="Webhook URL"
                    hint="Адрес, на который iiko будет отправлять уведомления"
                    persistent-hint
                  />
                </VCol>
                <VCol cols="12"
md="4">
                  <VTextField
                    v-model="settings.webhook_auth_token"
                    label="Auth Token"
                    hint="Токен для защиты (Authorization header)"
                    persistent-hint
                  />
                </VCol>
                <VCol cols="12">
                  <VBtn
                    color="primary"
                    :loading="registeringWebhook"
                    prepend-icon="mdi-webhook"
                    @click="registerWebhook"
                  >
                    Зарегистрировать вручную
                  </VBtn>
                  <VBtn
                    color="success"
                    variant="elevated"
                    class="ms-2"
                    :loading="registeringWebhook"
                    prepend-icon="mdi-auto-fix"
                    @click="autoRegisterWebhook"
                  >
                    Авто-генератор вебхука
                  </VBtn>
                  <VBtn
                    variant="outlined"
                    class="ms-2"
                    @click="loadWebhookLogs"
                  >
                    Обновить логи
                  </VBtn>
                </VCol>
              </VRow>
            </VCardText>
          </VCard>

          <VCard title="Журнал событий">
            <VTable>
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Тип</th>
                  <th>Payload</th>
                  <th>Статус</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in webhookLogs"
:key="log.id">
                  <td>{{ new Date(log.created_at).toLocaleString() }}</td>
                  <td>{{ log.event_type }}</td>
                  <td>
                    <pre
                      style="font-size: 10px; max-height: 100px; overflow: auto"
                      >{{ JSON.stringify(log.payload, null, 2) }}</pre
                    >
                  </td>
                  <td>
                    <VChip
                      :color="log.processed ? 'success' : 'warning'"
                      size="small"
                    >
                      {{ log.processed ? "Processed" : "Received" }}
                    </VChip>
                  </td>
                </tr>
                <tr v-if="webhookLogs.length === 0">
                  <td colspan="4"
class="text-center text-disabled">
                    Нет событий
                  </td>
                </tr>
              </tbody>
            </VTable>
          </VCard>
        </VWindowItem>
      </VWindow>
    </VCol>
  </VRow>

  <!-- ==================== Snackbar ==================== -->
  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="3000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>
