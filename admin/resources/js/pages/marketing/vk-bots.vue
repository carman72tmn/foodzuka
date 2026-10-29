<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import VkMarketingBotModal from '@/components/VkMarketingBotModal.vue'

const toast = useToast()

// Состояние подключений и ботов
const connections = ref([])
const birthdayBots = ref([])
const coverBots = ref([])
const selectedConnectionId = ref(null)
const loading = ref(false)

// Состояние бота первокоммента
const currentFirstCommentSettings = ref(null)
const showFirstCommentSettingsDialog = ref(false)
const savingFirstComment = ref(false)
const newCommentText = ref("")
const activeFirstCommentTab = ref("general")
const isRandomDelay = ref(false)
const firstCommentForm = ref({
  id: null,
  vk_bot_connection_id: null,
  is_active: false,
  comments: [],
  post_type_filter: 'all',
  include_keywords: '',
  exclude_keywords: '',
  delay_seconds: 0,
  ignore_empty_text: false,
  exclude_reposts: false,
  delay_min: 0,
  delay_max: 0
})

// Состояние бота дней рождения
const showBirthdaySettingsDialog = ref(false)
const savingBirthday = ref(false)
const testingBirthday = ref(false)
const imageBirthdayUploading = ref(false)

const birthdayForm = ref({
  id: null,
  vk_bot_connection_id: null,
  is_active: true,
  message_template: "Поздравляем с днем рождения наших подписчиков: {names}! 🎉 Желаем отличного настроения и приятного аппетита! 🎂🍕",
  image_url: null,
  include_names: true,
  name_format: "fullname",
  make_links: true,
  publish_time: "10:00",
  delete_mode: "interval",
  delete_interval_minutes: 720,
  delete_time: "22:00",
  vk_bot_token: ""
})

// Состояние бота динамических обложек
const showCoverSettingsDialog = ref(false)
const savingCover = ref(false)
const publishingCover = ref(false)
const imageCoverUploading = ref(false)
const previewLoading = ref(false)
const previewImageUrl = ref(null)
const selectedWidgetIndex = ref(-1)

const coverForm = ref({
  id: null,
  vk_bot_connection_id: null,
  name: "Основная обложка",
  is_active: true,
  is_rotation_enabled: true,
  schedule_type: "always",
  schedule_start_time: "09:00",
  schedule_end_time: "22:00",
  rotation_order: 0,
  background_image_url: null,
  slideshow_images: [],
  slideshow_interval_minutes: 5,
  slideshow_mode: "sequence",
  city_weather: "Москва",
  widgets: [],
  update_interval: "1m",
  use_custom_callback: false,
  callback_confirmation_code: "",
  callback_secret_key: "",
  vk_bot_token: ""
})

// Состояние бота конкурсов (геймификации)
const showContestSettingsDialog = ref(false)
const contestList = ref([])
const activeContestTab = ref('list') // list, edit, players, winners
const loadingContests = ref(false)
const savingContest = ref(false)
const launchingContest = ref(false)

const contestPlayers = ref([])
const contestWinners = ref([])
const currentContestId = ref(null)

const contestForm = ref({
  id: null,
  vk_bot_connection_id: null,
  title: "",
  rules_text: "",
  game_type: "roulette",
  prizes: [],
  start_attempts: 3,
  max_attempts: 10,
  delay_between_moves: 60,
  repost_attempts: 3,
  subscribe_attempts: 0,
  like_attempts: 1,
  safe_code: "",
  msg_miss: "🎰 {name}, увы! Этот сектор оказался пустым. Попробуйте еще раз!",
  msg_win: "🎉 Поздравляем, {name}! Вы выиграли приз: {prize}! Инструкция по получению отправлена в ЛС.",
  msg_out_of_attempts: "❌ {name}, у вас закончились попытки!",
  msg_cooldown: "⌛ {name}, вы делаете ходы слишком часто! Пожалуйста, подождите еще {cooldown} сек.",
  msg_subscribe_needed: "⚠️ {name}, вы не подписаны на наше сообщество! Для участия в конкурсе обязательно подпишитесь на группу.",
  msg_like_needed: "❤️ {name}, для участия необходимо поставить лайк к этому посту!",
  msg_repost_needed: "📢 {name}, для участия необходимо сделать репост этого поста на свою страницу!",
  msg_invalid_format: "❓ {name}, я не понял ваш ход. Пожалуйста, напишите правильный формат ходов (например, {example}).",
  msg_pm_congratulations: "🎉 Здравствуйте, {name}!\n\nВы выиграли в конкурсе «{title}» приз:\n🎁 {prize}!\n\n🔑 Ваш уникальный промокод для заказа: {code}\n\nВведите его в корзине при оформлении заказа на сайте или назовите оператору.",
  can_win_once: true,
  help_draw_prizes: true,
  black_list: [],
  white_list: [],
  remind_winner_pm: false,
  remind_attempts: true,
  remind_attempts_count: 3,
  remind_attempts_quiet_from: 22,
  remind_attempts_quiet_to: 8,
  anti_prize_hunters: false,
  draw_type: "probability",
  draw_probability_interval: 100,
  vk_bot_token: ""
})

const blackListText = computed({
  get: () => (contestForm.value.black_list || []).join(', '),
  set: (val) => {
    contestForm.value.black_list = val ? val.split(',').map(s => s.trim()).filter(Boolean) : []
  }
})

const whiteListText = computed({
  get: () => (contestForm.value.white_list || []).join(', '),
  set: (val) => {
    contestForm.value.white_list = val ? val.split(',').map(s => s.trim()).filter(Boolean) : []
  }
})

// Хелперы для призов
const newPrizeName = ref("")
const newPrizeQty = ref(1)
const newPrizeImageUrl = ref("")
const isUploadingPrize = ref(false)
const activeUploadIndex = ref(null)

const triggerPrizeUpload = () => {
  const el = document.getElementById('prize-image-input')
  if (el) el.click()
}

const onPrizeImageSelected = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const formData = new FormData()
  formData.append('file', file)
  
  isUploadingPrize.value = true
  try {
    const res = await axios.post('/api/v1/vk-contests/prizes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    if (res.data && res.data.image_url) {
      newPrizeImageUrl.value = res.data.image_url
    }
  } catch (err) {
    console.error(err)
    alert("Ошибка загрузки изображения: " + (err.response?.data?.detail || err.message))
  } finally {
    isUploadingPrize.value = false
  }
}

const triggerPrizeItemUpload = (index) => {
  activeUploadIndex.value = index
  const el = document.getElementById('prize-item-image-input')
  if (el) el.click()
}

const onPrizeItemImageSelected = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  if (activeUploadIndex.value === null) return
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const res = await axios.post('/api/v1/vk-contests/prizes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    if (res.data && res.data.image_url) {
      contestForm.value.prizes[activeUploadIndex.value].image_url = res.data.image_url
    }
  } catch (err) {
    console.error(err)
    alert("Ошибка загрузки изображения: " + (err.response?.data?.detail || err.message))
  } finally {
    activeUploadIndex.value = null
  }
}

const addPrizeToForm = () => {
  if (!newPrizeName.value.trim()) return
  contestForm.value.prizes.push({
    id: Date.now(),
    name: newPrizeName.value.trim(),
    qty: parseInt(newPrizeQty.value) || 1,
    image_url: newPrizeImageUrl.value || null,
    won_count: 0
  })
  newPrizeName.value = ""
  newPrizeQty.value = 1
  newPrizeImageUrl.value = ""
}

const removePrizeFromForm = (index) => {
  contestForm.value.prizes.splice(index, 1)
}

const insertTextAtCursor = (textToInsert) => {
  const textarea = document.getElementById('rules-text-input')
  if (!textarea) {
    contestForm.value.rules_text = (contestForm.value.rules_text || "") + textToInsert
    return
  }
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = contestForm.value.rules_text || ""
  
  contestForm.value.rules_text = text.substring(0, start) + textToInsert + text.substring(end)
  
  nextTick(() => {
    textarea.focus()
    textarea.selectionStart = textarea.selectionEnd = start + textToInsert.length
  })
}

const processedPreviewText = computed(() => {
  let txt = contestForm.value.rules_text || ""
  if (!txt) return "Текст поста пуст. Напишите правила розыгрыша!"
  
  const conn = connections.value.find(c => c.id === contestForm.value.vk_bot_connection_id)
  const groupLink = conn ? `https://vk.com/club${conn.vk_group_id}` : 'https://vk.com/group'
  
  const prizesList = contestForm.value.prizes.map(p => `🎁 ${p.name} — ${p.qty} шт.`).join('\n') || 'Не добавлены'
  
  const gameNames = {
    'roulette': 'Рулетка 🎰',
    'seabattle': 'Морской бой ⚓',
    'chests': 'Сундуки 📦',
    'safe': 'Сейф 🔓',
    'battle': 'Битва за поле 🏖️'
  }
  const gameName = gameNames[contestForm.value.game_type] || 'Игра'

  txt = txt.replace(/{ссылка}/g, groupLink)
  txt = txt.replace(/{название}/g, gameName)
  txt = txt.replace(/{призы}/g, prizesList)
  txt = txt.replace(/{время_кд}/g, `${contestForm.value.delay_between_moves || 30} сек`)
  txt = txt.replace(/{попытки}/g, `${contestForm.value.start_attempts || 3} шт`)
  
  return txt
})

