<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const settings = ref({
  is_active: false,
  provider: 'red_sms',
  api_login: '',
  api_key: '',
  sender_name: 'REDSMS',
  wait_call_num: '',
  wait_call_no_voice: false,
  active_route: 'sms',
  cascade_routes: 'fcall,voice,sms',
  cascade_delay: 30,
  vk_verification_method: 'none',
  vk_mini_app_id: '',
  vk_mini_app_secret: '',
  vk_lead_form_url: '',
  vk_alternative_methods: 'fcall,wcall,tg,max',
  vk_msg_start: '',
  vk_msg_choose_method: '',
  vk_msg_fcall_prompt: '',
  vk_msg_fcall_code: '',
  vk_msg_wcall_prompt: '',
  vk_msg_wcall_instruct: '',
  vk_msg_tg_instruct: '',
  vk_msg_max_instruct: '',
  vk_msg_success: '',
  vk_msg_error_code: '',
  telegram_bot_token: '',
  telegram_bot_username: '',
  max_bot_token: '',
  max_bot_username: ''
})

const vkAlternativeMethods = ref(['fcall', 'wcall', 'tg', 'max'])

// Настройка каскада через отдельные шаги
const step1 = ref('fcall')
const step2 = ref('voice')
const step3 = ref('sms')

const routeOptions = [
  { title: 'SMS (Текстовое сообщение)', value: 'sms' },
  { title: 'Voice (Голосовой код)', value: 'voice' },
  { title: 'Flash Call (Код в номере входящего звонка)', value: 'fcall' },
  { title: 'Wait Call (Входящий звонок от клиента)', value: 'wcall' },
  { title: 'Каскадная отправка (Несколько каналов)', value: 'cascade' }
]

const cascadeStepOptions = [
  { title: 'Flash Call', value: 'fcall' },
  { title: 'Voice (Голосовой код)', value: 'voice' },
  { title: 'Wait Call', value: 'wcall' },
  { title: 'SMS', value: 'sms' },
  { title: 'Отключено', value: 'none' }
]

// Синхронизация шагов каскада с общей строкой cascade_routes
const updateCascadeRoutes = () => {
  const steps = []
  if (step1.value && step1.value !== 'none') steps.push(step1.value)
  if (step2.value && step2.value !== 'none') steps.push(step2.value)
  if (step3.value && step3.value !== 'none') steps.push(step3.value)
  settings.value.cascade_routes = steps.join(',')
}

// Загрузка шагов из строки cascade_routes при получении настроек
const loadCascadeSteps = (routesStr) => {
  if (!routesStr) return
  const parts = routesStr.split(',')
  step1.value = parts[0] || 'none'
  step2.value = parts[1] || 'none'
  step3.value = parts[2] || 'none'
}

const loading = ref(false)
const testLoading = ref(false)
const testResult = ref(null)
const showTestResult = ref(false)

const testForm = ref({
  phone: '',
  code: '',
  route: 'default'
})

const testRouteOptions = [
  { title: 'По умолчанию (из настроек)', value: 'default' },
  { title: 'SMS', value: 'sms' },
  { title: 'Voice (Голосовой код)', value: 'voice' },
  { title: 'Flash Call', value: 'fcall' },
  { title: 'Wait Call', value: 'wcall' },
  { title: 'Каскад (fcall -> voice -> sms)', value: 'cascade' }
]

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const API_BASE = '/api/v1/validation'

const fetchSettings = async () => {
  try {
    const response = await axios.get(`${API_BASE}/settings`)
    settings.value = response.data
    loadCascadeSteps(response.data.cascade_routes)
    if (response.data.vk_alternative_methods) {
      vkAlternativeMethods.value = response.data.vk_alternative_methods.split(',').filter(Boolean)
    } else {
      vkAlternativeMethods.value = []
    }
  } catch (error) {
    console.error('Error fetching validation settings:', error)
  }
}

const saveSettings = async () => {
  loading.value = true
  updateCascadeRoutes()
  settings.value.vk_alternative_methods = vkAlternativeMethods.value.join(',')
  try {
    const response = await axios.post(`${API_BASE}/settings`, settings.value)
    snackbar.value = {
      show: true,
      text: 'Настройки успешно сохранены',
      color: 'success'
    }
    await fetchSettings()
  } catch (error) {
    const detail = error.response?.data?.detail || 'Ошибка при сохранении настроек'
    snackbar.value = {
      show: true,
      text: detail,
      color: 'error'
    }
  } finally {
    loading.value = false
  }
}

