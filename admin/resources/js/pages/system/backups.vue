<script setup>
import { ref, onMounted, computed } from 'vue'

const activeTab = ref('backups')
const loading = ref(false)
const creatingBackup = ref(false)
const runningRetention = ref(false)
const savingSettings = ref(false)
const savingPrompt = ref(false)
const savingDoc = ref(false)

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// Данные
const backups = ref([])
const diskInfo = ref({ total_gb: 30, used_gb: 12, free_gb: 18, used_pct: 40 })
const settings = ref({
  auto_backup_enabled: true,
  schedule_interval: 'daily_night',
  backup_type: 'db_and_code',
  retention_days: 14,
  max_backup_count: 10,
  min_disk_free_gb: 3.0,
  notify_admin_panel: true,
  last_backup_at: null,
  last_backup_status: 'idle',
  last_backup_message: ''
})

// Диалог создания
const isCreateDialogOpen = ref(false)
const selectedBackupType = ref('db_and_code')

// Диалог удаления
const isDeleteDialogOpen = ref(false)
const fileToDelete = ref('')

// ИИ-протоколы
const aiPrompts = ref([])
const selectedPromptCode = ref('system_protocol')
const activePrompt = computed(() => {
  return aiPrompts.value.find(p => p.code === selectedPromptCode.value) || { title: '', content: '', code: '' }
})

// Документация
const docOptions = [
  { title: 'Главный регламент проекта (system_faq.md)', value: 'system_faq' },
  { title: 'Карта навигации и структуры (sitenav.md)', value: 'sitenav' },
  { title: 'Учет полей базы данных (sql_faq.md)', value: 'sql_faq' }
]
const selectedDoc = ref('system_faq')
const docContent = ref('')
const docPath = ref('')
const docLoading = ref(false)

// Загрузка сводки бэкапов
const loadDashboard = async () => {
  loading.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/v1/system/backups', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      backups.value = data.backups || []
      diskInfo.value = data.disk || diskInfo.value
      if (data.settings) {
        settings.value = { ...settings.value, ...data.settings }
      }
    } else {
      showToast(data.detail || 'Не удалось загрузить данные', 'error')
    }
  } catch (e) {
    showToast(`Ошибка сети: ${e.message}`, 'error')
  } finally {
    loading.value = false
  }
}

// Создание бэкапа
const handleCreateBackup = async () => {
  creatingBackup.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/v1/system/backups/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ backup_type: selectedBackupType.value })
    })
    const data = await res.json()
    if (res.ok) {
      showToast(data.message || 'Бэкап успешно создан!', 'success')
      isCreateDialogOpen.value = false
      await loadDashboard()
    } else {
      showToast(data.detail || data.message || 'Ошибка создания бэкапа', 'error')
    }
  } catch (e) {
    showToast(`Ошибка: ${e.message}`, 'error')
  } finally {
    creatingBackup.value = false
  }
}

// Удаление бэкапа
const confirmDeleteBackup = (filename) => {
  fileToDelete.value = filename
  isDeleteDialogOpen.value = true
}

const executeDeleteBackup = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/v1/system/backups/${fileToDelete.value}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (res.ok) {
      showToast('Бэкап удален', 'success')
      isDeleteDialogOpen.value = false
      await loadDashboard()
    } else {
      showToast(data.detail || 'Ошибка удаления', 'error')
    }
  } catch (e) {
    showToast(`Ошибка: ${e.message}`, 'error')
  }
}

// Скачивание
const downloadBackup = (filename) => {
  const token = localStorage.getItem('token')
  const url = `/api/v1/system/backups/download/${encodeURIComponent(filename)}`
  window.open(url, '_blank')
}

// Сохранение настроек
const handleSaveSettings = async () => {
  savingSettings.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/v1/system/backups/settings', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(settings.value)
    })
    const data = await res.json()
    if (res.ok) {
      showToast('Настройки автоматизации успешно сохранены', 'success')
    } else {
      showToast(data.detail || 'Ошибка сохранения настроек', 'error')
    }
  } catch (e) {
    showToast(`Ошибка: ${e.message}`, 'error')
  } finally {
    savingSettings.value = false
  }
}

