<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()

// Активная вкладка: 'publish' | 'presets' | 'history'
const activeTab = ref('publish')

// Состояние аккаунтов ВК
const accounts = ref([])
const selectedAccountId = ref(null)
const accountsLoading = ref(false)
const accountWarningText = ref('')
const showAccountDialog = ref(false)
const linkingAccount = ref(false)
const newAccountToken = ref('')
const newAccountName = ref('')
const vkOAuthLink = 'https://oauth.vk.com/authorize?client_id=2685278&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=wall,photos,offline,groups,messages&response_type=token&v=5.131'

// --- Вкладка 1: Создание публикации ---
const postingMode = ref('preset') // 'preset' | 'manual'
const selectedPresetId = ref(null)
const manualGroupsInput = ref('')
const checkingGroups = ref(false)
const targetGroups = ref([]) // Список проверенных групп для отправки

const postText = ref('')
const uploadedImages = ref([])
const isUploadingImage = ref(false)
const fileInput = ref(null)
const delaySeconds = ref(20)

// Процесс выполнения рассылки
const isPublishing = ref(false)
const showPublishModal = ref(false)
const publishProgress = ref(0)
const publishLogs = ref([])
const publishSummary = ref(null)

// --- Вкладка 2: Блоки (Пресеты) групп ---
const presets = ref([])
const presetsLoading = ref(false)
const showPresetDialog = ref(false)
const presetSaving = ref(false)
const presetForm = ref({
  id: null,
  name: '',
  description: '',
  raw_input: '',
  groups_data: []
})
const presetChecking = ref(false)

// --- Вкладка 3: История и Аналитика ---
const historyItems = ref([])
const historyLoading = ref(false)
const historyPage = ref(1)
const historyPageSize = ref(20)
const historyTotal = ref(0)
const historyStatusFilter = ref('all')
const historySearch = ref('')
const historySummary = ref({
  published_posts: 0,
  total_views: 0,
  total_likes: 0,
  total_reposts: 0
})
const refreshingStats = ref(false)

// Список популярных эмодзи для быстрой вставки
const popularEmojis = ['🔥', '🎉', '🍕', '🍣', '🍔', '🎁', '✨', '⚡', '📢', '🔔', '❤️', '👍', '😋', '🚗', '📞']

// --- Жизненный цикл ---
onMounted(async () => {
  await loadAccounts()
  await loadPresets()
  await loadHistory()
})

// --- Загрузка аккаунтов ---
async function loadAccounts() {
  accountsLoading.value = true
  try {
    const res = await axios.get('/api/v1/vk-group-posting/accounts')
    accounts.value = res.data || []
    if (accounts.value.length > 0 && !selectedAccountId.value) {
      selectedAccountId.value = accounts.value[0].id
    }
  } catch (err) {
    console.error('Ошибка загрузки аккаунтов ВК:', err)
    toast.error('Не удалось загрузить личные аккаунты ВКонтакте')
  } finally {
    accountsLoading.value = false
  }
}

// --- Загрузка пресетов ---
async function loadPresets() {
  presetsLoading.value = true
  try {
    const res = await axios.get('/api/v1/vk-group-posting/presets')
    presets.value = res.data || []
  } catch (err) {
    console.error('Ошибка загрузки пресетов:', err)
  } finally {
    presetsLoading.value = false
  }
}

// --- Загрузка истории ---
async function loadHistory() {
  historyLoading.value = true
  try {
    const params = {
      page: historyPage.value,
      page_size: historyPageSize.value,
      status: historyStatusFilter.value !== 'all' ? historyStatusFilter.value : undefined,
      search: historySearch.value ? historySearch.value.trim() : undefined
    }
    const res = await axios.get('/api/v1/vk-group-posting/history', { params })
    historyItems.value = res.data.items || []
    historyTotal.value = res.data.total || 0
    if (res.data.summary) {
      historySummary.value = res.data.summary
    }
  } catch (err) {
    console.error('Ошибка загрузки истории постов:', err)
    toast.error('Не удалось загрузить историю постов')
  } finally {
    historyLoading.value = false
  }
}

// --- Проверка введенных групп (Вкладка Публикация) ---
async function checkManualGroups() {
  if (!selectedAccountId.value) {
    toast.warning('Сначала выберите личный аккаунт ВКонтакте')
    return
  }
  if (!manualGroupsInput.value.trim()) {
    toast.warning('Введите хотя бы одну ссылку или ID группы')
    return
  }

  checkingGroups.value = true
  try {
    const res = await axios.post('/api/v1/vk-group-posting/groups/check', {
      account_id: selectedAccountId.value,
      raw_input: manualGroupsInput.value
    })
    targetGroups.value = res.data.groups || []
    if (res.data.account_warning) {
      accountWarningText.value = res.data.account_warning
      toast.warning(res.data.account_warning)
    } else {
      accountWarningText.value = ''
    }
    if (targetGroups.value.length === 0) {
      toast.info('Группы по указанным ссылкам не найдены')
    } else {
      toast.success(`Проверено сообществ: ${res.data.total}. Открытых стен: ${res.data.open_count}`)
    }
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Ошибка проверки сообществ'
    toast.error(msg)
  } finally {
    checkingGroups.value = false
  }
}

async function linkNewAccount() {
  if (!newAccountToken.value.trim()) {
    toast.warning('Вставьте токен доступа ВКонтакте')
    return
  }
  linkingAccount.value = true
  try {
    const res = await axios.post('/api/v1/vk-group-posting/accounts/link-token', {
      token: newAccountToken.value.trim(),
      name: newAccountName.value.trim() || undefined
    })
    toast.success(res.data.message || 'Аккаунт успешно подключен!')
    showAccountDialog.value = false
    newAccountToken.value = ''
    newAccountName.value = ''
    accountWarningText.value = ''
    await loadAccounts()
    if (res.data.account?.id) {
      selectedAccountId.value = res.data.account.id
    }
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Ошибка привязки аккаунта'
    toast.error(msg)
  } finally {
    linkingAccount.value = false
  }
}

