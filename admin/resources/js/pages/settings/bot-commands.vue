<script setup>
import { ref, onMounted } from "vue"

const API_BASE = "/api/v1/bot-commands"
const commands = ref([])
const loading = ref(false)
const saving = ref(false)
const deletingId = ref(null)

const snackbar = ref(false)
const snackbarText = ref("")
const snackbarColor = ref("success")

const showMessage = (text, color = "success") => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const showDialog = ref(false)
const isEdit = ref(false)

const defaultForm = {
  id: null,
  name: "",
  trigger_phrase: "",
  action_type: "get_balance",
  channels: ["vk", "telegram"],
  is_active: true,
  response_text: "",
  request_phone_text: "Ваш аккаунт не привязан к номеру телефона. Пожалуйста, отправьте ваш номер телефона (в формате 7**********) для привязки к карте гостя.",
  phone_not_found_text: "К сожалению, данный номер в базе не определен.",
  register_confirm_text: "Хотите зарегистрироваться в нашей бонусной системе? Ответьте Да или Нет.",
  register_success_text: "Вы успешно зарегистрированы в нашей бонусной системе! Ваш бонусный баланс: {balance} бонусов.",
  balance_text: "Ваш бонусный баланс: {balance} бонусов."
}

const form = ref({ ...defaultForm })