// Принудительная ротация
const handleRunRetention = async () => {
  runningRetention.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/v1/system/backups/retention/run', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (res.ok) {
      showToast(`Ротация выполнена. Удалено устаревших копий: ${data.deleted_count || 0}`, 'info')
      await loadDashboard()
    }
  } catch (e) {
    showToast(`Ошибка: ${e.message}`, 'error')
  } finally {
    runningRetention.value = false
  }
}

// ИИ-протоколы
const loadAiPrompts = async () => {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/api/v1/system/backups/ai-prompts', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (res.ok && data.prompts) {
      aiPrompts.value = data.prompts
    }
  } catch (e) {
    console.error('Ошибка загрузки промптов:', e)
  }
}

const handleSavePrompt = async () => {
  savingPrompt.value = true
  try {
    const token = localStorage.getItem('token')
    const p = activePrompt.value
    const res = await fetch('/api/v1/system/backups/ai-prompts', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        code: p.code,
        title: p.title,
        content: p.content,
        is_active: p.is_active !== false,
        priority: p.priority || 10
      })
    })
    const data = await res.json()
    if (res.ok) {
      showToast('Регламент для ИИ успешно сохранен и обновлен', 'success')
      await loadAiPrompts()
    } else {
      showToast(data.detail || 'Ошибка сохранения промпта', 'error')
    }
  } catch (e) {
    showToast(`Ошибка: ${e.message}`, 'error')
  } finally {
    savingPrompt.value = false
  }
}

const copyPromptToClipboard = () => {
  if (!activePrompt.value?.content) return
  navigator.clipboard.writeText(activePrompt.value.content)
  showToast('Текст инструкции скопирован в буфер обмена!', 'success')
}

// Документация
const loadDoc = async () => {
  docLoading.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/v1/system/backups/docs/${selectedDoc.value}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (res.ok && data.status === 'success') {
      docContent.value = data.content || ''
      docPath.value = data.path || ''
    } else {
      showToast(data.detail || 'Документ не найден', 'warning')
    }
  } catch (e) {
    showToast(`Ошибка чтения: ${e.message}`, 'error')
  } finally {
    docLoading.value = false
  }
}

const handleSaveDoc = async () => {
  savingDoc.value = true
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/v1/system/backups/docs/${selectedDoc.value}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content: docContent.value })
    })
    const data = await res.json()
    if (res.ok) {
      showToast(`Документ ${selectedDoc.value}.md успешно сохранен на сервере!`, 'success')
    } else {
      showToast(data.detail || 'Ошибка сохранения', 'error')
    }
  } catch (e) {
    showToast(`Ошибка: ${e.message}`, 'error')
  } finally {
    savingDoc.value = false
  }
}

const showToast = (text, color = 'success') => {
  snackbar.value = { show: true, text, color }
}

const diskColor = computed(() => {
  const pct = diskInfo.value.used_pct || 0
  if (pct > 85) return 'error'
  if (pct > 70) return 'warning'
  return 'success'
})

onMounted(async () => {
  await loadDashboard()
  await loadAiPrompts()
  await loadDoc()
})
</script>