// Выбор пресета в публикациях
function onPresetSelect(presetId) {
  selectedPresetId.value = presetId
  const preset = presets.value.find(p => p.id === presetId)
  if (preset && preset.groups_data) {
    targetGroups.value = [...preset.groups_data]
  } else {
    targetGroups.value = []
  }
}

// Оставить только открытые группы
function filterOnlyOpenTargetGroups() {
  targetGroups.value = targetGroups.value.filter(g => g.can_publish)
  toast.info(`Оставлены только открытые сообщества (${targetGroups.value.length} шт.)`)
}

// Удалить конкретную группу из списка публикации
function removeTargetGroup(index) {
  targetGroups.value.splice(index, 1)
}

// Вставка эмодзи в текст
function insertEmoji(emoji) {
  postText.value += emoji
}

// Загрузка фото
function triggerFileUpload() {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

async function handleFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    toast.error('Пожалуйста, выберите файл изображения (JPG, PNG)')
    return
  }

  isUploadingImage.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await axios.post('/api/v1/vk-group-posting/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    if (res.data.url) {
      uploadedImages.value.push(res.data.url)
      toast.success('Изображение успешно прикреплено')
    }
  } catch (err) {
    toast.error('Ошибка загрузки изображения на сервер')
  } finally {
    isUploadingImage.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

function removeUploadedImage(index) {
  uploadedImages.value.splice(index, 1)
}

// --- Запуск публикации ---
async function startPublishing() {
  if (!selectedAccountId.value) {
    toast.warning('Выберите личный аккаунт ВК')
    return
  }
  if (!targetGroups.value.length) {
    toast.warning('Список целевых сообществ пуст. Добавьте или проверьте группы')
    return
  }
  if (!postText.value.trim() && uploadedImages.value.length === 0) {
    toast.warning('Введите текст записи или прикрепите хотя бы одно изображение')
    return
  }

  const validGroups = targetGroups.value.filter(g => g.can_publish)
  if (validGroups.length === 0) {
    toast.error('Ни в одной из выбранных групп стена не открыта для публикации!')
    return
  }

  const confirmed = confirm(
    `Запустить публикацию записи в ${validGroups.length} открытых группах?\nЗадержка антиспама: ${delaySeconds.value} сек.`
  )
  if (!confirmed) return

  isPublishing.value = true
  showPublishModal.value = true
  publishProgress.value = 0
  publishLogs.value = []
  publishSummary.value = null

  try {
    const payload = {
      account_id: selectedAccountId.value,
      text: postText.value,
      media_urls: uploadedImages.value,
      groups: validGroups.map(g => ({
        id: g.id,
        name: g.name,
        screen_name: g.screen_name,
        photo: g.photo
      })),
      delay_seconds: delaySeconds.value,
      preset_id: postingMode.value === 'preset' ? selectedPresetId.value : null
    }

    const res = await axios.post('/api/v1/vk-group-posting/publish', payload)
    publishSummary.value = res.data
    publishLogs.value = res.data.results || []
    toast.success(`Рассылка завершена! Опубликовано: ${res.data.success_count} из ${res.data.total}`)
    
    // Перезагружаем историю
    await loadHistory()
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Ошибка во время рассылки'
    toast.error(msg)
  } finally {
    isPublishing.value = false
  }
}

// --- Логика Пресетов (Блоков групп) ---
function openCreatePresetDialog() {
  presetForm.value = {
    id: null,
    name: '',
    description: '',
    raw_input: '',
    groups_data: []
  }
  showPresetDialog.value = true
}

function openEditPresetDialog(preset) {
  presetForm.value = {
    id: preset.id,
    name: preset.name,
    description: preset.description || '',
    raw_input: (preset.groups_data || []).map(g => g.url || `https://vk.com/${g.screen_name || g.id}`).join('\n'),
    groups_data: [...(preset.groups_data || [])]
  }
  showPresetDialog.value = true
}

async function checkPresetGroups() {
  if (!selectedAccountId.value) {
    toast.warning('Выберите аккаунт ВК в верхней панели для проверки')
    return
  }
  if (!presetForm.value.raw_input.trim()) {
    toast.warning('Введите ссылки на группы для проверки')
    return
  }

  presetChecking.value = true
  try {
    const res = await axios.post('/api/v1/vk-group-posting/groups/check', {
      account_id: selectedAccountId.value,
      raw_input: presetForm.value.raw_input
    })
    presetForm.value.groups_data = res.data.groups || []
    if (res.data.account_warning) {
      accountWarningText.value = res.data.account_warning
      toast.warning(res.data.account_warning)
    } else {
      accountWarningText.value = ''
    }
    toast.success(`Проверено: ${res.data.total}. Открытых для публикации: ${res.data.open_count}`)
  } catch (err) {
    const msg = err.response?.data?.detail || err.message || 'Ошибка проверки групп'
    toast.error(msg)
  } finally {
    presetChecking.value = false
  }
}

async function savePreset() {
  if (!presetForm.value.name.trim()) {
    toast.warning('Укажите название списка групп')
    return
  }

  presetSaving.value = true
  try {
    await axios.post('/api/v1/vk-group-posting/presets', {
      id: presetForm.value.id,
      name: presetForm.value.name.trim(),
      description: presetForm.value.description?.trim(),
      groups_data: presetForm.value.groups_data
    })
    toast.success('Блок групп успешно сохранен')
    showPresetDialog.value = false
    await loadPresets()
  } catch (err) {
    toast.error('Не удалось сохранить блок групп')
  } finally {
    presetSaving.value = false
  }
}

async function deletePreset(presetId) {
  if (!confirm('Вы уверены, что хотите удалить этот блок групп?')) return
  try {
    await axios.delete(`/api/v1/vk-group-posting/presets/${presetId}`)
    toast.success('Блок групп удален')
    await loadPresets()
    if (selectedPresetId.value === presetId) {
      selectedPresetId.value = null
      targetGroups.value = []
    }
  } catch (err) {
    toast.error('Ошибка удаления блока')
  }
}

// --- Обновление метрик и удаление постов ---
async function refreshAllStats() {
  refreshingStats.value = true
  try {
    const res = await axios.post('/api/v1/vk-group-posting/history/refresh-stats', {
      account_id: selectedAccountId.value
    })
    toast.success(res.data.message || 'Метрики успешно обновлены')
    await loadHistory()
  } catch (err) {
    const msg = err.response?.data?.detail || 'Ошибка обновления метрик'
    toast.error(msg)
  } finally {
    refreshingStats.value = false
  }
}

async function deleteHistoryPost(itemId) {
  if (!confirm('Удалить эту запись из истории? Сам пост в ВК не будет затронут.')) return
  try {
    await axios.delete(`/api/v1/vk-group-posting/history/${itemId}`)
    toast.success('Запись удалена из истории')
    await loadHistory()
  } catch (err) {
    toast.error('Ошибка удаления записи')
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '—'
  try {
    const d = new Date(isoStr)
    return d.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return isoStr
  }
}
</script>

<template>
  <div class="group-posting-page">
    <!-- Верхняя информационная карточка с выбором аккаунта -->
    <VCard class="mb-5 elevation-1">
      <VCardItem class="py-4">
        <div class="d-flex flex-wrap align-center justify-space-between gap-4">
          <div class="d-flex align-center gap-3">
            <VAvatar color="primary" variant="tonal" size="44">
              <VIcon icon="bx-share-alt" size="26" />
            </VAvatar>
            <div>
              <h2 class="text-h6 font-weight-bold mb-0">Постинг в группах ВКонтакте</h2>
              <div class="text-body-2 text-medium-emphasis">
                Рассылка постов на стены открытых сообществ от имени личного аккаунта и сбор аналитики
              </div>
            </div>
          </div>

          <!-- Селект выбора аккаунта ВК -->
          <div class="d-flex align-center gap-3" style="min-width: 320px;">
            <VSelect
              v-model="selectedAccountId"
              :items="accounts"
              item-title="name"
              item-value="id"
              label="Личный аккаунт ВК (автор)"
              density="compact"
              variant="outlined"
              hide-details
              prepend-inner-icon="bx-user"
              :loading="accountsLoading"
              :disabled="accounts.length === 0"
            >
              <template #item="{ props, item }">
                <VListItem v-bind="props" :subtitle="item.raw.phone || 'Активен в мультичате'">
                  <template #prepend>
                    <VIcon icon="bx-user-check" color="success" class="mr-2" />
                  </template>
                </VListItem>
              </template>
              <template #no-data>
                <div class="pa-3 text-caption text-medium-emphasis">
                  Нет подключенных личных аккаунтов. Подключите аккаунт ВК в Мультичате.
                </div>
              </template>
            </VSelect>

            <VBtn
              variant="tonal"
              color="primary"
              size="small"
              icon="bx-refresh"
              title="Обновить аккаунты"
              @click="loadAccounts"
            />

            <VBtn
              color="primary"
              variant="flat"
              size="small"
              prepend-icon="bx-user-plus"
              @click="showAccountDialog = true"
            >
              Подключить
            </VBtn>
          </div>
        </div>
      </VCardItem>

      <!-- Навигационные вкладки -->
      <VTabs v-model="activeTab" density="comfortable" color="primary" class="border-t px-2">
        <VTab value="publish">
          <VIcon icon="bx-send" class="mr-2" />
          Новая рассылка
        </VTab>
        <VTab value="presets">
          <VIcon icon="bx-folder" class="mr-2" />
          Списки групп (Блоки)
          <VChip size="x-small" color="primary" class="ml-2 font-weight-bold">{{ presets.length }}</VChip>
        </VTab>
        <VTab value="history">
          <VIcon icon="bx-history" class="mr-2" />
          История и Аналитика постов
          <VChip size="x-small" color="success" class="ml-2 font-weight-bold">{{ historyTotal }}</VChip>
        </VTab>
      </VTabs>
    </VCard>

    <!-- Предупреждение о статусе аккаунта ВК -->
    <VAlert
      v-if="accountWarningText"
      type="warning"
      variant="tonal"
      closable
      class="mb-4 elevation-1"
    >
      <div class="d-flex align-center justify-space-between flex-wrap gap-2">
        <div class="d-flex align-center gap-2">
          <VIcon icon="bx-error-circle" />
          <span>{{ accountWarningText }}</span>
        </div>
        <VBtn
          size="small"
          color="warning"
          variant="flat"
          prepend-icon="bx-refresh"
          @click="showAccountDialog = true"
        >
          Обновить токен аккаунта
        </VBtn>
      </div>
    </VAlert>

    <VWindow v-model="activeTab">
      <!-- ================= ВКЛАДКА 1: НОВАЯ РАССЫЛКА ================= -->
      <VWindowItem value="publish">
        <VRow>
          <!-- Левая колонка: Выбор и проверка групп -->
          <VCol cols="12" md="5">
            <VCard class="elevation-1 mb-4 h-100 d-flex flex-column">
              <VCardItem class="pb-2">
                <VCardTitle class="text-subtitle-1 font-weight-bold d-flex align-center gap-2">
                  <VIcon icon="bx-group" color="primary" />
                  1. Целевые сообщества
                </VCardTitle>
                <VCardSubtitle>
                  Выберите готовый список или вставьте ссылки на группы
                </VCardSubtitle>
              </VCardItem>

              <VCardText class="flex-grow-1">
                <!-- Переключатель режима выбора -->
                <VBtnToggle
                  v-model="postingMode"
                  mandatory
                  density="compact"
                  color="primary"
                  variant="outlined"
                  class="mb-4 w-100"
                >
                  <VBtn value="preset" class="flex-1">
                    <VIcon icon="bx-collection" class="mr-1" />
                    Готовый список
                  </VBtn>
                  <VBtn value="manual" class="flex-1">
                    <VIcon icon="bx-link" class="mr-1" />
                    Ввести ссылки
                  </VBtn>
                </VBtnToggle>

                <!-- Режим: Готовый пресет -->
                <div v-if="postingMode === 'preset'">
                  <VSelect
                    :model-value="selectedPresetId"
                    :items="presets"
                    item-title="name"
                    item-value="id"
                    label="Выберите готовый блок групп"
                    variant="outlined"
                    density="comfortable"
                    placeholder="Например: Барахолки Самары"
                    @update:model-value="onPresetSelect"
                  >
                    <template #item="{ props, item }">
                      <VListItem v-bind="props" :subtitle="`${(item.raw.groups_data || []).length} сообществ`">
                        <template #prepend>
                          <VIcon icon="bx-folder" color="primary" class="mr-2" />
                        </template>
                      </VListItem>
                    </template>
                  </VSelect>
                </div>

                <!-- Режим: Ручной ввод ссылок -->
                <div v-else>
                  <VTextarea
                    v-model="manualGroupsInput"
                    label="Ссылки на группы (по одной на строку)"
                    placeholder="https://vk.com/club123456&#10;https://vk.com/baraholka_samara&#10;public987654"
                    rows="4"
                    variant="outlined"
                    density="comfortable"
                    hint="Поддерживаются полные URL, короткие имена и ID"
                    persistent-hint
                    class="mb-3"
                  />
                  <VBtn
                    color="primary"
                    variant="tonal"
                    block
                    :loading="checkingGroups"
                    :disabled="checkingGroups || !manualGroupsInput.trim()"
                    @click="checkManualGroups"
                  >
                    <VIcon icon="bx-check-shield" class="mr-2" />
                    Проверить открытость стен
                  </VBtn>
                </div>

                <!-- Блок со списком проверенных сообществ -->
                <div v-if="targetGroups.length > 0" class="mt-4">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption font-weight-bold text-uppercase">
                      Группы к отправке ({{ targetGroups.length }}):
                    </span>
                    <VBtn
                      size="x-small"
                      variant="text"
                      color="warning"
                      @click="filterOnlyOpenTargetGroups"
                    >
                      Исключить закрытые
                    </VBtn>
                  </div>

                  <div class="target-groups-list border rounded pa-2" style="max-height: 280px; overflow-y: auto;">
                    <div
                      v-for="(grp, idx) in targetGroups"
                      :key="grp.id || idx"
                      class="d-flex align-center justify-space-between pa-2 border-b last-border-none group-item"
                    >
                      <div class="d-flex align-center gap-2 overflow-hidden mr-2">
                        <VAvatar size="30" rounded>
                          <VImg v-if="grp.photo" :src="grp.photo" />
                          <VIcon v-else icon="bx-group" size="20" />
                        </VAvatar>
                        <div class="text-truncate">
                          <a
                            :href="grp.url"
                            target="_blank"
                            class="text-body-2 font-weight-medium text-decoration-none text-high-emphasis text-truncate d-block"
                          >
                            {{ grp.name }}
                          </a>
                          <div class="d-flex align-center gap-1">
                            <VChip
                              size="x-small"
                              :color="grp.can_publish ? 'success' : 'error'"
                              variant="flat"
                              class="font-weight-medium"
                            >
                              {{ grp.can_publish ? '🟢 Открыта' : '🔴 Закрыта' }}
                            </VChip>
                            <span v-if="grp.members_count" class="text-caption text-medium-emphasis">
                              {{ grp.members_count.toLocaleString() }} уч.
                            </span>
                          </div>
                        </div>
                      </div>

                      <VBtn
                        icon="bx-x"
                        variant="text"
                        size="x-small"
                        color="error"
                        @click="removeTargetGroup(idx)"
                      />
                    </div>
                  </div>
                </div>
              </VCardText>
            </VCard>
          </VCol>

          <!-- Правая колонка: Текст, Картинка и Настройки отправки -->
          <VCol cols="12" md="7">
            <VCard class="elevation-1">
              <VCardItem class="pb-2">
                <VCardTitle class="text-subtitle-1 font-weight-bold d-flex align-center gap-2">
                  <VIcon icon="bx-edit" color="primary" />
                  2. Содержимое публикации и параметры
                </VCardTitle>
                <VCardSubtitle>
                  Текст записи, прикрепленное фото и настройки задержки антиспама
                </VCardSubtitle>
              </VCardItem>

              <VCardText>
                <!-- Текст поста -->
                <div class="mb-3">
                  <div class="d-flex align-center justify-space-between mb-1">
                    <label class="text-caption font-weight-bold text-uppercase">Текст записи на стене</label>
                    <!-- Быстрые эмодзи -->
                    <div class="d-flex gap-1 flex-wrap">
                      <span
                        v-for="em in popularEmojis"
                        :key="em"
                        class="emoji-btn cursor-pointer"
                        @click="insertEmoji(em)"
                      >
                        {{ em }}
                      </span>
                    </div>
                  </div>
                  <VTextarea
                    v-model="postText"
                    placeholder="Введите текст вашей публикации... Поддерживаются эмодзи, ссылки и контакты."
                    rows="6"
                    variant="outlined"
                    counter
                    auto-grow
                  />
                </div>

                <!-- Загрузка изображения -->
                <div class="mb-4">
                  <label class="text-caption font-weight-bold text-uppercase d-block mb-1">
                    Прикрепленное фото
                  </label>

                  <input
                    ref="fileInput"
                    type="file"
                    accept="image/*"
                    class="d-none"
                    @change="handleFileSelected"
                  />

                  <div class="d-flex align-center gap-3 flex-wrap">
                    <VBtn
                      variant="tonal"
                      color="primary"
                      prepend-icon="bx-image-add"
                      :loading="isUploadingImage"
                      @click="triggerFileUpload"
                    >
                      Загрузить изображение
                    </VBtn>

                    <!-- Превью загруженных фото -->
                    <div
                      v-for="(imgUrl, idx) in uploadedImages"
                      :key="idx"
                      class="position-relative border rounded overflow-hidden"
                      style="width: 70px; height: 70px;"
                    >
                      <VImg :src="imgUrl" cover class="h-100 w-100" />
                      <VBtn
                        icon="bx-x"
                        size="x-small"
                        color="error"
                        class="position-absolute"
                        style="top: 2px; right: 2px; min-width: 20px; width: 20px; height: 20px;"
                        @click="removeUploadedImage(idx)"
                      />
                    </div>
                  </div>
                </div>

                <!-- Настройки задержки антиспама -->
                <div class="pa-3 bg-light rounded border mb-4">
                  <div class="d-flex align-center justify-space-between mb-1">
                    <span class="text-body-2 font-weight-medium d-flex align-center gap-1">
                      <VIcon icon="bx-shield-quarter" color="success" size="18" />
                      Интервал между публикациями:
                    </span>
                    <span class="text-body-2 font-weight-bold text-primary">{{ delaySeconds }} сек.</span>
                  </div>
                  <VSlider
                    v-model="delaySeconds"
                    min="10"
                    max="60"
                    step="5"
                    thumb-label
                    color="primary"
                    hide-details
                  />
                  <div class="text-caption text-medium-emphasis mt-1">
                    Рекомендуемый интервал от 15 до 30 секунд для предотвращения блокировок за спам от алгоритмов ВКонтакте.
                  </div>
                </div>

                <!-- Кнопка запуска -->
                <VBtn
                  color="success"
                  size="large"
                  block
                  prepend-icon="bx-rocket"
                  :disabled="targetGroups.length === 0 || (!postText.trim() && uploadedImages.length === 0) || isPublishing"
                  @click="startPublishing"
                >
                  Опубликовать в {{ targetGroups.filter(g => g.can_publish).length }} сообществах
                </VBtn>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VWindowItem>

      <!-- ================= ВКЛАДКА 2: БЛОКИ (ПРЕСЕТЫ) ГРУПП ================= -->
      <VWindowItem value="presets">
        <VCard class="elevation-1">
          <VCardItem class="py-4">
            <div class="d-flex align-center justify-space-between flex-wrap gap-3">
              <div>
                <VCardTitle class="text-h6 font-weight-bold mb-0">Сохраненные блоки сообществ</VCardTitle>
                <VCardSubtitle>
                  Создавайте готовые наборы групп (по тематикам, городам или интересам) для быстрой рассылки
                </VCardSubtitle>
              </div>
              <VBtn color="primary" prepend-icon="bx-plus" @click="openCreatePresetDialog">
                Создать новый блок
              </VBtn>
            </div>
          </VCardItem>

          <VCardText>
            <div v-if="presetsLoading" class="text-center py-6">
              <VProgressCircular indeterminate color="primary" />
            </div>

            <div v-else-if="presets.length === 0" class="text-center py-8 text-medium-emphasis">
              <VIcon icon="bx-folder-open" size="48" class="mb-2" />
              <div>Нет сохраненных списков групп. Нажмите «Создать новый блок» для добавления.</div>
            </div>

            <VRow v-else>
              <VCol v-for="prs in presets" :key="prs.id" cols="12" md="4">
                <VCard variant="outlined" class="h-100 d-flex flex-column">
                  <VCardItem>
                    <div class="d-flex align-start justify-space-between">
                      <div>
                        <div class="text-subtitle-1 font-weight-bold text-truncate">{{ prs.name }}</div>
                        <div class="text-caption text-medium-emphasis text-truncate mb-2">
                          {{ prs.description || 'Без описания' }}
                        </div>
                      </div>
                      <VChip size="small" color="primary" variant="tonal" class="font-weight-bold">
                        {{ (prs.groups_data || []).length }} групп
                      </VChip>
                    </div>
                  </VCardItem>

                  <VCardText class="flex-grow-1 pt-0">
                    <!-- Мини-превью групп в блоке -->
                    <div class="d-flex align-center gap-1 flex-wrap mb-3">
                      <VAvatar
                        v-for="(grp, gIdx) in (prs.groups_data || []).slice(0, 5)"
                        :key="gIdx"
                        size="28"
                        rounded
                        :title="grp.name"
                      >
                        <VImg v-if="grp.photo" :src="grp.photo" />
                        <VIcon v-else icon="bx-group" size="18" />
                      </VAvatar>
                      <span v-if="(prs.groups_data || []).length > 5" class="text-caption text-medium-emphasis ml-1">
                        +{{ (prs.groups_data || []).length - 5 }}
                      </span>
                    </div>

                    <div class="text-caption text-medium-emphasis">
                      Открытых стен:
                      <b class="text-success">
                        {{ (prs.groups_data || []).filter(g => g.can_publish).length }}
                      </b>
                    </div>
                  </VCardText>

                  <VDivider />

                  <VCardActions class="pa-2">
                    <VBtn
                      size="small"
                      color="primary"
                      variant="text"
                      prepend-icon="bx-send"
                      @click="() => { activeTab = 'publish'; postingMode = 'preset'; onPresetSelect(prs.id) }"
                    >
                      Использовать
                    </VBtn>
                    <VSpacer />
                    <VBtn
                      icon="bx-edit"
                      size="small"
                      variant="text"
                      color="default"
                      @click="openEditPresetDialog(prs)"
                    />
                    <VBtn
                      icon="bx-trash"
                      size="small"
                      variant="text"
                      color="error"
                      @click="deletePreset(prs.id)"
                    />
                  </VCardActions>
                </VCard>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VWindowItem>

      <!-- ================= ВКЛАДКА 3: ИСТОРИЯ И АНАЛИТИКА ================= -->
      <VWindowItem value="history">
        <!-- Виджеты общей статистики -->
        <VRow class="mb-4">
          <VCol cols="12" sm="6" md="3">
            <VCard class="pa-3 elevation-1">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="text-caption text-medium-emphasis font-weight-medium">Опубликовано постов</div>
                  <div class="text-h5 font-weight-bold text-success">{{ historySummary.published_posts }}</div>
                </div>
                <VAvatar color="success" variant="tonal" rounded size="42">
                  <VIcon icon="bx-check-circle" size="24" />
                </VAvatar>
              </div>
            </VCard>
          </VCol>

          <VCol cols="12" sm="6" md="3">
            <VCard class="pa-3 elevation-1">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="text-caption text-medium-emphasis font-weight-medium">Просмотры постов (👁️)</div>
                  <div class="text-h5 font-weight-bold text-primary">{{ historySummary.total_views.toLocaleString() }}</div>
                </div>
                <VAvatar color="primary" variant="tonal" rounded size="42">
                  <VIcon icon="bx-show" size="24" />
                </VAvatar>
              </div>
            </VCard>
          </VCol>

          <VCol cols="12" sm="6" md="3">
            <VCard class="pa-3 elevation-1">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="text-caption text-medium-emphasis font-weight-medium">Лайки сообществ (❤️)</div>
                  <div class="text-h5 font-weight-bold text-error">{{ historySummary.total_likes.toLocaleString() }}</div>
                </div>
                <VAvatar color="error" variant="tonal" rounded size="42">
                  <VIcon icon="bx-heart" size="24" />
                </VAvatar>
              </div>
            </VCard>
          </VCol>

          <VCol cols="12" sm="6" md="3">
            <VCard class="pa-3 elevation-1">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <div class="text-caption text-medium-emphasis font-weight-medium">Репосты (🔁)</div>
                  <div class="text-h5 font-weight-bold text-info">{{ historySummary.total_reposts.toLocaleString() }}</div>
                </div>
                <VAvatar color="info" variant="tonal" rounded size="42">
                  <VIcon icon="bx-share" size="24" />
                </VAvatar>
              </div>
            </VCard>
          </VCol>
        </VRow>

        <!-- Таблица истории постов -->
        <VCard class="elevation-1">
          <VCardItem class="py-3">
            <div class="d-flex flex-wrap align-center justify-space-between gap-3">
              <div class="d-flex align-center gap-3 flex-wrap">
                <VTextField
                  v-model="historySearch"
                  placeholder="Поиск по группе или тексту..."
                  density="compact"
                  variant="outlined"
                  hide-details
                  prepend-inner-icon="bx-search"
                  clearable
                  style="min-width: 260px;"
                  @update:model-value="loadHistory"
                />

                <VSelect
                  v-model="historyStatusFilter"
                  :items="[
                    { title: 'Все статусы', value: 'all' },
                    { title: 'Опубликованные', value: 'published' },
                    { title: 'Удаленные', value: 'deleted' },
                    { title: 'Ошибки', value: 'failed' }
                  ]"
                  density="compact"
                  variant="outlined"
                  hide-details
                  style="min-width: 170px;"
                  @update:model-value="loadHistory"
                />
              </div>

              <div class="d-flex align-center gap-2">
                <VBtn
                  color="primary"
                  variant="tonal"
                  prepend-icon="bx-refresh"
                  :loading="refreshingStats"
                  @click="refreshAllStats"
                >
                  Обновить метрики из VK
                </VBtn>
              </div>
            </div>
          </VCardItem>

          <VTable class="text-no-wrap">
            <thead>
              <tr>
                <th>Дата</th>
                <th>Сообщество</th>
                <th>Текст / Медиа</th>
                <th>Ссылка на пост</th>
                <th>👁️ Просмотры</th>
                <th>❤️ Лайки</th>
                <th>Статус</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="historyLoading">
                <td colspan="8" class="text-center py-6">
                  <VProgressCircular indeterminate color="primary" />
                </td>
              </tr>
              <tr v-else-if="historyItems.length === 0">
                <td colspan="8" class="text-center py-6 text-medium-emphasis">
                  История размещенных постов пуста
                </td>
              </tr>
              <tr v-for="item in historyItems" :key="item.id">
                <td class="text-caption">
                  {{ formatDate(item.published_at || item.created_at) }}
                  <div class="text-medium-emphasis">{{ item.account_name || 'Личный аккаунт' }}</div>
                </td>

                <td>
                  <div class="d-flex align-center gap-2">
                    <VAvatar size="32" rounded>
                      <VImg v-if="item.group_photo" :src="item.group_photo" />
                      <VIcon v-else icon="bx-group" size="20" />
                    </VAvatar>
                    <div style="max-width: 180px;">
                      <a
                        :href="`https://vk.com/${item.group_screen_name || 'club' + item.group_id}`"
                        target="_blank"
                        class="text-body-2 font-weight-medium text-decoration-none text-truncate d-block"
                      >
                        {{ item.group_name || `Группа ${item.group_id}` }}
                      </a>
                    </div>
                  </div>
                </td>

                <td>
                  <div class="d-flex align-center gap-2" style="max-width: 250px;">
                    <VImg
                      v-if="item.media_urls && item.media_urls.length > 0"
                      :src="item.media_urls[0]"
                      width="36"
                      height="36"
                      cover
                      rounded
                    />
                    <div class="text-caption text-truncate" :title="item.text">
                      {{ item.text || '—' }}
                    </div>
                  </div>
                </td>

                <td>
                  <VBtn
                    v-if="item.post_url"
                    :href="item.post_url"
                    target="_blank"
                    size="small"
                    variant="tonal"
                    color="primary"
                    prepend-icon="bx-link-external"
                  >
                    Открыть в VK
                  </VBtn>
                  <span v-else class="text-caption text-medium-emphasis">—</span>
                </td>

                <td>
                  <span class="font-weight-bold text-primary">
                    {{ item.views_count.toLocaleString() }}
                  </span>
                </td>

                <td>
                  <span class="font-weight-bold text-error">
                    {{ item.likes_count.toLocaleString() }}
                  </span>
                </td>

                <td>
                  <VChip
                    v-if="item.status === 'published'"
                    color="success"
                    size="small"
                    variant="tonal"
                    prepend-icon="bx-check"
                  >
                    Активен
                  </VChip>
                  <VChip
                    v-else-if="item.status === 'deleted'"
                    color="warning"
                    size="small"
                    variant="tonal"
                    prepend-icon="bx-trash"
                  >
                    Удален
                  </VChip>
                  <VChip
                    v-else
                    color="error"
                    size="small"
                    variant="tonal"
                    :title="item.error_message"
                  >
                    Ошибка
                  </VChip>
                </td>

                <td>
                  <VBtn
                    icon="bx-trash"
                    size="small"
                    variant="text"
                    color="error"
                    @click="deleteHistoryPost(item.id)"
                  />
                </td>
              </tr>
            </tbody>
          </VTable>

          <!-- Пагинация -->
          <VCardActions v-if="historyTotal > historyPageSize" class="pa-3 d-flex justify-center">
            <VPagination
              v-model="historyPage"
              :length="Math.ceil(historyTotal / historyPageSize)"
              :total-visible="5"
              density="comfortable"
              @update:model-value="loadHistory"
            />
          </VCardActions>
        </VCard>
      </VWindowItem>
    </VWindow>

    <!-- МОДАЛЬНОЕ ОКНО: Создание/Редактирование блока групп -->
    <VDialog v-model="showPresetDialog" max-width="650px" persistent>
      <VCard>
        <VCardTitle class="pa-4 font-weight-bold d-flex align-center justify-space-between">
          <span>{{ presetForm.id ? 'Редактирование блока групп' : 'Создание блока групп' }}</span>
          <VBtn icon="bx-x" variant="text" size="small" @click="showPresetDialog = false" />
        </VCardTitle>

        <VCardText class="pa-4 pt-0">
          <VTextField
            v-model="presetForm.name"
            label="Название блока *"
            placeholder="Например: Самара Барахолки и Объявления"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <VTextField
            v-model="presetForm.description"
            label="Описание или теги"
            placeholder="Тематические сообщества для акций"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <VTextarea
            v-model="presetForm.raw_input"
            label="Ссылки на сообщества ВКонтакте *"
            placeholder="https://vk.com/club12345&#10;https://vk.com/samara_free&#10;baraholka_tlt"
            rows="5"
            variant="outlined"
            hint="Вставьте ссылки на группы. Каждая ссылка с новой строки."
            persistent-hint
            class="mb-3"
          />

          <div class="d-flex align-center justify-space-between mb-3">
            <VBtn
              color="primary"
              variant="tonal"
              size="small"
              prepend-icon="bx-check-circle"
              :loading="presetChecking"
              :disabled="presetChecking || !presetForm.raw_input.trim()"
              @click="checkPresetGroups"
            >
              Проверить открытость стен
            </VBtn>

            <span v-if="presetForm.groups_data.length > 0" class="text-caption text-medium-emphasis">
              Проверено: {{ presetForm.groups_data.length }} групп
              (открыто: {{ presetForm.groups_data.filter(g => g.can_publish).length }})
            </span>
          </div>

          <!-- Список проверенных групп в пресете -->
          <div
            v-if="presetForm.groups_data.length > 0"
            class="border rounded pa-2"
            style="max-height: 180px; overflow-y: auto;"
          >
            <div
              v-for="(grp, idx) in presetForm.groups_data"
              :key="idx"
              class="d-flex align-center justify-space-between py-1 border-b last-border-none"
            >
              <div class="text-caption text-truncate mr-2">
                {{ grp.name }}
              </div>
              <VChip
                size="x-small"
                :color="grp.can_publish ? 'success' : 'error'"
                variant="flat"
              >
                {{ grp.can_publish ? 'Открыта' : 'Закрыта' }}
              </VChip>
            </div>
          </div>
        </VCardText>

        <VCardActions class="pa-4 pt-0">
          <VSpacer />
          <VBtn variant="text" @click="showPresetDialog = false">Отмена</VBtn>
          <VBtn
            color="primary"
            variant="flat"
            :loading="presetSaving"
            :disabled="!presetForm.name.trim() || presetSaving"
            @click="savePreset"
          >
            Сохранить блок
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО: Ход рассылки и результаты -->
    <VDialog v-model="showPublishModal" max-width="600px" persistent>
      <VCard>
        <VCardTitle class="pa-4 font-weight-bold d-flex align-center justify-space-between">
          <div class="d-flex align-center gap-2">
            <VProgressCircular v-if="isPublishing" indeterminate size="22" color="primary" />
            <VIcon v-else icon="bx-check-circle" color="success" size="24" />
            <span>{{ isPublishing ? 'Идет рассылка постов...' : 'Рассылка завершена' }}</span>
          </div>
          <VBtn v-if="!isPublishing" icon="bx-x" variant="text" size="small" @click="showPublishModal = false" />
        </VCardTitle>

        <VCardText class="pa-4 pt-0">
          <div v-if="isPublishing" class="mb-3 text-body-2 text-medium-emphasis">
            Публикация постов на стенах сообществ с интервалом {{ delaySeconds }} сек. Пожалуйста, не закрывайте страницу.
          </div>

          <div v-if="publishSummary" class="d-flex gap-3 mb-4">
            <VChip color="success" class="font-weight-bold">
              Успешно: {{ publishSummary.success_count }}
            </VChip>
            <VChip color="error" class="font-weight-bold">
              Ошибок: {{ publishSummary.failed_count }}
            </VChip>
            <VChip color="default">
              Всего: {{ publishSummary.total }}
            </VChip>
          </div>

          <!-- Лог отправки -->
          <div class="border rounded pa-2 bg-light" style="max-height: 250px; overflow-y: auto;">
            <div
              v-for="(log, lIdx) in publishLogs"
              :key="lIdx"
              class="d-flex align-center justify-space-between py-1 border-b last-border-none text-caption"
            >
              <span class="text-truncate mr-2">{{ log.group_name }}</span>
              <div>
                <a
                  v-if="log.post_url"
                  :href="log.post_url"
                  target="_blank"
                  class="text-success font-weight-bold text-decoration-none"
                >
                  ✓ Опубликован
                </a>
                <span v-else class="text-error" :title="log.error">
                  ✗ Ошибка
                </span>
              </div>
            </div>
          </div>
        </VCardText>

        <VCardActions class="pa-4 pt-0" v-if="!isPublishing">
          <VSpacer />
          <VBtn color="primary" variant="flat" @click="showPublishModal = false">
            Готово
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО: Подключение / Обновление личного аккаунта ВК -->
    <VDialog v-model="showAccountDialog" max-width="620px" persistent>
      <VCard>
        <VCardTitle class="pa-4 font-weight-bold d-flex align-center justify-space-between">
          <div class="d-flex align-center gap-2">
            <VIcon icon="bx-user-check" color="primary" />
            <span>Подключение личного аккаунта ВКонтакте</span>
          </div>
          <VBtn icon="bx-x" variant="text" size="small" @click="showAccountDialog = false" />
        </VCardTitle>

        <VCardText class="pa-4 pt-0">
          <VAlert type="info" variant="tonal" class="mb-4">
            <div class="text-caption">
              Для публикации постов на открытых стенах групп от вашего имени требуется личный токен доступа ВКонтакте с правами <b>wall, photos, offline</b>.
            </div>
          </VAlert>

          <div class="mb-4">
            <div class="font-weight-medium mb-1 text-body-2">Шаг 1: Получите токен доступа</div>
            <div class="text-caption text-medium-emphasis mb-2">
              Нажмите кнопку ниже, разрешите доступ в открывшейся вкладке ВКонтакте, затем скопируйте адресную строку (или значение access_token) из адресной строки страницы:
            </div>
            <VBtn
              color="primary"
              variant="tonal"
              prepend-icon="bx-link-external"
              :href="vkOAuthLink"
              target="_blank"
              size="small"
            >
              Открыть страницу авторизации ВКонтакте
            </VBtn>
          </div>

          <div class="mb-3">
            <div class="font-weight-medium mb-1 text-body-2">Шаг 2: Вставьте токен</div>
            <VTextarea
              v-model="newAccountToken"
              label="Токен доступа (access_token) или ссылка из браузера *"
              placeholder="vk1.a... или https://oauth.vk.com/blank.html#access_token=vk1.a..."
              rows="3"
              variant="outlined"
              density="comfortable"
              hint="Можно вставить всю ссылку целиком из адресной строки, токен извлечется автоматически"
              persistent-hint
            />
          </div>

          <div>
            <VTextField
              v-model="newAccountName"
              label="Название аккаунта (необязательно)"
              placeholder="Например: Мой личный аккаунт"
              variant="outlined"
              density="comfortable"
              hint="Если оставить пустым, имя и фамилия подтянутся автоматически из профиля ВКонтакте"
              persistent-hint
            />
          </div>
        </VCardText>

        <VCardActions class="pa-4 pt-0">
          <VSpacer />
          <VBtn variant="text" @click="showAccountDialog = false">Отмена</VBtn>
          <VBtn
            color="primary"
            variant="flat"
            :loading="linkingAccount"
            :disabled="!newAccountToken.trim() || linkingAccount"
            @click="linkNewAccount"
          >
            Сохранить и привязать
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.emoji-btn {
  font-size: 1.15rem;
  padding: 2px 4px;
  border-radius: 4px;
  transition: background 0.15s ease;
  user-select: none;
}
.emoji-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}
.last-border-none:last-child {
  border-bottom: none !important;
}
</style>
