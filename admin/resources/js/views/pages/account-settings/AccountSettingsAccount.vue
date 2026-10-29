<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import avatar1 from '@images/avatars/avatar-1.png'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const accountData = {
  avatarImg: avatar1,
  firstName: '',
  lastName: '',
  email: '',
  username: '',
  phone: '',
  address: '',
  state: '',
  zip: '',
  country: 'Россия',
  language: 'Русский',
  timezone: '(GMT+03:00) Москва',
  currency: 'RUB',
}

const refInputEl = ref()
const accountDataLocal = ref(JSON.parse(JSON.stringify(accountData)))
const isAccountDeactivated = ref(false)
const loading = ref(false)
const saving = ref(false)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const showMessage = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const headers = {
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json'
}

let initialData = JSON.parse(JSON.stringify(accountData))

const vkUserId = ref(null)
const isUnlinkingVk = ref(false)

const loadUserData = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/users/me', { headers })
    const user = response.data
    
    vkUserId.value = user.vk_user_id
    
    const fullName = user.full_name || ''
    const parts = fullName.split(' ')
    
    accountData.firstName = parts[0] || ''
    accountData.lastName = parts.slice(1).join(' ') || ''
    accountData.email = user.email || ''
    accountData.username = user.username || ''
    
    const profile = user.profile_data || {}
    accountData.phone = profile.phone || ''
    accountData.address = profile.address || ''
    accountData.state = profile.state || ''
    accountData.zip = profile.zip || ''
    accountData.country = profile.country || 'Россия'
    accountData.language = profile.language || 'Русский'
    accountData.timezone = profile.timezone || '(GMT+03:00) Москва'
    accountData.currency = profile.currency || 'RUB'
    
    accountDataLocal.value = JSON.parse(JSON.stringify(accountData))
    initialData = JSON.parse(JSON.stringify(accountData))
  } catch (e) {
    console.error('Ошибка загрузки данных профиля', e)
    showMessage('Не удалось загрузить данные профиля', 'error')
  } finally {
    loading.value = false
  }
}

const handleLinkVk = () => {
  const token = localStorage.getItem('access_token')
  if (!token) return
  window.location.href = `/api/v1/auth/vk/oauth-redirect?action=link&source=admin&token=${token}`
}

const handleUnlinkVk = async () => {
  isUnlinkingVk.value = true
  try {
    const response = await axios.post('/api/v1/auth/unlink-vk', {}, { headers })
    if (response.data?.status === 'success') {
      showMessage('Аккаунт ВКонтакте успешно отвязан')
      vkUserId.value = null
    } else {
      throw new Error('Не удалось отвязать аккаунт')
    }
  } catch (e) {
    console.error('Ошибка отвязки ВК', e)
    showMessage(e.response?.data?.detail || 'Ошибка при отвязке аккаунта', 'error')
  } finally {
    isUnlinkingVk.value = false
  }
}

