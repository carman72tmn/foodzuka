<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const router = useRouter()
const toast = useToast()

// Состояния подключений и публикаций
const connections = ref([])
const selectedConnectionId = ref(null)
const publications = ref([])
const loading = ref(false)

// Состояние диалога публикации
const showDialog = ref(false)
const saving = ref(false)
const dialogMode = ref('create') // 'create' or 'edit'

// Форма создания/редактирования
const form = ref({
  id: null,
  vk_bot_connection_id: null,
  type: 'post', // 'post' or 'story'
  content_text: '',
  media_url: '',
  publish_at: '',
  link_url: '',
  button_text: 'Открыть'
})

// Локальное время (для ввода во Vue)
const localPublishDateTime = ref('')

// Список популярных эмодзи для быстрой вставки
const popularEmojis = ['🎉', '🍕', '🎂', '🥳', '🎁', '🍕', '🍔', '🍟', '🥤', '🔥', '✨', '❤️', '👍', '🔔', '📢', '💬']

// Состояние предпросмотра
const previewDevice = ref('phone') // 'phone' or 'tablet'

// Фильтры
const filterType = ref('all') // 'all', 'post', 'story'
const filterStatus = ref('all') // 'all', 'pending', 'published', 'failed'

// --- Фоторедактор Canvas ---
const showEditorDialog = ref(false)
const imageEditorCanvas = ref(null)
const imageEditorFile = ref(null)
const editorLoading = ref(false)
const originalImage = ref(null) // HTMLImageElement
const editorFilter = ref('none')
const editorText = ref('')
const editorTextColor = ref('#ffffff')
const editorTextSize = ref(32)
const editorObjects = ref([]) // Наложенные объекты: { id, type: 'text'|'sticker', content, x, y, size, color }
const selectedObjectId = ref(null)
const isDragging = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const cropRatio = ref(null) // null (свободный), 1 (пост 1:1), 0.5625 (сториз 9:16)
const rotationAngle = ref(0) // 0, 90, 180, 270

// Список стикеров для редактора
const availableStickers = ['🎁', '🍕', '🔥', '🎉', '💥', '⭐️', '👑', '🐼', '🐱', '🐶', '🍕', '🍔', '🍟', '🚀', '❤️', '⏰']

// Фильтры для фото
const filtersList = [
  { name: 'Оригинал', value: 'none' },
  { name: 'Черно-белый', value: 'grayscale(100%)' },
  { name: 'Сепия', value: 'sepia(80%)' },
  { name: 'Инверсия', value: 'invert(100%)' },
  { name: 'Размытие', value: 'blur(3px)' },
  { name: 'Яркий', value: 'brightness(130%) contrast(110%)' }
]

// Доступные тексты для кнопок историй
const storyButtonTexts = [
  { title: 'Подробнее', value: 'more' },
  { title: 'Открыть', value: 'go_to' },
  { title: 'В магазин', value: 'to_store' },
  { title: 'Заказать', value: 'order' },
  { title: 'Забронировать', value: 'book' }
]

onMounted(async () => {
  await loadConnections()
})

async function loadConnections() {
  loading.value = true
  try {
    const res = await axios.get('/api/v1/vk/bots')
    connections.value = res.data
    if (connections.value.length > 0) {
      selectedConnectionId.value = connections.value[0].id
    }
  } catch (error) {
    toast.error('Не удалось загрузить подключения ВК')
  } finally {
    loading.value = false
  }
}

async function loadPublications() {
  if (!selectedConnectionId.value) return
  loading.value = true
  try {
    const res = await axios.get('/api/v1/vk-scheduler/', {
      params: { vk_bot_connection_id: selectedConnectionId.value }
    })
    publications.value = res.data
  } catch (error) {
    toast.error('Ошибка загрузки публикаций')
  } finally {
    loading.value = false
  }
}

watch(selectedConnectionId, () => {
  loadPublications()
})

const filteredPublications = computed(() => {
  return publications.value.filter(pub => {
    const typeMatch = filterType.value === 'all' || pub.type === filterType.value
    const statusMatch = filterStatus.value === 'all' || pub.status === filterStatus.value
    return typeMatch && statusMatch
  })
})