// Загрузка данных
const loadData = async () => {
  loading.value = true
  try {
    const connRes = await axios.get('/api/v1/vk/bots')
    connections.value = connRes.data

    const birthdayRes = await axios.get('/api/v1/vk-birthday-bots/')
    birthdayBots.value = birthdayRes.data

    const coverRes = await axios.get('/api/v1/vk-cover-bots/')
    coverBots.value = coverRes.data

    if (connections.value.length > 0) {
      selectedConnectionId.value = connections.value[0].id
      loadMarketingBotsConfig(selectedConnectionId.value)
    }
  } catch (error) {
    console.error('Ошибка загрузки данных:', error)
    toast.error('Не удалось загрузить настройки ботов')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

// Отслеживание смены сообщества
watch(selectedConnectionId, (newVal) => {
  if (!newVal) return
  updateForms(newVal)
  loadMarketingBotsConfig(newVal)
})

function updateForms(connectionId) {
  // Обновляем форму Дней рождения
  const existingBBot = birthdayBots.value.find(b => b.vk_bot_connection_id === connectionId)
  if (existingBBot) {
    birthdayForm.value = { 
      ...existingBBot,
      vk_bot_token: existingBBot.vk_bot_token || ""
    }
  } else {
    birthdayForm.value = {
      id: null,
      vk_bot_connection_id: connectionId,
      is_active: true,
      message_template: "Поздравляем с днем рождения наших подписчиков: {names}! 🎉 Желаем отличного настроения и приятного аппетита! 🎂🍕",
      image_url: null,
      include_names: true,
      name_format: "fullname",
      make_links: true,
      publish_time: "10:00",
      delete_mode: "interval",
      delete_interval_minutes: 720,
      delete_time: "22:00",
      vk_bot_token: ""
    }
  }

  // Обновляем форму динамической обложки
  const existingCBot = coverBots.value.find(b => b.vk_bot_connection_id === connectionId)
  if (existingCBot) {
    coverForm.value = {
      ...existingCBot,
      name: existingCBot.name || "Основная обложка",
      is_rotation_enabled: existingCBot.is_rotation_enabled ?? true,
      schedule_type: existingCBot.schedule_type || "always",
      schedule_start_time: existingCBot.schedule_start_time || "09:00",
      schedule_end_time: existingCBot.schedule_end_time || "22:00",
      rotation_order: existingCBot.rotation_order || 0,
      slideshow_images: existingCBot.slideshow_images || [],
      slideshow_interval_minutes: existingCBot.slideshow_interval_minutes || 5,
      slideshow_mode: existingCBot.slideshow_mode || "sequence",
      update_interval: existingCBot.update_interval || "1m",
      use_custom_callback: existingCBot.use_custom_callback || false,
      callback_confirmation_code: existingCBot.callback_confirmation_code || "",
      callback_secret_key: existingCBot.callback_secret_key || "",
      vk_bot_token: existingCBot.vk_bot_token || ""
    }
  } else {
    coverForm.value = {
      id: null,
      vk_bot_connection_id: connectionId,
      name: "Основная обложка",
      is_active: true,
      is_rotation_enabled: true,
      schedule_type: "always",
      schedule_start_time: "09:00",
      schedule_end_time: "22:00",
      rotation_order: 0,
      background_image_url: null,
      slideshow_images: [],
      slideshow_interval_minutes: 5,
      slideshow_mode: "sequence",
      city_weather: "Москва",
      widgets: [],
      update_interval: "1m",
      use_custom_callback: false,
      callback_confirmation_code: "",
      callback_secret_key: "",
      vk_bot_token: ""
    }
  }
  previewImageUrl.value = null
  selectedWidgetIndex.value = -1
  loadActivitySettingsOnly(connectionId)
  loadFirstCommentSettingsOnly(connectionId)
}

const showMultiCoverManagerDialog = ref(false)

const selectedConnectionCoverBots = computed(() => {
  if (!selectedConnectionId.value) return []
  return coverBots.value.filter(b => b.vk_bot_connection_id === selectedConnectionId.value)
})

const openCoverManager = () => {
  if (!selectedConnectionId.value) return
  showMultiCoverManagerDialog.value = true
}

const createNewCoverBot = () => {
  const count = selectedConnectionCoverBots.value.length
  coverForm.value = {
    id: null,
    vk_bot_connection_id: selectedConnectionId.value,
    name: `Обложка #${count + 1}`,
    is_active: true,
    is_rotation_enabled: true,
    schedule_type: "always",
    schedule_start_time: "09:00",
    schedule_end_time: "22:00",
    rotation_order: count,
    background_image_url: null,
    slideshow_images: [],
    slideshow_interval_minutes: 5,
    slideshow_mode: "sequence",
    city_weather: "Москва",
    widgets: [],
    update_interval: "1m",
    use_custom_callback: false,
    callback_confirmation_code: "",
    callback_secret_key: "",
    vk_bot_token: ""
  }
  previewImageUrl.value = null
  selectedWidgetIndex.value = -1
  showCoverSettingsDialog.value = true
}

const editCoverBot = (bot) => {
  coverForm.value = {
    ...bot,
    name: bot.name || "Основная обложка",
    is_rotation_enabled: bot.is_rotation_enabled ?? true,
    schedule_type: bot.schedule_type || "always",
    schedule_start_time: bot.schedule_start_time || "09:00",
    schedule_end_time: bot.schedule_end_time || "22:00",
    rotation_order: bot.rotation_order || 0,
    slideshow_images: bot.slideshow_images || [],
    slideshow_interval_minutes: bot.slideshow_interval_minutes || 5,
    slideshow_mode: bot.slideshow_mode || "sequence",
    widgets: bot.widgets || [],
    update_interval: bot.update_interval || "1m",
    use_custom_callback: bot.use_custom_callback || false,
    callback_confirmation_code: bot.callback_confirmation_code || "",
    callback_secret_key: bot.callback_secret_key || "",
    vk_bot_token: bot.vk_bot_token || ""
  }
  previewImageUrl.value = null
  selectedWidgetIndex.value = -1
  showCoverSettingsDialog.value = true
}

const cloneCoverBot = async (bot) => {
  try {
    const cloneData = {
      ...bot,
      id: null,
      name: `${bot.name || 'Обложка'} (Копия)`
    }
    const res = await axios.post('/api/v1/vk-cover-bots/', cloneData)
    coverBots.value.push(res.data)
    toast.success('Обложка успешно скопирована!')
  } catch (err) {
    toast.error('Ошибка при копировании обложки')
  }
}

const deleteCoverBot = async (botId) => {
  if (!confirm('Вы уверены, что хотите удалить эту обложку?')) return
  try {
    await axios.delete(`/api/v1/vk-cover-bots/${botId}`)
    coverBots.value = coverBots.value.filter(b => b.id !== botId)
    toast.success('Обложка удалена')
  } catch (err) {
    toast.error('Ошибка при удалении обложки')
  }
}

const handleSlideshowUpload = async (event) => {
  const files = event.target.files
  if (!files || files.length === 0) return

  imageCoverUploading.value = true
  try {
    for (let i = 0; i < files.length; i++) {
      const formData = new FormData()
      formData.append('file', files[i])
      const res = await axios.post('/api/v1/vk-cover-bots/upload-background', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      if (!coverForm.value.slideshow_images) {
        coverForm.value.slideshow_images = []
      }
      coverForm.value.slideshow_images.push(res.data.image_url)
    }
    toast.success('Изображения успешно добавлены в слайд-шоу!')
  } catch (err) {
    toast.error('Ошибка при загрузке картинок слайд-шоу')
  } finally {
    imageCoverUploading.value = false
  }
}

const removeSlideshowImage = (idx) => {
  if (coverForm.value.slideshow_images) {
    coverForm.value.slideshow_images.splice(idx, 1)
  }
}

// Получение статусов для плашек
const getBirthdayBotStatus = () => {
  if (!selectedConnectionId.value) return { text: 'Недоступен', color: 'secondary' }
  const existing = birthdayBots.value.find(b => b.vk_bot_connection_id === selectedConnectionId.value)
  if (!existing) return { text: 'Не настроен', color: 'warning' }
  return existing.is_active ? { text: 'Активен', color: 'success' } : { text: 'Отключен', color: 'error' }
}

const getCoverBotStatus = () => {
  if (!selectedConnectionId.value) return { text: 'Недоступен', color: 'secondary' }
  const existing = coverBots.value.find(b => b.vk_bot_connection_id === selectedConnectionId.value)
  if (!existing) return { text: 'Не настроен', color: 'warning' }
  return existing.is_active ? { text: 'Активен', color: 'success' } : { text: 'Отключен', color: 'error' }
}

// --- Управление Ботом Именинников ---
const openBirthdaySettings = () => {
  if (!selectedConnectionId.value) {
    toast.warning('Выберите сообщество ВКонтакте!')
    return
  }
  updateForms(selectedConnectionId.value)
  showBirthdaySettingsDialog.value = true
}

const onBirthdayImageSelected = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  imageBirthdayUploading.value = true
  try {
    const res = await axios.post('/api/v1/vk-birthday-bots/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    birthdayForm.value.image_url = res.data.image_url
    toast.success('Изображение загружено')
  } catch (error) {
    console.error(error)
    toast.error('Ошибка загрузки изображения')
  } finally {
    imageBirthdayUploading.value = false
  }
}

const saveBirthdaySettings = async () => {
  savingBirthday.value = true
  try {
    if (birthdayForm.value.id) {
      const res = await axios.patch(`/api/v1/vk-birthday-bots/${birthdayForm.value.id}`, birthdayForm.value)
      const idx = birthdayBots.value.findIndex(b => b.id === birthdayForm.value.id)
      if (idx !== -1) birthdayBots.value[idx] = res.data
    } else {
      const res = await axios.post('/api/v1/vk-birthday-bots/', birthdayForm.value)
      birthdayBots.value.push(res.data)
      birthdayForm.value.id = res.data.id
    }
    toast.success('Настройки сохранены')
    showBirthdaySettingsDialog.value = false
  } catch (error) {
    console.error(error)
    toast.error('Не удалось сохранить настройки')
  } finally {
    savingBirthday.value = false
  }
}

const testBirthdayPublish = async () => {
  if (!birthdayForm.value.id) {
    toast.warning('Сначала сохраните настройки бота!')
    return
  }
  testingBirthday.value = true
  try {
    const res = await axios.post(`/api/v1/vk-birthday-bots/${birthdayForm.value.id}/test-publish`)
    if (res.data.status === 'success') {
      toast.success(res.data.message)
    } else {
      toast.info(res.data.message)
    }
  } catch (error) {
    console.error(error)
    toast.error('Ошибка при запуске теста')
  } finally {
    testingBirthday.value = false
  }
}

// --- Управление Ботом Обложек ---
const openCoverSettings = () => {
  if (!selectedConnectionId.value) {
    toast.warning('Выберите сообщество ВКонтакте!')
    return
  }
  openCoverManager()
}

const onCoverBackgroundSelected = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  imageCoverUploading.value = true
  try {
    const res = await axios.post('/api/v1/vk-cover-bots/upload-background', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    coverForm.value.background_image_url = res.data.image_url
    previewImageUrl.value = null // Сбрасываем превью
    toast.success('Фоновое изображение загружено')
  } catch (error) {
    console.error(error)
    toast.error('Ошибка загрузки фона')
  } finally {
    imageCoverUploading.value = false
  }
}

const showMobileSafeArea = ref(true)

const addWidget = (type) => {
  previewImageUrl.value = null
  const defaultWidgets = {
    clock: { type: 'clock', x: 260, y: 120, font_size: 28, color: '#ffffff', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, icon: '•', show_date: true },
    weather: { type: 'weather', x: 880, y: 120, font_size: 26, color: '#ffffff', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, city: coverForm.value.city_weather || 'Москва', icon: '☀' },
    work_hours: { type: 'work_hours', x: 260, y: 220, font_size: 24, color: '#ffffff', bg_style: 'glass', container_padding: 12, container_radius: 14, text_shadow: true, text_stroke: true, open_time: '10:00', close_time: '22:00', work_days: [1, 2, 3, 4, 5, 6, 7], text_open: '🟢 Открыты до {close_time}', text_closing_soon: '🟡 Закрываемся через {time_left}', text_opening_soon: '🟡 Откроемся через {time_left}', text_closed: '🔴 Закрыто! Откроемся в {next_open_time}', opening_soon_threshold: 60, closing_soon_threshold: 60, icon: '' },
    timer: { type: 'timer', x: 260, y: 220, font_size: 24, color: '#ffea00', bg_style: 'neon', container_padding: 12, container_radius: 14, text_shadow: true, text_stroke: true, label: 'До конца акции:', target_date: new Date(Date.now() + 86400000 * 3).toISOString().slice(0, 16), expired_text: 'Акция завершена!', icon: '•' },
    text: { type: 'text', x: 260, y: 200, font_size: 24, color: '#ffffff', bg_style: 'solid', container_padding: 10, container_radius: 10, text_shadow: true, text_stroke: true, text: 'Заказывайте на vezuroll.ru ●', icon: '◆' },
    active_subscriber: { type: 'active_subscriber', x: 260, y: 310, font_size: 24, color: '#ffffff', bg_style: 'glass', container_padding: 12, container_radius: 16, text_shadow: true, text_stroke: true, label: 'Лидер недели:', period: 'week', avatar_size: 50, icon: '★' },
    orders_counter: { type: 'orders_counter', x: 880, y: 220, font_size: 24, color: '#00e676', bg_style: 'pill', container_padding: 10, container_radius: 20, text_shadow: true, text_stroke: true, label: 'Сегодня доставлено:', icon: '▶' },
    last_winner: { type: 'last_winner', x: 880, y: 310, font_size: 22, color: '#ff9100', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, label: 'Победитель игры:', icon: '✦' },
    promo_code: { type: 'promo_code', x: 550, y: 220, font_size: 26, color: '#ffffff', bg_style: 'gradient', container_padding: 12, container_radius: 14, text_shadow: true, text_stroke: true, label: 'Промокод:', code: 'VK2026', icon: '★' }
  }

  coverForm.value.widgets.push({ ...defaultWidgets[type] })
  selectedWidgetIndex.value = coverForm.value.widgets.length - 1
}

const applyPreset = (presetName) => {
  previewImageUrl.value = null
  selectedWidgetIndex.value = -1
  if (presetName === 'premium') {
    coverForm.value.widgets = [
      { type: 'clock', x: 260, y: 120, font_size: 28, color: '#ffffff', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, icon: '•', show_date: true },
      { type: 'weather', x: 880, y: 120, font_size: 26, color: '#ffffff', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, city: coverForm.value.city_weather || 'Москва', icon: '☀' },
      { type: 'promo_code', x: 550, y: 210, font_size: 26, color: '#ffffff', bg_style: 'gradient', container_padding: 12, container_radius: 14, text_shadow: true, text_stroke: true, label: 'Промокод:', code: 'VK2026', icon: '★' },
      { type: 'active_subscriber', x: 260, y: 310, font_size: 24, color: '#ffffff', bg_style: 'glass', container_padding: 12, container_radius: 16, text_shadow: true, text_stroke: true, label: 'Лидер недели:', period: 'week', avatar_size: 50, icon: '★' }
    ]
  } else if (presetName === 'promo') {
    coverForm.value.widgets = [
      { type: 'clock', x: 260, y: 120, font_size: 26, color: '#ffffff', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, icon: '•', show_date: false },
      { type: 'orders_counter', x: 880, y: 120, font_size: 24, color: '#00e676', bg_style: 'pill', container_padding: 10, container_radius: 20, text_shadow: true, text_stroke: true, label: 'Сегодня доставлено:', icon: '▶' },
      { type: 'timer', x: 260, y: 220, font_size: 24, color: '#ffea00', bg_style: 'neon', container_padding: 12, container_radius: 14, text_shadow: true, text_stroke: true, label: 'До конца акции:', target_date: new Date(Date.now() + 86400000 * 3).toISOString().slice(0, 16), expired_text: 'Акция завершена!', icon: '•' },
      { type: 'promo_code', x: 880, y: 220, font_size: 26, color: '#ffffff', bg_style: 'gradient', container_padding: 12, container_radius: 14, text_shadow: true, text_stroke: true, label: 'Промокод:', code: 'VK2026', icon: '★' }
    ]
  } else if (presetName === 'community') {
    coverForm.value.widgets = [
      { type: 'active_subscriber', x: 260, y: 120, font_size: 24, color: '#ffffff', bg_style: 'glass', container_padding: 12, container_radius: 16, text_shadow: true, text_stroke: true, label: 'Лидер недели:', period: 'week', avatar_size: 50, icon: '★' },
      { type: 'weather', x: 880, y: 120, font_size: 26, color: '#ffffff', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, city: coverForm.value.city_weather || 'Москва', icon: '☀' },
      { type: 'last_winner', x: 260, y: 230, font_size: 22, color: '#ff9100', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, label: 'Победитель игры:', icon: '✦' },
      { type: 'clock', x: 880, y: 230, font_size: 26, color: '#ffffff', bg_style: 'glass', container_padding: 10, container_radius: 12, text_shadow: true, text_stroke: true, icon: '•', show_date: true }
    ]
  }
  toast.success(`Пресет "${presetName}" успешно применен!`)
}

const removeWidget = (index) => {
  previewImageUrl.value = null
  coverForm.value.widgets.splice(index, 1)
  if (selectedWidgetIndex.value === index) {
    selectedWidgetIndex.value = -1
  } else if (selectedWidgetIndex.value > index) {
    selectedWidgetIndex.value--
  }
}

const getWidgetLabel = (w) => {
  const titles = {
    clock: '⏰ Часы & Дата',
    weather: `🌤 Погода (${w.city || 'Москва'})`,
    work_hours: `🟢 Время работы (${w.open_time || '10:00'}-${w.close_time || '22:00'})`,
    timer: '⏱ Таймер акции',
    text: `📝 Текст: "${w.text || ''}"`,
    active_subscriber: '👑 Лидер недели',
    orders_counter: '🚚 Заказы сегодня',
    last_winner: '🎉 Победитель игры',
    promo_code: '🎁 Промокод дня'
  }
  return titles[w.type] || 'Виджет'
}

// Drag & Drop виджетов по холсту
const startDrag = (index, event) => {
  event.preventDefault()
  selectedWidgetIndex.value = index
  previewImageUrl.value = null

  const canvasElement = event.currentTarget.parentElement
  const rect = canvasElement.getBoundingClientRect()

  const handleMouseMove = (moveEvent) => {
    const x_px = moveEvent.clientX - rect.left
    const y_px = moveEvent.clientY - rect.top

    let x_val = Math.round((x_px / rect.width) * 1590)
    let y_val = Math.round((y_px / rect.height) * 530)

    x_val = Math.max(0, Math.min(1590, x_val))
    y_val = Math.max(0, Math.min(530, y_val))

    coverForm.value.widgets[index].x = x_val
    coverForm.value.widgets[index].y = y_val
  }

  const handleMouseUp = () => {
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

const loadPreview = async () => {
  previewLoading.value = true
  try {
    const res = await axios.post('/api/v1/vk-cover-bots/preview', coverForm.value)
    previewImageUrl.value = res.data.image
    toast.success('Превью успешно сгенерировано!')
  } catch (error) {
    console.error(error)
    toast.error('Не удалось сгенерировать превью')
  } finally {
    previewLoading.value = false
  }
}

const saveCoverSettings = async () => {
  savingCover.value = true
  try {
    if (coverForm.value.id) {
      const res = await axios.patch(`/api/v1/vk-cover-bots/${coverForm.value.id}`, coverForm.value)
      const idx = coverBots.value.findIndex(b => b.id === coverForm.value.id)
      if (idx !== -1) coverBots.value[idx] = res.data
    } else {
      const res = await axios.post('/api/v1/vk-cover-bots/', coverForm.value)
      coverBots.value.push(res.data)
      coverForm.value.id = res.data.id
    }
    toast.success('Настройки обложки сохранены!')
    showCoverSettingsDialog.value = false
  } catch (error) {
    console.error(error)
    toast.error('Не удалось сохранить настройки обложки')
  } finally {
    savingCover.value = false
  }
}

const publishCoverNow = async () => {
  publishingCover.value = true
  try {
    if (!coverForm.value.id) {
      const res = await axios.post('/api/v1/vk-cover-bots/', coverForm.value)
      coverBots.value.push(res.data)
      coverForm.value.id = res.data.id
      toast.success('Настройки обложки сохранены!')
    }
    await axios.post(`/api/v1/vk-cover-bots/${coverForm.value.id}/publish-now`)
    toast.success('Обложка сообщества успешно опубликована в ВК!')
  } catch (error) {
    console.error(error)
    toast.error(error.response?.data?.detail || 'Ошибка при публикации обложки на сервере ВК')
  } finally {
    publishingCover.value = false
  }
}

// --- Управление Ботом Конкурсов (Геймификации) ---
const openContests = async () => {
  if (!selectedConnectionId.value) {
    toast.warning('Выберите сообщество ВКонтакте!')
    return
  }
  showContestSettingsDialog.value = true
  activeContestTab.value = 'list'
  await loadContests()
}

const loadContests = async () => {
  loadingContests.value = true
  try {
    const res = await axios.get('/api/v1/vk-contests/', {
      params: { vk_bot_connection_id: selectedConnectionId.value }
    })
    contestList.value = res.data
  } catch (error) {
    console.error(error)
    toast.error('Не удалось загрузить список конкурсов')
  } finally {
    loadingContests.value = false
  }
}

const createContestDraft = () => {
  contestForm.value = {
    id: null,
    vk_bot_connection_id: selectedConnectionId.value,
    title: "Новый конкурс",
    rules_text: "Напишите комментарий 'крутить' под этим постом и попытайте удачу! Разыгрываем вкусные призы 🍕🍔",
    game_type: "roulette",
    prizes: [],
    start_attempts: 3,
    max_attempts: 10,
    delay_between_moves: 60,
    repost_attempts: 3,
    subscribe_attempts: 0,
    like_attempts: 1,
    safe_code: "",
    msg_miss: "🎰 {name}, увы! Этот сектор оказался пустым. Попробуйте еще раз!",
    msg_win: "🎉 Поздравляем, {name}! Вы выиграли приз: {prize}! Инструкция по получению отправлена в ЛС.",
    msg_out_of_attempts: "❌ {name}, у вас закончились попытки!",
    msg_cooldown: "⌛ {name}, вы делаете ходы слишком часто! Пожалуйста, подождите еще {cooldown} сек.",
    msg_subscribe_needed: "⚠️ {name}, вы не подписаны на наше сообщество! Для участия в конкурсе обязательно подпишитесь на группу.",
    msg_like_needed: "❤️ {name}, для участия необходимо поставить лайк к этому посту!",
    msg_repost_needed: "📢 {name}, для участия необходимо сделать репост этого поста на свою страницу!",
    msg_invalid_format: "❓ {name}, я не понял ваш ход. Пожалуйста, напишите правильный формат ходов (например, {example}).",
    msg_pm_congratulations: "🎉 Здравствуйте, {name}!\n\nВы выиграли в конкурсе «{title}» приз:\n🎁 {prize}!\n\n🔑 Ваш уникальный промокод для заказа: {code}\n\nВведите его в корзине при оформлении заказа на сайте или назовите оператору.",
    can_win_once: true,
    help_draw_prizes: true,
    black_list: [],
    white_list: [],
    remind_winner_pm: false,
    remind_attempts: true,
    remind_attempts_count: 3,
    remind_attempts_quiet_from: 22,
    remind_attempts_quiet_to: 8,
    anti_prize_hunters: false,
    draw_type: "probability",
    draw_probability_interval: 100,
    penalty_percent: 10,
    bonus_percent: 20,
    vk_bot_token: ""
  }
  activeContestTab.value = 'edit'
}

const editContest = (contest) => {
  contestForm.value = { 
    ...contest,
    vk_bot_token: contest.vk_bot_token || ""
  }
  activeContestTab.value = 'edit'
}

const saveContestSettings = async () => {
  savingContest.value = true
  try {
    if (contestForm.value.id) {
      await axios.patch(`/api/v1/vk-contests/${contestForm.value.id}`, contestForm.value)
    } else {
      await axios.post('/api/v1/vk-contests/', contestForm.value)
    }
    toast.success('Параметры конкурса сохранены!')
    activeContestTab.value = 'list'
    await loadContests()
  } catch (error) {
    console.error(error)
    toast.error(error.response?.data?.detail || 'Не удалось сохранить настройки конкурса')
  } finally {
    savingContest.value = false
  }
}

const launchContest = async (contestId) => {
  launchingContest.value = true
  try {
    await axios.post(`/api/v1/vk-contests/${contestId}/launch`)
    toast.success('Конкурс успешно опубликован на стене ВК и запущен!')
    await loadContests()
  } catch (error) {
    console.error(error)
    toast.error(error.response?.data?.detail || 'Не удалось запустить конкурс')
  } finally {
    launchingContest.value = false
  }
}

const stopContest = async (contestId) => {
  try {
    await axios.post(`/api/v1/vk-contests/${contestId}/stop`)
    toast.success('Конкурс остановлен')
    await loadContests()
  } catch (error) {
    console.error(error)
    toast.error('Не удалось остановить конкурс')
  }
}

const deleteContest = async (contestId) => {
  if (!confirm('Вы действительно хотите удалить этот конкурс со всей статистикой?')) return
  try {
    await axios.delete(`/api/v1/vk-contests/${contestId}`)
    toast.success('Конкурс удален')
    await loadContests()
  } catch (error) {
    console.error(error)
    toast.error('Не удалось удалить конкурс')
  }
}

const finishBattleContest = async (contestId) => {
  if (!confirm('Вы действительно хотите досрочно подвести итоги битвы за поле и раздать призы лидерам? Конкурс будет завершен.')) {
    return
  }
  try {
    const res = await axios.post(`/api/v1/vk-contests/${contestId}/finish`)
    if (res.data.status === 'success') {
      toast.success('Итоги успешно подведены! Победители получили уведомления в ЛС.')
      await loadContests()
      await viewWinners(contestId) // Открываем список победителей
    }
  } catch (error) {
    console.error(error)
    toast.error(error.response?.data?.detail || 'Не удалось подвести итоги конкурса')
  }
}

const viewPlayers = async (contestId) => {
  currentContestId.value = contestId
  try {
    const res = await axios.get(`/api/v1/vk-contests/${contestId}/players`)
    contestPlayers.value = res.data
    activeContestTab.value = 'players'
  } catch (error) {
    console.error(error)
    toast.error('Не удалось загрузить список участников')
  }
}

const viewWinners = async (contestId) => {
  currentContestId.value = contestId
  try {
    const res = await axios.get(`/api/v1/vk-contests/${contestId}/winners`)
    contestWinners.value = res.data
    activeContestTab.value = 'winners'
  } catch (error) {
    console.error(error)
    toast.error('Не удалось загрузить победителей')
  }
}

// Статистика конкурсов
const statsContestId = ref(null)
const statsActions = ref([])
const statsPlayers = ref([])
const statsWinners = ref([])
const loadingStats = ref(false)
const activeStatsSubTab = ref('actions')

const openStatsPage = async (contestId) => {
  activeContestTab.value = 'stats'
  if (contestId) {
    statsContestId.value = contestId
  } else if (contests.value.length > 0) {
    statsContestId.value = contests.value[0].id
  } else {
    statsContestId.value = null
  }
  await loadStatsData()
}

const loadStatsData = async () => {
  if (!statsContestId.value) return
  loadingStats.value = true
  try {
    const [actRes, plyRes, winRes] = await Promise.all([
      axios.get(`/api/v1/vk-contests/${statsContestId.value}/actions`),
      axios.get(`/api/v1/vk-contests/${statsContestId.value}/players`),
      axios.get(`/api/v1/vk-contests/${statsContestId.value}/winners`)
    ])
    statsActions.value = actRes.data
    statsPlayers.value = plyRes.data
    statsWinners.value = winRes.data
  } catch (err) {
    console.error(err)
    toast.error('Не удалось загрузить данные статистики')
  } finally {
    loadingStats.value = false
  }
}

watch(statsContestId, () => {
  loadStatsData()
})

const getGameTypeLabel = (type) => {
  const labels = {
    roulette: "🎰 Рулетка",
    safe: "🔒 Сейф",
    knb: "✊ Камень-ножницы-бумага",
    chests: "📦 Сундуки (4x4)",
    seabattle: "⚓ Морской бой (10x10)",
    battle: "🏖️ Битва за поле (10x10)"
  }
  return labels[type] || type
}

// --- Бот активности ВК ---
const currentActivitySettings = ref(null)
const showActivitySettingsDialog = ref(false)
const savingActivity = ref(false)
const loadingActivity = ref(false)
const resettingActivity = ref(false)
const syncingIiko = ref(false)
const activityRanking = ref([])
const ratingSearch = ref('')
const activeActivityTab = ref('settings')

const showUserHistoryDialog = ref(false)
const selectedUserForHistory = ref(null)
const userHistoryData = ref(null)
const loadingUserHistory = ref(false)

const activityForm = ref({
  id: null,
  vk_bot_connection_id: null,
  is_active: true,
  points_like: 5,
  points_like_first_n: 10,
  like_first_n_count: 5,
  points_like_fast: 8,
  like_fast_seconds: 900,
  points_comment: 10,
  points_comment_first_n: 15,
  comment_first_n_count: 5,
  points_comment_fast: 12,
  comment_fast_seconds: 900,
  min_comment_length: 5,
  max_comments_per_post: 3,
  ignore_consecutive_comments: true,
  ignore_stickers: true,
  points_repost: 20,
  points_poll: 5,
  points_join: 50,
  period_start_date: null,
  period_duration_days: 7,
  ignored_post_ids: "",
  post_max_age_days: 7,
  override_keywords: "",
  penalty_duration_seconds: 3600,
  penalty_points: 0,
  msg_penalty: "",
  msg_points_like: "",
  msg_points_comment: "",
  msg_points_repost: "",
  msg_points_poll: "",
  msg_points_join: "",
  msg_balance_info: "",
  msg_unlinked_notice: "",
  sync_with_iiko: false,
  iiko_conversion_rate: 1.0,
  iiko_sync_mode: "realtime",
  iiko_summing_logic: "both",
  sync_on_verification: true,
  sync_on_balance_request: true,
  last_sync_at: null,
  vk_bot_token: ""
})

async function loadActivitySettingsOnly(connectionId) {
  try {
    const res = await axios.get(`/api/v1/vk-activity-settings/connection/${connectionId}`)
    currentActivitySettings.value = res.data
  } catch (err) {
    console.error(err)
    currentActivitySettings.value = null
  }
}

const openActivitySettings = async () => {
  if (!selectedConnectionId.value) {
    toast.warning('Выберите сообщество ВКонтакте!')
    return
  }
  showActivitySettingsDialog.value = true
  activeActivityTab.value = 'settings'
  await loadActivitySettings()
  await loadActivityRanking()
}

const loadActivitySettings = async () => {
  loadingActivity.value = true
  try {
    const res = await axios.get(`/api/v1/vk-activity-settings/connection/${selectedConnectionId.value}`)
    if (res.data && res.data.id) {
      activityForm.value = { 
        ...res.data,
        vk_bot_token: res.data.vk_bot_token || ""
      }
      if (activityForm.value.period_start_date) {
        activityForm.value.period_start_date = activityForm.value.period_start_date.slice(0, 16)
      }
    } else {
      activityForm.value = {
        id: null,
        vk_bot_connection_id: selectedConnectionId.value,
        is_active: true,
        points_like: 5,
        points_like_first_n: 10,
        like_first_n_count: 5,
        points_like_fast: 8,
        like_fast_seconds: 900,
        points_comment: 10,
        points_comment_first_n: 15,
        comment_first_n_count: 5,
        points_comment_fast: 12,
        comment_fast_seconds: 900,
        min_comment_length: 5,
        max_comments_per_post: 3,
        ignore_consecutive_comments: true,
        ignore_stickers: true,
        points_repost: 20,
        points_poll: 5,
        points_join: 50,
        penalty_duration_seconds: 3600,
        penalty_points: 0,
        msg_penalty: "",
        period_start_date: null,
        period_duration_days: 7,
        ignored_post_ids: "",
        sync_with_iiko: false,
        iiko_conversion_rate: 1.0,
        iiko_sync_mode: "realtime",
        iiko_summing_logic: "both",
        sync_on_verification: true,
        sync_on_balance_request: true,
        last_sync_at: null,
        vk_bot_token: ""
      }
    }
  } catch (err) {
    console.error(err)
    toast.error('Не удалось загрузить настройки активности')
  } finally {
    loadingActivity.value = false
  }
}

const loadActivityRanking = async () => {
  try {
    const res = await axios.get(`/api/v1/vk-activity-settings/connection/${selectedConnectionId.value}/ranking`)
    activityRanking.value = res.data
  } catch (err) {
    console.error(err)
    toast.error('Не удалось загрузить рейтинг участников')
  }
}

const saveActivitySettings = async () => {
  savingActivity.value = true
  try {
    const payload = { ...activityForm.value }
    if (payload.period_start_date) {
      payload.period_start_date = new Date(payload.period_start_date).toISOString()
    }
    const res = await axios.post('/api/v1/vk-activity-settings/', payload)
    activityForm.value = { ...res.data }
    if (activityForm.value.period_start_date) {
      activityForm.value.period_start_date = activityForm.value.period_start_date.slice(0, 16)
    }
    await loadActivitySettingsOnly(selectedConnectionId.value)
    toast.success('Настройки активности успешно сохранены!')
    showActivitySettingsDialog.value = false
  } catch (err) {
    console.error(err)
    toast.error('Не удалось сохранить настройки активности')
  } finally {
    savingActivity.value = false
  }
}

const resetActivity = async () => {
  if (!confirm('Вы действительно хотите обнулить все баллы активности пользователей этой группы и стереть историю? Это действие необратимо.')) {
    return
  }
  resettingActivity.value = true
  try {
    await axios.post(`/api/v1/vk-activity-settings/connection/${selectedConnectionId.value}/reset`)
    toast.success('Рейтинг активности успешно сброшен!')
    await loadActivityRanking()
    await loadActivitySettingsOnly(selectedConnectionId.value)
  } catch (err) {
    console.error(err)
    toast.error('Не удалось сбросить рейтинг активности')
  } finally {
    resettingActivity.value = false
  }
}

const syncActivityIiko = async () => {
  syncingIiko.value = true
  try {
    const res = await axios.post(`/api/v1/vk-activity-settings/connection/${selectedConnectionId.value}/sync-iiko`)
    toast.success(res.data.message || 'Синхронизация с iiko успешно завершена!')
    await loadActivitySettings()
  } catch (err) {
    console.error(err)
    toast.error(err.response?.data?.detail || 'Не удалось запустить синхронизацию с iiko')
  } finally {
    syncingIiko.value = false
  }
}

const adjustUserPoints = async (vk_id, points_delta) => {
  try {
    const res = await axios.post('/api/v1/vk-activity-settings/update-points', {
      vk_id,
      points_delta
    })
    toast.success(res.data.message)
    await loadActivityRanking()
  } catch (err) {
    console.error(err)
    toast.error('Не удалось изменить баланс пользователя')
  }
}

const syncUserPointsToIiko = async (vk_id) => {
  try {
    const res = await axios.post(`/api/v1/vk-activity-settings/users/${vk_id}/sync-iiko`)
    toast.success(res.data.message || 'Синхронизация баллов успешно выполнена!')
    await loadActivityRanking()
  } catch (err) {
    console.error(err)
    toast.error(err.response?.data?.detail || 'Не удалось синхронизировать баллы с iikoCard')
  }
}

const expandedItems = ref([])

const loadHistoryForExpandedRow = async (user) => {
  selectedUserForHistory.value = user
  loadingUserHistory.value = true
  userHistoryData.value = null
  try {
    const res = await axios.get(`/api/v1/vk-activity-settings/users/${user.vk_id}/history`)
    userHistoryData.value = res.data
  } catch (err) {
    console.error(err)
    toast.error('Не удалось загрузить историю')
  } finally {
    loadingUserHistory.value = false
  }
}

const transferUserPointsToIiko = async (vk_id) => {
  if (!confirm('Вы уверены, что хотите принудительно перевести все накопленные баллы активности ВК в бонусы iikoCard? Баланс ВК этого пользователя будет обнулен.')) {
    return
  }
  try {
    const res = await axios.post(`/api/v1/vk-activity-settings/users/${vk_id}/transfer-to-iiko`)
    toast.success(res.data.message || 'Перевод баллов в бонусы успешно завершен!')
    await loadActivityRanking()
  } catch (err) {
    console.error(err)
    toast.error(err.response?.data?.detail || 'Не удалось перевести баллы в бонусы')
  }
}

const openUserHistory = async (user) => {
  selectedUserForHistory.value = user
  showUserHistoryDialog.value = true
  loadingUserHistory.value = true
  userHistoryData.value = null
  try {
    const res = await axios.get(`/api/v1/vk-activity-settings/users/${user.vk_id}/history`)
    userHistoryData.value = res.data
  } catch (err) {
    console.error(err)
    toast.error('Не удалось загрузить историю начислений пользователя')
  } finally {
    loadingUserHistory.value = false
  }
}

const getActivityColor = (type) => {
  if (type === 'like_add') return 'primary'
  if (type === 'wall_reply_new') return 'info'
  if (type === 'wall_repost') return 'purple'
  if (type === 'manual_adjustment' || type === 'manual_adjust') return 'warning'
  return 'secondary'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getActivityBotStatus = () => {
  if (!selectedConnectionId.value) return { text: 'Недоступен', color: 'secondary' }
  if (!currentActivitySettings.value) return { text: 'Не настроен', color: 'warning' }
  return currentActivitySettings.value.is_active ? { text: 'Активен', color: 'success' } : { text: 'Отключен', color: 'error' }
}

// --- Бот первокоммент ---
async function loadFirstCommentSettingsOnly(connectionId) {
  try {
    const res = await axios.get(`/api/v1/vk-first-comment-settings/connection/${connectionId}`)
    currentFirstCommentSettings.value = res.data
  } catch (err) {
    console.error(err)
    currentFirstCommentSettings.value = null
  }
}

const getFirstCommentBotStatus = () => {
  if (!selectedConnectionId.value) return { text: 'Недоступен', color: 'secondary' }
  if (!currentFirstCommentSettings.value) return { text: 'Не настроен', color: 'warning' }
  return currentFirstCommentSettings.value.is_active ? { text: 'Активен', color: 'success' } : { text: 'Отключен', color: 'error' }
}

const openFirstCommentSettings = async () => {
  if (!selectedConnectionId.value) {
    toast.warning('Выберите сообщество ВКонтакте!')
    return
  }
  activeFirstCommentTab.value = 'general'
  showFirstCommentSettingsDialog.value = true
  loading.value = true
  try {
    const res = await axios.get(`/api/v1/vk-first-comment-settings/connection/${selectedConnectionId.value}`)
    if (res.data) {
      firstCommentForm.value = {
        id: res.data.id,
        vk_bot_connection_id: selectedConnectionId.value,
        is_active: res.data.is_active,
        comments: res.data.comments || [],
        post_type_filter: res.data.post_type_filter || 'all',
        include_keywords: res.data.include_keywords || '',
        exclude_keywords: res.data.exclude_keywords || '',
        delay_seconds: res.data.delay_seconds || 0,
        ignore_empty_text: res.data.ignore_empty_text || false,
        exclude_reposts: res.data.exclude_reposts || false,
        delay_min: res.data.delay_min || 0,
        delay_max: res.data.delay_max || 0
      }
      isRandomDelay.value = (res.data.delay_max > 0)
    } else {
      firstCommentForm.value = {
        id: null,
        vk_bot_connection_id: selectedConnectionId.value,
        is_active: false,
        comments: [],
        post_type_filter: 'all',
        include_keywords: '',
        exclude_keywords: '',
        delay_seconds: 0,
        ignore_empty_text: false,
        exclude_reposts: false,
        delay_min: 0,
        delay_max: 0
      }
      isRandomDelay.value = false
    }
  } catch (err) {
    console.error(err)
    toast.error('Не удалось загрузить настройки первокоммента')
  } finally {
    loading.value = false
  }
}

const saveFirstCommentSettings = async () => {
  savingFirstComment.value = true
  if (!isRandomDelay.value) {
    firstCommentForm.value.delay_min = 0
    firstCommentForm.value.delay_max = 0
  } else {
    firstCommentForm.value.delay_seconds = 0
  }
  try {
    const res = await axios.post('/api/v1/vk-first-comment-settings/', firstCommentForm.value)
    currentFirstCommentSettings.value = res.data
    toast.success('Настройки автокомментатора успешно сохранены!')
    showFirstCommentSettingsDialog.value = false
  } catch (err) {
    console.error(err)
    toast.error(err.response?.data?.detail || 'Не удалось сохранить настройки автокомментатора')
  } finally {
    savingFirstComment.value = false
  }
}

const addCommentToForm = () => {
  if (!newCommentText.value.trim()) return
  if (firstCommentForm.value.comments.length >= 15) {
    toast.warning('Максимальное количество вариантов комментариев - 15')
    return
  }
  firstCommentForm.value.comments.push(newCommentText.value.trim())
  newCommentText.value = ""
}

const removeCommentFromForm = (index) => {
  firstCommentForm.value.comments.splice(index, 1)
}

const commonEmojis = ['🍕', '🍱', '🍣', '🍥', '🥘', '🍜', '🍤', '❤️', '😍', '👍', '🔥', '🎉', '😉', '🚀', '✨', '🎁', '💬', '📢', '🔔', '✅', '💥', '🍔', '🍟', '🥤']

const insertEmoji = (emoji) => {
  newCommentText.value += emoji
}

const getVkTokenUrl = () => {
  const conn = connections.value.find(c => c.id === selectedConnectionId.value)
  if (!conn || !conn.vk_group_id) return 'https://vk.com/groups?tab=admin'
  return `https://vk.com/club${conn.vk_group_id}?act=api`
}


// ----------------- СОСТОЯНИЯ НОВЫХ МАРКЕТИНГОВЫХ БОТОВ -----------------
const showMarketingModal = ref(false)
const selectedMarketingBotType = ref('shop')
const marketingBotsConfig = ref({})

const loadMarketingBotsConfig = async (connectionId) => {
  if (!connectionId) return
  try {
    const res = await axios.get(`/api/v1/vk/marketing-bots/config/${connectionId}`)
    marketingBotsConfig.value = res.data || {}
  } catch (e) {
    console.error('Ошибка загрузки статусов маркетинговых ботов:', e)
  }
}

const getMarketingBotStatus = (botKey) => {
  if (!selectedConnectionId.value) return { text: 'Недоступен', color: 'secondary' }
  const bot = marketingBotsConfig.value?.[botKey]
  if (!bot) return { text: 'Загрузка...', color: 'secondary' }
  return bot.is_active ? { text: 'Активен', color: 'success' } : { text: 'Отключен', color: 'secondary' }
}

const openNewBotSettings = (botKey) => {
  selectedMarketingBotType.value = botKey
  showMarketingModal.value = true
}

const onMarketingBotSaved = async (savedData) => {
  const botKey = typeof savedData === 'object' ? savedData.botType : savedData
  const savedCfg = typeof savedData === 'object' ? savedData.config : null

  if (botKey && savedCfg) {
    marketingBotsConfig.value = {
      ...marketingBotsConfig.value,
      [botKey]: {
        ...(marketingBotsConfig.value[botKey] || {}),
        ...savedCfg
      }
    }
  }

  if (selectedConnectionId.value) {
    await loadMarketingBotsConfig(selectedConnectionId.value)
  }
}
</script>

<template>
  <div>
    <div class="d-flex align-center justify-space-between mb-6">
      <div>
        <h2 class="text-h4 mb-1">Боты ВКонтакте</h2>
        <p class="text-subtitle-1 text-muted mb-0">Каталог умных ботов для автоматизации работы в группах ВК</p>
      </div>
    </div>

    <!-- Панель выбора сообщества ВК -->
    <VCard class="mb-6">
      <VCardText class="d-flex align-center py-4">
        <div class="me-4 d-none d-sm-block">
          <VIcon icon="ri-community-line" size="28" color="primary" />
        </div>
        <div style="flex-grow: 1; max-width: 400px;">
          <VSelect
            v-model="selectedConnectionId"
            :connections="connections"
            :items="connections"
            item-title="name"
            item-value="id"
            label="Активное сообщество ВК"
            variant="outlined"
            density="compact"
            hide-details
            :loading="loading"
            no-data-text="Нет подключенных групп ВК"
          >
            <template #item="{ props, item }">
              <VListItem v-bind="props" :subtitle="`ID: ${item.raw.vk_group_id}`" />
            </template>
          </VSelect>
        </div>
        <div class="ms-4 text-caption text-muted d-none d-md-block" v-if="selectedConnectionId">
          Все настройки ниже применяются индивидуально для выбранного сообщества.
        </div>

        <div class="ms-auto d-none d-sm-flex align-center gap-2" v-if="selectedConnectionId">
          <VChip
            v-if="marketingBotsConfig?.max_bridge_status?.connected"
            color="success"
            variant="tonal"
            size="small"
            class="font-weight-medium"
          >
            <VIcon start icon="ri-chat-voice-line" size="14" />
            MAX (Личный №): {{ marketingBotsConfig.max_bridge_status.user_phone }}
          </VChip>
          <VChip
            v-else
            color="warning"
            variant="tonal"
            size="small"
            class="font-weight-medium"
          >
            <VIcon start icon="ri-error-warning-line" size="14" />
            MAX (Личный №): Web Bridge отключен
          </VChip>
        </div>
      </VCardText>
    </VCard>

    <!-- Сетка плашек (Каталог Ботов) -->
    <VRow v-if="selectedConnectionId">
      
      <!-- Плашка: Отложенный постинг (АКТИВНЫЙ) -->
      <VCol cols="12" sm="6" md="4">
        <VCard 
          class="bot-card h-100 d-flex flex-column clickable-card"
          hover
          to="/marketing/vk-scheduler"
        >
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-warning-lighten rounded pa-3">
                <VIcon icon="ri-calendar-todo-line" size="32" color="warning" />
              </div>
              <VChip
                size="small"
                color="success"
                variant="tonal"
                class="font-weight-bold"
              >
                Доступно
              </VChip>
            </div>

            <h3 class="text-h6 font-weight-bold mb-2">Отложенный постинг</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Планируйте публикации постов и историй с умным Canvas-редактором изображений, наложением текста, стикеров, ссылок и кнопок действий.
            </p>

            <VDivider class="mb-4" />

            <div class="d-flex align-center justify-space-between text-caption text-warning font-weight-bold mt-auto">
              <span>Открыть планировщик</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- Плашка: Бот Дней Рождения (АКТИВНЫЙ) -->
      <VCol cols="12" sm="6" md="4">
        <VCard 
          class="bot-card h-100 d-flex flex-column clickable-card"
          hover
          @click="openBirthdaySettings"
        >
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-primary-lighten rounded pa-3">
                <VIcon icon="ri-cake-2-line" size="32" color="primary" />
              </div>
              <VChip
                size="small"
                :color="getBirthdayBotStatus().color"
                variant="tonal"
                class="font-weight-bold"
              >
                {{ getBirthdayBotStatus().text }}
              </VChip>
            </div>

            <h3 class="text-h6 font-weight-bold mb-2">Бот Дней Рождения</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Отслеживает именинников среди подписчиков группы. Публикует поздравления на стене с красивой открыткой и автоматически удаляет посты по расписанию.
            </p>

            <VDivider class="mb-4" />

            <div class="d-flex align-center justify-space-between text-caption text-primary font-weight-bold mt-auto">
              <span>Открыть настройки</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- Плашка: Конструктор динамических обложек (АКТИВНЫЙ) -->
      <VCol cols="12" sm="6" md="4">
        <VCard 
          class="bot-card h-100 d-flex flex-column clickable-card"
          hover
          @click="openCoverSettings"
        >
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-success-lighten rounded pa-3">
                <VIcon icon="ri-image-edit-line" size="32" color="success" />
              </div>
              <VChip
                size="small"
                :color="getCoverBotStatus().color"
                variant="tonal"
                class="font-weight-bold"
              >
                {{ getCoverBotStatus().text }}
              </VChip>
            </div>

            <h3 class="text-h6 font-weight-bold mb-2">Динамическая обложка</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Создавайте обложку сообщества со встроенным визуальным редактором. Выводите время, погоду, таймеры акций и топ-активных подписчиков (лайки/комменты).
            </p>

            <VDivider class="mb-4" />

            <div class="d-flex align-center justify-space-between text-caption text-success font-weight-bold mt-auto">
              <span>Открыть конструктор</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- Плашка: Бот Конкурсов и Геймификации (АКТИВНЫЙ) -->
      <VCol cols="12" sm="6" md="4">
        <VCard 
          class="bot-card h-100 d-flex flex-column clickable-card"
          hover
          @click="openContests"
        >
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-warning-lighten rounded pa-3">
                <VIcon icon="ri-trophy-line" size="32" color="warning" />
              </div>
              <VChip
                size="small"
                color="warning"
                variant="tonal"
                class="font-weight-bold"
              >
                Настроить
              </VChip>
            </div>

            <h3 class="text-h6 font-weight-bold mb-2">Конкурсы и Геймификация</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Проводите игры (Рулетка, Сейф, КНБ, Сундуки, Морской бой) прямо в комментариях на стене. Бот автоматически отвечает, считает попытки и выдает промокоды в ЛС!
            </p>

            <VDivider class="mb-4" />

            <div class="d-flex align-center justify-space-between text-caption text-warning font-weight-bold mt-auto">
              <span>Запустить конкурс</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- Плашка: Рейтинг активности (АКТИВНЫЙ) -->
      <VCol cols="12" sm="6" md="4">
        <VCard 
          class="bot-card h-100 d-flex flex-column clickable-card"
          hover
          @click="openActivitySettings"
        >
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-info-lighten rounded pa-3">
                <VIcon icon="ri-radar-line" size="32" color="info" />
              </div>
              <VChip
                size="small"
                :color="getActivityBotStatus().color"
                variant="tonal"
                class="font-weight-bold"
              >
                {{ getActivityBotStatus().text }}
              </VChip>
            </div>

            <h3 class="text-h6 font-weight-bold mb-2">Рейтинг активности</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Начисляйте подписчикам баллы за лайки, комментарии, репосты, участие в опросах и вступление. Интегрировано с iikoCard для траты баллов.
            </p>

            <VDivider class="mb-4" />

            <div class="d-flex align-center justify-space-between text-caption text-info font-weight-bold mt-auto">
              <span>Открыть настройки рейтинга</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- Плашка: Бот первокоммент (АКТИВНЫЙ) -->
      <VCol cols="12" sm="6" md="4">
        <VCard 
          class="bot-card h-100 d-flex flex-column clickable-card"
          hover
          @click="openFirstCommentSettings"
        >
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-primary-lighten rounded pa-3">
                <VIcon icon="ri-chat-new-line" size="32" color="primary" />
              </div>
              <VChip
                size="small"
                :color="getFirstCommentBotStatus().color"
                variant="tonal"
                class="font-weight-bold"
              >
                {{ getFirstCommentBotStatus().text }}
              </VChip>
            </div>

            <h3 class="text-h6 font-weight-bold mb-2">Бот первокоммент</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Оставляет первый комментарий к новым постам в автоматическом режиме от имени сообщества. Поддерживает до 15 вариантов комментариев в случайном порядке.
            </p>

            <VDivider class="mb-4" />

            <div class="d-flex align-center justify-space-between text-caption text-primary font-weight-bold mt-auto">
              <span>Открыть настройки автокомментатора</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- РАЗДЕЛ: НОВЫЕ МАРКЕТИНГОВЫЕ БОТЫ -->
      <VCol cols="12" class="mt-4">
        <div class="d-flex align-center gap-2">
          <VIcon icon="ri-rocket-2-line" color="primary" size="24" />
          <h3 class="text-h5 font-weight-bold">Новые Маркетинговые и Продающие Боты</h3>
          <VChip size="small" color="primary" class="font-weight-bold">6 ботов</VChip>
        </div>
        <p class="text-caption text-muted mb-0">Интеграция с iiko, возврат спящих клиентов, геймификация и автоматизация продаж в ВК</p>
      </VCol>

      <!-- 1. Интерактивный Каталог и Повтор Заказа (VkShopBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" :class="{ 'disabled-card': marketingBotsConfig?.shop && !marketingBotsConfig.shop.is_active }" hover @click="openNewBotSettings('shop')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-primary-lighten rounded pa-3">
                <VIcon icon="ri-shopping-bag-3-line" size="32" color="primary" />
              </div>
              <div class="d-flex flex-column align-end gap-1">
                <div class="d-flex gap-1">
                  <VChip size="x-small" :color="(marketingBotsConfig?.shop?.vk_enabled ?? true) ? 'primary' : 'secondary'" variant="flat">
                    ВК {{ (marketingBotsConfig?.shop?.vk_enabled ?? true) ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                  <VChip size="x-small" :color="marketingBotsConfig?.shop?.max_enabled ? 'success' : 'secondary'" variant="flat">
                    MAX {{ marketingBotsConfig?.shop?.max_enabled ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                </div>
                <VChip size="x-small" :color="getMarketingBotStatus('shop').color" variant="tonal" class="font-weight-bold">
                  {{ getMarketingBotStatus('shop').text }}
                </VChip>
              </div>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Каталог и Повтор Заказа</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Витрина хитов в ЛС, статус доставки онлайн («Где мой заказ?») и повтор прошлого заказа из iiko в 1 клик.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-primary font-weight-bold mt-auto">
              <span>Настроить витрину</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 2. Триггерная Реактивация (VkRetentionBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" :class="{ 'disabled-card': marketingBotsConfig?.retention && !marketingBotsConfig.retention.is_active }" hover @click="openNewBotSettings('retention')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-success-lighten rounded pa-3">
                <VIcon icon="ri-user-heart-line" size="32" color="success" />
              </div>
              <div class="d-flex flex-column align-end gap-1">
                <div class="d-flex gap-1">
                  <VChip size="x-small" :color="(marketingBotsConfig?.retention?.vk_enabled ?? true) ? 'primary' : 'secondary'" variant="flat">
                    ВК {{ (marketingBotsConfig?.retention?.vk_enabled ?? true) ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                  <VChip size="x-small" :color="marketingBotsConfig?.retention?.max_enabled ? 'success' : 'secondary'" variant="flat">
                    MAX {{ marketingBotsConfig?.retention?.max_enabled ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                </div>
                <VChip size="x-small" :color="getMarketingBotStatus('retention').color" variant="tonal" class="font-weight-bold">
                  {{ getMarketingBotStatus('retention').text }}
                </VChip>
              </div>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Реактивация Гостей (RFM)</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Возврат клиентов через 7, 21 и 45 дней. Механика «Бонусный будильник» (сгораемые баллы в iiko).
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-success font-weight-bold mt-auto">
              <span>Цепочки реактивации</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 3. NPS и Фото-Отзывы (VkReviewNpsBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" :class="{ 'disabled-card': marketingBotsConfig?.nps && !marketingBotsConfig.nps.is_active }" hover @click="openNewBotSettings('nps')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-warning-lighten rounded pa-3">
                <VIcon icon="ri-star-smile-line" size="32" color="warning" />
              </div>
              <div class="d-flex flex-column align-end gap-1">
                <div class="d-flex gap-1">
                  <VChip size="x-small" :color="(marketingBotsConfig?.nps?.vk_enabled ?? true) ? 'primary' : 'secondary'" variant="flat">
                    ВК {{ (marketingBotsConfig?.nps?.vk_enabled ?? true) ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                  <VChip size="x-small" :color="marketingBotsConfig?.nps?.max_enabled ? 'success' : 'secondary'" variant="flat">
                    MAX {{ marketingBotsConfig?.nps?.max_enabled ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                </div>
                <VChip size="x-small" :color="getMarketingBotStatus('nps').color" variant="tonal" class="font-weight-bold">
                  {{ getMarketingBotStatus('nps').text }}
                </VChip>
              </div>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">NPS и Фото-Отзывы</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Запрос оценки через 45 мин после доставки. Перехват негатива в Мультичат и авто-бонусы за фото блюд на стене.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-warning font-weight-bold mt-auto">
              <span>Параметры NPS</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 4. Колесо Фортуны (VkWheelOfFortuneBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" :class="{ 'disabled-card': marketingBotsConfig?.wheel && !marketingBotsConfig.wheel.is_active }" hover @click="openNewBotSettings('wheel')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-error-lighten rounded pa-3">
                <VIcon icon="ri-pie-chart-2-line" size="32" color="error" />
              </div>
              <div class="d-flex flex-column align-end gap-1">
                <div class="d-flex gap-1">
                  <VChip size="x-small" :color="(marketingBotsConfig?.wheel?.vk_enabled ?? true) ? 'primary' : 'secondary'" variant="flat">
                    ВК {{ (marketingBotsConfig?.wheel?.vk_enabled ?? true) ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                  <VChip size="x-small" :color="marketingBotsConfig?.wheel?.max_enabled ? 'success' : 'secondary'" variant="flat">
                    MAX {{ marketingBotsConfig?.wheel?.max_enabled ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                </div>
                <VChip size="x-small" :color="getMarketingBotStatus('wheel').color" variant="tonal" class="font-weight-bold">
                  {{ getMarketingBotStatus('wheel').text }}
                </VChip>
              </div>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Колесо Фортуны</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Взрывной рост комментариев (рулетка), выдача секретных промокодов на 48 часов и спины за заказы доставки.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-error font-weight-bold mt-auto">
              <span>Сектора и вероятности</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 5. Рассылки и Счастливые Часы (VkSmartBroadcastBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" :class="{ 'disabled-card': marketingBotsConfig?.broadcast && !marketingBotsConfig.broadcast.is_active }" hover @click="openNewBotSettings('broadcast')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-info-lighten rounded pa-3">
                <VIcon icon="ri-broadcast-line" size="32" color="info" />
              </div>
              <div class="d-flex flex-column align-end gap-1">
                <div class="d-flex gap-1">
                  <VChip size="x-small" :color="(marketingBotsConfig?.broadcast?.vk_enabled ?? true) ? 'primary' : 'secondary'" variant="flat">
                    ВК {{ (marketingBotsConfig?.broadcast?.vk_enabled ?? true) ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                  <VChip size="x-small" :color="marketingBotsConfig?.broadcast?.max_enabled ? 'success' : 'secondary'" variant="flat">
                    MAX {{ marketingBotsConfig?.broadcast?.max_enabled ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                </div>
                <VChip size="x-small" :color="getMarketingBotStatus('broadcast').color" variant="tonal" class="font-weight-bold">
                  {{ getMarketingBotStatus('broadcast').text }}
                </VChip>
              </div>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Рассылки и Счастливые Часы</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Таргетированные рассылки по сегментам и авто-дозагрузка кухни в будни 14:00-16:00 при падении числа заказов.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-info font-weight-bold mt-auto">
              <span>Сегменты и триггеры</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>

      <!-- 6. Реферальный Бот (VkReferralBot) -->
      <VCol cols="12" sm="6" md="4">
        <VCard class="bot-card h-100 d-flex flex-column clickable-card" :class="{ 'disabled-card': marketingBotsConfig?.referral && !marketingBotsConfig.referral.is_active }" hover @click="openNewBotSettings('referral')">
          <div class="pa-5 d-flex flex-column h-100">
            <div class="d-flex align-center justify-space-between mb-4">
              <div class="bot-icon-wrapper bg-purple-lighten rounded pa-3">
                <VIcon icon="ri-gift-line" size="32" color="purple" />
              </div>
              <div class="d-flex flex-column align-end gap-1">
                <div class="d-flex gap-1">
                  <VChip size="x-small" :color="(marketingBotsConfig?.referral?.vk_enabled ?? true) ? 'primary' : 'secondary'" variant="flat">
                    ВК {{ (marketingBotsConfig?.referral?.vk_enabled ?? true) ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                  <VChip size="x-small" :color="marketingBotsConfig?.referral?.max_enabled ? 'success' : 'secondary'" variant="flat">
                    MAX {{ marketingBotsConfig?.referral?.max_enabled ? 'ВКЛ' : 'ВЫКЛ' }}
                  </VChip>
                </div>
                <VChip size="x-small" :color="getMarketingBotStatus('referral').color" variant="tonal" class="font-weight-bold">
                  {{ getMarketingBotStatus('referral').text }}
                </VChip>
              </div>
            </div>
            <h3 class="text-h6 font-weight-bold mb-2">Реферальный «Приведи Друга»</h3>
            <p class="text-body-2 text-muted flex-grow-1 mb-4">
              Персональные промокоды, приветственный бонус новому гостю и выплата баллов только после закрытого заказа.
            </p>
            <VDivider class="mb-4" />
            <div class="d-flex align-center justify-space-between text-caption text-purple font-weight-bold mt-auto">
              <span>Реферальная программа</span>
              <VIcon icon="ri-arrow-right-line" size="18" />
            </div>
          </div>
        </VCard>
      </VCol>


    </VRow>

    <VRow v-else>
      <VCol cols="12" class="text-center py-12">
        <VIcon icon="ri-robot-2-line" size="64" color="secondary" class="mb-4" />
        <h3 class="text-h6">Выберите сообщество ВКонтакте</h3>
        <p class="text-body-2 text-muted">Для вывода доступных ботов необходимо выбрать подключенную группу ВК сверху</p>
      </VCol>
    </VRow>

    <!-- МОДАЛЬНОЕ ОКНО НАСТРОЕК БОТА ДНЕЙ РОЖДЕНИЯ -->
    <VDialog v-model="showBirthdaySettingsDialog" max-width="850px" scrollable persistent>
      <VCard class="rounded-xl">
        <VCardTitle class="d-flex align-center justify-space-between pa-5 bg-surface border-b">
          <div class="d-flex align-center">
            <div class="bg-primary-lighten rounded-lg pa-2 me-3">
              <VIcon icon="ri-cake-2-line" color="primary" size="24" />
            </div>
            <div>
              <span class="text-h6 font-weight-bold d-block">Настройки бота: Дни рождения</span>
              <span class="text-caption text-muted">Для сообщества: {{ connections.find(c => c.id === selectedConnectionId)?.name }}</span>
            </div>
          </div>
          <VBtn icon="ri-close-line" variant="text" color="secondary" density="comfortable" @click="showBirthdaySettingsDialog = false" />
        </VCardTitle>

        <VCardText class="pa-6" style="max-height: 70vh;">
          <div class="d-flex align-center justify-space-between mb-6 bg-light rounded-xl pa-4">
            <div>
              <span class="text-subtitle-1 font-weight-bold d-block">Статус автопубликации</span>
              <span class="text-caption text-muted">Включите для автоматического постинга поздравлений на стене</span>
            </div>
            <VSwitch v-model="birthdayForm.is_active" color="success" hide-details />
          </div>

          <!-- Поле индивидуального API-ключа -->
          <div class="mb-6 bg-light rounded-xl pa-4">
            <span class="font-weight-bold d-block mb-1">Индивидуальный ключ доступа сообщества</span>
            <span class="text-caption text-muted d-block mb-3">
              Позволяет использовать отдельный токен для работы этого конкретного бота. Если поле пустое, будет использоваться токен основного подключения.
              <a :href="getVkTokenUrl()" target="_blank" class="text-primary font-weight-bold text-decoration-none d-inline-block ms-1">Получить токен сообщества автоматически ↗</a>
            </span>
            <VTextField
              v-model="birthdayForm.vk_bot_token"
              label="API-ключ сообщества ВК (Токен)"
              placeholder="Вставьте токен vk1.a.***"
              variant="outlined"
              density="comfortable"
              hide-details
              type="password"
            />
          </div>

          <VDivider class="mb-6" />

          <VRow>
            <VCol cols="12">
              <VTextarea v-model="birthdayForm.message_template" label="Шаблон поздравительного поста" variant="outlined" rows="4" hint="Используйте тег {names}." />
            </VCol>
            <VCol cols="12" sm="6" class="py-1">
              <VCheckbox v-model="birthdayForm.include_names" label="Указывать имена именинников" color="primary" hide-details />
            </VCol>
            <VCol cols="12" sm="6" class="py-1">
              <VCheckbox v-model="birthdayForm.make_links" :disabled="!birthdayForm.include_names" label="Имена ссылками на профили ВК" color="primary" hide-details />
            </VCol>
            <VCol cols="12" class="pt-0">
              <VRadioGroup v-model="birthdayForm.name_format" :disabled="!birthdayForm.include_names" inline label="Формат отображения имен">
                <VRadio label="Имя Фамилия (как в ВК)" value="fullname" color="primary" class="me-4" />
                <VRadio label="Только Имя" value="name_only" color="primary" />
              </VRadioGroup>
            </VCol>
            <VDivider class="my-4 mx-3" />
            <VCol cols="12" sm="6">
              <VTextField v-model="birthdayForm.publish_time" label="Время публикации поздравления" variant="outlined" type="time" />
            </VCol>
            <VCol cols="12" sm="6">
              <div class="d-flex align-center flex-column border rounded-xl pa-4 justify-center" style="height: 100%; min-height: 120px;">
                <span class="text-caption text-muted mb-2 font-weight-bold">Поздравительное изображение</span>
                <div v-if="birthdayForm.image_url" class="position-relative mb-1">
                  <VImg :src="birthdayForm.image_url" height="80" width="120" cover class="rounded-lg" />
                  <VBtn icon="ri-close-circle-fill" size="x-small" color="error" variant="text" class="position-absolute" style="top: -10px; right: -10px" @click="birthdayForm.image_url = null" />
                </div>
                <div v-else class="d-flex align-center flex-column">
                  <input type="file" id="birthday-upload-file" style="display: none" accept="image/*" @change="onBirthdayImageSelected" />
                  <VBtn color="primary" variant="tonal" size="small" prepend-icon="ri-image-add-line" :loading="imageBirthdayUploading" onclick="document.getElementById('birthday-upload-file').click()">
                    Загрузить картинку
                  </VBtn>
                </div>
              </div>
            </VCol>
            <VDivider class="my-4 mx-3" />
            <VCol cols="12">
              <span class="text-subtitle-2 text-muted mb-3 d-block font-weight-bold">Автоудаление опубликованного поздравления</span>
              <VRadioGroup v-model="birthdayForm.delete_mode" inline class="mb-2">
                <VRadio label="Через определенный интервал времени" value="interval" color="primary" class="me-4" />
                <VRadio label="В точное время суток" value="exact_time" color="primary" />
              </VRadioGroup>
            </VCol>
            <VCol v-if="birthdayForm.delete_mode === 'interval'" cols="12" sm="6">
              <VTextField v-model.number="birthdayForm.delete_interval_minutes" label="Интервал до удаления (в минутах)" variant="outlined" type="number" suffix="мин" />
            </VCol>
            <VCol v-if="birthdayForm.delete_mode === 'exact_time'" cols="12" sm="6">
              <VTextField v-model="birthdayForm.delete_time" label="Время удаления поздравления" variant="outlined" type="time" />
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-5 bg-surface border-t d-flex justify-between">
          <VBtn v-if="birthdayForm.id" color="warning" variant="tonal" prepend-icon="ri-play-line" :loading="testingBirthday" @click="testBirthdayPublish">
            Тест (Запустить сейчас)
          </VBtn>
          <div class="ms-auto">
            <VBtn color="secondary" variant="outlined" class="me-2" @click="showBirthdaySettingsDialog = false">Отмена</VBtn>
            <VBtn color="success" prepend-icon="ri-save-3-line" :loading="savingBirthday" @click="saveBirthdaySettings">Сохранить</VBtn>
          </div>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО КОНСТРУКТОРА ДИНАМИЧЕСКИХ ОБЛОЖЕК ВК -->
    <VDialog v-model="showCoverSettingsDialog" max-width="1200px" scrollable persistent>
      <VCard class="rounded-xl">
        <VCardTitle class="d-flex align-center justify-space-between pa-5 bg-surface border-b">
          <div class="d-flex align-center">
            <div class="bg-success-lighten rounded-lg pa-2 me-3">
              <VIcon icon="ri-image-edit-line" color="success" size="24" />
            </div>
            <div>
              <span class="text-h6 font-weight-bold d-block">Конструктор динамической обложки</span>
              <span class="text-caption text-muted">Размер холста: 1590 x 530 px • Сообщество: {{ connections.find(c => c.id === selectedConnectionId)?.name }}</span>
            </div>
          </div>
          <VBtn icon="ri-close-line" variant="text" color="secondary" density="comfortable" @click="showCoverSettingsDialog = false" />
        </VCardTitle>

        <VCardText class="pa-6" style="max-height: 80vh;">
          <VRow>
            <VCol cols="12" lg="8">
              <VRow class="mb-2">
                <VCol cols="12" md="6">
                  <VTextField
                    v-model="coverForm.name"
                    label="Название обложки"
                    placeholder="например, Дневная обложка"
                    density="comfortable"
                    variant="outlined"
                    hide-details
                    class="mb-3"
                  />
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect
                    v-model="coverForm.schedule_type"
                    label="Режим активности / Ротации"
                    :items="[
                      { title: '🟢 Всегда активна', value: 'always' },
                      { title: '⏰ По расписанию часов (HH:MM)', value: 'time_range' },
                      { title: '🔄 Циклическая очередь', value: 'interval' }
                    ]"
                    density="comfortable"
                    variant="outlined"
                    hide-details
                    class="mb-3"
                  />
                </VCol>
                <template v-if="coverForm.schedule_type === 'time_range'">
                  <VCol cols="6">
                    <VTextField
                      v-model="coverForm.schedule_start_time"
                      label="Время начала работы (HH:MM)"
                      type="time"
                      density="comfortable"
                      variant="outlined"
                      hide-details
                      class="mb-3"
                    />
                  </VCol>
                  <VCol cols="6">
                    <VTextField
                      v-model="coverForm.schedule_end_time"
                      label="Время окончания работы (HH:MM)"
                      type="time"
                      density="comfortable"
                      variant="outlined"
                      hide-details
                      class="mb-3"
                    />
                  </VCol>
                </template>
                <VCol cols="12">
                  <!-- Поле индивидуального API-ключа -->
                  <div class="mb-4 bg-light rounded-xl pa-4 border">
                    <span class="font-weight-bold d-block mb-1">Индивидуальный ключ доступа сообщества</span>
                    <span class="text-caption text-muted d-block mb-3">
                      Позволяет использовать отдельный токен для работы этого конкретного бота. Если поле пустое, будет использоваться токен основного подключения.
                      <a :href="getVkTokenUrl()" target="_blank" class="text-primary font-weight-bold text-decoration-none d-inline-block ms-1">Получить токен сообщества автоматически ↗</a>
                    </span>
                    <VTextField
                      v-model="coverForm.vk_bot_token"
                      label="API-ключ сообщества ВК (Токен)"
                      placeholder="Вставьте токен vk1.a.***"
                      variant="outlined"
                      density="comfortable"
                      hide-details
                      type="password"
                    />
                  </div>
                </VCol>
                <VCol cols="12" md="6">
                  <div class="d-flex align-center justify-space-between bg-light rounded-lg pa-3 h-100">
                    <div>
                      <span class="text-body-1 font-weight-bold d-block">Активность динамической обложки</span>
                      <span class="text-caption text-muted">Включите для применения и обновления обложки</span>
                    </div>
                    <VSwitch v-model="coverForm.is_active" color="success" hide-details />
                  </div>
                </VCol>
                <VCol cols="12" md="6">
                  <VSelect
                    v-model="coverForm.update_interval"
                    :items="[
                      { title: 'Каждую минуту', value: '1m' },
                      { title: 'Каждые 2 минуты', value: '2m' },
                      { title: 'Каждые 3 минуты', value: '3m' },
                      { title: 'Каждые 5 минут', value: '5m' },
                      { title: 'Каждые 15 минут', value: '15m' },
                      { title: 'Каждые 30 минут', value: '30m' },
                      { title: 'Каждый час', value: '1h' },
                      { title: 'Каждые 6 часов', value: '6h' },
                      { title: 'Каждые 12 часов', value: '12h' },
                      { title: 'Утром (с 0:00 до 11:00 МСК)', value: 'morning' },
                      { title: 'В обеденное/дневное время (с 11:00 до 16:00 МСК)', value: 'day' },
                      { title: 'Вечером (с 16:00 до 23:59 МСК)', value: 'evening' },
                      { title: 'Обновлять по событиям Callback API ВК', value: 'callback' }
                    ]"
                    label="Периодичность обновления"
                    density="comfortable"
                    variant="outlined"
                    hide-details
                  />
                </VCol>
              </VRow>
              
              <!-- НАСТРОЙКИ CUSTOM CALLBACK API -->
              <VCard variant="outlined" class="mb-4 pa-4 rounded-xl border-dashed">
                <div class="d-flex align-center justify-space-between mb-2">
                  <div>
                    <span class="font-weight-bold text-body-1 d-block">Отдельный Callback API для обложки</span>
                    <span class="text-caption text-muted">Используйте для отправки событий активности ВК на выделенный вебхук</span>
                  </div>
                  <VSwitch v-model="coverForm.use_custom_callback" color="primary" hide-details />
                </div>
                
                <VExpandTransition>
                  <div v-if="coverForm.use_custom_callback">
                    <VRow density="compact" class="mt-2">
                      <VCol cols="12">
                        <VTextField
                          :model-value="coverForm.id ? `${window.location.origin}/api/v1/vk-covers/webhook/${coverForm.id}` : 'Сохраните обложку, чтобы получить адрес вебхука'"
                          label="Адрес Callback API Webhook (укажите в настройках ВК)"
                          readonly
                          density="comfortable"
                          variant="outlined"
                          hide-details
                          prepend-inner-icon="ri-link"
                          class="mb-3"
                          append-inner-icon="ri-file-copy-line"
                          @click:append-inner="() => {
                            if (coverForm.id) {
                              navigator.clipboard.writeText(`${window.location.origin}/api/v1/vk-covers/webhook/${coverForm.id}`);
                              alert('Ссылка скопирована!');
                            }
                          }"
                        />
                      </VCol>
                      <VCol cols="12" md="6">
                        <VTextField
                          v-model="coverForm.callback_confirmation_code"
                          label="Код подтверждения (Confirmation Code)"
                          placeholder="Код, который запрашивает ВК при подключении сервера"
                          density="comfortable"
                          variant="outlined"
                          hide-details
                        />
                      </VCol>
                      <VCol cols="12" md="6">
                        <VTextField
                          v-model="coverForm.callback_secret_key"
                          label="Секретный ключ (Secret Key)"
                          placeholder="Секретное слово для проверки подлинности"
                          density="comfortable"
                          variant="outlined"
                          hide-details
                        />
                      </VCol>
                    </VRow>
                  </div>
                </VExpandTransition>
              </VCard>
              <!-- Переключатель безопасности и пресеты -->
              <div class="d-flex align-center justify-space-between mb-2">
                <div class="d-flex align-center gap-2">
                  <span class="text-subtitle-2 font-weight-bold">🎨 Дизайнерские пресеты:</span>
                  <VBtn size="x-small" color="primary" variant="tonal" @click="applyPreset('premium')">🔥 Премиум Тёмный</VBtn>
                  <VBtn size="x-small" color="success" variant="tonal" @click="applyPreset('promo')">🍕 Промо & Заказы</VBtn>
                  <VBtn size="x-small" color="warning" variant="tonal" @click="applyPreset('community')">🏆 Лидеры Сообщества</VBtn>
                </div>
                <VSwitch
                  v-model="showMobileSafeArea"
                  label="📱 Безопасная зона (VK Mobile)"
                  color="info"
                  density="compact"
                  hide-details
                />
              </div>

              <div class="canvas-container position-relative rounded-lg elevation-2 mb-4 overflow-hidden border" style="height: 300px;">
                <div v-if="previewImageUrl" class="h-100 w-100 d-flex align-center justify-center bg-black">
                  <img :src="previewImageUrl" class="w-100 h-100" style="object-fit: cover;" />
                  <VBtn icon="ri-edit-line" color="primary" size="small" class="position-absolute" style="top: 15px; right: 15px;" @click="previewImageUrl = null">Редактор</VBtn>
                </div>
                <div v-else class="cover-canvas position-relative h-100 w-100" :style="{ backgroundImage: coverForm.background_image_url ? `url(${coverForm.background_image_url})` : 'linear-gradient(135deg, #12121e 0%, #1e1e30 100%)', backgroundSize: 'cover', backgroundPosition: 'center' }">
                  <!-- Визуализация безопасной зоны VK Mobile -->
                  <div v-if="showMobileSafeArea" class="position-absolute h-100 w-100 pointer-events-none" style="z-index: 1;">
                    <!-- Обрезаемый левый край -->
                    <div class="position-absolute h-100 bg-black text-caption d-flex align-center justify-center text-white" style="left: 0; width: 13.5%; opacity: 0.45; border-right: 1px dashed rgba(255,255,255,0.6);">📱 Обрезка</div>
                    <!-- Обрезаемый правый край -->
                    <div class="position-absolute h-100 bg-black text-caption d-flex align-center justify-center text-white" style="right: 0; width: 13.5%; opacity: 0.45; border-left: 1px dashed rgba(255,255,255,0.6);">📱 Обрезка</div>
                    <!-- Верхний статус-бар VK App -->
                    <div class="position-absolute w-100 bg-red text-caption d-flex align-center justify-center text-white" style="top: 0; height: 17%; opacity: 0.35; border-bottom: 1px dashed rgba(255,255,255,0.6);">⚠️ Статус-бар VK Mobile</div>
                    <!-- Нижняя зона аватара сообщества -->
                    <div class="position-absolute w-100 bg-red text-caption d-flex align-center justify-center text-white" style="bottom: 0; height: 21%; opacity: 0.35; border-top: 1px dashed rgba(255,255,255,0.6);">⚠️ Кнопки и Аватар ВК</div>
                    <!-- Безопасное центральное окно -->
                    <div class="position-absolute d-flex align-center justify-center text-caption font-weight-bold" style="left: 13.5%; right: 13.5%; top: 17%; bottom: 21%; border: 2px dashed #00e676; color: #00e676; opacity: 0.85;">
                      ✅ Безопасная зона VK Mobile & PC
                    </div>
                  </div>

                  <!-- Виджеты на холсте -->
                  <div
                    v-for="(w, idx) in coverForm.widgets"
                    :key="idx"
                    class="canvas-widget position-absolute px-2 py-1 rounded cursor-move"
                    :class="{
                      'widget-selected': selectedWidgetIndex === idx,
                      'bg-glass': w.bg_style === 'glass',
                      'bg-solid': w.bg_style === 'solid',
                      'bg-neon': w.bg_style === 'neon',
                      'bg-pill': w.bg_style === 'pill',
                      'bg-gradient': w.bg_style === 'gradient'
                    }"
                    :style="{
                      left: `${(w.x / 1590) * 100}%`,
                      top: `${(w.y / 530) * 100}%`,
                      color: w.color,
                      fontSize: `${(w.font_size / 530) * 26}vw`,
                      lineHeight: '1.2',
                      zIndex: 2
                    }"
                    @mousedown="startDrag(idx, $event)"
                    @click.stop="selectedWidgetIndex = idx"
                  >
                    <template v-if="w.type === 'clock'">{{ w.icon || '⏰' }} 15:45{{ w.show_date ? ' (вт, 21 июл)' : '' }}</template>
                    <template v-else-if="w.type === 'weather'">{{ w.icon || '🌤' }} {{ w.city || coverForm.city_weather }}: +21°C ☀️</template>
                    <template v-else-if="w.type === 'work_hours'">{{ w.icon || '' }} {{ w.text_open ? w.text_open.replace('{close_time}', w.close_time || '22:00') : '🟢 Открыты до ' + (w.close_time || '22:00') }}</template>
                    <template v-else-if="w.type === 'timer'">{{ w.icon || '⏱' }} {{ w.label || 'До конца акции:' }} 2д. 04:12</template>
                    <template v-else-if="w.type === 'orders_counter'">{{ w.icon || '🚚' }} {{ w.label || 'Сегодня доставлено:' }} 42 заказа</template>
                    <template v-else-if="w.type === 'last_winner'">{{ w.icon || '🎉' }} {{ w.label || 'Победитель:' }} Анна С. (Роллы)</template>
                    <template v-else-if="w.type === 'promo_code'">{{ w.icon || '🎁' }} {{ w.label || 'Промокод:' }} {{ w.code || 'VK2026' }}</template>
                    <template v-else-if="w.type === 'text'">{{ w.icon ? w.icon + ' ' : '' }}{{ w.text || 'Ваш текст' }}</template>
                    <template v-else-if="w.type === 'active_subscriber'">
                      <div class="d-flex align-center">
                        <div class="rounded-circle bg-secondary me-2 d-flex align-center justify-center font-weight-bold text-caption" :style="{ width: `${(w.avatar_size / 530) * 26}vw`, height: `${(w.avatar_size / 530) * 26}vw`, fontSize: `${(w.font_size / 530) * 16}vw` }">👑</div>
                        <div>
                          <span>{{ w.label || 'Лидер недели:' }}</span>
                          <span class="font-weight-bold d-block">Иван Иванов (45 б.)</span>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </VCol>
            <VCol cols="12" lg="4" class="d-flex flex-column" style="border-left: 1px solid rgba(var(--v-theme-on-surface), 0.08);">
              <h4 class="text-subtitle-1 font-weight-bold mb-3">Загрузка фона обложки</h4>
              <div class="d-flex align-center mb-2">
                <input type="file" id="cover-bg-file" style="display: none" accept="image/*" @change="onCoverBackgroundSelected" />
                <VBtn color="primary" variant="outlined" size="small" prepend-icon="ri-upload-2-line" :loading="imageCoverUploading" onclick="document.getElementById('cover-bg-file').click()" class="me-2">Главный фон</VBtn>
                <VBtn v-if="coverForm.background_image_url" color="error" variant="text" size="small" @click="coverForm.background_image_url = null">Сбросить</VBtn>
              </div>

              <!-- Слайд-шоу фона -->
              <div class="mb-3 pa-2 bg-light rounded-lg border">
                <span class="text-caption font-weight-bold d-block mb-1">🖼 Слайд-шоу фона (смена фонов)</span>
                <input type="file" id="cover-slideshow-files" style="display: none" accept="image/*" multiple @change="handleSlideshowUpload" />
                <div class="d-flex align-center gap-2 mb-2">
                  <VBtn size="x-small" color="info" variant="tonal" prepend-icon="ri-image-add-line" :loading="imageCoverUploading" onclick="document.getElementById('cover-slideshow-files').click()">+ Фоны слайд-шоу</VBtn>
                  <span class="text-caption text-muted">({{ (coverForm.slideshow_images || []).length }} шт.)</span>
                </div>
                <div v-if="coverForm.slideshow_images && coverForm.slideshow_images.length > 0" class="d-flex flex-wrap gap-1 mb-2 max-h-30 overflow-y-auto">
                  <div v-for="(imgUrl, sIdx) in coverForm.slideshow_images" :key="sIdx" class="position-relative border rounded overflow-hidden" style="width: 45px; height: 30px;">
                    <img :src="imgUrl" class="w-100 h-100" style="object-fit: cover;" />
                    <VBtn icon="ri-close-line" size="x-small" color="error" variant="text" class="position-absolute" style="top: -6px; right: -6px; font-size: 10px;" @click="removeSlideshowImage(sIdx)" />
                  </div>
                </div>
                <div v-if="coverForm.slideshow_images && coverForm.slideshow_images.length > 0" class="d-flex gap-2">
                  <VSelect v-model.number="coverForm.slideshow_interval_minutes" label="Смена каждые" :items="[{title:'1 мин',value:1},{title:'2 мин',value:2},{title:'5 мин',value:5},{title:'15 мин',value:15},{title:'30 мин',value:30},{title:'1 час',value:60}]" density="compact" variant="outlined" hide-details class="mb-1" />
                  <VSelect v-model="coverForm.slideshow_mode" label="Порядок" :items="[{title:'По порядку',value:'sequence'},{title:'Случайно',value:'random'}]" density="compact" variant="outlined" hide-details class="mb-1" />
                </div>
              </div>

              <VDivider class="mb-3" />
              <h4 class="text-subtitle-1 font-weight-bold mb-2">Добавить элементы (9 виджетов)</h4>
              <div class="d-flex flex-wrap gap-2 mb-3">
                <VBtn size="x-small" variant="tonal" color="primary" prepend-icon="ri-time-line" @click="addWidget('clock')">Часы & Дата</VBtn>
                <VBtn size="x-small" variant="tonal" color="success" prepend-icon="ri-store-2-line" @click="addWidget('work_hours')">Время работы</VBtn>
                <VBtn size="x-small" variant="tonal" color="primary" prepend-icon="ri-sun-line" @click="addWidget('weather')">Погода</VBtn>
                <VBtn size="x-small" variant="tonal" color="primary" prepend-icon="ri-trophy-line" @click="addWidget('active_subscriber')">Лидер недели</VBtn>
                <VBtn size="x-small" variant="tonal" color="primary" prepend-icon="ri-timer-line" @click="addWidget('timer')">Таймер</VBtn>
                <VBtn size="x-small" variant="tonal" color="success" prepend-icon="ri-truck-line" @click="addWidget('orders_counter')">Заказы сегодня</VBtn>
                <VBtn size="x-small" variant="tonal" color="warning" prepend-icon="ri-gift-line" @click="addWidget('last_winner')">Победитель</VBtn>
                <VBtn size="x-small" variant="tonal" color="error" prepend-icon="ri-coupon-line" @click="addWidget('promo_code')">Промокод</VBtn>
                <VBtn size="x-small" variant="tonal" color="secondary" prepend-icon="ri-text" @click="addWidget('text')">Текст</VBtn>
              </div>
              <h4 class="text-subtitle-1 font-weight-bold mb-2">Список элементов</h4>
              <div class="flex-grow-1 overflow-y-auto mb-3" style="max-height: 140px;">
                <VList v-if="coverForm.widgets.length > 0" density="compact">
                  <VListItem v-for="(w, idx) in coverForm.widgets" :key="idx" :class="{ 'bg-primary-lighten': selectedWidgetIndex === idx }" @click="selectedWidgetIndex = idx" rounded="lg" class="mb-1 pa-1">
                    <VListItemTitle class="font-weight-bold text-body-2">{{ getWidgetLabel(w) }}</VListItemTitle>
                    <template #append>
                      <VBtn icon="ri-delete-bin-6-line" size="x-small" color="error" variant="text" @click.stop="removeWidget(idx)" />
                    </template>
                  </VListItem>
                </VList>
                <div v-else class="text-caption text-medium-emphasis text-center py-2 border rounded-lg">Нажмите кнопку выше, чтобы добавить виджет</div>
              </div>
              <div v-if="selectedWidgetIndex !== -1 && coverForm.widgets[selectedWidgetIndex]" class="border rounded-lg pa-3 bg-light" style="max-height: 250px; overflow-y: auto;">
                <h5 class="text-subtitle-2 font-weight-bold mb-2">⚙️ Настройки виджета & Подложки</h5>
                <VRow density="compact">
                  <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].font_size" label="Размер шрифта" type="number" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  <VCol cols="6"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].color" label="Цвет текста" type="color" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].x" label="X (горизонталь)" type="number" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].y" label="Y (вертикаль)" type="number" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  <VCol cols="12">
                    <VSelect
                      v-model="coverForm.widgets[selectedWidgetIndex].bg_style"
                      label="Стиль подложки (контейнера)"
                      :items="[
                        { title: 'Без подложки', value: 'none' },
                        { title: '✨ Glassmorphism (Стекло)', value: 'glass' },
                        { title: '⚡️ Neon (Неоновая рамка)', value: 'neon' },
                        { title: '⬛️ Solid (Тёмный)', value: 'solid' },
                        { title: '💊 Pill (Капсула)', value: 'pill' },
                        { title: '🟣 Gradient (Градиент)', value: 'gradient' },
                        { title: '🎨 Свой цвет (Ручная настройка)', value: 'custom' }
                      ]"
                      density="compact"
                      variant="outlined"
                      hide-details
                      class="mb-1"
                    />
                  </VCol>
                  <!-- Поля ручной настройки подложки -->
                  <template v-if="coverForm.widgets[selectedWidgetIndex].bg_style === 'custom'">
                    <VCol cols="6"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].custom_bg_color" label="Цвет фона" type="color" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].custom_bg_opacity" label="Прозрачность (%)" type="number" min="0" max="100" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="6"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].custom_border_color" label="Цвет рамки" type="color" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].custom_border_width" label="Толщина рамки" type="number" min="0" max="10" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  </template>
                  <template v-if="coverForm.widgets[selectedWidgetIndex].bg_style !== 'none'">
                    <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].container_radius" label="Закругление (px)" type="number" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].container_padding" label="Отступы (px)" type="number" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  </template>

                  <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].icon" label="Иконка/Индекс (★, •, ☀, ▶, ✦, ●, ▲, ◆)" placeholder="например ★" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  <VCol cols="6"><VSwitch v-model="coverForm.widgets[selectedWidgetIndex].text_shadow" label="Тень" color="primary" density="compact" hide-details class="mb-1" /></VCol>
                  <VCol cols="6"><VSwitch v-model="coverForm.widgets[selectedWidgetIndex].text_stroke" label="Обводка" color="primary" density="compact" hide-details class="mb-1" /></VCol>
                  
                  <VCol cols="12" v-if="coverForm.widgets[selectedWidgetIndex].type === 'text'"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].text" label="Шаблон текста ({time}, {date}, {weather}, {today_orders}, {last_winner})" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  <VCol cols="12" v-if="coverForm.widgets[selectedWidgetIndex].type === 'weather'"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].city" label="Город" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  <VCol cols="12" v-if="coverForm.widgets[selectedWidgetIndex].type === 'clock'"><VSwitch v-model="coverForm.widgets[selectedWidgetIndex].show_date" label="Показывать дату" color="success" density="compact" hide-details class="mb-1" /></VCol>
                  <VCol cols="12" v-if="coverForm.widgets[selectedWidgetIndex].type === 'promo_code'"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].code" label="Промокод" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  
                  <template v-if="coverForm.widgets[selectedWidgetIndex].type === 'work_hours'">
                    <VCol cols="6"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].open_time" label="Открытие (HH:MM)" type="time" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="6"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].close_time" label="Закрытие (HH:MM)" type="time" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].text_open" label="Когда открыты" placeholder="🟢 Открыты до {close_time}" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].text_closing_soon" label="Когда скоро закроемся" placeholder="🟡 Закрываемся через {time_left}" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].text_opening_soon" label="Когда скоро откроемся" placeholder="🟡 Откроемся через {time_left}" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].text_closed" label="Когда закрыто" placeholder="🔴 Закрыто! Откроемся в {next_open_time}" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].closing_soon_threshold" label="Скоро закроемся (мин)" type="number" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="6"><VTextField v-model.number="coverForm.widgets[selectedWidgetIndex].opening_soon_threshold" label="Скоро откроемся (мин)" type="number" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  </template>
                  
                  <template v-if="coverForm.widgets[selectedWidgetIndex].type === 'timer'">
                    <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].label" label="Заголовок" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                    <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].target_date" label="Дата окончания" type="datetime-local" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  </template>
                  <template v-if="coverForm.widgets[selectedWidgetIndex].type === 'active_subscriber'">
                    <VCol cols="12">
                      <VSelect
                        v-model="coverForm.widgets[selectedWidgetIndex].period"
                        label="Период расчета рейтинга"
                        :items="[
                          { title: '☀️ Лидер дня (за сегодня)', value: 'day' },
                          { title: '👑 Лидер недели (текущая неделя)', value: 'week' },
                          { title: '🏆 Лидер месяца (текущий месяц)', value: 'month' },
                          { title: '⭐️ Лидер за всё время', value: 'all_time' }
                        ]"
                        density="compact"
                        variant="outlined"
                        hide-details
                        class="mb-1"
                      />
                    </VCol>
                    <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].label" label="Заголовок (например 'Лидер дня:')" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  </template>
                  <template v-if="['orders_counter', 'last_winner'].includes(coverForm.widgets[selectedWidgetIndex].type)">
                    <VCol cols="12"><VTextField v-model="coverForm.widgets[selectedWidgetIndex].label" label="Заголовок" density="compact" variant="outlined" hide-details class="mb-1" /></VCol>
                  </template>
                </VRow>
              </div>
            </VCol>
          </VRow>
        </VCardText>
        <VDivider />
        <VCardActions class="pa-5 bg-surface border-t d-flex justify-between">
          <div class="d-flex">
            <VBtn color="primary" variant="tonal" prepend-icon="ri-eye-line" :loading="previewLoading" class="me-2" @click="loadPreview">Предпросмотр</VBtn>
            <VBtn color="warning" variant="tonal" prepend-icon="ri-send-plane-line" :loading="publishingCover" @click="publishCoverNow">{{ coverForm.id ? 'Обновить в ВК' : 'Опубликовать в ВК' }}</VBtn>
          </div>
          <div class="ms-auto">
            <VBtn color="secondary" variant="outlined" class="me-2" @click="showCoverSettingsDialog = false">Отмена</VBtn>
            <VBtn color="success" prepend-icon="ri-save-3-line" :loading="savingCover" @click="saveCoverSettings">Сохранить</VBtn>
          </div>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО МУЛЬТИ-ОБЛОЖЕК (СПИСОК И РОТАЦИЯ) -->
    <VDialog v-model="showMultiCoverManagerDialog" max-width="950px" scrollable persistent>
      <VCard class="rounded-xl">
        <VCardTitle class="d-flex align-center justify-space-between pa-5 bg-surface border-b">
          <div class="d-flex align-center">
            <div class="bg-success-lighten rounded-lg pa-2 me-3">
              <VIcon icon="ri-stack-line" color="success" size="24" />
            </div>
            <div>
              <span class="text-h6 font-weight-bold d-block">Управление динамическими обложками (Ротация)</span>
              <span class="text-caption text-muted">Сообщество: {{ connections.find(c => c.id === selectedConnectionId)?.name }}</span>
            </div>
          </div>
          <VBtn icon="ri-close-line" variant="text" color="secondary" density="comfortable" @click="showMultiCoverManagerDialog = false" />
        </VCardTitle>

        <VCardText class="pa-6" style="max-height: 75vh;">
          <div class="d-flex align-center justify-space-between mb-4">
            <div>
              <h4 class="text-subtitle-1 font-weight-bold">Список динамических обложек</h4>
              <span class="text-caption text-muted">Создавайте разные варианты обложек для утреннего, дневного, вечернего времени или акционных баннеров</span>
            </div>
            <VBtn color="success" prepend-icon="ri-add-line" @click="createNewCoverBot">
              Создать обложку
            </VBtn>
          </div>

          <VRow v-if="selectedConnectionCoverBots.length > 0">
            <VCol v-for="cBot in selectedConnectionCoverBots" :key="cBot.id" cols="12" md="6">
              <VCard variant="outlined" class="pa-4 rounded-xl position-relative border-hover">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="font-weight-bold text-subtitle-1">{{ cBot.name || 'Обложка' }}</span>
                  <VChip size="small" :color="cBot.is_active ? 'success' : 'secondary'" variant="tonal">
                    {{ cBot.is_active ? 'Активна' : 'Отключена' }}
                  </VChip>
                </div>

                <div class="text-caption text-muted mb-3">
                  <div><strong>Режим расписания:</strong> 
                    <span v-if="cBot.schedule_type === 'time_range'" class="text-primary font-weight-bold">⏰ {{ cBot.schedule_start_time || '00:00' }} - {{ cBot.schedule_end_time || '23:59' }}</span>
                    <span v-else-if="cBot.schedule_type === 'interval'" class="text-warning font-weight-bold">🔄 Циклическая ротация</span>
                    <span v-else class="text-success font-weight-bold">🟢 Всегда</span>
                  </div>
                  <div><strong>Элементов виджетов:</strong> {{ (cBot.widgets || []).length }} шт.</div>
                  <div v-if="cBot.slideshow_images && cBot.slideshow_images.length > 0">
                    <strong>Слайд-шоу фона:</strong> {{ cBot.slideshow_images.length }} картинок (смена каждые {{ cBot.slideshow_interval_minutes || 5 }} мин)
                  </div>
                </div>

                <VDivider class="mb-3" />

                <div class="d-flex align-center justify-space-between">
                  <VBtn size="small" color="primary" variant="tonal" prepend-icon="ri-edit-line" @click="editCoverBot(cBot)">
                    Редактировать
                  </VBtn>
                  <div class="d-flex gap-1">
                    <VBtn icon="ri-file-copy-line" size="small" color="secondary" variant="text" title="Клонировать обложку" @click="cloneCoverBot(cBot)" />
                    <VBtn icon="ri-delete-bin-6-line" size="small" color="error" variant="text" title="Удалить обложку" @click="deleteCoverBot(cBot.id)" />
                  </div>
                </div>
              </VCard>
            </VCol>
          </VRow>

          <div v-else class="text-center py-8 bg-light rounded-xl border-dashed">
            <VIcon icon="ri-image-edit-line" size="48" color="muted" class="mb-2" />
            <h4 class="text-subtitle-1 font-weight-bold mb-1">Нет созданных обложек</h4>
            <p class="text-caption text-muted mb-3">Для этого сообщества еще не созданы динамические обложки</p>
            <VBtn color="success" size="small" prepend-icon="ri-add-line" @click="createNewCoverBot">
              Создать первую обложку
            </VBtn>
          </div>
        </VCardText>

        <VCardActions class="pa-4 bg-surface border-t d-flex justify-end">
          <VBtn color="secondary" variant="outlined" @click="showMultiCoverManagerDialog = false">
            Закрыть
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО БОТА КОНКУРСОВ И ГЕЙМИФИКАЦИИ -->
    <VDialog v-model="showContestSettingsDialog" max-width="1000px" scrollable persistent>
      <VCard class="rounded-xl">
        <VCardTitle class="d-flex align-center justify-space-between pa-5 bg-surface border-b">
          <div class="d-flex align-center">
            <div class="bg-warning-lighten rounded-lg pa-2 me-3">
              <VIcon icon="ri-trophy-line" color="warning" size="24" />
            </div>
            <div>
              <span class="text-h6 font-weight-bold d-block">Менеджер конкурсов и геймификации</span>
              <span class="text-caption text-muted">Сообщество: {{ connections.find(c => c.id === selectedConnectionId)?.name }}</span>
            </div>
          </div>
          <VBtn icon="ri-close-line" variant="text" color="secondary" density="comfortable" @click="showContestSettingsDialog = false" />
        </VCardTitle>

        <!-- Навигация внутри диалога конкурсов -->
        <VCardText class="pa-6" style="max-height: 75vh;">
          
          <!-- Вкладка 1: Список конкурсов -->
          <div v-if="activeContestTab === 'list'">
            <div class="d-flex align-center justify-space-between mb-4">
              <h3 class="text-subtitle-1 font-weight-bold">Список конкурсов</h3>
              <div class="d-flex align-center gap-2">
                <VBtn color="info" variant="outlined" size="small" prepend-icon="ri-bar-chart-box-line" @click="openStatsPage(null)" :disabled="contestList.length === 0">
                  Статистика
                </VBtn>
                <VBtn color="primary" size="small" prepend-icon="ri-add-line" @click="createContestDraft">
                  Создать конкурс
                </VBtn>
              </div>
            </div>
            
            <VDataTable
              :headers="[
                { title: 'Название', key: 'title' },
                { title: 'Игра', key: 'game_type' },
                { title: 'Статус', key: 'status' },
                { title: 'Пост ВК', key: 'post_id' },
                { title: 'Действия', key: 'actions', sortable: false }
              ]"
              :items="contestList"
              :loading="loadingContests"
              density="comfortable"
              no-data-text="Конкурсы пока не созданы"
            >
              <template #item.game_type="{ item }">
                {{ getGameTypeLabel(item.game_type) }}
              </template>
              <template #item.status="{ item }">
                <VChip
                  size="small"
                  :color="item.is_active ? 'success' : item.post_id ? 'secondary' : 'warning'"
                  variant="flat"
                  class="font-weight-bold"
                >
                  {{ item.is_active ? 'Активен (Запущен)' : item.post_id ? 'Завершен' : 'Черновик' }}
                </VChip>
              </template>
              <template #item.post_id="{ item }">
                <a
                  v-if="item.post_id"
                  :href="`https://vk.com/wall-${connections.find(c => c.id === selectedConnectionId)?.vk_group_id}_${item.post_id}`"
                  target="_blank"
                  class="text-primary text-decoration-none"
                >
                  Пост ВК (ID: {{ item.post_id }})
                </a>
                <span v-else class="text-muted">—</span>
              </template>
              <template #item.actions="{ item }">
                <div class="d-flex align-center gap-1">
                  <!-- Кнопки статистики -->
                  <VBtn v-if="item.post_id" icon="ri-bar-chart-box-line" size="x-small" color="info" variant="text" title="Детальная статистика" @click="openStatsPage(item.id)" />
                  <VBtn v-if="item.post_id" icon="ri-group-line" size="x-small" color="primary" variant="text" title="Участники" @click="viewPlayers(item.id)" />
                  <VBtn v-if="item.post_id" icon="ri-medal-line" size="x-small" color="success" variant="text" title="Победители" @click="viewWinners(item.id)" />
                  
                  <!-- Редактировать -->
                  <VBtn v-if="!item.is_active" icon="ri-edit-line" size="x-small" color="secondary" variant="text" title="Редактировать" @click="editContest(item)" />
                  
                  <!-- Пуск/Стоп -->
                  <VBtn
                    v-if="!item.is_active && !item.post_id"
                    icon="ri-play-line"
                    size="x-small"
                    color="success"
                    variant="text"
                    title="Опубликовать и запустить"
                    :loading="launchingContest"
                    @click="launchContest(item.id)"
                  />
                  <VBtn
                    v-if="item.is_active"
                    icon="ri-stop-line"
                    size="x-small"
                    color="error"
                    variant="text"
                    title="Остановить"
                    @click="stopContest(item.id)"
                  />
                  
                  <VBtn
                    v-if="item.is_active && item.game_type === 'battle'"
                    icon="ri-award-line"
                    size="x-small"
                    color="warning"
                    variant="text"
                    title="Подвести итоги"
                    @click="finishBattleContest(item.id)"
                  />
                  
                  <!-- Удалить -->
                  <VBtn icon="ri-delete-bin-6-line" size="x-small" color="error" variant="text" title="Удалить" @click="deleteContest(item.id)" />
                </div>
              </template>
            </VDataTable>
          </div>

          <!-- Вкладка 2: Создание / Редактирование -->
          <div v-else-if="activeContestTab === 'edit'">
            <div class="d-flex align-center justify-space-between mb-4">
              <h3 class="text-subtitle-1 font-weight-bold">
                {{ contestForm.id ? 'Редактирование настроек конкурса' : 'Новый конкурс' }}
              </h3>
              <VBtn variant="outlined" size="small" prepend-icon="ri-arrow-left-line" @click="activeContestTab = 'list'">
                Назад к списку
              </VBtn>
            </div>
            <div class="mb-4">
              <!-- Поле индивидуального API-ключа -->
              <div class="mb-4 bg-light rounded-xl pa-4 border">
                <span class="font-weight-bold d-block mb-1">Индивидуальный ключ доступа сообщества</span>
                <span class="text-caption text-muted d-block mb-3">
                  Позволяет использовать отдельный токен для работы этого конкретного бота. Если поле пустое, будет использоваться токен основного подключения.
                  <a :href="getVkTokenUrl()" target="_blank" class="text-primary font-weight-bold text-decoration-none d-inline-block ms-1">Получить токен сообщества автоматически ↗</a>
                </span>
                <VTextField
                  v-model="contestForm.vk_bot_token"
                  label="API-ключ сообщества ВК (Токен)"
                  placeholder="Вставьте токен vk1.a.***"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  type="password"
                />
              </div>
            </div>

            <VRow>
              <VCol cols="12" sm="6">
                <VTextField v-model="contestForm.title" label="Название конкурса" variant="outlined" class="mb-4" />
              </VCol>
              <VCol cols="12" sm="6">
                <VSelect
                  v-model="contestForm.game_type"
                  label="Тип игры"
                  :items="[
                    { title: '🎰 Рулетка (слово Крутить)', value: 'roulette' },
                    { title: '🔒 Сейф (угадать 4 цифры)', value: 'safe' },
                    { title: '✊ Камень-ножницы-бумага', value: 'knb' },
                    { title: '📦 Сундуки (сетка 4x4)', value: 'chests' },
                    { title: '⚓ Морской бой (сетка 10x10)', value: 'seabattle' },
                    { title: '🏖️ Битва за поле (пляжная битва 10x10)', value: 'battle' }
                  ]"
                  item-title="title"
                  item-value="value"
                  variant="outlined"
                  class="mb-4"
                />
              </VCol>

              <!-- Для сейфа -->
              <VCol cols="12" sm="6" v-if="contestForm.game_type === 'safe'">
                <VTextField v-model="contestForm.safe_code" label="Секретный код сейфа (4 цифры)" variant="outlined" class="mb-4" maxlength="4" />
              </VCol>

              <!-- Для пляжной битвы -->
              <VCol cols="12" sm="6" v-if="contestForm.game_type === 'battle'">
                <VSlider
                  v-model="contestForm.penalty_percent"
                  label="Штрафные ячейки (мины, %)"
                  min="0"
                  max="50"
                  step="1"
                  thumb-label="always"
                  class="mb-4"
                />
              </VCol>
              <VCol cols="12" sm="6" v-if="contestForm.game_type === 'battle'">
                <VSlider
                  v-model="contestForm.bonus_percent"
                  label="Бонусные ячейки (+2 хода, %)"
                  min="0"
                  max="50"
                  step="1"
                  thumb-label="always"
                  class="mb-4"
                />
              </VCol>

              <VCol cols="12">
                <VRow>
                  <!-- Левая колонка: редактор -->
                  <VCol cols="12" md="7">
                    <VCard variant="outlined" class="pa-4">
                      <div class="d-flex align-center justify-space-between mb-2">
                        <span class="text-subtitle-2 font-weight-bold">Текст публикации (правила розыгрыша)</span>
                      </div>
                      
                      <!-- Эмодзи-панель -->
                      <div class="d-flex align-center gap-1 mb-2 flex-wrap border rounded pa-2 bg-var-theme-background">
                        <span class="text-caption text-muted mr-1">Смайлы:</span>
                        <VBtn v-for="emoji in ['🎁', '🏖️', '🍕', '🍔', '🥤', '🎲', '🏆', '🎉', '🔥', '✨', '💥', '🛑', '🔔', '🎯', '🚀', '💬', '📢']" :key="emoji" variant="text" size="x-small" class="px-1" min-width="24" @click="insertTextAtCursor(emoji)">
                          {{ emoji }}
                        </VBtn>
                      </div>

                      <!-- Панель вставки тегов -->
                      <div class="d-flex align-center gap-1 mb-3 flex-wrap">
                        <span class="text-caption text-muted mr-1">Вставить тег:</span>
                        <VChip size="small" variant="outlined" color="primary" style="cursor: pointer;" @click="insertTextAtCursor('{название}')" title="Название игры (Рулетка, Сейф и др.)">
                          {название}
                        </VChip>
                        <VChip size="small" variant="outlined" color="primary" style="cursor: pointer;" @click="insertTextAtCursor('{призы}')" title="Список всех добавленных призов">
                          {призы}
                        </VChip>
                        <VChip size="small" variant="outlined" color="primary" style="cursor: pointer;" @click="insertTextAtCursor('{ссылка}')" title="Ссылка на ваше сообщество ВК">
                          {ссылка}
                        </VChip>
                        <VChip size="small" variant="outlined" color="primary" style="cursor: pointer;" @click="insertTextAtCursor('{время_кд}')" title="Время задержки между ходами">
                          {время_кд}
                        </VChip>
                        <VChip size="small" variant="outlined" color="primary" style="cursor: pointer;" @click="insertTextAtCursor('{попытки}')" title="Стартовые попытки">
                          {попытки}
                        </VChip>
                      </div>

                      <VTextarea id="rules-text-input" v-model="contestForm.rules_text" label="Текст правил (описание поста)" variant="outlined" rows="8" class="mb-2" hint="Этот текст будет опубликован в вашей группе ВК вместе с обложкой игры." />
                    </VCard>
                  </VCol>

                  <!-- Правая колонка: предпросмотр ВК -->
                  <VCol cols="12" md="5">
                    <VCard variant="outlined" class="pa-4 bg-var-theme-background fill-height" style="border-color: #e7e8ec !important;">
                      <div class="d-flex align-center justify-space-between mb-3 border-bottom pb-2">
                        <span class="text-subtitle-2 font-weight-bold d-flex align-center gap-1">
                          <VIcon icon="ri-facebook-circle-fill" color="info" /> Предпросмотр поста ВКонтакте
                        </span>
                      </div>

                      <div class="vk-post-mockup border rounded pa-3 bg-white text-dark shadow-sm">
                        <!-- Шапка поста -->
                        <div class="d-flex align-center gap-2 mb-3">
                          <VAvatar size="40" color="primary">
                            <VIcon icon="ri-community-line" color="white" />
                          </VAvatar>
                          <div>
                            <div class="font-weight-bold text-body-2 text-primary" style="color: #2a5885 !important; cursor: pointer;">
                              {{ connections.find(c => c.id === contestForm.vk_bot_connection_id)?.group_name || 'Ваше сообщество ВКонтакте' }}
                            </div>
                            <div class="text-caption text-muted">только что</div>
                          </div>
                        </div>

                        <!-- Текст поста -->
                        <div class="text-body-2 mb-3 whitespace-pre-wrap" style="line-height: 1.4; color: #000; font-family: -apple-system, BlinkMacSystemFont, 'Roboto', 'Helvetica Neue', sans-serif;">
                          {{ processedPreviewText }}
                        </div>

                        <!-- Вложение: интерактивная карта -->
                        <div class="vk-post-attachment border rounded overflow-hidden bg-light position-relative" style="aspect-ratio: 16/9; max-height: 200px;">
                          <div class="d-flex flex-column align-center justify-center fill-height pa-4 text-center">
                            <VIcon size="48" :icon="contestForm.game_type === 'battle' ? 'ri-temp-hot-line' : (contestForm.game_type === 'seabattle' ? 'ri-ship-2-line' : (contestForm.game_type === 'safe' ? 'ri-safe-2-line' : 'ri-gamepad-line'))" color="grey" />
                            <div class="font-weight-bold text-caption mt-2">Интерактивная карта игры</div>
                            <div class="text-caption text-muted">Генерируется автоматически во время хода участников</div>
                          </div>
                        </div>

                        <!-- Лайки / Репосты -->
                        <div class="d-flex align-center gap-4 mt-3 pt-2 border-top text-muted text-caption">
                          <span class="d-flex align-center gap-1"><VIcon icon="ri-heart-line" size="16" /> Лайк</span>
                          <span class="d-flex align-center gap-1"><VIcon icon="ri-chat-1-line" size="16" /> Комментарий</span>
                          <span class="d-flex align-center gap-1"><VIcon icon="ri-share-forward-line" size="16" /> Поделиться</span>
                        </div>
                      </div>
                    </VCard>
                  </VCol>
                </VRow>
              </VCol>

              <!-- Настройка призов -->
              <VCol cols="12">
                <input type="file" id="prize-image-input" accept="image/*" style="display:none" @change="onPrizeImageSelected">
                <input type="file" id="prize-item-image-input" accept="image/*" style="display:none" @change="onPrizeItemImageSelected">

                <VCard variant="outlined" class="pa-4 mb-4">
                  <h4 class="text-subtitle-2 font-weight-bold mb-3">Настройка призов</h4>
                  
                  <div class="d-flex align-center gap-3 mb-4 flex-wrap">
                    <VTextField v-model="newPrizeName" label="Название приза (пицца, ролл и т.д.)" variant="outlined" density="compact" hide-details style="min-width: 250px;" />
                    <VTextField v-model.number="newPrizeQty" label="Кол-во" type="number" variant="outlined" density="compact" hide-details style="max-width: 100px;" />
                    
                    <div class="d-flex align-center gap-2">
                      <VBtn :color="newPrizeImageUrl ? 'success' : 'secondary'" variant="tonal" size="small" prepend-icon="ri-image-add-line" @click="triggerPrizeUpload" :loading="isUploadingPrize">
                        {{ newPrizeImageUrl ? 'Фото добавлено' : 'Добавить фото' }}
                      </VBtn>
                      <VAvatar v-if="newPrizeImageUrl" size="36" rounded class="border">
                        <VImg :src="newPrizeImageUrl" />
                      </VAvatar>
                    </div>

                    <VBtn color="primary" size="small" prepend-icon="ri-add-line" @click="addPrizeToForm">Добавить приз</VBtn>
                  </div>

                  <VList v-if="contestForm.prizes.length > 0">
                    <VListItem v-for="(p, idx) in contestForm.prizes" :key="p.id || idx" density="compact" rounded="lg" class="border mb-1">
                      <template #prepend>
                        <VAvatar size="40" rounded class="border mr-2" style="cursor: pointer;" @click="triggerPrizeItemUpload(idx)" title="Изменить изображение приза">
                          <VImg v-if="p.image_url" :src="p.image_url" />
                          <VIcon v-else icon="ri-image-line" color="grey" />
                        </VAvatar>
                      </template>
                      <VListItemTitle class="font-weight-bold text-body-2">
                        🎁 {{ p.name }} • Количество: <strong>{{ p.qty }} шт.</strong>
                      </VListItemTitle>
                      <template #append>
                        <VBtn icon="ri-image-add-line" size="x-small" color="primary" variant="text" class="mr-1" @click="triggerPrizeItemUpload(idx)" title="Загрузить фото" />
                        <VBtn icon="ri-delete-bin-line" size="x-small" color="error" variant="text" @click="removePrizeFromForm(idx)" />
                      </template>
                    </VListItem>
                  </VList>
                  <div v-else class="text-caption text-muted text-center py-4">Добавьте хотя бы один приз</div>
                </VCard>
              </VCol>

              <!-- Настройка попыток -->
              <VCol cols="12" sm="4">
                <VTextField v-model.number="contestForm.start_attempts" label="Стартовые попытки" type="number" variant="outlined" class="mb-4" />
              </VCol>
              <VCol cols="12" sm="4">
                <VTextField v-model.number="contestForm.max_attempts" label="Лимит попыток (макс)" type="number" variant="outlined" class="mb-4" />
              </VCol>
              <VCol cols="12" sm="4">
                <VTextField v-model.number="contestForm.delay_between_moves" label="Кулдаун ходов (сек)" type="number" variant="outlined" class="mb-4" />
              </VCol>

              <VCol cols="12" sm="4">
                <VTextField v-model.number="contestForm.like_attempts" label="Попыток за лайк поста" type="number" variant="outlined" class="mb-4" />
              </VCol>
              <VCol cols="12" sm="4">
            <VTextField v-model.number="contestForm.repost_attempts" label="Попыток за репост" type="number" variant="outlined" class="mb-4" />
              </VCol>
              <VCol cols="12" sm="4">
                <VTextField v-model.number="contestForm.subscribe_attempts" label="Попыток за подписку" type="number" variant="outlined" class="mb-4" />
              </VCol>
            </VRow>

            <!-- Настройки ответов бота (сообщений) -->
            <VExpansionPanels class="mb-4">
              <VExpansionPanel>
                <VExpansionPanelTitle class="font-weight-bold">
                  💬 Настройка шаблонов ответов бота (сообщений)
                </VExpansionPanelTitle>
                <VExpansionPanelText class="pt-4">
                  <VRow>
                    <VCol cols="12">
                      <VTextField
                        v-model="contestForm.msg_miss"
                        label="Ответ бота при промахе / пустом секторе"
                        variant="outlined"
                        hint="Доступно: {name}, {cell} (координата ячейки/выстрела)"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12">
                      <VTextField
                        v-model="contestForm.msg_win"
                        label="Ответ бота при выигрыше (в комментариях)"
                        variant="outlined"
                        hint="Доступно: {name}, {prize}, {cell} (ячейка/выстрел)"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12">
                      <VTextField
                        v-model="contestForm.msg_out_of_attempts"
                        label="Ответ бота, когда закончились попытки"
                        variant="outlined"
                        hint="Доступно: {name}"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12">
                      <VTextField
                        v-model="contestForm.msg_cooldown"
                        label="Ответ бота при кулдауне ходов"
                        variant="outlined"
                        hint="Доступно: {name}, {cooldown} (оставшееся время в сек)"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12">
                      <VTextField
                        v-model="contestForm.msg_subscribe_needed"
                        label="Ответ бота при отсутствии подписки на группу"
                        variant="outlined"
                        hint="Доступно: {name}"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12">
                      <VTextField
                        v-model="contestForm.msg_like_needed"
                        label="Ответ бота при отсутствии лайка"
                        variant="outlined"
                        hint="Доступно: {name}"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12">
                      <VTextField
                        v-model="contestForm.msg_repost_needed"
                        label="Ответ бота при отсутствии репоста"
                        variant="outlined"
                        hint="Доступно: {name}"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12">
                      <VTextField
                        v-model="contestForm.msg_invalid_format"
                        label="Ответ бота при неверном формате хода"
                        variant="outlined"
                        hint="Доступно: {name}, {example} (пример правильного хода)"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12">
                      <VTextarea
                        v-model="contestForm.msg_pm_congratulations"
                        label="Сообщение в ЛС победителю с промокодом"
                        variant="outlined"
                        rows="4"
                        hint="Доступно: {name}, {title} (название конкурса), {prize}, {code} (уникальный промокод)"
                        persistent-hint
                        class="mb-4"
                      />
                    </VCol>
                  </VRow>
                </VExpansionPanelText>
              </VExpansionPanel>

              <VExpansionPanel>
                <VExpansionPanelTitle class="font-weight-bold">
                  ⚙️ Продвинутые настройки игры
                </VExpansionPanelTitle>
                <VExpansionPanelText class="pt-4">
                  <VRow>
                    <!-- Алгоритм выдачи -->
                    <VCol cols="12" sm="6">
                      <VSelect
                        v-model="contestForm.draw_type"
                        :items="[
                          { title: 'Указать вероятность выпадения приза', value: 'probability' },
                          { title: 'Указать продолжительность', value: 'duration' }
                        ]"
                        label="Алгоритм выдачи призов"
                        variant="outlined"
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12" sm="6">
                      <VTextField
                        v-if="contestForm.draw_type === 'probability'"
                        v-model.number="contestForm.draw_probability_interval"
                        label="Вероятность выпадения (примерно каждую N попытку)"
                        type="number"
                        variant="outlined"
                        hint="Например, 100 означает, что призы будут выпадать в среднем раз в 100 попыток (шанс 1%)"
                        persistent-hint
                        class="mb-4"
                      />
                      <div v-else class="text-caption text-muted py-2 mb-4">
                        Призы будут автоматически распределены равномерно по всему сроку проведения конкурса.
                      </div>
                    </VCol>

                    <!-- Переключатели правил -->
                    <VCol cols="12" sm="6">
                      <VSwitch
                        v-model="contestForm.can_win_once"
                        label="Можно выиграть только один раз"
                        color="primary"
                        hide-details
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12" sm="6">
                      <VSwitch
                        v-model="contestForm.help_draw_prizes"
                        label="Помочь разыграть призы при затягивании (автоускорение)"
                        color="primary"
                        hide-details
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12" sm="6">
                      <VSwitch
                        v-model="contestForm.anti_prize_hunters"
                        label="Включить защиту от призоловов"
                        color="primary"
                        hide-details
                        class="mb-4"
                      />
                    </VCol>
                    <VCol cols="12" sm="6">
                      <VSwitch
                        v-model="contestForm.remind_winner_pm"
                        label="Напоминать о незабранном призе в ЛС"
                        color="primary"
                        hide-details
                        class="mb-4"
                      />
                    </VCol>

                    <!-- Напоминания о попытках -->
                    <VCol cols="12">
                      <VCard variant="outlined" class="pa-4 mb-4">
                        <div class="d-flex align-center justify-space-between mb-2">
                          <h5 class="text-subtitle-2 font-weight-bold">Напоминания о неиспользованных попытках в комментариях</h5>
                          <VSwitch v-model="contestForm.remind_attempts" color="success" hide-details />
                        </div>
                        <div v-if="contestForm.remind_attempts" class="mt-4">
                          <VRow>
                            <VCol cols="12" sm="4">
                              <VSelect
                                v-model.number="contestForm.remind_attempts_count"
                                :items="[1, 2, 3]"
                                label="Сколько раз напомнить"
                                variant="outlined"
                              />
                            </VCol>
                            <VCol cols="12" sm="4">
                              <VTextField
                                v-model.number="contestForm.remind_attempts_quiet_from"
                                label="Тихий час: Не писать от (час, МСК)"
                                type="number"
                                min="0"
                                max="23"
                                variant="outlined"
                              />
                            </VCol>
                            <VCol cols="12" sm="4">
                              <VTextField
                                v-model.number="contestForm.remind_attempts_quiet_to"
                                label="Тихий час: Не писать до (час, МСК)"
                                type="number"
                                min="0"
                                max="23"
                                variant="outlined"
                              />
                            </VCol>
                          </VRow>
                          <div class="text-caption text-muted mt-2">
                            Первое напоминание придет через 10 минут, второе – через 30 минут, третье – через 3 часа после последнего хода игрока.
                          </div>
                        </div>
                      </VCard>
                    </VCol>

                    <!-- Черный и белый списки -->
                    <VCol cols="12" sm="6">
                      <VTextarea
                        v-model="blackListText"
                        label="Черный список пользователей (ID или ссылки через запятую)"
                        variant="outlined"
                        rows="3"
                        hint="Игрокам из черного списка бот не будет давать играть."
                        persistent-hint
                      />
                    </VCol>
                    <VCol cols="12" sm="6">
                      <VTextarea
                        v-model="whiteListText"
                        label="Белый список пользователей (ID или ссылки через запятую)"
                        variant="outlined"
                        rows="3"
                        hint="Если не пустой, играть смогут ТОЛЬКО пользователи из списка."
                        persistent-hint
                      />
                    </VCol>
                  </VRow>
                </VExpansionPanelText>
              </VExpansionPanel>
            </VExpansionPanels>

            <div class="d-flex justify-end gap-2 mt-4">
              <VBtn color="secondary" variant="outlined" @click="activeContestTab = 'list'">Отмена</VBtn>
              <VBtn color="success" prepend-icon="ri-save-line" :loading="savingContest" @click="saveContestSettings">Сохранить черновик</VBtn>
            </div>
          </div>

          <!-- Вкладка 3: Список участников -->
          <div v-else-if="activeContestTab === 'players'">
            <div class="d-flex align-center justify-space-between mb-4">
              <h3 class="text-subtitle-1 font-weight-bold">Список участников</h3>
              <VBtn variant="outlined" size="small" prepend-icon="ri-arrow-left-line" @click="activeContestTab = 'list'">
                Назад к списку
              </VBtn>
            </div>

            <VDataTable
              :headers="[
                { title: 'Имя Фамилия', key: 'name' },
                { title: 'Попыток осталось', key: 'attempts_left' },
                { title: 'Попыток сделано', key: 'attempts_used' },
                { title: 'Репост / Лайк', key: 'activity' },
                { title: 'Последний ход', key: 'last_move_at' }
              ]"
              :items="contestPlayers"
              density="comfortable"
              no-data-text="Участников пока нет"
            >
              <template #item.name="{ item }">
                <a :href="`https://vk.com/id${item.vk_user_id}`" target="_blank" class="text-primary text-decoration-none font-weight-bold">
                  {{ item.first_name }} {{ item.last_name }}
                </a>
              </template>
              <template #item.activity="{ item }">
                <span class="me-2">{{ item.repost_done ? '📢 Репост' : '' }}</span>
                <span>{{ item.like_done ? '❤️ Лайк' : '' }}</span>
              </template>
              <template #item.last_move_at="{ item }">
                {{ item.last_move_at ? new Date(item.last_move_at).toLocaleString() : '—' }}
              </template>
            </VDataTable>
          </div>

          <!-- Вкладка 4: Список победителей -->
          <div v-else-if="activeContestTab === 'winners'">
            <div class="d-flex align-center justify-space-between mb-4">
              <h3 class="text-subtitle-1 font-weight-bold">Список победителей и промокодов</h3>
              <VBtn variant="outlined" size="small" prepend-icon="ri-arrow-left-line" @click="activeContestTab = 'list'">
                Назад к списку
              </VBtn>
            </div>

            <VDataTable
              :headers="[
                { title: 'Победитель', key: 'name' },
                { title: 'Приз', key: 'prize_name' },
                { title: 'Промокод для iiko', key: 'win_code' },
                { title: 'Дата выигрыша', key: 'won_at' }
              ]"
              :items="contestWinners"
              density="comfortable"
              no-data-text="Победителей пока нет"
            >
              <template #item.name="{ item }">
                <a :href="`https://vk.com/id${item.vk_user_id}`" target="_blank" class="text-primary text-decoration-none font-weight-bold">
                  {{ item.first_name }} {{ item.last_name }}
                </a>
              </template>
              <template #item.win_code="{ item }">
                <VChip color="success" size="small" class="font-weight-bold">{{ item.win_code }}</VChip>
              </template>
              <template #item.won_at="{ item }">
                {{ new Date(item.won_at).toLocaleString() }}
              </template>
            </VDataTable>
          </div>

          <!-- Вкладка 5: Детальная статистика конкурса -->
          <div v-else-if="activeContestTab === 'stats'">
            <!-- Панель выбора конкурса -->
            <div class="d-flex align-center justify-space-between mb-5 flex-wrap gap-3">
              <div class="d-flex align-center gap-3" style="min-width: 350px;">
                <span class="text-subtitle-2 font-weight-bold text-no-wrap">Конкурс:</span>
                <VSelect
                  v-model="statsContestId"
                  :items="contestList"
                  item-title="title"
                  item-value="id"
                  variant="outlined"
                  density="compact"
                  hide-details
                  placeholder="Выберите конкурс для просмотра статистики"
                />
              </div>
              <VBtn variant="outlined" size="small" prepend-icon="ri-arrow-left-line" @click="activeContestTab = 'list'">
                Назад к списку
              </VBtn>
            </div>

            <div v-if="statsContestId">
              <!-- Карточки суммарных показателей -->
              <VRow class="mb-5">
                <VCol cols="12" sm="3">
                  <VCard variant="outlined" class="pa-4 text-center">
                    <div class="text-caption text-muted mb-1">Всего участников</div>
                    <div class="text-h5 font-weight-bold text-primary">{{ statsPlayers.length }}</div>
                  </VCard>
                </VCol>
                <VCol cols="12" sm="3">
                  <VCard variant="outlined" class="pa-4 text-center">
                    <div class="text-caption text-muted mb-1">Сделано ходов</div>
                    <div class="text-h5 font-weight-bold text-info">
                      {{ statsActions.filter(a => a.action_type === 'move').length }}
                    </div>
                  </VCard>
                </VCol>
                <VCol cols="12" sm="3">
                  <VCard variant="outlined" class="pa-4 text-center">
                    <div class="text-caption text-muted mb-1">Выиграно призов</div>
                    <div class="text-h5 font-weight-bold text-success">{{ statsWinners.length }}</div>
                  </VCard>
                </VCol>
                <VCol cols="12" sm="3">
                  <VCard variant="outlined" class="pa-4 text-center">
                    <div class="text-caption text-muted mb-1">Активировано промокодов</div>
                    <div class="text-h5 font-weight-bold text-warning">
                      {{ statsWinners.filter(w => w.is_activated).length }}
                    </div>
                  </VCard>
                </VCol>
              </VRow>

              <!-- Навигация подразделов статистики -->
              <VTabs v-model="activeStatsSubTab" class="mb-4" density="comfortable">
                <VTab value="actions" prepend-icon="ri-history-line">Ходы и действия</VTab>
                <VTab value="players" prepend-icon="ri-group-line">Участники</VTab>
                <VTab value="winners" prepend-icon="ri-medal-line">Победители</VTab>
              </VTabs>

              <!-- Контент подразделов -->
              <VWindow v-model="activeStatsSubTab">
                <!-- Подвкладка: Ходы и действия -->
                <VWindowItem value="actions">
                  <VDataTable
                    :headers="[
                      { title: 'Игрок', key: 'player' },
                      { title: 'Тип действия', key: 'action_type' },
                      { title: 'Детали действия', key: 'detail' },
                      { title: 'Время', key: 'created_at' }
                    ]"
                    :items="statsActions"
                    :loading="loadingStats"
                    density="comfortable"
                    no-data-text="Действий игроков пока не зафиксировано"
                  >
                    <template #item.player="{ item }">
                      <a :href="`https://vk.com/id${item.vk_user_id}`" target="_blank" class="text-primary text-decoration-none font-weight-bold">
                        {{ item.first_name }} {{ item.last_name }}
                      </a>
                    </template>
                    <template #item.action_type="{ item }">
                      <VChip
                        :color="item.action_type === 'move' ? 'primary' : (item.action_type === 'reward' ? 'success' : (item.action_type === 'system' ? 'warning' : 'secondary'))"
                        size="x-small"
                        class="font-weight-bold text-uppercase"
                      >
                        {{ item.action_type === 'move' ? 'Ход' : (item.action_type === 'reward' ? 'Бонус' : (item.action_type === 'system' ? 'Системное' : item.action_type)) }}
                      </VChip>
                    </template>
                    <template #item.created_at="{ item }">
                      {{ new Date(item.created_at).toLocaleString() }}
                    </template>
                  </VDataTable>
                </VWindowItem>

                <!-- Подвкладка: Участники -->
                <VWindowItem value="players">
                  <VDataTable
                    :headers="[
                      { title: 'Участник', key: 'player' },
                      { title: 'Использовано ходов', key: 'attempts_used' },
                      { title: 'Осталось ходов', key: 'attempts_left' },
                      { title: 'Активность', key: 'activity' },
                      { title: 'Статус', key: 'is_game_over' },
                      { title: 'Последнее действие', key: 'last_move_at' }
                    ]"
                    :items="statsPlayers"
                    :loading="loadingStats"
                    density="comfortable"
                    no-data-text="Участников пока нет"
                  >
                    <template #item.player="{ item }">
                      <a :href="`https://vk.com/id${item.vk_user_id}`" target="_blank" class="text-primary text-decoration-none font-weight-bold">
                        {{ item.first_name }} {{ item.last_name }}
                      </a>
                    </template>
                    <template #item.activity="{ item }">
                      <div class="d-flex gap-1 flex-wrap">
                        <VChip v-if="item.like_done" color="error" size="x-small" variant="tonal">❤️ Лайк</VChip>
                        <VChip v-if="item.repost_done" color="success" size="x-small" variant="tonal">📢 Репост</VChip>
                        <VChip v-if="item.subscribe_done" color="info" size="x-small" variant="tonal">🔔 Подписка</VChip>
                      </div>
                    </template>
                    <template #item.is_game_over="{ item }">
                      <VChip :color="item.is_game_over ? 'error' : 'success'" size="x-small" class="font-weight-bold">
                        {{ item.is_game_over ? 'GAME OVER' : 'Активен' }}
                      </VChip>
                    </template>
                    <template #item.last_move_at="{ item }">
                      {{ item.last_move_at ? new Date(item.last_move_at).toLocaleString() : '—' }}
                    </template>
                  </VDataTable>
                </VWindowItem>

                <!-- Подвкладка: Победители -->
                <VWindowItem value="winners">
                  <VDataTable
                    :headers="[
                      { title: 'Победитель', key: 'player' },
                      { title: 'Приз', key: 'prize_name' },
                      { title: 'Код получения', key: 'win_code' },
                      { title: 'Статус промокода', key: 'status' },
                      { title: 'Время выигрыша', key: 'won_at' }
                    ]"
                    :items="statsWinners"
                    :loading="loadingStats"
                    density="comfortable"
                    no-data-text="Победителей пока нет"
                  >
                    <template #item.player="{ item }">
                      <a :href="`https://vk.com/id${item.vk_user_id}`" target="_blank" class="text-primary text-decoration-none font-weight-bold">
                        {{ item.first_name }} {{ item.last_name }}
                      </a>
                    </template>
                    <template #item.win_code="{ item }">
                      <VChip color="primary" size="small" class="font-weight-bold">{{ item.win_code }}</VChip>
                    </template>
                    <template #item.status="{ item }">
                      <div class="d-flex align-center gap-1">
                        <VChip :color="item.is_activated ? 'success' : 'warning'" size="x-small" class="font-weight-bold">
                          {{ item.is_activated ? 'Применен' : 'Ожидает активации' }}
                        </VChip>
                        <span v-if="item.is_activated" class="text-caption text-muted">
                          (Заказ: {{ item.order_id || '—' }})
                        </span>
                      </div>
                    </template>
                    <template #item.won_at="{ item }">
                      {{ new Date(item.won_at).toLocaleString() }}
                    </template>
                  </VDataTable>
                </VWindowItem>
              </VWindow>
            </div>
            <div v-else class="text-center py-8 text-muted">
              Нет созданных конкурсов для вывода статистики
            </div>
          </div>

        </VCardText>
        <VDivider />
        <VCardActions class="pa-5 bg-surface border-t">
          <VBtn color="secondary" variant="outlined" class="ms-auto" @click="showContestSettingsDialog = false">
            Закрыть
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО НАСТРОЕК БОТА АКТИВНОСТИ -->
    <VDialog v-model="showActivitySettingsDialog" max-width="950px" scrollable persistent>
      <VCard class="rounded-xl">
        <VCardTitle class="d-flex align-center justify-space-between pa-5 bg-surface border-b">
          <div class="d-flex align-center">
            <div class="bg-info-lighten rounded-lg pa-2 me-3">
              <VIcon icon="ri-radar-line" color="info" size="24" />
            </div>
            <div>
              <span class="text-h6 font-weight-bold d-block">Рейтинг активности сообщества</span>
              <span class="text-caption text-muted">Сообщество: {{ connections.find(c => c.id === selectedConnectionId)?.name }}</span>
            </div>
          </div>
          <VBtn icon="ri-close-line" variant="text" color="secondary" density="comfortable" @click="showActivitySettingsDialog = false" />
        </VCardTitle>

        <VTabs v-model="activeActivityTab" bg-color="surface" class="border-b" color="info">
          <VTab value="settings"><VIcon icon="ri-settings-4-line" class="me-2" />Основные</VTab>
          <VTab value="rules_like"><VIcon icon="ri-heart-line" class="me-2" />Лайки</VTab>
          <VTab value="rules_comment"><VIcon icon="ri-chat-3-line" class="me-2" />Комментарии</VTab>
          <VTab value="rules_other"><VIcon icon="ri-share-line" class="me-2" />Другое</VTab>
          <VTab value="rules_penalty"><VIcon icon="ri-error-warning-line" class="me-2" />Штрафы</VTab>
          <VTab value="messages"><VIcon icon="ri-message-3-line" class="me-2" />Тексты сообщений</VTab>
          <VTab value="iiko"><VIcon icon="ri-bank-card-line" class="me-2" />iikoCard</VTab>
          <VTab value="ranking"><VIcon icon="ri-trophy-line" class="me-2" />Рейтинг</VTab>
        </VTabs>

        <VCardText class="pa-6" style="max-height: 70vh;">
          <div v-if="loadingActivity" class="text-center py-12">
            <VProgressCircular indeterminate color="info" size="48" />
            <span class="d-block mt-2 text-muted">Загрузка настроек...</span>
          </div>
          
          <div v-else>
            <!-- ТАБ 1: ОСНОВНЫЕ -->
            <div v-if="activeActivityTab === 'settings'">
              <div class="d-flex align-center justify-space-between mb-6 bg-light rounded-xl pa-4">
                <div>
                  <span class="text-subtitle-1 font-weight-bold d-block">Запуск подсчета баллов</span>
                  <span class="text-caption text-muted">Включите для начала начисления баллов за новые активности</span>
                </div>
                <VSwitch v-model="activityForm.is_active" color="success" hide-details />
              </div>

              <!-- Поле индивидуального API-ключа -->
              <div class="mb-6 bg-light rounded-xl pa-4">
                <span class="font-weight-bold d-block mb-1">Индивидуальный ключ доступа сообщества</span>
                <span class="text-caption text-muted d-block mb-3">
                  Позволяет использовать отдельный токен для работы этого конкретного бота. Если поле пустое, будет использоваться токен основного подключения.
                  <a :href="getVkTokenUrl()" target="_blank" class="text-primary font-weight-bold text-decoration-none d-inline-block ms-1">Получить токен сообщества автоматически ↗</a>
                </span>
                <VTextField
                  v-model="activityForm.vk_bot_token"
                  label="API-ключ сообщества ВК (Токен)"
                  placeholder="Вставьте токен vk1.a.***"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  type="password"
                />
              </div>

              <VRow>
                <VCol cols="12" sm="6">
                  <VTextField 
                    v-model="activityForm.period_start_date" 
                    label="Дата и время старта конкурса" 
                    variant="outlined" 
                    type="datetime-local" 
                    hint="Баллы будут начисляться только за активности к постам, опубликованным после этой даты"
                    persistent-hint
                  />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField 
                    v-model.number="activityForm.period_duration_days" 
                    label="Продолжительность конкурса (в днях)" 
                    variant="outlined" 
                    type="number"
                    suffix="дн"
                    hint="Укажите 0 для бессрочного подсчета"
                    persistent-hint
                  />
                </VCol>
              </VRow>

              <VRow class="mt-2">
                <VCol cols="12" sm="6">
                  <VTextField 
                    v-model.number="activityForm.post_max_age_days" 
                    label="Срок давности постов (в днях)" 
                    variant="outlined" 
                    type="number"
                    suffix="дн"
                    hint="Посты старше этого кол-ва дней НЕ участвуют в программе. Укажите 0 для участия всех постов."
                    persistent-hint
                  />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField 
                    v-model="activityForm.override_keywords" 
                    label="Ключевые слова-исключения (участвуют всегда)" 
                    placeholder="акция, подарок, первокоммент"
                    variant="outlined" 
                    hint="Посты с этими словами участвуют в начислении НЕЗАВИСИМО от срока давности (через запятую)."
                    persistent-hint
                  />
                </VCol>
              </VRow>

              <VRow class="mt-4">
                <VCol cols="12">
                  <VTextarea
                    v-model="activityForm.ignored_post_ids"
                    label="Игнорируемые ID постов"
                    variant="outlined"
                    rows="2"
                    hint="Список ID постов ВК через запятую, за действия под которыми баллы НЕ будут начисляться (например: 1243, 1566, 1899)"
                    persistent-hint
                  />
                </VCol>
              </VRow>
            </div>

            <!-- ТАБ 2: ЛАЙКИ -->
            <div v-if="activeActivityTab === 'rules_like'">
              <span class="text-subtitle-1 font-weight-bold mb-4 d-block">Правила начисления за лайки постов</span>
              <VRow>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.points_like" label="Базовый балл за лайк" variant="outlined" type="number" />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.points_like_fast" label="Балл за быстрый лайк" variant="outlined" type="number" />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.like_fast_seconds" label="Интервал быстрого лайка (в сек)" variant="outlined" type="number" suffix="сек" />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField v-model.number="activityForm.points_like_first_n" label="Балл первым N лайкнувшим" variant="outlined" type="number" />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField v-model.number="activityForm.like_first_n_count" label="Количество первых лайкнувших (N)" variant="outlined" type="number" suffix="чел" />
                </VCol>
              </VRow>
            </div>

            <!-- ТАБ 3: КОММЕНТАРИИ -->
            <div v-if="activeActivityTab === 'rules_comment'">
              <span class="text-subtitle-1 font-weight-bold mb-4 d-block">Правила начисления за комментарии</span>
              <VRow>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.points_comment" label="Базовый балл за коммент" variant="outlined" type="number" />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.points_comment_fast" label="Балл за быстрый коммент" variant="outlined" type="number" />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.comment_fast_seconds" label="Интервал быстрого коммента" variant="outlined" type="number" suffix="сек" />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField v-model.number="activityForm.points_comment_first_n" label="Балл первым N комментаторам" variant="outlined" type="number" />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField v-model.number="activityForm.comment_first_n_count" label="Количество первых комментаторов (N)" variant="outlined" type="number" suffix="чел" />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField v-model.number="activityForm.min_comment_length" label="Минимальная длина (в символах)" variant="outlined" type="number" suffix="симв" />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField v-model.number="activityForm.max_comments_per_post" label="Лимит комментов на один пост" variant="outlined" type="number" suffix="шт" />
                </VCol>
                <VCol cols="12" sm="6" class="py-1">
                  <VCheckbox v-model="activityForm.ignore_consecutive_comments" label="Игнорировать комменты подряд от одного лица" color="info" hide-details />
                </VCol>
                <VCol cols="12" sm="6" class="py-1">
                  <VCheckbox v-model="activityForm.ignore_stickers" label="Игнорировать комментарии со стикерами" color="info" hide-details />
                </VCol>
              </VRow>
            </div>

            <!-- ТАБ 4: ДРУГОЕ -->
            <div v-if="activeActivityTab === 'rules_other'">
              <span class="text-subtitle-1 font-weight-bold mb-4 d-block">Репосты, опросы и подписки</span>
              <VRow>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.points_repost" label="Балл за репост поста на стену" variant="outlined" type="number" />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.points_poll" label="Балл за участие в опросе" variant="outlined" type="number" />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField v-model.number="activityForm.points_join" label="Балл за вступление в группу" variant="outlined" type="number" />
                </VCol>
              </VRow>
            </div>

            <!-- ТАБ: ШТРАФЫ -->
            <div v-if="activeActivityTab === 'rules_penalty'">
              <span class="text-subtitle-1 font-weight-bold mb-1 d-block">Штрафы за отмену активности</span>
              <span class="text-caption text-muted d-block mb-4">
                Настройки штрафного таймера и баллов при выходе из группы, убирании лайка, удалении репоста или комментария. Во время действия таймера за повторные действия начисляется штрафное количество баллов и отправляется специальное сообщение.
              </span>
              <VRow>
                <VCol cols="12" sm="6">
                  <VTextField 
                    v-model.number="activityForm.penalty_duration_seconds" 
                    label="Время действия штрафного таймера (в секундах)" 
                    variant="outlined" 
                    type="number"
                    hint="Повторные действия с постом или группой в этот период будут считаться штрафными"
                    persistent-hint
                  />
                </VCol>
                <VCol cols="12" sm="6">
                  <VTextField 
                    v-model.number="activityForm.penalty_points" 
                    label="Штрафные баллы за повторные действия" 
                    variant="outlined" 
                    type="number"
                    hint="Количество баллов, начисляемое за повторное действие в штрафной период (по умолчанию 0)"
                    persistent-hint
                  />
                </VCol>
                <VCol cols="12" class="mt-4">
                  <VTextarea
                    v-model="activityForm.msg_penalty"
                    label="Текст уведомления о штрафном времени и баллах"
                    placeholder="⚠️ Вы совершили повторное действие во время действия штрафа. Начислено баллов: {points}. Штрафной период активен."
                    variant="outlined"
                    rows="3"
                    hint="Оставьте пустым для использования стандартного текста. Доступны плейсхолдеры: {points}."
                    persistent-hint
                  />
                </VCol>
              </VRow>
            </div>

            <!-- ТАБ: ТЕКСТЫ СООБЩЕНИЙ -->
            <div v-if="activeActivityTab === 'messages'">
              <span class="text-subtitle-1 font-weight-bold mb-1 d-block">Настройка информационных сообщений бота</span>
              <span class="text-caption text-muted mb-4 d-block">В текстах доступна подстановка тегов: <b>{points}</b> (начислено баллов), <b>{balance}</b> (баланс), <b>{reason}</b> (причина), <b>{vk_points}</b> (набранные баллы ВК).</span>
              
              <VRow>
                <VCol cols="12">
                  <VTextarea
                    v-model="activityForm.msg_points_like"
                    label="Уведомление за лайк"
                    placeholder="❤️ Вам начислено {points} баллов за лайк к посту{reason}! Ваш баланс активности: {balance} баллов."
                    variant="outlined"
                    rows="2"
                    hint="Оставьте пустым для использования стандартного текста"
                    persistent-hint
                  />
                </VCol>

                <VCol cols="12">
                  <VTextarea
                    v-model="activityForm.msg_points_comment"
                    label="Уведомление за комментарий"
                    placeholder="💬 Вам начислено {points} баллов за комментарий к посту{reason}! Ваш баланс активности: {balance} баллов."
                    variant="outlined"
                    rows="2"
                    hint="Оставьте пустым для использования стандартного текста"
                    persistent-hint
                  />
                </VCol>

                <VCol cols="12">
                  <VTextarea
                    v-model="activityForm.msg_points_repost"
                    label="Уведомление за репост"
                    placeholder="📢 Вам начислено {points} баллов за репост нашей записи! Ваш баланс активности: {balance} баллов."
                    variant="outlined"
                    rows="2"
                    hint="Оставьте пустым для использования стандартного текста"
                    persistent-hint
                  />
                </VCol>

                <VCol cols="12">
                  <VTextarea
                    v-model="activityForm.msg_points_poll"
                    label="Уведомление за опрос"
                    placeholder="🗳 Вам начислено {points} баллов за участие в опросе! Ваш баланс активности: {balance} баллов."
                    variant="outlined"
                    rows="2"
                    hint="Оставьте пустым для использования стандартного текста"
                    persistent-hint
                  />
                </VCol>

                <VCol cols="12">
                  <VTextarea
                    v-model="activityForm.msg_points_join"
                    label="Уведомление за подписку / вступление"
                    placeholder="🎉 Вам начислено {points} баллов за подписку на наше сообщество! Ваш баланс активности: {balance} баллов."
                    variant="outlined"
                    rows="2"
                    hint="Оставьте пустым для использования стандартного текста"
                    persistent-hint
                  />
                </VCol>

                <VCol cols="12">
                  <VTextarea
                    v-model="activityForm.msg_balance_info"
                    label="Текст ответа на запрос баланса"
                    placeholder="Ваш бонусный баланс: {balance} бонусов."
                    variant="outlined"
                    rows="2"
                    hint="Оставьте пустым для использования стандартного текста"
                    persistent-hint
                  />
                </VCol>

                <VCol cols="12">
                  <VTextarea
                    v-model="activityForm.msg_unlinked_notice"
                    label="Подсказка для непривязанных клиентов при старте"
                    placeholder="У вас накоплено {vk_points} баллов активности ВК! 🎁 Привяжите номер телефона, чтобы перенести их на карту iikoCard и получить единый бонусный баланс."
                    variant="outlined"
                    rows="2"
                    hint="Оставьте пустым для использования стандартного текста"
                    persistent-hint
                  />
                </VCol>
              </VRow>
            </div>

            <!-- ТАБ 5: IIKO -->
            <div v-if="activeActivityTab === 'iiko'">
              <div class="d-flex align-center justify-space-between mb-6 bg-light rounded-xl pa-4">
                <div>
                  <span class="text-subtitle-1 font-weight-bold d-block">Синхронизация с iikoCard</span>
                  <span class="text-caption text-muted">Конвертировать баллы в реальные бонусы iikoCard для связанных гостей</span>
                </div>
                <VSwitch v-model="activityForm.sync_with_iiko" color="info" hide-details />
              </div>

              <VRow v-if="activityForm.sync_with_iiko">
                <VCol cols="12" sm="6">
                  <VTextField 
                    v-model.number="activityForm.iiko_conversion_rate" 
                    label="Курс конвертации (1 балл = X бонусов iiko)" 
                    variant="outlined" 
                    type="number"
                    step="0.1"
                  />
                </VCol>
                <VCol cols="12" sm="6" class="d-flex align-center">
                  <div class="text-caption text-muted">
                    При курсе 1.0 за каждый начисленный балл активности гость получит 1 бонус в iiko. При курсе 0.1 - 10 баллов активности = 1 бонус.
                  </div>
                </VCol>

                <!-- Детальные настройки синхронизации и суммирования -->
                <VCol cols="12" sm="6">
                  <VSelect
                    v-model="activityForm.iiko_sync_mode"
                    :items="[
                      { title: 'В реальном времени (при каждом действии)', value: 'realtime' },
                      { title: 'Вручную / По расписанию', value: 'manual' }
                    ]"
                    label="Режим синхронизации баллов"
                    variant="outlined"
                  />
                </VCol>
                <VCol cols="12" sm="6">
                  <VSelect
                    v-model="activityForm.iiko_summing_logic"
                    :items="[
                      { title: 'Суммировать (iikoCard + ВК активность)', value: 'both' },
                      { title: 'Только бонусы iikoCard', value: 'iiko_only' },
                      { title: 'Только баллы активности ВК', value: 'vk_only' }
                    ]"
                    label="Логика отображения баланса гостю"
                    variant="outlined"
                  />
                </VCol>

                <VCol cols="12" sm="6" class="d-flex align-center">
                  <div class="border rounded-xl pa-4 w-100 d-flex align-center justify-space-between">
                    <div>
                      <span class="font-weight-bold d-block text-body-2">Синхронизировать при верификации</span>
                      <span class="text-caption text-muted">Переводить накопленные баллы в iikoCard при привязке телефона</span>
                    </div>
                    <VSwitch v-model="activityForm.sync_on_verification" color="info" hide-details />
                  </div>
                </VCol>

                <VCol cols="12" sm="6" class="d-flex align-center">
                  <div class="border rounded-xl pa-4 w-100 d-flex align-center justify-space-between">
                    <div>
                      <span class="font-weight-bold d-block text-body-2">Синхронизировать при запросе баланса</span>
                      <span class="text-caption text-muted">Отправлять несинхронизированные баллы при проверке баланса в боте</span>
                    </div>
                    <VSwitch v-model="activityForm.sync_on_balance_request" color="info" hide-details />
                  </div>
                </VCol>

                <VCol cols="12" class="d-flex align-center justify-space-between mt-4 pa-4 border rounded-xl">
                  <div>
                    <span class="font-weight-bold d-block text-body-1">Ручная синхронизация балансов</span>
                    <span class="text-caption text-muted d-block" v-if="activityForm.last_sync_at">Последний раз запускалась: {{ new Date(activityForm.last_sync_at).toLocaleString() }}</span>
                    <span class="text-caption text-muted d-block" v-else>Синхронизация еще не проводилась</span>
                  </div>
                  <VBtn 
                    color="info" 
                    prepend-icon="ri-refresh-line" 
                    :loading="syncingIiko" 
                    @click="syncActivityIiko"
                  >
                    Запустить синхронизацию
                  </VBtn>
                </VCol>
              </VRow>
            </div>

            <!-- ТАБ 6: РЕЙТИНГ -->
            <div v-if="activeActivityTab === 'ranking'">
              <div class="d-flex align-center justify-space-between mb-4">
                <div>
                  <h3 class="text-subtitle-1 font-weight-bold">Рейтинг участников</h3>
                  <span class="text-caption text-muted">Общее количество участников: {{ activityRanking.length }}</span>
                </div>
                <div class="d-flex align-center" style="gap: 12px; width: 60%; max-width: 500px;">
                  <VTextField
                    v-model="ratingSearch"
                    placeholder="Поиск по имени, VK, телефону..."
                    density="compact"
                    variant="outlined"
                    hide-details
                    prepend-inner-icon="ri-search-line"
                    clearable
                  />
                  <VBtn 
                    color="error" 
                    variant="outlined" 
                    size="small" 
                    prepend-icon="ri-delete-bin-line"
                    :loading="resettingActivity"
                    @click="resetActivity"
                    style="flex-shrink: 0;"
                  >
                    Сбросить рейтинг
                  </VBtn>
                </div>
              </div>

              <VDataTable
                v-model:expanded="expandedItems"
                show-expand
                :search="ratingSearch"
                :headers="[
                  { title: '', key: 'data-table-expand' },
                  { title: 'Участник', key: 'user' },
                  { title: 'Баллы ВК', key: 'points', sortable: true },
                  { title: 'Бонусы iiko', key: 'iiko_balance', sortable: true },
                  { title: 'Синхр.', key: 'synced_points', sortable: true },
                  { title: 'Итого', key: 'total_balance', sortable: true },
                  { title: 'Статус iiko', key: 'is_synced_to_iiko', sortable: true },
                  { title: 'Лайки', key: 'likes', sortable: true },
                  { title: 'Комменты', key: 'comments', sortable: true },
                  { title: 'Репосты', key: 'reposts', sortable: true },
                  { title: 'iiko телефон', key: 'phone' },
                  { title: 'Действия', key: 'actions', sortable: false }
                ]"
                :items="activityRanking"
                density="comfortable"
                no-data-text="Участники пока не набрали баллов"
              >
                <template #item.user="{ item }">
                  <div class="d-flex align-center py-2">
                    <VAvatar size="36" class="me-3" v-if="item.photo_50">
                      <VImg :src="item.photo_50" />
                    </VAvatar>
                    <VAvatar size="36" color="secondary" class="me-3 font-weight-bold text-caption" v-else>
                      👤
                    </VAvatar>
                    <div>
                      <a :href="`https://vk.com/${item.screen_name || 'id' + item.vk_id}`" target="_blank" class="font-weight-bold text-decoration-none text-primary d-block">
                        {{ item.first_name }} {{ item.last_name }}
                      </a>
                      <span class="text-caption text-muted" v-if="item.customer_name">Карта гостя: {{ item.customer_name }}</span>
                    </div>
                  </div>
                </template>
                <template #item.points="{ item }">
                  <VChip color="info" size="small" class="font-weight-bold">
                    {{ item.points }}
                  </VChip>
                </template>
                <template #item.iiko_balance="{ item }">
                  <span v-if="item.is_linked" class="text-body-2 font-weight-bold text-info">
                    {{ item.iiko_balance }}
                  </span>
                  <span v-else class="text-muted text-caption">-</span>
                </template>
                <template #item.synced_points="{ item }">
                  <span v-if="item.is_linked" class="text-body-2 text-success font-weight-bold">
                    {{ item.synced_points }}
                  </span>
                  <span v-else class="text-muted text-caption">-</span>
                </template>
                <template #item.total_balance="{ item }">
                  <VChip v-if="item.is_linked" color="primary" size="small" class="font-weight-bold">
                    {{ item.total_balance }}
                  </VChip>
                  <span v-else class="text-muted text-caption">-</span>
                </template>
                <template #item.is_synced_to_iiko="{ item }">
                  <div class="d-flex align-center justify-center">
                    <VIcon v-if="item.is_linked && item.is_synced_to_iiko" icon="ri-checkbox-circle-line" color="success" size="20" title="Все баллы добавлены в iikoCard" />
                    <VIcon v-else-if="item.is_linked && !item.is_synced_to_iiko" icon="ri-error-warning-line" color="warning" size="20" title="Ожидает синхронизации дельты баллов" />
                    <VIcon v-else icon="ri-close-circle-line" color="secondary" size="20" title="Профиль не привязан к карте гостя" />
                  </div>
                </template>
                <template #item.phone="{ item }">
                  <span v-if="item.is_linked" class="text-body-2 font-weight-bold">{{ item.phone }}</span>
                  <VChip v-else size="x-small" color="secondary" variant="tonal">Не привязан</VChip>
                </template>
                <template #item.actions="{ item }">
                  <div class="d-flex gap-1 align-center">
                    <VBtn icon="ri-history-line" size="x-small" color="info" variant="tonal" title="История начислений" @click="openUserHistory(item)" />
                    <VBtn icon="ri-refresh-line" size="x-small" color="primary" variant="text" title="Синхронизировать с iiko" @click="syncUserPointsToIiko(item.vk_id)" :disabled="!item.is_linked" />
                    <VBtn icon="ri-bank-card-line" size="x-small" color="warning" variant="text" title="Принудительно перевести баллы в бонусы (с обнулением ВК)" @click="transferUserPointsToIiko(item.vk_id)" :disabled="!item.is_linked || item.points <= 0" />
                    <VBtn icon="ri-add-line" size="x-small" color="success" variant="text" title="Добавить 10 баллов" @click="adjustUserPoints(item.vk_id, 10)" />
                    <VBtn icon="ri-subtract-line" size="x-small" color="warning" variant="text" title="Снять 10 баллов" @click="adjustUserPoints(item.vk_id, -10)" :disabled="item.points <= 0" />
                  </div>
                </template>
                
                <template #expanded-row="{ columns, item }">
                  <tr>
                    <td :colspan="columns.length" class="pa-4 bg-light-gray" style="background-color: rgba(var(--v-theme-surface), 0.05);">
                      <VRow>
                        <VCol cols="12" md="4">
                          <VCard variant="outlined" class="pa-3 bg-surface rounded-xl">
                            <div class="text-subtitle-2 font-weight-bold text-primary mb-2">Статистика активности</div>
                            <VDivider class="mb-2" />
                            <div class="d-flex justify-space-between mb-1">
                              <span class="text-body-2 text-muted">Лайков поставлено:</span>
                              <span class="font-weight-bold">{{ item.likes }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-1">
                              <span class="text-body-2 text-muted">Комментариев оставлено:</span>
                              <span class="font-weight-bold">{{ item.comments }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-1">
                              <span class="text-body-2 text-muted">Репостов сделано:</span>
                              <span class="font-weight-bold">{{ item.reposts }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-1">
                              <span class="text-body-2 text-muted">Курс iiko:</span>
                              <span class="font-weight-bold">1 балл = {{ item.iiko_conversion_rate }} руб</span>
                            </div>
                          </VCard>
                        </VCol>
                        <VCol cols="12" md="8">
                          <VCard variant="outlined" class="pa-3 bg-surface rounded-xl">
                            <div class="d-flex align-center justify-space-between mb-2">
                              <div class="text-subtitle-2 font-weight-bold text-primary">Последние действия (История)</div>
                              <VBtn size="x-small" variant="text" prepend-icon="ri-history-line" @click="openUserHistory(item)">
                                Открыть полную историю
                              </VBtn>
                            </div>
                            <VDivider class="mb-2" />
                            
                            <div v-if="loadingUserHistory && selectedUserForHistory?.vk_id === item.vk_id" class="text-center py-4">
                              <VProgressCircular indeterminate size="20" color="primary" />
                            </div>
                            <div v-else-if="selectedUserForHistory?.vk_id === item.vk_id && userHistoryData">
                              <div v-if="userHistoryData.history.length === 0" class="text-caption text-muted py-2 text-center">
                                История активностей пуста
                              </div>
                              <div v-else class="history-mini-timeline" style="max-height: 150px; overflow-y: auto;">
                                <div v-for="h in userHistoryData.history.slice(0, 5)" :key="h.id" class="d-flex justify-space-between text-body-2 mb-1 border-b pb-1">
                                  <div>
                                    <VChip size="x-small" :color="getActivityColor(h.action_type)" class="me-1 font-weight-bold" variant="tonal">
                                      {{ h.title }}
                                    </VChip>
                                    <span class="text-caption text-muted">{{ formatDate(h.created_at) }}</span>
                                  </div>
                                  <span :class="h.points >= 0 ? 'text-success font-weight-bold' : 'text-error font-weight-bold'">
                                    {{ h.points >= 0 ? '+' + h.points : h.points }}
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div v-else class="text-center py-4">
                              <VBtn size="small" variant="tonal" color="info" @click="loadHistoryForExpandedRow(item)">
                                Загрузить последние действия
                              </VBtn>
                            </div>
                          </VCard>
                        </VCol>
                      </VRow>
                    </td>
                  </tr>
                </template>
              </VDataTable>
            </div>
          </div>
        </VCardText>

        <VDivider />
        <VCardActions class="pa-5 bg-surface border-t d-flex justify-end">
          <VBtn color="secondary" variant="outlined" class="me-2" @click="showActivitySettingsDialog = false">Отмена</VBtn>
          <VBtn color="success" prepend-icon="ri-save-3-line" :loading="savingActivity" @click="saveActivitySettings" :disabled="loadingActivity">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО НАСТРОЕК БОТА ПЕРВОКОММЕНТ -->
    <VDialog v-model="showFirstCommentSettingsDialog" max-width="750px" scrollable persistent>
      <VCard class="rounded-xl">
        <VCardTitle class="d-flex align-center justify-space-between pa-5 bg-surface border-b">
          <div class="d-flex align-center">
            <div class="bg-primary-lighten rounded-lg pa-2 me-3">
              <VIcon icon="ri-chat-new-line" color="primary" size="24" />
            </div>
            <div>
              <span class="text-h6 font-weight-bold d-block">Бот первокоммент</span>
              <span class="text-caption text-muted">Сообщество: {{ connections.find(c => c.id === selectedConnectionId)?.name }}</span>
            </div>
          </div>
          <VBtn icon="ri-close-line" variant="text" color="secondary" density="comfortable" @click="showFirstCommentSettingsDialog = false" />
        </VCardTitle>

        <VTabs v-model="activeFirstCommentTab" bg-color="surface" class="border-b" color="primary">
          <VTab value="general"><VIcon icon="ri-settings-4-line" class="me-2" />Основные</VTab>
          <VTab value="filters"><VIcon icon="ri-filter-3-line" class="me-2" />Фильтрация постов</VTab>
        </VTabs>

        <VCardText class="pa-6" style="max-height: 70vh;">
          <div class="d-flex align-center justify-space-between mb-6 bg-light rounded-xl pa-4">
            <div>
              <span class="text-subtitle-1 font-weight-bold d-block">Статус автокомментатора</span>
              <span class="text-caption text-muted">Включите для автоматического комментирования новых постов</span>
            </div>
            <VSwitch v-model="firstCommentForm.is_active" color="success" hide-details />
          </div>

          <!-- Поле индивидуального API-ключа -->
          <div class="mb-6 bg-light rounded-xl pa-4">
            <span class="font-weight-bold d-block mb-1">Индивидуальный ключ доступа сообщества</span>
            <span class="text-caption text-muted d-block mb-3">
              Позволяет использовать отдельный токен для работы этого конкретного бота. Если поле пустое, будет использоваться токен основного подключения.
              <a :href="getVkTokenUrl()" target="_blank" class="text-primary font-weight-bold text-decoration-none d-inline-block ms-1">Получить токен сообщества автоматически ↗</a>
            </span>
            <VTextField
              v-model="firstCommentForm.vk_bot_token"
              label="API-ключ сообщества ВК (Токен)"
              placeholder="Вставьте токен vk1.a.***"
              variant="outlined"
              density="comfortable"
              hide-details
              type="password"
            />
          </div>

          <VDivider class="mb-6" />

          <!-- Вкладка: Основные -->
          <div v-if="activeFirstCommentTab === 'general'">
            <div class="mb-6">
              <div class="d-flex align-center justify-space-between mb-4">
                <div>
                  <span class="text-subtitle-1 font-weight-bold d-block">Случайная задержка</span>
                  <span class="text-caption text-muted">Использовать случайное время задержки в заданном диапазоне</span>
                </div>
                <VSwitch v-model="isRandomDelay" color="primary" hide-details />
              </div>

              <!-- Если фиксированная задержка -->
              <VRow align="center" v-if="!isRandomDelay">
                <VCol cols="12" sm="6">
                  <VTextField
                    v-model.number="firstCommentForm.delay_seconds"
                    label="Задержка (в секундах)"
                    type="number"
                    min="0"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                  />
                </VCol>
                <VCol cols="12" sm="6">
                  <span class="text-caption text-muted">Рекомендуется: от 5 до 30 секунд. 0 — мгновенная отправка.</span>
                </VCol>
              </VRow>

              <!-- Если случайная задержка (диапазон) -->
              <VRow align="center" v-else>
                <VCol cols="12" sm="4">
                  <VTextField
                    v-model.number="firstCommentForm.delay_min"
                    label="От (секунд)"
                    type="number"
                    min="0"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                  />
                </VCol>
                <VCol cols="12" sm="4">
                  <VTextField
                    v-model.number="firstCommentForm.delay_max"
                    label="До (секунд)"
                    type="number"
                    min="0"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                  />
                </VCol>
                <VCol cols="12" sm="4">
                  <span class="text-caption text-muted">Бот выберет случайное время ожидания в этом интервале.</span>
                </VCol>
              </VRow>
            </div>

            <VDivider class="mb-6" />

            <div>
              <div class="d-flex align-center justify-space-between mb-3">
                <h4 class="text-subtitle-1 font-weight-bold">Варианты комментариев (до 15 шт)</h4>
                <span class="text-caption text-muted">{{ firstCommentForm.comments.length }} / 15</span>
              </div>

              <!-- Добавление нового варианта -->
              <div class="mb-4 pa-4 border rounded-xl" v-if="firstCommentForm.comments.length < 15">
                <VTextarea
                  v-model="newCommentText"
                  label="Новый комментарий"
                  placeholder="Введите текст комментария..."
                  variant="outlined"
                  rows="3"
                  auto-grow
                  class="mb-2"
                />
                
                <!-- Панель эмодзи -->
                <div class="d-flex align-center gap-1 flex-wrap mb-4 bg-light rounded-lg pa-2 border">
                  <span class="text-caption font-weight-bold text-muted me-2">Вставить эмодзи:</span>
                  <VBtn 
                    v-for="emoji in commonEmojis" 
                    :key="emoji" 
                    size="x-small" 
                    variant="text" 
                    class="pa-0 min-w-0" 
                    style="font-size: 16px; width: 28px; height: 28px;"
                    @click="insertEmoji(emoji)"
                  >
                    {{ emoji }}
                  </VBtn>
                </div>

                <div class="d-flex align-center justify-space-between mt-2">
                  <div class="text-caption text-muted">
                    Поддерживаются вложения: <br/>
                    • <b>Случайное:</b> <code class="text-primary">[rand]photo-XXX_XX|photo-YYY_YY[/rand]</code> <br/>
                    • <b>По словам (полное):</b> <code class="text-primary">[keyText]photo-XXX_XX|роллы,пицца[/keyText]</code> <br/>
                    • <b>По словам (вхождение):</b> <code class="text-primary">[keyTextEntry]photo-XXX_XX|суши,wok[/keyTextEntry]</code>
                  </div>
                  <VBtn color="primary" @click="addCommentToForm" :disabled="!newCommentText.trim()">
                    Добавить в список
                  </VBtn>
                </div>
              </div>
              <div class="text-caption text-warning mb-4" v-else>
                Достигнут лимит в 15 вариантов комментариев. Удалите один из существующих, чтобы добавить новый.
              </div>

              <!-- Список добавленных вариантов -->
              <div v-if="firstCommentForm.comments.length > 0" class="border rounded-xl overflow-hidden">
                <VList density="compact">
                  <VListItem v-for="(comment, index) in firstCommentForm.comments" :key="index" class="border-b last:border-b-0 pa-4">
                    <div class="d-flex align-start w-100 justify-space-between">
                      <span class="text-body-2 font-weight-medium text-wrap pe-4" style="white-space: pre-wrap;">{{ comment }}</span>
                      <VBtn
                        icon="ri-delete-bin-6-line"
                        size="x-small"
                        color="error"
                        variant="text"
                        @click="removeCommentFromForm(index)"
                      />
                    </div>
                  </VListItem>
                </VList>
              </div>
              <div v-else class="text-center py-8 border rounded-xl border-dashed">
                <VIcon icon="ri-chat-delete-line" size="48" color="secondary" class="mb-2" />
                <p class="text-body-2 text-muted mb-0">Комментарии еще не добавлены</p>
              </div>
            </div>
          </div>

          <!-- Вкладка: Фильтрация постов -->
          <div v-if="activeFirstCommentTab === 'filters'">
            <div class="mb-6">
              <span class="text-subtitle-1 font-weight-bold d-block mb-1">Где оставлять комментарии?</span>
              <span class="text-caption text-muted d-block mb-3">Выберите типы постов на стене, под которыми бот будет писать комментарий</span>
              
              <VRadioGroup v-model="firstCommentForm.post_type_filter" inline hide-details class="mb-4">
                <VRadio label="Все посты" value="all" color="primary" />
                <VRadio label="Только от имени сообщества" value="only_group" color="primary" />
                <VRadio label="Только от пользователей (предложка)" value="only_users" color="primary" />
              </VRadioGroup>
            </div>

            <VDivider class="mb-6" />

            <div class="mb-6 bg-light rounded-xl pa-4 d-flex align-center justify-space-between">
              <div>
                <span class="font-weight-bold d-block">Исключить репосты из комментирования</span>
                <span class="text-caption text-muted">Бот не будет писать комментарии под репостами других записей</span>
              </div>
              <VSwitch v-model="firstCommentForm.exclude_reposts" color="primary" hide-details />
            </div>

            <VDivider class="mb-6" />

            <div class="mb-6 bg-light rounded-xl pa-4 d-flex align-center justify-space-between">
              <div>
                <span class="font-weight-bold d-block">Игнорировать посты без текста</span>
                <span class="text-caption text-muted">Не оставлять комментарии, если пост содержит только медиафайлы (картинки, видео) без описания</span>
              </div>
              <VSwitch v-model="firstCommentForm.ignore_empty_text" color="primary" hide-details />
            </div>

            <VDivider class="mb-6" />

            <div class="mb-6">
              <span class="text-subtitle-1 font-weight-bold d-block mb-1">Пост должен содержать слова (include)</span>
              <span class="text-caption text-muted d-block mb-3">Укажите ключевые слова через запятую. Бот оставит комментарий только если в посте есть хотя бы одно из этих слов. Оставьте пустым, чтобы комментировать всё.</span>
              <VTextField
                v-model="firstCommentForm.include_keywords"
                placeholder="пицца, роллы, скидка, промокод"
                variant="outlined"
                density="comfortable"
              />
            </div>

            <div class="mb-4">
              <span class="text-subtitle-1 font-weight-bold d-block mb-1">Стоп-слова (exclude)</span>
              <span class="text-caption text-muted d-block mb-3">Укажите слова через запятую. Если в посте есть хотя бы одно из этих слов, бот проигнорирует пост.</span>
              <VTextField
                v-model="firstCommentForm.exclude_keywords"
                placeholder="розыгрыш, итоги, конкурс, вакансия"
                variant="outlined"
                density="comfortable"
              />
            </div>
          </div>
        </VCardText>

        <VDivider />
        <VCardActions class="pa-5 bg-surface border-t d-flex justify-end">
          <VBtn color="secondary" variant="outlined" class="me-2" @click="showFirstCommentSettingsDialog = false">Отмена</VBtn>
          <VBtn color="success" prepend-icon="ri-save-3-line" :loading="savingFirstComment" @click="saveFirstCommentSettings" :disabled="firstCommentForm.is_active && firstCommentForm.comments.length === 0">Сохранить</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- МОДАЛЬНОЕ ОКНО ИСТОРИИ НАЧИСЛЕНИЙ УЧАСТНИКА -->
    <VDialog v-model="showUserHistoryDialog" max-width="850px" scrollable>
      <VCard class="rounded-xl">
        <VCardTitle class="d-flex align-center justify-space-between pa-5 bg-surface border-b">
          <div class="d-flex align-center" v-if="selectedUserForHistory">
            <VAvatar size="40" class="me-3" v-if="selectedUserForHistory.photo_50">
              <VImg :src="selectedUserForHistory.photo_50" />
            </VAvatar>
            <VAvatar size="40" color="primary" class="me-3 font-weight-bold" v-else>
              👤
            </VAvatar>
            <div>
              <div class="text-subtitle-1 font-weight-bold">
                История начислений: {{ selectedUserForHistory.first_name }} {{ selectedUserForHistory.last_name }}
              </div>
              <div class="text-caption text-muted d-flex align-center gap-2">
                <span>VK ID: {{ selectedUserForHistory.vk_id }}</span>
                <span v-if="selectedUserForHistory.phone">• Тел: {{ selectedUserForHistory.phone }}</span>
                <span v-if="selectedUserForHistory.customer_name">• Карта: {{ selectedUserForHistory.customer_name }}</span>
              </div>
            </div>
          </div>
          <VBtn icon="ri-close-line" variant="text" size="small" @click="showUserHistoryDialog = false" />
        </VCardTitle>

        <VCardText class="pa-5" style="max-height: 600px;">
          <div v-if="loadingUserHistory" class="text-center py-8">
            <VProgressCircular indeterminate color="primary" class="mb-3" />
            <div class="text-caption text-muted">Загрузка истории начислений...</div>
          </div>

          <div v-else>
            <!-- Сводные бэйджи баланса пользователя -->
            <div class="d-flex flex-wrap gap-3 mb-5 p-3 rounded-lg bg-light" v-if="userHistoryData" style="background-color: rgba(var(--v-theme-surface), 0.5);">
              <div class="pa-3 border rounded bg-surface flex-grow-1 text-center">
                <span class="text-caption text-muted d-block">Баллы ВК</span>
                <span class="text-h6 font-weight-bold text-info">{{ userHistoryData.vk_bonus_balance || 0 }}</span>
              </div>
              <div class="pa-3 border rounded bg-surface flex-grow-1 text-center">
                <span class="text-caption text-muted d-block">Синхронизировано iiko</span>
                <span class="text-h6 font-weight-bold text-success">{{ userHistoryData.vk_bonus_balance_synced || 0 }}</span>
              </div>
              <div class="pa-3 border rounded bg-surface flex-grow-1 text-center" v-if="userHistoryData.is_linked">
                <span class="text-caption text-muted d-block">Бонусы iikoCard</span>
                <span class="text-h6 font-weight-bold text-primary">{{ userHistoryData.iiko_balance || 0 }}</span>
              </div>
            </div>

            <h4 class="text-subtitle-2 font-weight-bold mb-3">Детализированный лог активностей</h4>

            <VDataTable
              :headers="[
                { title: 'Дата и время', key: 'created_at' },
                { title: 'Активность', key: 'title' },
                { title: 'Контекст', key: 'item_id' },
                { title: 'Баллы', key: 'points', sortable: true },
                { title: 'iiko Статус', key: 'is_synced' }
              ]"
              :items="userHistoryData ? userHistoryData.history : []"
              density="comfortable"
              no-data-text="История начислений пока пуста"
            >
              <template #item.created_at="{ item }">
                <span class="text-body-2 font-weight-medium">{{ formatDate(item.created_at) }}</span>
              </template>

              <template #item.title="{ item }">
                <div class="d-flex align-center gap-2">
                  <VChip 
                    size="small" 
                    :color="getActivityColor(item.action_type)"
                    variant="tonal"
                    class="font-weight-bold"
                  >
                    {{ item.title }}
                  </VChip>
                </div>
              </template>

              <template #item.item_id="{ item }">
                <span class="text-caption font-mono text-muted" v-if="item.item_id">{{ item.item_id }}</span>
                <span class="text-muted text-caption" v-else>-</span>
              </template>

              <template #item.points="{ item }">
                <span :class="item.points >= 0 ? 'text-success font-weight-bold' : 'text-error font-weight-bold'">
                  {{ item.points >= 0 ? '+' + item.points : item.points }}
                </span>
              </template>

              <template #item.is_synced="{ item }">
                <VChip size="x-small" color="success" v-if="item.is_synced" variant="flat">Синхронизировано</VChip>
                <VChip size="x-small" color="warning" v-else variant="tonal">В очереди</VChip>
              </template>
            </VDataTable>
          </div>
        </VCardText>

        <VDivider />
        <VCardActions class="pa-4 bg-surface border-t d-flex justify-end">
          <VBtn color="secondary" variant="outlined" @click="showUserHistoryDialog = false">Закрыть</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>


    <!-- ДИАЛОГ НАСТРОЙКИ НОВОГО МАРКЕТИНГОВОГО БОТА (ПОЛНОФУНКЦИОНАЛЬНЫЙ) -->
    <VkMarketingBotModal
      v-model="showMarketingModal"
      :bot-type="selectedMarketingBotType"
      :connection-id="selectedConnectionId"
      :group-info="connections.find(c => c.id === selectedConnectionId)"
      @saved="onMarketingBotSaved"
    />
</template>

<style scoped>
.text-muted {
  color: rgba(var(--v-theme-on-surface), 0.6) !important;
}

.bg-primary-lighten {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.bg-success-lighten {
  background-color: rgba(var(--v-theme-success), 0.1);
}

.bg-warning-lighten {
  background-color: rgba(var(--v-theme-warning), 0.1);
}

.bg-secondary-lighten {
  background-color: rgba(var(--v-theme-secondary), 0.08);
}

.bg-light {
  background-color: rgba(var(--v-theme-on-surface), 0.03);
}

.bot-card {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08) !important;
}

.clickable-card {
  cursor: pointer;
}

.clickable-card:hover {
  transform: translateY(-4px);
  border-color: rgba(var(--v-theme-primary), 0.3) !important;
  box-shadow: 0 8px 24px rgba(var(--v-theme-primary), 0.08) !important;
}

.disabled-card {
  opacity: 0.7;
  background-color: rgba(var(--v-theme-on-surface), 0.01);
}

.text-muted-dark {
  color: rgba(var(--v-theme-on-surface), 0.8) !important;
}

.bot-icon-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* Стили конструктора обложек */
.canvas-container {
  width: 100%;
  aspect-ratio: 1590 / 530;
  max-width: 100%;
  box-sizing: border-box;
}

.cover-canvas {
  user-select: none;
}

.canvas-widget {
  transform: translate(0, 0);
  background-color: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  border: 1px dashed transparent;
  transition: border-color 0.2s, background-color 0.2s;
  white-space: nowrap;
}

.canvas-widget:hover {
  border-color: rgba(255, 255, 255, 0.5);
  background-color: rgba(0, 0, 0, 0.6);
}

.canvas-widget:hover .widget-actions {
  display: block !important;
}

.widget-selected {
  border-color: rgba(var(--v-theme-primary), 1) !important;
  border-style: solid;
  background-color: rgba(var(--v-theme-primary), 0.2) !important;
  box-shadow: 0 0 10px rgba(var(--v-theme-primary), 0.5);
}

.cursor-move {
  cursor: move;
}

.uppercase {
  text-transform: uppercase;
  letter-spacing: 1px;
}
</style>
