<script setup>
import { ref, onMounted } from 'vue'
import AuthProvider from '@/views/pages/authentication/AuthProvider.vue'
import logo from '@images/logo.svg?raw'
import authV1BottomShape from '@images/svg/auth-v1-bottom-shape.svg?url'
import authV1TopShape from '@images/svg/auth-v1-top-shape.svg?url'
import { login, authState, syncVkLinking, linkVkMiniApp } from '@/utils/auth'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const form = ref({
  username: '',
  password: '',
  remember: false,
})

const isPasswordVisible = ref(false)
const isLoading = ref(false)
const isVkLoading = ref(false)
const loginError = ref('')
const isVkLinkMode = ref(false)

const handleLogin = async () => {
  isLoading.value = true
  loginError.value = ''
  try {
    if (isVkLinkMode.value) {
      // Режим связывания VK Mini App
      const launchParams = localStorage.getItem('vk_launch_params') || window.location.search
      console.log('[VK Mini App] Linking account with params:', launchParams)
      const result = await linkVkMiniApp(form.value.username, form.value.password, launchParams)
      
      console.log('[VK Mini App] Link successful, redirecting...')
      if (result.is_courier) {
        router.push('/pers/dashboard')
      } else {
        router.push('/admin/dashboard')
      }
    } else {
      // Обычный логин
      await login(form.value.username, form.value.password, form.value.remember)
      try {
        await syncVkLinking()
      } catch (vkErr) {
        console.error('Failed to link VK after login:', vkErr)
      }
      router.push('/')
    }
  } catch (e) {
    loginError.value = e.message || 'Ошибка авторизации'
  } finally {
    isLoading.value = false
  }
}

const handleVkLogin = () => {
  isVkLoading.value = true
  loginError.value = ''
  try {
    window.location.href = '/api/v1/auth/vk/oauth-redirect?action=login'
  } catch (e) {
    loginError.value = e.message || 'Ошибка запуска авторизации ВКонтакте'
    isVkLoading.value = false
  }
}

onMounted(async () => {
  // Проверяем режим привязки VK Mini App из query параметров
  if (route.query.vk_link_mode === '1') {
    isVkLinkMode.value = true
    console.log('[VK Mini App] Mounted in link mode. VK User ID:', route.query.vk_user_id)
  }

  const vkToken = route.query.vk_token || route.query.t_id_token
  if (vkToken) {
    isLoading.value = true
    try {
      localStorage.setItem('access_token', vkToken)
      authState.token = vkToken
      try {
        await syncVkLinking()
      } catch (vkErr) {
        console.error('Failed to link VK after VK login:', vkErr)
      }
      router.push('/')
    } catch (e) {
      loginError.value = 'Ошибка входа через ВКонтакте'
    } finally {
      isLoading.value = false
    }
  }

  const error = route.query.error
  if (error) {
    if (error === 'vk_user_not_linked') {
      loginError.value = 'Ваш аккаунт ВКонтакте не привязан к пользователю в системе. Пожалуйста, войдите по логину и паролю и привяжите ВК в личном кабинете.'
    } else if (error === 'vk_no_user_id') {
      loginError.value = 'Не удалось получить ID пользователя ВКонтакте.'
    } else if (error === 'vk_oauth_error') {
      loginError.value = 'Ошибка при авторизации через ВКонтакте.'
    } else if (error === 'user_inactive') {
      loginError.value = 'Пользователь заблокирован в системе.'
    } else {
      loginError.value = 'Произошла неизвестная ошибка при входе.'
    }
  }
})
</script>