<template>
  <div>
    <!-- Верхняя панель заголовка -->
    <VRow class="mb-4 align-center">
      <VCol cols="12" md="7">
        <h2 class="text-h4 font-weight-bold d-flex align-center gap-2">
          <VIcon icon="bx-shield-quarter" color="primary" size="36" />
          Бэкапы и ИИ-протоколы
        </h2>
        <p class="text-body-1 text-medium-emphasis mb-0">
          Резервные копии базы данных и кода, расписание автосохранения, ротация и единые регламенты для ИИ-ассистентов
        </p>
      </VCol>
      <VCol cols="12" md="5" class="d-flex justify-md-end gap-3 align-center flex-wrap">
        <VBtn
          color="primary"
          prepend-icon="bx-plus-circle"
          size="large"
          elevation="2"
          @click="isCreateDialogOpen = true"
        >
          Создать бэкап
        </VBtn>
        <VBtn
          variant="tonal"
          color="secondary"
          icon="bx-refresh"
          :loading="loading"
          @click="loadDashboard"
        />
      </VCol>
    </VRow>

    <!-- Индикатор дискового пространства на VPS -->
    <VCard class="mb-6 elevation-1 border">
      <VCardText class="py-3">
        <VRow align="center" no-gutters>
          <VCol cols="12" md="3" class="d-flex align-center gap-3">
            <VAvatar color="primary" variant="tonal" size="44">
              <VIcon icon="bx-hdd" size="24" />
            </VAvatar>
            <div>
              <div class="text-caption text-medium-emphasis">Диск на сервере VPS</div>
              <div class="text-h6 font-weight-bold">
                {{ diskInfo.free_gb }} ГБ свободно
                <span class="text-caption text-medium-emphasis">из {{ diskInfo.total_gb }} ГБ</span>
              </div>
            </div>
          </VCol>

          <VCol cols="12" md="6" class="px-md-4 my-2 my-md-0">
            <div class="d-flex justify-space-between text-caption mb-1">
              <span>Занято: {{ diskInfo.used_gb }} ГБ ({{ diskInfo.used_pct }}%)</span>
              <span>Свободно: {{ diskInfo.free_gb }} ГБ</span>
            </div>
            <VProgressLinear
              :model-value="diskInfo.used_pct"
              :color="diskColor"
              height="10"
              rounded
            />
          </VCol>

          <VCol cols="12" md="3" class="text-md-end">
            <VChip
              :color="settings.auto_backup_enabled ? 'success' : 'secondary'"
              variant="tonal"
              size="small"
              class="font-weight-medium"
            >
              <VIcon :icon="settings.auto_backup_enabled ? 'bx-check-circle' : 'bx-pause-circle'" start />
              {{ settings.auto_backup_enabled ? 'Авто-бэкап: активен' : 'Авто-бэкап: выключен' }}
            </VChip>
          </VCol>
        </VRow>
      </VCardText>
    </VCard>

    <!-- Вкладки управления -->
    <VTabs v-model="activeTab" class="mb-4" color="primary">
      <VTab value="backups">
        <VIcon icon="bx-archive" start />
        Хранилище бэкапов ({{ backups.length }})
      </VTab>
      <VTab value="automation">
        <VIcon icon="bx-time-five" start />
        Автоматизация и ротация
      </VTab>
      <VTab value="ai-prompts">
        <VIcon icon="bx-bot" start />
        ИИ-протоколы и требования
      </VTab>
      <VTab value="docs">
        <VIcon icon="bx-file" start />
        Структура и документация
      </VTab>
    </VTabs>

    <!-- 1. ХРАНИЛИЩЕ БЭКАПОВ -->
    <VWindow v-model="activeTab">
      <VWindowItem value="backups">
        <VCard class="elevation-1 border">
          <VCardTitle class="d-flex justify-space-between align-center px-4 py-3">
            <div class="d-flex align-center gap-2">
              <VIcon icon="bx-list-ul" color="primary" />
              <span>Существующие резервные копии</span>
            </div>
            <VChip size="small" variant="outlined" color="primary">
              Всего копий: {{ backups.length }}
            </VChip>
          </VCardTitle>

          <VDivider />

          <VTable v-if="backups.length > 0" hover>
            <thead>
              <tr>
                <th>Тип</th>
                <th>Имя файла</th>
                <th>Размер</th>
                <th>Дата создания</th>
                <th class="text-end">Действия</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in backups" :key="b.filename">
                <td>
                  <VChip
                    size="small"
                    :color="b.type === 'db' ? 'info' : (b.type === 'code' ? 'success' : 'purple')"
                    variant="tonal"
                  >
                    <VIcon :icon="b.type === 'db' ? 'bx-data' : (b.type === 'code' ? 'bx-code-alt' : 'bx-archive')" start />
                    {{ b.type_label }}
                  </VChip>
                </td>
                <td class="font-weight-medium text-truncate" style="max-width: 380px;">
                  <code>{{ b.filename }}</code>
                </td>
                <td>
                  <VChip size="x-small" variant="outlined">{{ b.size_human }}</VChip>
                </td>
                <td class="text-body-2 text-medium-emphasis">
                  {{ b.created_at_human }}
                </td>
                <td class="text-end">
                  <VBtn
                    icon="bx-download"
                    size="small"
                    variant="text"
                    color="primary"
                    title="Скачать на компьютер"
                    @click="downloadBackup(b.filename)"
                  />
                  <VBtn
                    icon="bx-trash"
                    size="small"
                    variant="text"
                    color="error"
                    title="Удалить файл"
                    @click="confirmDeleteBackup(b.filename)"
                  />
                </td>
              </tr>
            </tbody>
          </VTable>

          <VCardText v-else class="text-center py-10 text-medium-emphasis">
            <VIcon icon="bx-archive-out" size="48" class="mb-2" />
            <div>Резервные копии пока не созданы.</div>
            <VBtn
              color="primary"
              variant="tonal"
              class="mt-3"
              prepend-icon="bx-plus"
              @click="isCreateDialogOpen = true"
            >
              Создать первую резервную копию
            </VBtn>
          </VCardText>
        </VCard>
      </VWindowItem>

      <!-- 2. АВТОМАТИЗАЦИЯ И РОТАЦИЯ -->
      <VWindowItem value="automation">
        <VRow>
          <VCol cols="12" md="6">
            <VCard class="elevation-1 border h-100">
              <VCardItem>
                <template #prepend>
                  <VAvatar color="primary" variant="tonal">
                    <VIcon icon="bx-calendar-event" />
                  </VAvatar>
                </template>
                <VCardTitle>Расписание автоматических бэкапов</VCardTitle>
                <VCardSubtitle>Настройка периодичности создания архивов</VCardSubtitle>
              </VCardItem>

              <VDivider />

              <VCardText class="d-flex flex-column gap-4">
                <VSwitch
                  v-model="settings.auto_backup_enabled"
                  label="Включить регулярное автосохранение"
                  color="primary"
                />

                <VSelect
                  v-model="settings.schedule_interval"
                  label="Частота запуска"
                  :items="[
                    { title: 'Ежедневно ночью (в 04:00 МСК)', value: 'daily_night' },
                    { title: 'Каждые 12 часов', value: 'every_12h' },
                    { title: 'Раз в неделю (в ночь на понедельник)', value: 'weekly' }
                  ]"
                  :disabled="!settings.auto_backup_enabled"
                />

                <VSelect
                  v-model="settings.backup_type"
                  label="Тип автоматического архива"
                  :items="[
                    { title: 'База данных + Код (рекомендуется, ~65 МБ)', value: 'db_and_code' },
                    { title: 'Только база данных (быстро, ~50 МБ)', value: 'db_only' },
                    { title: 'Только код и конфигурации (~15 МБ)', value: 'code_only' },
                    { title: 'Полный с медиа-файлами (~450 МБ)', value: 'full_with_media' }
                  ]"
                  :disabled="!settings.auto_backup_enabled"
                />

                <VSwitch
                  v-model="settings.notify_admin_panel"
                  label="Отправлять уведомление в админку при завершении"
                  color="info"
                />
              </VCardText>
            </VCard>
          </VCol>

          <VCol cols="12" md="6">
            <VCard class="elevation-1 border h-100">
              <VCardItem>
                <template #prepend>
                  <VAvatar color="warning" variant="tonal">
                    <VIcon icon="bx-recycle" />
                  </VAvatar>
                </template>
                <VCardTitle>Политика ротации (Автоудаление)</VCardTitle>
                <VCardSubtitle>Очистка устаревших копий и защита от переполнения диска</VCardSubtitle>
              </VCardItem>

              <VDivider />

              <VCardText class="d-flex flex-column gap-4">
                <div>
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-body-2 font-weight-medium">Хранить максимум копий:</span>
                    <span class="text-body-2 font-weight-bold text-primary">{{ settings.max_backup_count }} шт.</span>
                  </div>
                  <VSlider
                    v-model="settings.max_backup_count"
                    :min="3"
                    :max="30"
                    :step="1"
                    thumb-label
                    color="primary"
                  />
                  <div class="text-caption text-medium-emphasis">Старые архивы сверх лимита удаляются автоматически.</div>
                </div>

                <div>
                  <div class="d-flex justify-space-between mb-1">
                    <span class="text-body-2 font-weight-medium">Удалять бэкапы старше:</span>
                    <span class="text-body-2 font-weight-bold text-primary">{{ settings.retention_days }} дней</span>
                  </div>
                  <VSlider
                    v-model="settings.retention_days"
                    :min="3"
                    :max="60"
                    :step="1"
                    thumb-label
                    color="warning"
                  />
                </div>

                <VTextField
                  v-model.number="settings.min_disk_free_gb"
                  type="number"
                  label="Порог свободного места (ГБ)"
                  suffix="ГБ"
                  hint="Если свободно меньше этого значения, старые копии очищаются экстренно"
                  persistent-hint
                />

                <VBtn
                  variant="outlined"
                  color="warning"
                  prepend-icon="bx-trash-alt"
                  :loading="runningRetention"
                  @click="handleRunRetention"
                >
                  Запустить очистку устаревших копий сейчас
                </VBtn>
              </VCardText>

              <VDivider />

              <VCardActions class="pa-4">
                <VSpacer />
                <VBtn
                  color="primary"
                  prepend-icon="bx-save"
                  :loading="savingSettings"
                  @click="handleSaveSettings"
                >
                  Сохранить настройки
                </VBtn>
              </VCardActions>
            </VCard>
          </VCol>
        </VRow>
      </VWindowItem>

      <!-- 3. ИИ-ПРОТОКОЛЫ И ТРЕБОВАНИЯ -->
      <VWindowItem value="ai-prompts">
        <VCard class="elevation-1 border">
          <VCardItem>
            <template #prepend>
              <VAvatar color="primary" variant="tonal">
                <VIcon icon="bx-bot" />
              </VAvatar>
            </template>
            <VCardTitle>Единые системные протоколы для ИИ-ассистентов</VCardTitle>
            <VCardSubtitle>
              Инструкции, чеклисты и правила деплоя, обязательные для всех агентов Antigravity
            </VCardSubtitle>
          </VCardItem>

          <VDivider />

          <VCardText>
            <VRow>
              <VCol cols="12" md="4">
                <div class="text-subtitle-2 mb-2 font-weight-bold">Выберите регламент для редактирования:</div>
                <VList density="compact" select-strategy="single-independent">
                  <VListItem
                    v-for="p in aiPrompts"
                    :key="p.code"
                    :active="selectedPromptCode === p.code"
                    color="primary"
                    rounded
                    class="mb-1"
                    @click="selectedPromptCode = p.code"
                  >
                    <template #prepend>
                      <VIcon icon="bx-file-blank" />
                    </template>
                    <VListItemTitle class="font-weight-medium">{{ p.title }}</VListItemTitle>
                    <VListItemSubtitle>Код: {{ p.code }}</VListItemSubtitle>
                  </VListItem>
                </VList>

                <VAlert color="info" variant="tonal" class="mt-4 text-caption" density="compact">
                  <VIcon icon="bx-info-circle" start />
                  Любой агент перед стартом работы с кодом считывает эти правила из базы и файлов документации.
                </VAlert>

                <VBtn
                  block
                  variant="outlined"
                  color="primary"
                  class="mt-3"
                  prepend-icon="bx-copy"
                  @click="copyPromptToClipboard"
                >
                  Скопировать промпт в буфер
                </VBtn>
              </VCol>

              <VCol cols="12" md="8">
                <div class="d-flex justify-space-between align-center mb-2">
                  <span class="text-subtitle-1 font-weight-bold">{{ activePrompt.title }}</span>
                  <VBtn
                    color="primary"
                    size="small"
                    prepend-icon="bx-save"
                    :loading="savingPrompt"
                    @click="handleSavePrompt"
                  >
                    Сохранить изменения
                  </VBtn>
                </div>

                <VTextarea
                  v-model="activePrompt.content"
                  rows="18"
                  variant="outlined"
                  class="font-monospace text-body-2"
                  auto-grow
                />
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VWindowItem>

      <!-- 4. СТРУКТУРА И ДОКУМЕНТАЦИЯ -->
      <VWindowItem value="docs">
        <VCard class="elevation-1 border">
          <VCardItem>
            <template #prepend>
              <VAvatar color="info" variant="tonal">
                <VIcon icon="bx-book-content" />
              </VAvatar>
            </template>
            <VCardTitle>Главная документация и структура проекта</VCardTitle>
            <VCardSubtitle>Просмотр и редактирование файлов Service_info на сервере</VCardSubtitle>
          </VCardItem>

          <VDivider />

          <VCardText>
            <div class="d-flex gap-4 align-center mb-4 flex-wrap">
              <VSelect
                v-model="selectedDoc"
                :items="docOptions"
                label="Выберите документ"
                style="max-width: 480px;"
                density="compact"
                @update:model-value="loadDoc"
              />
              <VSpacer />
              <VBtn
                color="primary"
                prepend-icon="bx-save"
                :loading="savingDoc"
                @click="handleSaveDoc"
              >
                Сохранить файл на сервере
              </VBtn>
            </div>

            <div v-if="docPath" class="text-caption text-medium-emphasis mb-2">
              Путь: <code>{{ docPath }}</code>
            </div>

            <VTextarea
              v-model="docContent"
              rows="22"
              variant="outlined"
              class="font-monospace text-body-2"
              :loading="docLoading"
            />
          </VCardText>
        </VCard>
      </VWindowItem>
    </VWindow>

    <!-- Диалог создания бэкапа -->
    <VDialog v-model="isCreateDialogOpen" max-width="540">
      <VCard>
        <VCardTitle class="d-flex align-center gap-2 pt-4 px-4">
          <VIcon icon="bx-cloud-upload" color="primary" />
          <span>Создание новой резервной копии</span>
        </VCardTitle>
        <VDivider />
        <VCardText class="pa-4">
          <p class="text-body-2 mb-3">Выберите тип резервной копии для создания:</p>
          <VRadioGroup v-model="selectedBackupType">
            <VRadio value="db_and_code" color="primary">
              <template #label>
                <div>
                  <div class="font-weight-bold">База данных + Код (Рекомендуется)</div>
                  <div class="text-caption text-medium-emphasis">Полный дамп PostgreSQL + архив кодовой базы и настроек (~65 МБ)</div>
                </div>
              </template>
            </VRadio>
            <VDivider class="my-2" />
            <VRadio value="db_only" color="info">
              <template #label>
                <div>
                  <div class="font-weight-bold">Только база данных</div>
                  <div class="text-caption text-medium-emphasis">Все таблицы, заказы, пользователи, транзакции (~50 МБ)</div>
                </div>
              </template>
            </VRadio>
            <VDivider class="my-2" />
            <VRadio value="code_only" color="success">
              <template #label>
                <div>
                  <div class="font-weight-bold">Только код и конфигурации</div>
                  <div class="text-caption text-medium-emphasis">Бэкенд, фронтенд, файлы .env и документация (~15 МБ)</div>
                </div>
              </template>
            </VRadio>
            <VDivider class="my-2" />
            <VRadio value="full_with_media" color="purple">
              <template #label>
                <div>
                  <div class="font-weight-bold">Полный архив системы с медиафайлами</div>
                  <div class="text-caption text-medium-emphasis">Включая каталог всех загруженных картинок товаров (~450 МБ)</div>
                </div>
              </template>
            </VRadio>
          </VRadioGroup>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn variant="plain" @click="isCreateDialogOpen = false">Отмена</VBtn>
          <VBtn
            color="primary"
            prepend-icon="bx-check"
            :loading="creatingBackup"
            @click="handleCreateBackup"
          >
            Создать сейчас
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог подтверждения удаления -->
    <VDialog v-model="isDeleteDialogOpen" max-width="440">
      <VCard>
        <VCardTitle class="text-error pt-4 px-4 d-flex align-center gap-2">
          <VIcon icon="bx-error" />
          <span>Удалить резервную копию?</span>
        </VCardTitle>
        <VCardText class="pa-4">
          Вы уверены, что хотите удалить файл:
          <code class="d-block mt-2 pa-2 bg-var-theme-surface border rounded">{{ fileToDelete }}</code>
        </VCardText>
        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn variant="plain" @click="isDeleteDialogOpen = false">Отмена</VBtn>
          <VBtn color="error" @click="executeDeleteBackup">Удалить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Уведомления Snackbar -->
    <VSnackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3500"
      location="top right"
    >
      {{ snackbar.text }}
    </VSnackbar>
  </div>
</template>