function formatDateTime(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function openCreateDialog(type = 'post') {
  if (!selectedConnectionId.value) {
    toast.warning('Выберите сообщество!')
    return
  }
  dialogMode.value = 'create'
  
  // Устанавливаем время отправки на час вперед
  const future = new Date()
  future.setHours(future.getHours() + 1)
  future.setMinutes(0)
  
  // Локальный формат для datetime-local input: YYYY-MM-DDThh:mm
  const offset = future.getTimezoneOffset() * 60000
  const localISOTime = new Date(future - offset).toISOString().slice(0, 16)
  localPublishDateTime.value = localISOTime

  form.value = {
    id: null,
    vk_bot_connection_id: selectedConnectionId.value,
    type: type,
    content_text: '',
    media_url: '',
    publish_at: '',
    link_url: '',
    button_text: type === 'story' ? 'more' : 'Открыть'
  }
  showDialog.value = true
}

function openEditDialog(pub) {
  dialogMode.value = 'edit'
  
  const d = new Date(pub.publish_at)
  const offset = d.getTimezoneOffset() * 60000
  localPublishDateTime.value = new Date(d - offset).toISOString().slice(0, 16)

  form.value = { ...pub }
  showDialog.value = true
}

async function savePublication() {
  if (!localPublishDateTime.value) {
    toast.warning('Укажите время публикации!')
    return
  }

  saving.value = true
  try {
    // Конвертируем локальное время в UTC ISO строку
    const dateObj = new Date(localPublishDateTime.value)
    form.value.publish_at = dateObj.toISOString()

    if (dialogMode.value === 'create') {
      const res = await axios.post('/api/v1/vk-scheduler/', form.value)
      publications.value.push(res.data)
      toast.success('Публикация запланирована')
    } else {
      const res = await axios.patch(`/api/v1/vk-scheduler/${form.value.id}`, form.value)
      const idx = publications.value.findIndex(p => p.id === form.value.id)
      if (idx !== -1) publications.value[idx] = res.data
      toast.success('Публикация обновлена')
    }
    showDialog.value = false
  } catch (error) {
    console.error(error)
    toast.error(error.response?.data?.detail || 'Ошибка сохранения публикации')
  } finally {
    saving.value = false
  }
}

async function deletePublication(pub) {
  if (!confirm('Удалить эту запланированную публикацию?')) return
  try {
    await axios.delete(`/api/v1/vk-scheduler/${pub.id}`)
    publications.value = publications.value.filter(p => p.id !== pub.id)
    toast.success('Публикация удалена')
  } catch (error) {
    toast.error('Не удалось удалить публикацию')
  }
}

async function publishNow(pub) {
  if (!confirm('Вы действительно хотите опубликовать это прямо сейчас?')) return
  loading.value = true
  try {
    const res = await axios.post(`/api/v1/vk-scheduler/${pub.id}/publish`)
    toast.success(res.data.message)
    await loadPublications()
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Ошибка при публикации')
  } finally {
    loading.value = false
  }
}

function appendEmoji(emoji) {
  form.value.content_text += emoji
}

// --- Загрузка картинок на сервер ---
async function handleImageUpload(event) {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  loading.value = true
  try {
    const res = await axios.post('/api/v1/vk-scheduler/upload-media', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    form.value.media_url = res.data.media_url
    toast.success('Изображение загружено!')
  } catch (error) {
    toast.error('Ошибка при загрузке медиафайла')
  } finally {
    loading.value = false
  }
}

// --- Интеграция графического фоторедактора ---
function startEditingImage() {
  if (!form.value.media_url) {
    toast.warning('Сначала загрузите изображение!')
    return
  }

  editorLoading.value = true
  editorObjects.value = []
  selectedObjectId.value = null
  editorFilter.value = 'none'
  rotationAngle.value = 0
  
  // Задаем пропорции по умолчанию в зависимости от типа
  cropRatio.value = form.value.type === 'story' ? 0.5625 : 1.0

  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.src = form.value.media_url.startsWith('http') ? form.value.media_url : window.location.origin + form.value.media_url
  
  img.onload = () => {
    originalImage.value = img
    showEditorDialog.value = true
    setTimeout(drawCanvas, 100)
    editorLoading.value = false
  }

  img.onerror = () => {
    toast.error('Ошибка загрузки изображения в редактор')
    editorLoading.value = false
  }
}

function drawCanvas() {
  const canvas = imageEditorCanvas.value
  if (!canvas || !originalImage.value) return

  const ctx = canvas.getContext('2d')
  
  // Рассчитываем размеры холста с сохранением пропорций картинки
  let width = originalImage.value.width
  let height = originalImage.value.height

  // Ограничиваем максимальный размер холста для редактирования (например, до 1000px)
  const maxDim = 800
  if (width > maxDim || height > maxDim) {
    if (width > height) {
      height = (height / width) * maxDim
      width = maxDim
    } else {
      width = (width / height) * maxDim
      height = maxDim
    }
  }

  // Если есть поворот
  if (rotationAngle.value % 180 !== 0) {
    canvas.width = height
    canvas.height = width
  } else {
    canvas.width = width
    canvas.height = height
  }

  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  ctx.save()
  
  // Применяем фильтр
  ctx.filter = editorFilter.value

  // Рисуем с поворотом
  ctx.translate(canvas.width / 2, canvas.height / 2)
  ctx.rotate((rotationAngle.value * Math.PI) / 180)
  ctx.drawImage(originalImage.value, -width / 2, -height / 2, width, height)
  
  ctx.restore()

  // Рисуем наложенные объекты (текст и стикеры)
  editorObjects.value.forEach(obj => {
    ctx.save()
    if (obj.type === 'text') {
      ctx.fillStyle = obj.color
      ctx.font = `bold ${obj.size}px Outfit, Inter, sans-serif`
      ctx.textBaseline = 'top'
      ctx.fillText(obj.content, obj.x, obj.y)
      
      // Обводка для выделенного
      if (obj.id === selectedObjectId.value) {
        ctx.strokeStyle = '#2196F3'
        ctx.lineWidth = 2
        const metrics = ctx.measureText(obj.content)
        ctx.strokeRect(obj.x - 4, obj.y - 4, metrics.width + 8, obj.size + 8)
      }
    } else if (obj.type === 'sticker') {
      ctx.font = `${obj.size}px serif`
      ctx.textBaseline = 'top'
      ctx.fillText(obj.content, obj.x, obj.y)

      if (obj.id === selectedObjectId.value) {
        ctx.strokeStyle = '#2196F3'
        ctx.lineWidth = 2
        ctx.strokeRect(obj.x - 4, obj.y - 4, obj.size + 8, obj.size + 8)
      }
    }
    ctx.restore()
  })
}

function rotateImage() {
  rotationAngle.value = (rotationAngle.value + 90) % 360
  drawCanvas()
}

function addText() {
  if (!editorText.value) return
  const newObj = {
    id: Date.now(),
    type: 'text',
    content: editorText.value,
    x: 50,
    y: 50,
    size: parseInt(editorTextSize.value),
    color: editorTextColor.value
  }
  editorObjects.value.push(newObj)
  selectedObjectId.value = newObj.id
  editorText.value = ''
  drawCanvas()
}

function addSticker(sticker) {
  const newObj = {
    id: Date.now(),
    type: 'sticker',
    content: sticker,
    x: 100,
    y: 100,
    size: 64
  }
  editorObjects.value.push(newObj)
  selectedObjectId.value = newObj.id
  drawCanvas()
}

function deleteSelectedObject() {
  if (!selectedObjectId.value) return
  editorObjects.value = editorObjects.value.filter(o => o.id !== selectedObjectId.value)
  selectedObjectId.value = null
  drawCanvas()
}

// Drag & Drop объектов на холсте
function handleCanvasMouseDown(e) {
  const canvas = imageEditorCanvas.value
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  // Ищем кликнутый объект (с конца, чтобы захватить верхний)
  let found = null
  const ctx = canvas.getContext('2d')

  for (let i = editorObjects.value.length - 1; i >= 0; i--) {
    const obj = editorObjects.value[i]
    if (obj.type === 'text') {
      ctx.font = `bold ${obj.size}px Outfit, Inter, sans-serif`
      const metrics = ctx.measureText(obj.content)
      const w = metrics.width
      const h = obj.size
      if (mouseX >= obj.x && mouseX <= obj.x + w && mouseY >= obj.y && mouseY <= obj.y + h) {
        found = obj
        break
      }
    } else if (obj.type === 'sticker') {
      const size = obj.size
      if (mouseX >= obj.x && mouseX <= obj.x + size && mouseY >= obj.y && mouseY <= obj.y + size) {
        found = obj
        break
      }
    }
  }

  if (found) {
    selectedObjectId.value = found.id
    isDragging.value = true
    dragStartX.value = mouseX - found.x
    dragStartY.value = mouseY - found.y
    drawCanvas()
  } else {
    selectedObjectId.value = null
    drawCanvas()
  }
}

function handleCanvasMouseMove(e) {
  if (!isDragging.value || !selectedObjectId.value) return
  
  const canvas = imageEditorCanvas.value
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  const obj = editorObjects.value.find(o => o.id === selectedObjectId.value)
  if (obj) {
    obj.x = mouseX - dragStartX.value
    obj.y = mouseY - dragStartY.value
    drawCanvas()
  }
}

function handleCanvasMouseUp() {
  isDragging.value = false
}

// Применение обрезки в зависимости от соотношения
function applyCrop() {
  const canvas = imageEditorCanvas.value
  if (!canvas || !cropRatio.value) return

  const ctx = canvas.getContext('2d')
  
  // Рассчитываем размеры рамки обрезки
  let targetWidth = canvas.width
  let targetHeight = canvas.width * cropRatio.value

  if (targetHeight > canvas.height) {
    targetHeight = canvas.height
    targetWidth = canvas.height / cropRatio.value
  }

  const startX = (canvas.width - targetWidth) / 2
  const startY = (canvas.height - targetHeight) / 2

  // Создаем новый вспомогательный холст нужного размера
  const tempCanvas = document.createElement('canvas')
  tempCanvas.width = targetWidth
  tempCanvas.height = targetHeight
  const tempCtx = tempCanvas.getContext('2d')

  // Копируем центральную область
  tempCtx.drawImage(
    canvas, 
    startX, startY, targetWidth, targetHeight,
    0, 0, targetWidth, targetHeight
  )

  // Перерисовываем основной холст под новые размеры
  canvas.width = targetWidth
  canvas.height = targetHeight
  ctx.drawImage(tempCanvas, 0, 0)
  
  // Сдвигаем объекты, чтобы они не вылетели
  editorObjects.value.forEach(obj => {
    obj.x -= startX
    obj.y -= startY
  })

  drawCanvas()
  toast.success('Обрезка успешно применена!')
}

// Сохранение отредактированного файла
async function saveEditedImage() {
  const canvas = imageEditorCanvas.value
  if (!canvas) return

  editorLoading.value = true
  try {
    // Получаем dataURL в формате JPEG
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
    
    // Конвертируем в Blob для отправки на сервер
    const blobBin = atob(dataUrl.split(',')[1])
    const array = []
    for (let i = 0; i < blobBin.length; i++) {
      array.push(blobBin.charCodeAt(i))
    }
    const file = new Blob([new Uint8Array(array)], { type: 'image/jpeg' })

    const formData = new FormData()
    formData.append('file', file, 'edited_image.jpg')

    const res = await axios.post('/api/v1/vk-scheduler/upload-media', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    form.value.media_url = res.data.media_url
    showEditorDialog.value = false
    toast.success('Отредактированное фото сохранено!')
  } catch (error) {
    toast.error('Не удалось сохранить изменения')
  } finally {
    editorLoading.value = false
  }
}
</script>

<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h2 class="text-h4 mb-1">Отложенный постинг ВКонтакте</h2>
        <p class="text-subtitle-1 text-muted mb-0">Планируйте публикации постов и историй с кнопочными ссылками и визуальным редактором</p>
      </div>
      <VBtn color="secondary" variant="tonal" prepend-icon="ri-arrow-left-line" @click="router.push('/marketing/vk-bots')">
        В каталог ботов
      </VBtn>
    </div>

    <!-- Выбор группы -->
    <VCard class="mb-6">
      <VCardText class="d-flex align-center justify-space-between flex-wrap py-4 gap-4">
        <div style="flex-grow: 1; max-width: 400px;">
          <VSelect
            v-model="selectedConnectionId"
            :items="connections"
            item-title="name"
            item-value="id"
            label="Активное сообщество ВК"
            variant="outlined"
            density="compact"
            hide-details
            :loading="loading"
            no-data-text="Нет подключенных сообществ"
          />
        </div>
        <div class="d-flex gap-2">
          <VBtn color="primary" prepend-icon="ri-file-add-line" @click="openCreateDialog('post')">
            Создать пост
          </VBtn>
          <VBtn color="success" prepend-icon="ri-movie-line" @click="openCreateDialog('story')">
            Создать сторис
          </VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- Фильтры -->
    <VCard class="mb-6">
      <VCardText class="d-flex align-center gap-4 py-3 flex-wrap">
        <span class="text-subtitle-2 text-muted me-2">Фильтры:</span>
        <VBtnToggle v-model="filterType" mandatory density="compact" color="primary">
          <VBtn value="all">Все форматы</VBtn>
          <VBtn value="post">Посты</VBtn>
          <VBtn value="story">Сториз</VBtn>
        </VBtnToggle>
        
        <VBtnToggle v-model="filterStatus" mandatory density="compact" color="primary">
          <VBtn value="all">Все статусы</VBtn>
          <VBtn value="pending">В очереди</VBtn>
          <VBtn value="published">Опубликованы</VBtn>
          <VBtn value="failed">Ошибка</VBtn>
        </VBtnToggle>
      </VCardText>
    </VCard>

    <!-- Сетка публикаций -->
    <VRow v-if="filteredPublications.length > 0">
      <VCol cols="12" md="6" lg="4" v-for="pub in filteredPublications" :key="pub.id">
        <VCard class="h-100 d-flex flex-column" hover>
          <!-- Картинка/Медиа -->
          <VImg
            v-if="pub.media_url"
            :src="pub.media_url"
            height="180"
            cover
            class="align-start text-white"
          >
            <div class="pa-2">
              <VChip size="small" color="black" class="text-white">
                {{ pub.type === 'story' ? 'Сториз' : 'Пост' }}
              </VChip>
            </div>
          </VImg>
          <div v-else class="bg-lighten-4 d-flex align-center justify-center text-muted" style="height: 180px; background: #f5f5f5;">
            <VIcon :icon="pub.type === 'story' ? 'ri-movie-line' : 'ri-text-snippet'" size="48" />
          </div>

          <VCardText class="flex-grow-1">
            <div class="d-flex align-center justify-space-between mb-2">
              <VChip
                size="x-small"
                :color="pub.status === 'published' ? 'success' : pub.status === 'failed' ? 'error' : 'warning'"
                variant="tonal"
                class="font-weight-bold"
              >
                {{ pub.status === 'published' ? 'Опубликован' : pub.status === 'failed' ? 'Ошибка' : 'В очереди' }}
              </VChip>
              <span class="text-caption text-muted d-flex align-center">
                <VIcon icon="ri-calendar-line" size="14" class="me-1" />
                {{ formatDateTime(pub.publish_at) }}
              </span>
            </div>

            <p class="text-body-2 text-truncate-3 mb-4" style="height: 60px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;">
              {{ pub.content_text || 'Без текста' }}
            </p>

            <div class="d-flex align-center gap-2 mb-2 text-caption text-muted" v-if="pub.link_url">
              <VIcon icon="ri-links-line" size="14" />
              <span class="text-truncate">Кнопка «{{ pub.button_text || 'Открыть' }}»: {{ pub.link_url }}</span>
            </div>

            <div v-if="pub.status === 'failed' && pub.error_message" class="text-caption text-error border pa-2 rounded bg-error-lighten">
              Ошибка: {{ pub.error_message }}
            </div>
          </VCardText>

          <VDivider />

          <VCardActions class="pa-4 gap-2">
            <VBtn size="small" color="primary" variant="tonal" @click="openEditDialog(pub)">
              Изменить
            </VBtn>
            <VBtn size="small" color="success" variant="tonal" @click="publishNow(pub)">
              Опубликовать сейчас
            </VBtn>
            <VSpacer />
            <VBtn size="small" color="error" icon="ri-delete-bin-line" variant="text" @click="deletePublication(pub)" />
          </VCardActions>
        </VCard>
      </VCol>
    </VRow>

    <div v-else class="text-center py-12">
      <VIcon icon="ri-calendar-todo-line" size="64" color="muted" class="mb-4" />
      <h3 class="text-h6 text-muted">Запланированных публикаций не найдено</h3>
      <p class="text-body-2 text-muted">Создайте свой первый пост или историю прямо сейчас!</p>
    </div>

    <!-- Модальный диалог создания/редактирования -->
    <VDialog v-model="showDialog" max-width="1100" scrollable>
      <VCard class="rounded-lg">
        <VCardTitle class="d-flex justify-space-between align-center border-b pa-4">
          <span class="text-h6 font-weight-bold">
            {{ dialogMode === 'create' ? 'Новая публикация' : 'Редактировать публикацию' }}
          </span>
          <VBtn icon="ri-close-line" variant="text" @click="showDialog = false" />
        </VCardTitle>

        <VCardText class="pa-6">
          <VRow>
            <!-- Слева: Конструктор публикации -->
            <VCol cols="12" md="7">
              <VRadioGroup v-model="form.type" inline label="Тип публикации" class="mb-4">
                <VRadio label="Пост в ленту" value="post" color="primary" />
                <VRadio label="История (Сторис)" value="story" color="success" />
              </VRadioGroup>

              <!-- Поле ввода текста (только для постов) -->
              <div v-if="form.type === 'post'" class="mb-4">
                <div class="d-flex align-center justify-space-between mb-1">
                  <span class="text-subtitle-2">Текст публикации</span>
                  <div class="emoji-picker-inline">
                    <span
                      v-for="e in popularEmojis"
                      :key="e"
                      class="emoji-item cursor-pointer px-1 text-h6"
                      @click="appendEmoji(e)"
                    >
                      {{ e }}
                    </span>
                  </div>
                </div>
                <VTextarea
                  v-model="form.content_text"
                  placeholder="Напишите текст поста..."
                  rows="4"
                  variant="outlined"
                  hide-details
                />
              </div>

              <!-- Загрузка изображения -->
              <div class="mb-4">
                <span class="text-subtitle-2 d-block mb-1">Изображение публикации</span>
                <div class="d-flex align-center gap-3">
                  <VTextField
                    v-model="form.media_url"
                    placeholder="Ссылка на картинку или загрузите файл"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                  <input
                    type="file"
                    ref="mediaFileInput"
                    class="d-none"
                    accept="image/*"
                    @change="handleImageUpload"
                  />
                  <VBtn color="primary" variant="tonal" prepend-icon="ri-upload-2-line" @click="$refs.mediaFileInput.click()">
                    Файл
                  </VBtn>
                  <VBtn
                    v-if="form.media_url"
                    color="secondary"
                    variant="tonal"
                    prepend-icon="ri-image-edit-line"
                    @click="startEditingImage"
                  >
                    Редактировать
                  </VBtn>
                </div>
              </div>

              <!-- Настройка кнопок-ссылок -->
              <VCard variant="tonal" class="pa-4 mb-4" color="primary">
                <span class="text-subtitle-2 font-weight-bold d-block mb-2">
                  {{ form.type === 'story' ? 'Интерактивный стикер ссылки в историю' : 'Кнопка действия в пост' }}
                </span>
                <VRow>
                  <VCol cols="12" sm="6">
                    <VTextField
                      v-model="form.link_url"
                      label="Ссылка (URL)"
                      placeholder="https://example.com"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </VCol>
                  <VCol cols="12" sm="6">
                    <!-- Для истории кнопочный текст из пресетов ВК API -->
                    <VSelect
                      v-if="form.type === 'story'"
                      v-model="form.button_text"
                      :items="storyButtonTexts"
                      item-title="title"
                      item-value="value"
                      label="Текст стикера-кнопки"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                    <!-- Для постов любой текст кнопки -->
                    <VTextField
                      v-else
                      v-model="form.button_text"
                      label="Текст кнопки"
                      placeholder="Открыть"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </VCol>
                </VRow>
              </VCard>

              <!-- Время отправки -->
              <div class="mb-4">
                <span class="text-subtitle-2 d-block mb-1">Дата и время публикации (по вашему часовому поясу)</span>
                <VTextField
                  v-model="localPublishDateTime"
                  type="datetime-local"
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </div>
            </VCol>

            <!-- Справа: Интерактивный предпросмотр -->
            <VCol cols="12" md="5" class="d-flex align-center justify-center bg-lighten-4 rounded-lg py-6" style="background: #f7f7f7;">
              <div class="preview-phone border rounded-xl shadow-lg bg-white overflow-hidden relative" style="width: 290px; height: 530px; border: 8px solid #2d3748;">
                <div class="phone-notch absolute top-0 left-1/2 transform -translate-x-1/2 bg-black rounded-b-xl" style="height: 15px; width: 120px; z-index: 10;"></div>
                
                <!-- Заголовок ВК -->
                <div class="px-3 py-2 border-b d-flex align-center gap-2 bg-white" style="font-size: 11px;">
                  <VAvatar size="20" class="bg-primary text-white text-caption font-weight-bold">
                    VK
                  </VAvatar>
                  <div>
                    <div class="font-weight-bold">{{ connections.find(c => c.id === selectedConnectionId)?.name || 'Сообщество ВК' }}</div>
                    <div class="text-muted" style="font-size: 9px;">Реклама / Публикация</div>
                  </div>
                </div>

                <!-- Содержимое Предпросмотра: СТОРИС -->
                <div v-if="form.type === 'story'" class="h-100 bg-black text-white relative d-flex flex-column justify-center" style="height: calc(100% - 37px);">
                  <img v-if="form.media_url" :src="form.media_url" class="absolute inset-0 w-100 h-100 object-cover" />
                  <div v-else class="d-flex flex-column align-center justify-center text-muted">
                    <VIcon icon="ri-movie-line" size="40" />
                    <span class="text-caption">Добавьте изображение сторис</span>
                  </div>

                  <!-- Наложенный стикер-ссылка -->
                  <div
                    v-if="form.link_url"
                    class="absolute bg-white text-black px-4 py-2 rounded-lg font-weight-bold shadow-lg d-flex align-center gap-1 cursor-pointer"
                    style="bottom: 80px; left: 50%; transform: translateX(-50%); font-size: 12px; max-width: 80%; width: max-content;"
                  >
                    <VIcon icon="ri-links-line" size="14" class="text-primary" />
                    <span>{{ storyButtonTexts.find(b => b.value === form.button_text)?.title || 'Открыть' }}</span>
                  </div>
                </div>

                <!-- Содержимое Предпросмотра: ПОСТ -->
                <div v-else class="h-100 bg-white overflow-y-auto px-3 py-2" style="height: calc(100% - 37px); font-size: 12px;">
                  <p class="text-body-2 mb-2 text-pre-line">{{ form.content_text || 'Текст вашего поста...' }}</p>
                  
                  <img v-if="form.media_url" :src="form.media_url" class="w-100 rounded mb-2 object-cover" style="max-height: 160px;" />

                  <!-- Сниппет ссылки с кнопкой действия -->
                  <div v-if="form.link_url" class="border rounded pa-2 d-flex align-center justify-space-between mb-2" style="font-size: 11px; background: #f8fafc;">
                    <div class="text-truncate me-2" style="flex-grow: 1;">
                      <div class="font-weight-bold text-truncate">{{ form.link_url }}</div>
                      <div class="text-muted text-truncate">Перейти по адресу</div>
                    </div>
                    <VBtn size="small" color="primary" density="compact" class="text-none">
                      {{ form.button_text || 'Открыть' }}
                    </VBtn>
                  </div>
                </div>
              </div>
            </VCol>
          </VRow>
        </VCardText>

        <VDivider />

        <VCardActions class="pa-4 gap-2">
          <VSpacer />
          <VBtn color="secondary" variant="outlined" @click="showDialog = false">
            Отмена
          </VBtn>
          <VBtn color="primary" :loading="saving" @click="savePublication">
            Сохранить публикацию
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог графического Canvas-редактора -->
    <VDialog v-model="showEditorDialog" max-width="1200" persistent scrollable>
      <VCard class="rounded-lg">
        <VCardTitle class="d-flex justify-space-between align-center border-b pa-4">
          <span class="text-h6 font-weight-bold">Графический фоторедактор</span>
          <VBtn icon="ri-close-line" variant="text" @click="showEditorDialog = false" />
        </VCardTitle>

        <VCardText class="pa-4 bg-slate">
          <VRow>
            <!-- Слева: Панель инструментов редактора -->
            <VCol cols="12" md="4" class="border-e pe-6">
              <!-- Раздел: Соотношение сторон обрезки -->
              <div class="mb-4">
                <span class="text-subtitle-2 d-block mb-2 font-weight-bold">Рамка кадрирования</span>
                <VBtnToggle v-model="cropRatio" mandatory density="compact" color="primary" class="w-100">
                  <VBtn :value="1.0" class="flex-grow-1">1:1 (Пост)</VBtn>
                  <VBtn :value="0.5625" class="flex-grow-1">9:16 (Сториз)</VBtn>
                  <VBtn :value="null" class="flex-grow-1">Свободная</VBtn>
                </VBtnToggle>
                <VBtn color="primary" size="small" class="mt-2 w-100 text-none" prepend-icon="ri-crop-2-line" @click="applyCrop">
                  Применить обрезку
                </VBtn>
              </div>

              <!-- Раздел: Поворот -->
              <div class="mb-4">
                <VBtn color="secondary" variant="tonal" class="w-100 text-none" prepend-icon="ri-clockwise-line" @click="rotateImage">
                  Повернуть на 90°
                </VBtn>
              </div>

              <!-- Раздел: Цветовые фильтры -->
              <div class="mb-4">
                <span class="text-subtitle-2 d-block mb-2 font-weight-bold">Эффекты и фильтры</span>
                <VSelect
                  v-model="editorFilter"
                  :items="filtersList"
                  item-title="name"
                  item-value="value"
                  variant="outlined"
                  density="compact"
                  hide-details
                  @update:model-value="drawCanvas"
                />
              </div>

              <!-- Раздел: Добавление текста -->
              <VExpansionPanels class="mb-4" density="compact">
                <VExpansionPanel title="Добавить надпись">
                  <VExpansionPanelText class="pa-2">
                    <VTextField
                      v-model="editorText"
                      placeholder="Текст надписи"
                      variant="outlined"
                      density="compact"
                      class="mb-2"
                      hide-details
                    />
                    <div class="d-flex align-center gap-2 mb-2">
                      <VTextField
                        v-model="editorTextColor"
                        type="color"
                        label="Цвет"
                        variant="outlined"
                        density="compact"
                        style="width: 80px;"
                        hide-details
                      />
                      <VTextField
                        v-model="editorTextSize"
                        type="number"
                        label="Размер шрифта"
                        variant="outlined"
                        density="compact"
                        style="width: 120px;"
                        hide-details
                      />
                    </div>
                    <VBtn color="primary" size="small" class="w-100 text-none" @click="addText">
                      Поместить на фото
                    </VBtn>
                  </VExpansionPanelText>
                </VExpansionPanel>

                <!-- Раздел: Добавление стикеров / эмодзи -->
                <VExpansionPanel title="Добавить стикер / эмодзи">
                  <VExpansionPanelText class="pa-2">
                    <div class="d-flex flex-wrap gap-2 justify-center max-h-40 overflow-y-auto">
                      <span
                        v-for="s in availableStickers"
                        :key="s"
                        class="sticker-item cursor-pointer text-h4 hover-zoom"
                        @click="addSticker(s)"
                      >
                        {{ s }}
                      </span>
                    </div>
                  </VExpansionPanelText>
                </VExpansionPanel>
              </VExpansionPanels>

              <!-- Удаление выделенного объекта -->
              <VBtn
                v-if="selectedObjectId"
                color="error"
                variant="flat"
                class="w-100 text-none mb-4"
                prepend-icon="ri-delete-bin-line"
                @click="deleteSelectedObject"
              >
                Удалить выделенный объект
              </VBtn>
              
              <div class="text-caption text-muted">
                * Кликните и тяните текст или стикер на фото, чтобы переместить его.
              </div>
            </VCol>

            <!-- Справа: Холст с фоторедактором -->
            <VCol cols="12" md="8" class="d-flex align-center justify-center p-4 relative" style="background: #1e293b; min-height: 500px;">
              <canvas
                ref="imageEditorCanvas"
                style="max-width: 100%; max-height: 600px; box-shadow: 0px 8px 30px rgba(0, 0, 0, 0.5); cursor: move; border-radius: 4px;"
                @mousedown="handleCanvasMouseDown"
                @mousemove="handleCanvasMouseMove"
                @mouseup="handleCanvasMouseUp"
                @mouseleave="handleCanvasMouseUp"
              />
              <div v-if="editorLoading" class="absolute inset-0 d-flex align-center justify-center bg-black bg-opacity-50 text-white">
                <VProgressCircular indeterminate size="64" />
              </div>
            </VCol>
          </VRow>
        </VCardText>

        <VDivider />

        <VCardActions class="pa-4 gap-2">
          <VSpacer />
          <VBtn color="secondary" variant="outlined" @click="showEditorDialog = false">
            Сбросить и закрыть
          </VBtn>
          <VBtn color="success" :loading="editorLoading" @click="saveEditedImage">
            Применить изменения
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.clickable-card {
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}
.clickable-card:hover {
  transform: translateY(-4px);
  box-shadow: 0px 8px 20px rgba(0, 0, 0, 0.12) !important;
}
.emoji-item {
  transition: transform 0.1s;
}
.emoji-item:hover {
  transform: scale(1.3);
}
.sticker-item {
  transition: transform 0.1s;
}
.sticker-item:hover {
  transform: scale(1.25);
}
.preview-phone {
  user-select: none;
}
.text-truncate-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
