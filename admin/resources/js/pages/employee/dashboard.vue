<script setup>
import { useTheme } from 'vuetify'
import { authState, logout } from '@/utils/auth'
import { useRouter } from 'vue-router'

const { global: globalTheme } = useTheme()
const router = useRouter()

const handleLogout = () => {
  logout()
  router.push('/login')
}

console.log('[Dashboard] Loaded, user:', authState.user)
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Рабочее пространство сотрудника 🚀">
        <VCardText>
          <div v-if="authState.user" class="mb-6">
            <h3 class="text-h6 mb-2">Добро пожаловать, {{ authState.user.name }}!</h3>
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
</template>
