<script setup>
import { ref } from 'vue'
import axios from 'axios'

const isCurrentPasswordVisible = ref(false)
const isNewPasswordVisible = ref(false)
const isConfirmPasswordVisible = ref(false)

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const saving = ref(false)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const showMessage = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const changePassword = async () => {
  if (!newPassword.value || !confirmPassword.value) {
    showMessage('Пожалуйста, заполните поля нового пароля и подтверждения', 'error')
    return
  }

  if (newPassword.value.length < 8) {
    showMessage('Новый пароль должен содержать минимум 8 символов', 'error')
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    showMessage('Введенные пароли не совпадают', 'error')
    return
  }

  saving.value = true
  try {
    const headers = {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    }

    await axios.patch('/api/v1/users/me', {
      password: newPassword.value
    }, { headers })

    showMessage('Пароль успешно обновлен')
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e) {
    console.error('Ошибка изменения пароля', e)
    showMessage(e.response?.data?.detail || 'Не удалось изменить пароль', 'error')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
}

const passwordRequirements = [
  'Минимум 8 символов длиной — чем больше, тем лучше',
  'Рекомендуется использовать буквы разного регистра',
  'Хотя бы одна цифра или специальный символ',
]

const recentDevicesHeaders = [
  {
    title: 'БРАУЗЕР / ОС',
    key: 'browser',
  },
  {
    title: 'УСТРОЙСТВО',
    key: 'device',
  },
  {
    title: 'МЕСТОПОЛОЖЕНИЕ',
    key: 'location',
  },
  {
    title: 'ПОСЛЕДНЯЯ АКТИВНОСТЬ',
    key: 'recentActivity',
  },
]

const recentDevices = [
  {
    browser: 'Chrome на Windows',
    device: 'HP Spectre 360',
    location: 'Екатеринбург, RU',
    recentActivity: 'Сегодня, 15:20',
    deviceIcon: {
      icon: 'bxl-windows',
      color: 'primary',
    },
  },
  {
    browser: 'Safari на iPhone',
    device: 'iPhone 14 Pro',
    location: 'Москва, RU',
    recentActivity: 'Вчера, 10:20',
    deviceIcon: {
      icon: 'bx-mobile',
      color: 'error',
    },
  },
  {
    browser: 'Chrome на Android',
    device: 'Samsung S23',
    location: 'Тюмень, RU',
    recentActivity: '12 июня 2026, 04:20',
    deviceIcon: {
      icon: 'bxl-android',
      color: 'success',
    },
  }
]
</script>

<template>
  <VRow>
    <!-- SECTION: Change Password -->
    <VCol cols="12">
      <VCard title="Изменение пароля">
        <VForm @submit.prevent="changePassword">
          <VCardText>
            <!-- 👉 Current Password -->
            <VRow>
              <VCol
                cols="12"
                md="6"
              >
                <!-- 👉 current password -->
                <VTextField
                  v-model="currentPassword"
                  :type="isCurrentPasswordVisible ? 'text' : 'password'"
                  :append-inner-icon="isCurrentPasswordVisible ? 'bx-hide' : 'bx-show'"
                  label="Текущий пароль"
                  placeholder="············"
                  @click:append-inner="isCurrentPasswordVisible = !isCurrentPasswordVisible"
                />
              </VCol>
            </VRow>

            <!-- 👉 New Password -->
            <VRow class="mt-2">
              <VCol
                cols="12"
                md="6"
              >
                <!-- 👉 new password -->
                <VTextField
                  v-model="newPassword"
                  :type="isNewPasswordVisible ? 'text' : 'password'"
                  :append-inner-icon="isNewPasswordVisible ? 'bx-hide' : 'bx-show'"
                  label="Новый пароль"
                  autocomplete="on"
                  placeholder="············"
                  @click:append-inner="isNewPasswordVisible = !isNewPasswordVisible"
                />
              </VCol>

              <VCol
                cols="12"
                md="6"
              >
                <!-- 👉 confirm password -->
                <VTextField
                  v-model="confirmPassword"
                  :type="isConfirmPasswordVisible ? 'text' : 'password'"
                  :append-inner-icon="isConfirmPasswordVisible ? 'bx-hide' : 'bx-show'"
                  label="Подтвердите новый пароль"
                  placeholder="············"
                  @click:append-inner="isConfirmPasswordVisible = !isConfirmPasswordVisible"
                />
              </VCol>
            </VRow>
          </VCardText>

          <!-- 👉 Password Requirements -->
          <VCardText>
            <p class="text-base font-weight-medium mt-2">
              Требования к паролю:
            </p>

            <ul class="d-flex flex-column gap-y-3">
              <li
                v-for="item in passwordRequirements"
                :key="item"
                class="d-flex align-start"
              >
                <div>
                  <VIcon
                    size="7"
                    icon="bxs-circle"
                    class="me-3 mt-2"
                  />
                </div>
                <span class="font-weight-medium text-body-2">{{ item }}</span>
              </li>
            </ul>
          </VCardText>

          <!-- 👉 Action Buttons -->
          <VCardText class="d-flex flex-wrap gap-4">
            <VBtn type="submit" :loading="saving">Сохранить изменения</VBtn>

            <VBtn
              type="reset"
              color="secondary"
              variant="tonal"
              @click.prevent="resetForm"
            >
              Сбросить
            </VBtn>
          </VCardText>
        </VForm>
      </VCard>
    </VCol>
    <!-- !SECTION -->

    <!-- SECTION Two-steps verification -->
    <VCol cols="12">
      <VCard title="Двухфакторная аутентификация">
        <VCardText>
          <p class="font-weight-semibold text-warning">
            Двухфакторная аутентификация в данный момент отключена.
          </p>
          <p class="text-body-2">
            Двухфакторная аутентификация добавляет дополнительный уровень безопасности для вашего аккаунта, требуя одноразовый код при входе в систему.
          </p>

          <VBtn disabled color="secondary">
            Подключить 2FA
          </VBtn>
        </VCardText>
      </VCard>
    </VCol>
    <!-- !SECTION -->

    <!-- SECTION Recent Devices -->
    <VCol cols="12">
      <!-- 👉 Table -->
      <VCard title="История входов (Устройства)">
        <VDataTable
          :headers="recentDevicesHeaders"
          :items="recentDevices"
          class="text-no-wrap rounded-0 text-sm"
        >
          <template #item.browser="{ item }">
            <div class="d-flex align-center">
              <VIcon
                start
                :icon="item.deviceIcon.icon"
                :color="item.deviceIcon.color"
                class="me-2"
              />
              <span class="text-high-emphasis text-base">
                {{ item.browser }}
              </span>
            </div>
          </template>
          <!-- TODO Refactor this after vuetify provides proper solution for removing default footer -->
          <template #bottom />
        </VDataTable>
      </VCard>
    </VCol>
    <!-- !SECTION -->
  </VRow>

  <!-- Уведомления -->
  <VSnackbar
    v-model="snackbar"
    :color="snackbarColor"
    :timeout="4000"
    location="top"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>