const triggerTestSend = async () => {
  if (!testForm.value.phone) {
    snackbar.value = {
      show: true,
      text: 'Введите номер телефона для теста',
      color: 'warning'
    }
    return
  }
  
  testLoading.value = true
  testResult.value = null
  showTestResult.value = true
  
  const payload = {
    phone: testForm.value.phone,
    code: testForm.value.code || undefined,
    route: testForm.value.route === 'default' ? undefined : testForm.value.route
  }
  
  try {
    const response = await axios.post(`${API_BASE}/test-send`, payload)
    testResult.value = {
      success: true,
      code: response.data.code_sent,
      details: response.data.response
    }
    snackbar.value = {
      show: true,
      text: 'Тестовый запрос успешно отправлен',
      color: 'success'
    }
  } catch (error) {
    const detail = error.response?.data?.detail || 'Ошибка при отправке теста'
    testResult.value = {
      success: false,
      error: detail
    }
    snackbar.value = {
      show: true,
      text: detail,
      color: 'error'
    }
  } finally {
    testLoading.value = false
  }
}

const sessionsLoading = ref(false)

const clearSessions = async () => {
  sessionsLoading.value = true
  try {
    const response = await axios.post(`${API_BASE}/clear-sessions`)
    snackbar.value = {
      show: true,
      text: response.data.message || 'Сессии верификации успешно сброшены',
      color: 'success'
    }
  } catch (error) {
    const detail = error.response?.data?.detail || 'Не удалось сбросить сессии'
    snackbar.value = {
      show: true,
      text: detail,
      color: 'error'
    }
  } finally {
    sessionsLoading.value = false
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<template>
  <VRow>
    <VCol cols="12" md="8">
      <VCard title="Настройки валидации телефонных номеров" subtitle="Управление подтверждением телефонов и SMS сервисами">
        <VCardText>
          <VForm @submit.prevent="saveSettings">
            <VRow>
              <!-- Активность -->
              <VCol cols="12">
                <VSwitch
                  v-model="settings.is_active"
                  label="Включить подтверждение телефонов клиентов"
                  color="success"
                  hide-details
                />
                <p class="text-caption mt-1 ml-2 text-grey">
                  Если включено, при регистрации и подтверждении номера телефона клиентам будут отправляться коды верификации.
                </p>
              </VCol>

              <VCol cols="12">
                <VDivider class="my-2" />
              </VCol>

              <!-- Провайдер -->
              <VCol cols="12" md="6">
                <VSelect
                  v-model="settings.provider"
                  label="Провайдер услуг"
                  :items="[{ title: 'RED SMS (cp.redsms.ru)', value: 'red_sms' }]"
                  disabled
                />
              </VCol>

              <!-- Имя отправителя -->
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.sender_name"
                  label="Имя отправителя (Sender Name)"
                  placeholder="Например, REDSMS"
                  persistent-placeholder
                />
              </VCol>

              <!-- API Логин -->
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.api_login"
                  label="API Логин"
                  placeholder="Введите логин RedSMS"
                  persistent-placeholder
                />
              </VCol>

              <!-- API Ключ -->
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.api_key"
                  label="API Ключ"
                  type="password"
                  placeholder="Введите API ключ RedSMS"
                  persistent-placeholder
                />
              </VCol>

              <!-- Wait Call Номер -->
              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.wait_call_num"
                  label="Авторизационный номер Wait Call (опционально)"
                  placeholder="Например, +79991234567"
                  persistent-placeholder
                />
                <p class="text-caption mt-1 text-grey">
                  Используется для сверки или отображения номера при обратном звонке (Wait Call).
                </p>
              </VCol>

              <!-- Wait Call без озвучивания кода -->
              <VCol cols="12" md="6" class="d-flex align-center">
                <div>
                  <VCheckbox
                    v-model="settings.wait_call_no_voice"
                    label="Авторизация без озвучивания кода (сброс звонка)"
                    color="primary"
                    hide-details
                  />
                  <p class="text-caption mt-1 ml-8 text-grey">
                    При входящем звонке от клиента соединение сбросится автоматически. Код диктоваться не будет.
                  </p>
                </div>
              </VCol>

              <VCol cols="12">
                <VDivider class="my-2" />
              </VCol>

              <!-- Способ отправки -->
              <VCol cols="12" md="6">
                <VSelect
                  v-model="settings.active_route"
                  label="Способ отправки по умолчанию"
                  :items="routeOptions"
                  @update:model-value="updateCascadeRoutes"
                />
              </VCol>

              <!-- Настройки каскада -->
              <VCol cols="12" v-if="settings.active_route === 'cascade'">
                <VCard variant="outlined" class="pa-4 bg-grey-lighten-4">
                  <div class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
                    <VIcon icon="mdi-sort" class="mr-2" color="primary" />
                    Настройка цепочки каскада
                  </div>
                  <p class="text-caption text-grey mb-4">
                    Укажите последовательность каналов. Если первый канал не доставит код (таймаут или ошибка), RedSMS автоматически перенаправит его на следующий.
                  </p>
                  
                  <VRow>
                    <VCol cols="12" md="4">
                      <VSelect
                        v-model="step1"
                        label="Шаг 1"
                        :items="cascadeStepOptions"
                        @update:model-value="updateCascadeRoutes"
                      />
                    </VCol>
                    <VCol cols="12" md="4">
                      <VSelect
                        v-model="step2"
                        label="Шаг 2"
                        :items="cascadeStepOptions"
                        @update:model-value="updateCascadeRoutes"
                      />
                    </VCol>
                    <VCol cols="12" md="4">
                      <VSelect
                        v-model="step3"
                        label="Шаг 3"
                        :items="cascadeStepOptions"
                        @update:model-value="updateCascadeRoutes"
                      />
                    </VCol>

                    <VCol cols="12" md="6">
                      <VTextField
                        v-model.number="settings.cascade_delay"
                        label="Задержка переключения (сек)"
                        type="number"
                        min="10"
                        max="300"
                      />
                    </VCol>
                    <VCol cols="12" md="6" class="d-flex align-center">
                      <div class="text-subtitle-2 text-primary font-weight-bold">
                        Итоговый путь: <code class="bg-primary-lighten-5 px-2 py-1 rounded">{{ settings.cascade_routes || 'не выбран' }}</code>
                      </div>
                    </VCol>
                  </VRow>
                </VCard>
              </VCol>

              <VCol cols="12">
                <VDivider class="my-2" />
              </VCol>

              <!-- ВКонтакте и мессенджеры -->
              <VCol cols="12">
                <div class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center">
                  <VIcon icon="mdi-vk" class="mr-2" color="primary" />
                  Верификация в ВКонтакте и мессенджерах
                </div>
                <p class="text-caption text-grey mb-2">
                  Бот ВКонтакте сначала пробует приоритетный метод. Если не получилось, показывает клавиатуру со звонками и мессенджерами.
                </p>
              </VCol>

              <!-- Метод верификации ВК -->
              <VCol cols="12" md="6">
                <VSelect
                  v-model="settings.vk_verification_method"
                  label="Шаг 1: Приоритетный метод верификации в ВК"
                  :items="[
                    { title: 'Без авто-метода (сразу Шаг 2: выбор)', value: 'none' },
                    { title: 'VK Mini App (подтверждение в 1 клик)', value: 'mini_app' },
                    { title: 'VK Lead Forms (Лид-форма сбора заявок)', value: 'lead_form' }
                  ]"
                />
              </VCol>

              <!-- VK Mini App ID -->
              <VCol cols="12" md="6" v-if="settings.vk_verification_method === 'mini_app'">
                <VTextField
                  v-model="settings.vk_mini_app_id"
                  label="ID приложения VK Mini App"
                  placeholder="Например, 51782293"
                  persistent-placeholder
                />
              </VCol>

              <!-- VK Mini App Secret -->
              <VCol cols="12" md="6" v-if="settings.vk_verification_method === 'mini_app'">
                <VTextField
                  v-model="settings.vk_mini_app_secret"
                  label="Защищенный ключ приложения VK"
                  type="password"
                  placeholder="Client Secret"
                  persistent-placeholder
                />
              </VCol>

              <!-- VK Lead Form URL -->
              <VCol cols="12" md="6" v-if="settings.vk_verification_method === 'lead_form'">
                <VTextField
                  v-model="settings.vk_lead_form_url"
                  label="Ссылка на лид-форму ВК"
                  placeholder="Например, https://vk.com/app6013728_-XXXXXX"
                  persistent-placeholder
                />
              </VCol>

              <!-- Выбор альтернативных каналов -->
              <VCol cols="12">
                <div class="text-subtitle-2 font-weight-bold mb-1">
                  Шаг 2: Дополнительные (альтернативные) способы верификации в ВК-боте
                </div>
                <p class="text-caption text-grey mb-3">
                  Выберите способы подтверждения, которые будут предложены пользователю на втором шаге (после нажатия кнопки «Другие способы подтверждения» или если авто-метод отключен).
                </p>
                <div class="d-flex flex-wrap gap-4 align-center">
                  <VCheckbox
                    v-model="vkAlternativeMethods"
                    value="fcall"
                    label="📞 Flash Call"
                    color="secondary"
                    hide-details
                    class="mr-4"
                  />
                  <VCheckbox
                    v-model="vkAlternativeMethods"
                    value="wcall"
                    label="☎️ Wait Call"
                    color="secondary"
                    hide-details
                    class="mr-4"
                  />
                  <VCheckbox
                    v-model="vkAlternativeMethods"
                    value="tg"
                    label="✈️ Telegram-бот"
                    color="primary"
                    hide-details
                    class="mr-4"
                  />
                  <VCheckbox
                    v-model="vkAlternativeMethods"
                    value="max"
                    label="💬 Мессенджер МАКС"
                    color="primary"
                    hide-details
                    class="mr-4"
                  />
                </div>
              </VCol>

              <!-- Редактор текстов ВК -->
              <VCol cols="12">
                <VExpansionPanels class="mt-2">
                  <VExpansionPanel>
                    <VExpansionPanelTitle class="font-weight-bold">
                      <VIcon icon="mdi-message-draw" class="mr-2" color="primary" />
                      💬 Шаблоны текстов бота верификации ВК
                    </VExpansionPanelTitle>
                    <VExpansionPanelText class="pt-3">
                      <p class="text-caption text-grey mb-4">
                        Настройте тексты сообщений, которые отправляет бот верификации ВКонтакте. Оставьте поле пустым, чтобы использовать системный текст по умолчанию.
                      </p>
                      
                      <VRow>
                        <!-- vk_msg_start -->
                        <VCol cols="12">
                          <VTextarea
                            v-model="settings.vk_msg_start"
                            label="Начало проверки (Шаг 1)"
                            rows="2"
                            placeholder="Дефолтное: Для привязки карты гостя требуется подтвердить номер телефона. Пожалуйста, подтвердите его в 1 клик через наше приложение или выберите другой способ."
                            persistent-placeholder
                            hint="Используется как первое сообщение при начале верификации. Для Lead-форм используйте плейсхолдер {url} для автоматической вставки ссылки на форму."
                            persistent-hint
                          />
                        </VCol>

                        <!-- vk_msg_choose_method -->
                        <VCol cols="12">
                          <VTextarea
                            v-model="settings.vk_msg_choose_method"
                            label="Выбор альтернативного метода (Шаг 2)"
                            rows="2"
                            placeholder="Дефолтное: Не удалось получить номер автоматически. Пожалуйста, выберите другой удобный способ подтверждения:"
                            persistent-placeholder
                            hint="Текст перед выводом кнопок альтернативных способов."
                            persistent-hint
                          />
                        </VCol>

                        <!-- vk_msg_fcall_prompt -->
                        <VCol cols="12" md="6">
                          <VTextarea
                            v-model="settings.vk_msg_fcall_prompt"
                            label="Запрос телефона для Flash Call"
                            rows="2"
                            placeholder="Дефолтное: Пожалуйста, введите ваш номер телефона строго с 7 (в формате 79*********), на который поступит входящий звонок-сброс. Пример: 79991234567"
                            persistent-placeholder
                          />
                        </VCol>

                        <!-- vk_msg_fcall_code -->
                        <VCol cols="12" md="6">
                          <VTextarea
                            v-model="settings.vk_msg_fcall_code"
                            label="Инструкция ввода кода Flash Call"
                            rows="2"
                            placeholder="Дефолтное: На номер {phone} поступает входящий звонок. Пожалуйста, введите последние 4 цифры номера, который вам звонит:"
                            persistent-placeholder
                            hint="Доступен плейсхолдер: {phone} (номер телефона клиента)."
                            persistent-hint
                          />
                        </VCol>

                        <!-- vk_msg_wcall_prompt -->
                        <VCol cols="12" md="6">
                          <VTextarea
                            v-model="settings.vk_msg_wcall_prompt"
                            label="Запрос телефона для Wait Call"
                            rows="2"
                            placeholder="Дефолтное: Пожалуйста, введите ваш номер телефона строго с 7 (в формате 79*********), с которого вы будете звонить на наш виртуальный номер. Пример: 79991234567"
                            persistent-placeholder
                          />
                        </VCol>

                        <!-- vk_msg_wcall_instruct -->
                        <VCol cols="12" md="6">
                          <VTextarea
                            v-model="settings.vk_msg_wcall_instruct"
                            label="Инструкция для Wait Call"
                            rows="3"
                            placeholder="Дефолтное: Пожалуйста, совершите бесплатный вызов со своего номера {phone} на виртуальный номер:\n\n{call_phone}\n\nСистема распознает ваш звонок, автоматически сбросит его и подтвердит ваш профиль."
                            persistent-placeholder
                            hint="Доступны плейсхолдеры: {phone} (телефон клиента), {call_phone} (виртуальный номер для набора)."
                            persistent-hint
                          />
                        </VCol>

                        <!-- vk_msg_tg_instruct -->
                        <VCol cols="12" md="6">
                          <VTextarea
                            v-model="settings.vk_msg_tg_instruct"
                            label="Инструкция для Telegram-бота"
                            rows="2"
                            placeholder="Дефолтное: Для подтверждения через Telegram перейдите по ссылке ниже и нажмите «Запустить»/«Поделиться контактом»:\n\n{link}"
                            persistent-placeholder
                            hint="Доступен плейсхолдер: {link} (уникальная ссылка на Telegram-бот)."
                            persistent-hint
                          />
                        </VCol>

                        <!-- vk_msg_max_instruct -->
                        <VCol cols="12" md="6">
                          <VTextarea
                            v-model="settings.vk_msg_max_instruct"
                            label="Инструкция для мессенджера МАКС"
                            rows="2"
                            placeholder="Дефолтное: Для подтверждения через мессенджер МАКС (VK Teams) перейдите по ссылке ниже:\n\n{link}"
                            persistent-placeholder
                            hint="Доступен плейсхолдер: {link} (уникальная ссылка на МАКС-бот)."
                            persistent-hint
                          />
                        </VCol>

                        <!-- vk_msg_success -->
                        <VCol cols="12" md="6">
                          <VTextarea
                            v-model="settings.vk_msg_success"
                            label="Успешное подтверждение"
                            rows="2"
                            placeholder="Дефолтное: Проверка пройдена успешно!\nВаш бонусный баланс: {balance} бонусов."
                            persistent-placeholder
                            hint="Доступен плейсхолдер: {balance} (бонусы клиента после привязки)."
                            persistent-hint
                          />
                        </VCol>

                        <!-- vk_msg_error_code -->
                        <VCol cols="12" md="6">
                          <VTextarea
                            v-model="settings.vk_msg_error_code"
                            label="Ошибка неверного кода"
                            rows="2"
                            placeholder="Дефолтное: Неверный код. Пожалуйста, проверьте последние 4 цифры входящего номера и введите их еще раз:"
                            persistent-placeholder
                          />
                        </VCol>
                      </VRow>
                    </VExpansionPanelText>
                  </VExpansionPanel>
                </VExpansionPanels>
              </VCol>

              <!-- Telegram Бот -->
              <VCol cols="12">
                <VDivider class="my-2" />
              </VCol>

              <VCol cols="12">
                <div class="text-subtitle-2 font-weight-bold mb-2 d-flex align-center">
                  <VIcon icon="mdi-telegram" class="mr-2" color="info" />
                  Интеграция с Telegram-ботом (для Шага 2)
                </div>
              </VCol>

              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.telegram_bot_token"
                  label="Токен Telegram бота"
                  type="password"
                  placeholder="Bot token от @BotFather"
                  persistent-placeholder
                />
              </VCol>

              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.telegram_bot_username"
                  label="Имя пользователя Telegram бота (без @)"
                  placeholder="Например, my_verification_bot"
                  persistent-placeholder
                />
              </VCol>

              <!-- МАКС Бот -->
              <VCol cols="12">
                <VDivider class="my-2" />
              </VCol>

              <VCol cols="12">
                <div class="text-subtitle-2 font-weight-bold mb-2 d-flex align-center">
                  <VIcon icon="mdi-message-text" class="mr-2" color="success" />
                  Интеграция с ботом МАКС / VK Teams (для Шага 2)
                </div>
              </VCol>

              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.max_bot_token"
                  label="Токен МАКС бота"
                  type="password"
                  placeholder="Токен МАКС бота"
                  persistent-placeholder
                />
              </VCol>

              <VCol cols="12" md="6">
                <VTextField
                  v-model="settings.max_bot_username"
                  label="Имя пользователя МАКС бота"
                  placeholder="Например, my_max_bot"
                  persistent-placeholder
                />
              </VCol>

              <VCol cols="12">
                <VDivider class="my-2" />
              </VCol>

              <VCol cols="12" class="d-flex gap-4 mt-2">
                <VBtn
                  type="submit"
                  :loading="loading"
                  color="success"
                  prepend-icon="mdi-content-save"
                >
                  Сохранить настройки
                </VBtn>
              </VCol>
            </VRow>
          </VForm>
        </VCardText>
      </VCard>
    </VCol>

    <!-- Тестирование отправки -->
    <VCol cols="12" md="4">
      <VCard title="Тест отправки" subtitle="Проверка доставки кодов верификации">
        <VCardText>
          <VForm @submit.prevent="triggerTestSend">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="testForm.phone"
                  label="Номер телефона"
                  placeholder="+79991234567"
                  persistent-placeholder
                  required
                />
              </VCol>

              <VCol cols="12">
                <VTextField
                  v-model="testForm.code"
                  label="Тестовый код (необязательно)"
                  placeholder="Случайный 4-значный"
                  persistent-placeholder
                  type="number"
                />
              </VCol>

              <VCol cols="12">
                <VSelect
                  v-model="testForm.route"
                  label="Канал отправки"
                  :items="testRouteOptions"
                />
              </VCol>

              <VCol cols="12">
                <VBtn
                  block
                  color="primary"
                  type="submit"
                  :loading="testLoading"
                  prepend-icon="mdi-send"
                >
                  Отправить код
                </VBtn>
              </VCol>
            </VRow>
          </VForm>

          <!-- Результат теста -->
          <VExpandTransition>
            <div v-if="showTestResult" class="mt-4">
              <VDivider class="mb-4" />
              
              <div v-if="testLoading" class="d-flex justify-center my-4">
                <VProgressCircular indeterminate color="primary" />
              </div>

              <div v-else-if="testResult">
                <VAlert
                  :type="testResult.success ? 'success' : 'error'"
                  variant="tonal"
                  class="mb-3"
                >
                  <div class="font-weight-bold">
                    {{ testResult.success ? 'Успешно отправлено' : 'Ошибка отправки' }}
                  </div>
                  <div v-if="testResult.success">
                    Тестовый код: <strong>{{ testResult.code }}</strong>
                  </div>
                  <div v-else>
                    {{ testResult.error }}
                  </div>
                </VAlert>

                <!-- Дополнительная информация для Wait Call -->
                <div v-if="testResult.success && testResult.details?.phone_to_call" class="my-4">
                  <VAlert color="info" icon="mdi-phone-incoming" variant="flat" class="text-white text-center pa-4">
                    <div class="text-subtitle-1 font-weight-bold mb-1">ТРЕБУЕТСЯ ВХОДЯЩИЙ ЗВОНОК</div>
                    <div class="text-body-2 mb-2">Пожалуйста, совершите звонок с тестируемого телефона на номер:</div>
                    <div class="text-h5 font-weight-black tracking-wider bg-white text-info py-2 px-4 rounded d-inline-block">
                      {{ testResult.details.phone_to_call }}
                    </div>
                  </VAlert>
                </div>

                <div class="text-caption font-weight-bold text-grey">Детали ответа API:</div>
                <pre class="bg-grey-lighten-4 pa-2 rounded mt-1 overflow-x-auto text-caption" style="max-height: 250px;">{{ JSON.stringify(testResult.details || testResult.error, null, 2) }}</pre>
              </div>
            </div>
          </VExpandTransition>
        </VCardText>
      </VCard>

      <!-- Сброс сессий -->
      <VCard class="mt-4" title="Отладка верификации" subtitle="Сброс активных диалогов бота">
        <VCardText>
          <div class="text-body-2 text-grey-darken-1 mb-4">
            Если вы застряли в каком-то состоянии FSM бота ВК во время тестирования, вы можете принудительно сбросить все активные сессии верификации в базе данных.
          </div>
          <VBtn
            block
            color="error"
            variant="tonal"
            :loading="sessionsLoading"
            prepend-icon="mdi-refresh"
            @click="clearSessions"
          >
            Сбросить активные сессии бота
          </VBtn>
        </VCardText>
      </VCard>
    </VCol>
  </VRow>

  <VSnackbar
    v-model="snackbar.show"
    :color="snackbar.color"
    timeout="3000"
  >
    {{ snackbar.text }}
  </VSnackbar>
</template>

<style lang="scss" scoped>
.v-card {
  backdrop-filter: blur(10px);
  background: rgba(var(--v-theme-surface), 0.8);
}
</style>