const loadCommands = async () => {
  loading.value = true
  try {
    const res = await fetch(API_BASE)
    if (res.ok) {
      commands.value = await res.json()
    } else {
      showMessage("Ошибка при загрузке команд", "error")
    }
  } catch (e) {
    showMessage("Ошибка подключения к серверу", "error")
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  isEdit.value = false
  form.value = { ...defaultForm, channels: ["vk", "telegram"] }
  showDialog.value = true
}

const openEditDialog = (cmd) => {
  isEdit.value = true
  form.value = { ...cmd }
  // Убедимся, что channels это массив
  if (!Array.isArray(form.value.channels)) {
    form.value.channels = []
  }
  showDialog.value = true
}

const saveCommand = async () => {
  if (!form.value.name || !form.value.trigger_phrase) {
    showMessage("Заполните название и триггерную фразу", "warning")
    return
  }

  saving.value = true
  try {
    const url = isEdit.value ? `${API_BASE}/${form.value.id}` : API_BASE
    const method = isEdit.value ? "PUT" : "POST"

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form.value),
    })

    if (res.ok) {
      showMessage(isEdit.value ? "Команда обновлена" : "Команда создана")
      showDialog.value = false
      await loadCommands()
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

const deleteCommand = async (id) => {
  if (id === 100) {
    showMessage("Нельзя удалить системную команду", "error")
    return
  }
  if (!confirm("Вы уверены, что хотите удалить эту команду?")) {
    return
  }

  deletingId.value = id
  try {
    const res = await fetch(`${API_BASE}/${id}`, {
      method: "DELETE",
    })

    if (res.ok) {
      showMessage("Команда успешно удалена")
      await loadCommands()
    } else {
      const err = await res.json()
      showMessage(err.detail || "Ошибка удаления", "error")
    }
  } catch (e) {
    showMessage("Ошибка подключения к серверу", "error")
  } finally {
    deletingId.value = null
  }
}

const toggleStatus = async (cmd) => {
  try {
    const updated = { ...cmd, is_active: !cmd.is_active }
    const res = await fetch(`${API_BASE}/${cmd.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    })

    if (res.ok) {
      cmd.is_active = updated.is_active
      showMessage(cmd.is_active ? "Команда включена" : "Команда отключена")
    } else {
      showMessage("Не удалось изменить статус", "error")
    }
  } catch (e) {
    showMessage("Ошибка подключения к серверу", "error")
  }
}

onMounted(() => {
  loadCommands()
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard class="glass-card">
        <VCardTitle class="d-flex justify-between align-center py-4">
          <div class="d-flex align-center">
            <VIcon icon="bx-bot" class="me-2" color="primary" />
            <span>Команды ботов (Автоответы и FSM)</span>
          </div>
          <VBtn
            color="primary"
            prepend-icon="bx-plus"
            @click="openCreateDialog"
          >
            Создать команду
          </VBtn>
        </VCardTitle>

        <VCardText class="mt-2">
          <VTable class="text-no-wrap">
            <thead>
              <tr>
                <th class="text-uppercase text-xs font-semibold">ID</th>
                <th class="text-uppercase text-xs font-semibold">Название</th>
                <th class="text-uppercase text-xs font-semibold">Триггерная фраза</th>
                <th class="text-uppercase text-xs font-semibold">Действие</th>
                <th class="text-uppercase text-xs font-semibold text-center">Соцсети</th>
                <th class="text-uppercase text-xs font-semibold text-center">Статус</th>
                <th class="text-uppercase text-xs font-semibold text-center">Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="7" class="text-center py-4">
                  <VProgressCircular indeterminate color="primary" />
                </td>
              </tr>
              <tr v-else-if="commands.length === 0">
                <td colspan="7" class="text-center py-4 text-muted">
                  Команды не настроены. Создайте первую команду.
                </td>
              </tr>
              <tr v-for="cmd in commands" :key="cmd.id">
                <td>
                  <VChip size="small" variant="flat" color="secondary">{{ cmd.id }}</VChip>
                </td>
                <td class="font-medium">{{ cmd.name }}</td>
                <td>
                  <code>{{ cmd.trigger_phrase }}</code>
                </td>
                <td>
                  <VChip
                    size="small"
                    :color="cmd.action_type === 'get_balance' ? 'success' : (cmd.action_type === 'transfer_points' ? 'primary' : (cmd.action_type === 'unlink_phone' ? 'warning' : 'info'))"
                    variant="tonal"
                  >
                    {{ cmd.action_type === 'get_balance' ? 'Баланс бонусов' : (cmd.action_type === 'transfer_points' ? 'Перевести баллы' : (cmd.action_type === 'unlink_phone' ? 'Отвязать телефон' : 'Текст')) }}
                  </VChip>
                </td>
                <td class="text-center">
                  <div class="d-flex justify-center gap-1">
                    <VIcon
                      v-if="cmd.channels.includes('vk')"
                      icon="mdi-vk"
                      color="#0077FF"
                      title="ВКонтакте"
                    />
                    <VIcon
                      v-if="cmd.channels.includes('telegram')"
                      icon="mdi-telegram"
                      color="#229ED9"
                      title="Telegram"
                    />
                    <VIcon
                      v-if="cmd.channels.includes('whatsapp')"
                      icon="mdi-whatsapp"
                      color="#25D366"
                      title="WhatsApp"
                    />
                    <VIcon
                      v-if="cmd.channels.includes('max')"
                      icon="mdi-message-text"
                      color="#7360F2"
                      title="MAX"
                    />
                  </div>
                </td>
                <td class="text-center">
                  <VSwitch
                    :model-value="cmd.is_active"
                    color="primary"
                    hide-details
                    density="compact"
                    class="d-inline-flex"
                    @change="toggleStatus(cmd)"
                  />
                </td>
                <td class="text-center">
                  <div class="d-flex justify-center gap-1">
                    <VBtn
                      icon
                      variant="text"
                      color="primary"
                      size="small"
                      @click="openEditDialog(cmd)"
                    >
                      <VIcon icon="bx-edit" />
                      <VTooltip activator="parent">Редактировать</VTooltip>
                    </VBtn>
                    <VBtn
                      icon
                      variant="text"
                      color="error"
                      size="small"
                      :disabled="cmd.id === 100"
                      :loading="deletingId === cmd.id"
                      @click="deleteCommand(cmd.id)"
                    >
                      <VIcon icon="bx-trash" />
                      <VTooltip activator="parent">Удалить</VTooltip>
                    </VBtn>
                  </div>
                </td>
              </tr>
            </tbody>
          </VTable>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <!-- Диалог CRUD -->
  <VDialog
    v-model="showDialog"
    max-width="800px"
    scrollable
  >
    <VCard>
      <VCardTitle class="py-4 px-6 d-flex justify-between align-center border-bottom">
        <span class="text-h6 font-semibold">
          {{ isEdit ? `Редактирование команды #${form.id}` : 'Создание команды бота' }}
        </span>
        <VBtn
          icon
          variant="text"
          density="comfortable"
          @click="showDialog = false"
        >
          <VIcon icon="bx-x" />
        </VBtn>
      </VCardTitle>

      <VCardText class="py-4 px-6" style="max-height: 70vh;">
        <VRow>
          <VCol cols="12" md="6">
            <VTextField
              v-model="form.name"
              label="Название команды"
              placeholder="Напр. Мой бонусный баланс"
              required
            />
          </VCol>
          <VCol cols="12" md="6">
            <VTextField
              v-model="form.trigger_phrase"
              label="Триггерная фраза (слово от гостя)"
              placeholder="Напр. Баланс"
              required
              hint="Регистр букв значения не имеет"
              persistent-hint
            />
          </VCol>

          <VCol cols="12" md="6">
            <VSelect
              v-model="form.action_type"
              label="Тип действия"
              :items="[
                { title: 'Проверка баланса бонусов (FSM)', value: 'get_balance' },
                { title: 'Перевести баллы в бонусы (FSM)', value: 'transfer_points' },
                { title: 'Простой текстовый ответ', value: 'custom_text' },
                { title: 'Отвязать номер телефона', value: 'unlink_phone' }
              ]"
            />
          </VCol>
          <VCol cols="12" md="6">
            <div class="text-xs text-muted mb-1">Активные каналы (соцсети):</div>
            <div class="d-flex flex-wrap gap-x-4">
              <VCheckbox
                v-model="form.channels"
                label="ВКонтакте"
                value="vk"
                density="compact"
                hide-details
              />
              <VCheckbox
                v-model="form.channels"
                label="Telegram"
                value="telegram"
                density="compact"
                hide-details
              />
              <VCheckbox
                v-model="form.channels"
                label="WhatsApp"
                value="whatsapp"
                density="compact"
                hide-details
              />
              <VCheckbox
                v-model="form.channels"
                label="MAX"
                value="max"
                density="compact"
                hide-details
              />
            </div>
          </VCol>

          <!-- Поля для custom_text или unlink_phone -->
          <VCol cols="12" v-if="form.action_type === 'custom_text' || form.action_type === 'unlink_phone'">
            <VTextarea
              v-model="form.response_text"
              label="Текст ответа бота"
              placeholder="Введите текст сообщения, которое получит гость..."
              rows="4"
              required
            />
          </VCol>

          <!-- Поля для get_balance и transfer_points -->
          <template v-if="form.action_type === 'get_balance' || form.action_type === 'transfer_points'">
            <VCol cols="12">
              <div class="text-subtitle-2 font-semibold text-primary mb-2">Настройки шагов диалога (FSM)</div>
              <VDivider />
            </VCol>

            <VCol cols="12">
              <VTextarea
                v-model="form.request_phone_text"
                label="1. Запрос номера телефона"
                rows="2"
                hint="Отправляется непривязанному пользователю"
                persistent-hint
              />
            </VCol>

            <VCol cols="12">
              <VTextarea
                v-model="form.phone_not_found_text"
                label="2. Номер телефона не найден в базе"
                rows="2"
                hint="Информационное сообщение перед запросом регистрации"
                persistent-hint
              />
            </VCol>

            <VCol cols="12">
              <VTextarea
                v-model="form.register_confirm_text"
                label="3. Запрос на регистрацию в базе (Да / Нет)"
                rows="2"
                hint="Запрос согласия на регистрацию в бонусной системе"
                persistent-hint
              />
            </VCol>

            <VCol cols="12">
              <VTextarea
                v-model="form.register_success_text"
                label="4. Успешная регистрация и привязка"
                rows="2"
                hint="Доступна переменная {balance} для баланса бонусов"
                persistent-hint
              />
            </VCol>

            <VCol cols="12">
              <VTextarea
                v-model="form.balance_text"
                label="5. Отправка бонусного баланса"
                rows="2"
                hint="Отправляется, если телефон уже был привязан. Доступна переменная {balance}"
                persistent-hint
              />
            </VCol>
          </template>
        </VRow>
      </VCardText>

      <VCardActions class="py-4 px-6 border-top">
        <VSpacer />
        <VBtn
          color="secondary"
          variant="outlined"
          @click="showDialog = false"
        >
          Отмена
        </VBtn>
        <VBtn
          color="primary"
          :loading="saving"
          @click="saveCommand"
        >
          Сохранить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="3000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>

<style scoped>
.glass-card {
  backdrop-filter: blur(10px);
  background: rgba(var(--v-theme-surface), 0.8) !important;
}
.border-bottom {
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
.border-top {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
</style>