<template>
  <div class="auth-wrapper d-flex align-center justify-center pa-4">
    <div class="position-relative my-sm-16">
      <!-- 👉 Top shape -->
      <VImg
        :src="authV1TopShape"
        class="text-primary auth-v1-top-shape d-none d-sm-block"
      />

      <!-- 👉 Bottom shape -->
      <VImg
        :src="authV1BottomShape"
        class="text-primary auth-v1-bottom-shape d-none d-sm-block"
      />

      <!-- 👉 Auth Card -->
      <VCard
        class="auth-card"
        max-width="460"
        :class="$vuetify.display.smAndUp ? 'pa-6' : 'pa-0'"
      >
        <VCardItem class="justify-center">
          <RouterLink
            to="/"
            class="app-logo"
          >
            <!-- eslint-disable vue/no-v-html -->
            <div
              class="d-flex"
              v-html="logo"
            />
            <h1 class="app-logo-title">
              FoodTech
            </h1>
          </RouterLink>
        </VCardItem>

        <VCardText>
          <h4 class="text-h4 mb-1">
            {{ isVkLinkMode ? 'Связывание аккаунта ВКонтакте 🤝' : 'Добро пожаловать в FoodTech! 👋🏻' }}
          </h4>
          <p class="mb-0">
            {{ isVkLinkMode ? 'Введите логин и пароль вашей панели, чтобы связать аккаунт ВК' : 'Пожалуйста, войдите в свой аккаунт, чтобы начать работу' }}
          </p>
        </VCardText>

        <VCardText>
          <VAlert
            v-if="loginError"
            type="error"
            variant="tonal"
            closable
            class="mb-4"
            @click:close="loginError = ''"
          >
            {{ loginError }}
          </VAlert>

          <VForm @submit.prevent="handleLogin">
            <VRow>
              <!-- login -->
              <VCol cols="12">
                <VTextField
                  v-model="form.username"
                  autofocus
                  label="Логин"
                  type="text"
                  placeholder="0001"
                />
              </VCol>

              <!-- password -->
              <VCol cols="12">
                <VTextField
                  v-model="form.password"
                  label="Пароль"
                  placeholder="············"
                  :type="isPasswordVisible ? 'text' : 'password'"
                  autocomplete="password"
                  :append-inner-icon="isPasswordVisible ? 'bx-hide' : 'bx-show'"
                  @click:append-inner="isPasswordVisible = !isPasswordVisible"
                />

                <!-- remember me checkbox -->
                <div class="d-flex align-center justify-space-between flex-wrap my-6">
                  <VCheckbox
                    v-model="form.remember"
                    label="Запомнить меня"
                  />

                  <a
                    class="text-primary"
                    href="javascript:void(0)"
                  >
                    Забыли пароль?
                  </a>
                </div>

                <!-- login button -->
                <VBtn
                  block
                  type="submit"
                  :loading="isLoading"
                >
                  {{ isVkLinkMode ? 'Связать и войти' : 'Войти' }}
                </VBtn>

                <!-- VK Login Button (hidden in link mode) -->
                <VBtn
                  v-if="!isVkLinkMode"
                  block
                  color="#0077FF"
                  class="mt-4 text-none font-weight-black vk-login-btn-premium"
                  style="color: #FFFFFF !important; border-radius: 12px; height: 48px; box-shadow: 0 4px 14px rgba(0, 119, 255, 0.3) !important;"
                  :loading="isVkLoading"
                  @click="handleVkLogin"
                >
                  <VIcon icon="bxl-vk" class="me-2" style="color: #FFFFFF" />
                  Войти через ВКонтакте
                </VBtn>
              </VCol>

              <!-- create account (hidden in link mode) -->
              <VCol
                v-if="!isVkLinkMode"
                cols="12"
                class="text-body-1 text-center"
              >
                <span class="d-inline-block">
                  Впервые у нас?
                </span>
                <RouterLink
                  class="text-primary ms-1 d-inline-block text-body-1"
                  to="/register"
                >
                  Создать аккаунт
                </RouterLink>
              </VCol>

              <VCol
                v-if="!isVkLinkMode"
                cols="12"
                class="d-flex align-center"
              >
                <VDivider />
                <span class="mx-4 text-high-emphasis">или</span>
                <VDivider />
              </VCol>

              <!-- auth providers (hidden in link mode) -->
              <VCol
                v-if="!isVkLinkMode"
                cols="12"
                class="text-center"
              >
                <AuthProvider />
              </VCol>
            </VRow>
          </VForm>
        </VCardText>
      </VCard>
    </div>
  </div>
</template>

<style lang="scss">
@use "@core-scss/template/pages/page-auth";
</style>