const saveChanges = async () => {
  saving.value = true
  try {
    const payload = {
      username: accountDataLocal.value.username,
      full_name: `${accountDataLocal.value.firstName} ${accountDataLocal.value.lastName}`.trim(),
      email: accountDataLocal.value.email,
      profile_data: {
        phone: accountDataLocal.value.phone,
        address: accountDataLocal.value.address,
        state: accountDataLocal.value.state,
        zip: accountDataLocal.value.zip,
        country: accountDataLocal.value.country,
        language: accountDataLocal.value.language,
        timezone: accountDataLocal.value.timezone,
        currency: accountDataLocal.value.currency
      }
    }
    
    await axios.patch('/api/v1/users/me', payload, { headers })
    showMessage('Изменения успешно сохранены')
    initialData = JSON.parse(JSON.stringify(accountDataLocal.value))
  } catch (e) {
    console.error('Ошибка сохранения данных профиля', e)
    showMessage(e.response?.data?.detail || 'Не удалось сохранить изменения', 'error')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  accountDataLocal.value = JSON.parse(JSON.stringify(initialData))
}

const changeAvatar = file => {
  const fileReader = new FileReader()
  const { files } = file.target
  if (files && files.length) {
    fileReader.readAsDataURL(files[0])
    fileReader.onload = () => {
      if (typeof fileReader.result === 'string')
        accountDataLocal.value.avatarImg = fileReader.result
    }
  }
}

const resetAvatar = () => {
  accountDataLocal.value.avatarImg = initialData.avatarImg
}

onMounted(() => {
  loadUserData()
  
  const vkLink = route.query.vk_link
  if (vkLink) {
    if (vkLink === 'success') {
      showMessage('Аккаунт ВКонтакте успешно привязан!')
    } else if (vkLink === 'already_linked_to_another') {
      showMessage('Этот аккаунт ВКонтакте уже привязан к другому пользователю!', 'error')
    } else if (vkLink === 'user_not_found') {
      showMessage('Пользователь не найден в системе!', 'error')
    }
    router.replace({ query: {} })
  }
})

const timezones = [
  '(GMT+02:00) Калининград',
  '(GMT+03:00) Москва',
  '(GMT+04:00) Самара',
  '(GMT+05:00) Екатеринбург',
  '(GMT+06:00) Омск',
  '(GMT+07:00) Красноярск',
  '(GMT+08:00) Иркутск',
  '(GMT+09:00) Якутск',
  '(GMT+10:00) Владивосток',
  '(GMT+11:00) Северо-Курильск',
  '(GMT+12:00) Анадырь'
]

const currencies = [
  'RUB',
  'USD',
  'EUR'
]

const countries = [
  'Россия',
  'Казахстан',
  'Беларусь'
]

const languages = [
  'Русский',
  'English'
]
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard title="Данные профиля">
        <VCardText v-if="loading" class="text-center py-6">
          <VProgressCircular indeterminate color="primary" />
        </VCardText>
        
        <VCardText v-else>
          <div class="d-flex mb-6">
            <!-- 👉 Avatar -->
            <VAvatar
              rounded="lg"
              size="100"
              class="me-6"
              :image="accountDataLocal.avatarImg"
            />

            <!-- 👉 Upload Photo -->
            <form class="d-flex flex-column justify-center gap-5">
              <div class="d-flex flex-wrap gap-2">
                <VBtn
                  color="primary"
                  @click="refInputEl?.click()"
                >
                  <VIcon
                    icon="bx-cloud-upload"
                    class="d-sm-none"
                  />
                  <span class="d-none d-sm-block">Загрузить фото</span>
                </VBtn>

                <input
                  ref="refInputEl"
                  type="file"
                  name="file"
                  accept=".jpeg,.png,.jpg,GIF"
                  hidden
                  @input="changeAvatar"
                >

                <VBtn
                  type="reset"
                  color="error"
                  variant="tonal"
                  @click="resetAvatar"
                >
                  <span class="d-none d-sm-block">Сбросить</span>
                  <VIcon
                    icon="bx-refresh"
                    class="d-sm-none"
                  />
                </VBtn>
              </div>

              <p class="text-body-1 mb-0">
                Разрешены JPG, GIF или PNG. Максимальный размер 800К
              </p>
            </form>
          </div>

          <VDivider />

          <!-- 👉 Form -->
          <VForm class="mt-6" @submit.prevent="saveChanges">
            <VRow>
              <!-- 👉 First Name -->
              <VCol
                md="6"
                cols="12"
              >
                <VTextField
                  v-model="accountDataLocal.firstName"
                  placeholder="Иван"
                  label="Имя"
                />
              </VCol>

              <!-- 👉 Last Name -->
              <VCol
                md="6"
                cols="12"
              >
                <VTextField
                  v-model="accountDataLocal.lastName"
                  placeholder="Иванов"
                  label="Фамилия"
                />
              </VCol>

              <!-- 👉 Email -->
              <VCol
                cols="12"
                md="6"
              >
                <VTextField
                  v-model="accountDataLocal.email"
                  label="Электронная почта"
                  placeholder="ivanov@example.com"
                  type="email"
                />
              </VCol>

              <!-- 👉 Username (Username вместо Organization) -->
              <VCol
                cols="12"
                md="6"
              >
                <VTextField
                  v-model="accountDataLocal.username"
                  label="Логин (Имя пользователя)"
                  placeholder="ivan_admin"
                />
              </VCol>

              <!-- 👉 Phone -->
              <VCol
                cols="12"
                md="6"
              >
                <VTextField
                  v-model="accountDataLocal.phone"
                  label="Номер телефона"
                  placeholder="+7 (999) 123-4567"
                />
              </VCol>

              <!-- 👉 Address -->
              <VCol
                cols="12"
                md="6"
              >
                <VTextField
                  v-model="accountDataLocal.address"
                  label="Адрес"
                  placeholder="ул. Ленина, д. 10"
                />
              </VCol>

              <!-- 👉 State -->
              <VCol
                cols="12"
                md="6"
              >
                <VTextField
                  v-model="accountDataLocal.state"
                  label="Регион / Область"
                  placeholder="Московская обл."
                />
              </VCol>

              <!-- 👉 Zip Code -->
              <VCol
                cols="12"
                md="6"
              >
                <VTextField
                  v-model="accountDataLocal.zip"
                  label="Почтовый индекс"
                  placeholder="101000"
                />
              </VCol>

              <!-- 👉 Country -->
              <VCol
                cols="12"
                md="6"
              >
                <VSelect
                  v-model="accountDataLocal.country"
                  label="Страна"
                  :items="countries"
                  placeholder="Выберите страну"
                />
              </VCol>

              <!-- 👉 Language -->
              <VCol
                cols="12"
                md="6"
              >
                <VSelect
                  v-model="accountDataLocal.language"
                  label="Язык интерфейса"
                  placeholder="Выберите язык"
                  :items="languages"
                />
              </VCol>

              <!-- 👉 Timezone -->
              <VCol
                cols="12"
                md="6"
              >
                <VSelect
                  v-model="accountDataLocal.timezone"
                  label="Часовой пояс"
                  placeholder="Выберите часовой пояс"
                  :items="timezones"
                  :menu-props="{ maxHeight: 200 }"
                />
              </VCol>

              <!-- 👉 Currency -->
              <VCol
                cols="12"
                md="6"
              >
                <VSelect
                  v-model="accountDataLocal.currency"
                  label="Валюта по умолчанию"
                  placeholder="Выберите валюту"
                  :items="currencies"
                  :menu-props="{ maxHeight: 200 }"
                />
              </VCol>

              <!-- 👉 Form Actions -->
              <VCol
                cols="12"
                class="d-flex flex-wrap gap-4"
              >
                <VBtn type="submit" :loading="saving">Сохранить изменения</VBtn>

                <VBtn
                  color="secondary"
                  variant="tonal"
                  type="reset"
                  @click.prevent="resetForm"
                >
                  Сбросить
                </VBtn>
              </VCol>
            </VRow>
          </VForm>
        </VCardText>
      </VCard>
    </VCol>

    <VCol cols="12">
      <!-- 👉 VK Integration -->
      <VCard title="Интеграция ВКонтакте 💬">
        <VCardText>
          <div v-if="vkUserId" class="d-flex align-center justify-space-between flex-wrap gap-4">
            <div>
              <p class="text-body-1 mb-1">
                Ваш аккаунт успешно связан с ВКонтакте!
              </p>
              <p class="text-caption text-disabled mb-0">
                ID пользователя ВК: <strong>{{ vkUserId }}</strong>
              </p>
            </div>
            <VBtn 
              color="error" 
              variant="outlined" 
              :loading="isUnlinkingVk" 
              @click="handleUnlinkVk"
            >
              Отвязать аккаунт
            </VBtn>
          </div>
          <div v-else class="d-flex align-center justify-space-between flex-wrap gap-4">
            <div>
              <p class="text-body-1 mb-1">
                Привяжите свой аккаунт ВКонтакте для входа в панель без пароля.
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

    <VCol cols="12">
      <!-- 👉 Deactivate Account -->
      <VCard title="Управление аккаунтом">
        <VCardText>
          <div class="mb-4 text-warning">
            <VIcon icon="bx-error" class="me-2" />
            Вы не можете самостоятельно деактивировать или удалить свой аккаунт администратора. 
            Пожалуйста, обратитесь к владельцу системы или системному интегратору для изменения статуса доступа.
          </div>

          <VBtn
            disabled
            color="error"
          >
            Деактивировать аккаунт
          </VBtn>
        </VCardText>
      </VCard>
    </VCol>
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
