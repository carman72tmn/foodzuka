<script setup>
import { ref, onMounted } from 'vue'
import { useTheme } from 'vuetify'
import { authState, logout, fetchMe } from '@/utils/auth'
import { useRouter, useRoute } from 'vue-router'

const { global: globalTheme } = useTheme()
const router = useRouter()
const route = useRoute()

const isUnlinking = ref(false)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const handleLogout = () => {
  logout()
  router.push('/login')
}

const handleLinkVk = () => {
  if (!authState.token) return
  window.location.href = `/api/v1/auth/vk/oauth-redirect?action=link&token=${authState.token}`
}

const handleUnlinkVk = async () => {
  isUnlinking.value = true
  try {
    const response = await fetch('/api/v1/auth/unlink-vk', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authState.token}`,
        'Content-Type': 'application/json'
      }
    })
    if (response.ok) {
      snackbarText.value = 'Аккаунт ВКонтакте успешно отвязан'
      snackbarColor.value = 'success'
      snackbar.value = true
      await fetchMe() // обновляем профиль
    } else {
      throw new Error('Не удалось отвязать аккаунт')
    }
  } catch (e) {
    snackbarText.value = e.message || 'Ошибка при отвязке аккаунта'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    isUnlinking.value = false
  }
}

onMounted(async () => {
  // Обновляем данные текущего пользователя при загрузке
  await fetchMe()

  const vkLink = route.query.vk_link
  if (vkLink) {
    if (vkLink === 'success') {
      snackbarText.value = 'Аккаунт ВКонтакте успешно привязан!'
      snackbarColor.value = 'success'
      snackbar.value = true
    } else if (vkLink === 'already_linked_to_another') {
      snackbarText.value = 'Этот аккаунт ВКонтакте уже привязан к другому пользователю!'
      snackbarColor.value = 'error'
      snackbar.value = true
    } else if (vkLink === 'user_not_found') {
      snackbarText.value = 'Пользователь не найден в системе!'
      snackbarColor.value = 'error'
      snackbar.value = true
    }
    // Убираем query-параметры, чтобы не показывать уведомление при обновлении страницы
    router.replace({ query: {} })
  }
})

console.log('[Dashboard] Loaded, user:', authState.user)
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Рабочее пространство сотрудника 🚀">
        <VCardText>
          <div v-if="authState.user" class="mb-6">
            <h3 class="text-h6 mb-2">Добро пожаловать, {{ authState.user.username }}!</h3>
            <p class="text-body-1">Вы успешно вошли в систему под ролью: <strong>{{ authState.user.role?.name || 'Сотрудник' }}</strong></p>
          </div>
          
          <p class="text-body-1">
            Это ваша персональная панель управления. Здесь будут отображаться задачи и инструменты, необходимые для вашей работы.
          </p>
          <p class="text-caption text-error" v-if="!authState.user?.iiko_id && !authState.user?.employee?.iiko_id">
            Внимание: iiko_id не найден в вашем профиле!
          </p>
        </VCardText>
        
        <VCardText class="d-flex gap-4 flex-wrap">
          <VBtn 
            v-if="authState.user?.iiko_id || authState.user?.employee?.iiko_id"
            color="success" 
            variant="elevated"
            to="/courier"
            prepend-icon="mdi-truck-delivery"
          >
            Доставки
          </VBtn>
          
          <VAlert
            v-else
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-0"
            title="Доступ ограничен"
            text="Для доступа к системе доставок ваш аккаунт должен быть связан с сотрудником в iiko."
          />
          
          <VBtn color="primary" variant="elevated">
            Мои задачи
          </VBtn>
          
          <VBtn color="error" variant="outlined" @click="handleLogout">
            Выйти из системы
          </VBtn>
        </VCardText>
      </VCard>

      <!-- Интеграция ВКонтакте [NEW] -->
      <VCard title="Интеграция ВКонтакте 💬" class="mt-6">
        <VCardText>
          <div v-if="authState.user?.vk_user_id" class="d-flex align-center justify-space-between flex-wrap gap-4">
            <div>
              <p class="text-body-1 mb-1">
                Ваш аккаунт успешно связан с ВКонтакте!
              </p>
              <p class="text-caption text-disabled mb-0">
                ID пользователя ВК: <strong>{{ authState.user.vk_user_id }}</strong>
              </p>
            </div>
            <VBtn 
              color="error" 
              variant="outlined" 
              :loading="isUnlinking" 
              @click="handleUnlinkVk"
            >
              Отвязать аккаунт
            </VBtn>
          </div>
          <div v-else class="d-flex align-center justify-space-between flex-wrap gap-4">
            <div>
              <p class="text-body-1 mb-1">
                Привяжите свой аккаунт ВКонтакте для получения уведомлений о событиях и быстрого входа без пароля.
              </p>
              <p class="text-caption text-warning mb-0">
                Аккаунт ВКонтакте в данный момент не привязан.
              </p>
            </div>
            <VBtn 
              color="primary" 
              variant="elevated" 
              prepend-icon="bxl-vk"
              @click="handleLinkVk"
            >
              Привязать ВКонтакте
            </VBtn>
          </div>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12" sm="6" md="4">
      <VCard title="Статус">
        <VCardText>
          <div class="d-flex align-center">
            <VIcon icon="mdi-check-circle" color="success" class="me-2" />
            <span>Система активна</span>
          </div>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <VSnackbar 
    v-model="snackbar" 
    :color="snackbarColor" 
    timeout="4000"
  >
    {{ snackbarText }}
  </VSnackbar>
</template>

