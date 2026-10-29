<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import VkMarketingBotMaxSettings from '@/components/VkMarketingBotMaxSettings.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  botType: {
    type: String,
    default: 'shop'
  },
  connectionId: {
    type: [Number, String],
    default: null
  },
  groupInfo: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const toast = useToast()
const activeTab = ref(0)
const saving = ref(false)
const testing = ref(false)
const testingVk = ref(false)
const testingMax = ref(false)
const selectedAnalyticsChannel = ref('all') // 'all', 'vk', 'max'

const activeMetrics = computed(() => {
  if (selectedAnalyticsChannel.value === 'vk') return analyticsData.value?.metrics_vk || {}
  if (selectedAnalyticsChannel.value === 'max') return analyticsData.value?.metrics_max || {}
  return analyticsData.value?.metrics || {}
})

const activeLogs = computed(() => {
  if (selectedAnalyticsChannel.value === 'vk') return analyticsData.value?.logs_vk || []
  if (selectedAnalyticsChannel.value === 'max') return analyticsData.value?.logs_max || []
  return analyticsData.value?.logs || []
})

const activeReviews = computed(() => {
  if (selectedAnalyticsChannel.value === 'vk') return analyticsData.value?.reviews_vk || []
  if (selectedAnalyticsChannel.value === 'max') return analyticsData.value?.reviews_max || []
  return analyticsData.value?.reviews || []
})

const activeSpins = computed(() => {
  if (selectedAnalyticsChannel.value === 'vk') return analyticsData.value?.spins_vk || []
  if (selectedAnalyticsChannel.value === 'max') return analyticsData.value?.spins_max || []
  return analyticsData.value?.spins || []
})

const activeLinks = computed(() => {
  if (selectedAnalyticsChannel.value === 'vk') return analyticsData.value?.links_vk || []
  if (selectedAnalyticsChannel.value === 'max') return analyticsData.value?.links_max || []
  return analyticsData.value?.links || []
})

// Общий объект конфигураций
const configs = ref({
  shop: {
    is_active: true,
    vk_enabled: true,
    max_enabled: false,
    max_send_mode: 'bridge_only',
    max_daily_limit: 100,
    max_delay_seconds: 15,
    test_admin_phones: ['79220079019'],
    max_welcome_message_verified: 'Привет, {first_name}! 🍣 Рады видеть вас в «Везу Ролл»! Напишите 1 для каталога, 2 для повтора заказа, 4 для статуса доставки.',
    max_welcome_message_guest: 'Привет! 🍣 Добро пожаловать в доставку суши «Везу Ролл»! Напишите 1 для просмотра каталога.',
    max_status_check_template: 'Статус вашего заказа №{order_number}: {status_human}. Курьер: {courier_name}.',
    test_mode_only_admins: false,
    min_order_sum: 700,
    first_vk_order_discount_percent: 10,
    trigger_keywords: 'меню, начать, start, каталог, заказать, роллы',
    welcome_message_verified: 'Привет, {first_name}! 🍣 Выберите действие в меню ниже:',
    welcome_message_guest: 'Привет! 🍣 Добро пожаловать в доставку суши и роллов «Везу Ролл»!',
    carousel_source_mode: 'auto_top_sales',
    hide_stop_list_items: true,
    card_button_1_mode: 'add_to_vk_cart',
    card_button_2_mode: 'link_to_site_product',
    enable_repeat_order: true,
    repeat_order_lookback_count: 3,
    allow_bonus_payment_in_bot: true,
    order_creation_mode: 'direct_iiko_and_db',
    status_check_template: 'Статус вашего заказа №{order_number}: {status_human}. Курьер: {courier_name}.',
    welcome_photo_url: null,
    welcome_photo_vk_id: null,
    show_on_start: true,
    attach_keyboard_always: true,
    featured_product_ids: [],
    max_bonus_payment_percent: 30,
    menu_buttons: [
      { id: 1, text: '🍣 Хиты и Сеты', color: 'primary', action: 'carousel', active: true },
      { id: 2, text: '🔁 Повторить заказ', color: 'positive', action: 'repeat_order', active: true },
      { id: 3, text: '🔥 Акции сегодня', color: 'primary', action: 'actions_text', active: true },
      { id: 4, text: '🛵 Где мой заказ?', color: 'secondary', action: 'status_iiko', active: true },
      { id: 5, text: '💰 Мои бонусы', color: 'secondary', action: 'bonus_balance', active: true },
      { id: 6, text: '👨‍💼 Позвать оператора', color: 'negative', action: 'operator', active: true }
    ]
  },
  retention: {
    is_active: true,
    vk_enabled: true,
    max_enabled: false,
    max_send_mode: 'bridge_only',
    max_daily_limit: 100,
    max_delay_seconds: 15,
    test_admin_phones: ['79220079019'],
    max_newbie_enabled: true,
    max_newbie_template: 'Привет, {first_name}! Неделю назад вы заказывали у нас сет. Как всё прошло? Дарим скидку 15% на второй заказ по промокоду {promo_code}!',
    max_sleeping_enabled: true,
    max_sleeping_template: '{first_name}, мы скучаем! 🥺 Прошло уже 21 день с вашего прошлого заказа. Начислили вам 🎁 300 бонусов! Они сгорят через 72 часа.',
    max_lost_vip_enabled: true,
    max_lost_vip_template: '{first_name}, как наш любимый VIP-гость, при следующем заказе от 1200 ₽ получите ролл «Филадельфия» в подарок по коду {promo_code}!',
    max_burn_reminder_enabled: true,
    max_burn_reminder_template: '⏰ {first_name}, напоминаем: ваши подарочные бонусы сгорят завтра! Успейте заказать любимые суши.',
    test_mode_only_admins: false,
    newbie_enabled: true,
    newbie_days: 7,
    newbie_gift_mode: 'promo_code',
    newbie_promo_code: 'VTOROY15',
    newbie_message_template: 'Привет, {first_name}! Неделю назад вы заказывали у нас сет. Как всё прошло? Дарим скидку 15% на второй заказ по промокоду {promo_code}!',
    sleeping_enabled: true,
    sleeping_days: 21,
    sleeping_gift_mode: 'expiring_iiko_points',
    sleeping_promo_code: 'MISSYOU',
    sleeping_message_template: '{first_name}, мы скучаем! 🥺 Прошло уже 21 день с вашего прошлого заказа. Специально для вас начислили 🎁 300 бонусов! Они сгорят через 72 часа.',
    lost_vip_enabled: true,
    lost_vip_days: 45,
    lost_vip_min_spent: 5000,
    lost_vip_gift_mode: 'both',
    lost_vip_promo_code: 'VIPBACK',
    lost_vip_message_template: '{first_name}, как наш любимый VIP-гость, при следующем заказе от 1200 ₽ получите ролл «Филадельфия» в подарок по коду {promo_code} + 300 бонусов!',
    newbie_photo_url: null,
    newbie_attachment_photo: null,
    sleeping_photo_url: null,
    sleeping_attachment_photo: null,
    lost_vip_photo_url: null,
    lost_vip_attachment_photo: null,
    enable_expiring_bonuses: true,
    expiring_bonus_amount: 300,
    expiring_bonus_hours: 72,
    send_burn_reminder: true,
    burn_reminder_hours_before: 24,
    burn_reminder_template: '⏰ {first_name}, напоминаем: ваши 300 подарочных бонусов сгорят завтра! Успейте заказать любимые суши.',
    run_time_local: '16:30',
    send_window_start: '11:00',
    send_window_end: '20:00',
    min_cooldown_days_between_touches: 14,
    max_messages_per_day: 150
  },
  nps: {
    is_active: true,
    vk_enabled: true,
    max_enabled: false,
    max_send_mode: 'bridge_only',
    max_daily_limit: 100,
    max_delay_seconds: 15,
    test_admin_phones: ['79220079019'],
    max_msg_ask_rating: 'Ваш заказ №{order_number} доставлен! Оцените, пожалуйста, вкус блюд и доставку от 1 до 5 в ответном сообщении:',
    max_msg_positive: 'Спасибо за высший балл! ❤️ Нам очень приятно радовать вас вкусными роллами!',
    max_msg_negative: 'Нам очень жаль, что блюда не порадовали 😔 Напишите, пожалуйста, что пошло не так — мы во всем разберемся!',
    max_alert_admin_phones: [],
    test_mode_only_admins: false,
    delay_minutes_after_delivery: 45,
    min_order_amount_for_nps: 500,
    points_for_rating: 20,
    points_for_photo_review: 100,
    positive_rating_threshold: 4,
    required_review_hashtag: '#отзыв_везуролл',
    require_photo_attachment: true,
    max_paid_reviews_per_month: 4,
    auto_tag_multichat: true,
    msg_ask_rating: 'Ваш заказ №{order_number} доставлен! Оцените, пожалуйста, вкус блюд и скорость курьера от 1 до 5:',
    msg_positive: 'Спасибо за высший балл! ❤️ Нам очень приятно! Опубликуйте фото заказа на стене группы с хэштегом #отзыв_везуролл — начислим ещё +100 бонусов в iiko!',
    msg_negative: 'Нам очень жаль, что блюда не порадовали 😔 Пожалуйста, напишите, что именно пошло не так (можно прикрепить фото) — сообщение сразу передается руководству!',
    msg_negative_thank_you: 'Спасибо! Ваше обращение передано управляющему.',
    alert_admin_vk_ids: [],
    auto_apology_promo_code: 'SORRY200'
  },
  wheel: {
    is_active: true,
    vk_enabled: true,
    max_enabled: false,
    max_send_mode: 'bridge_only',
    max_daily_limit: 100,
    max_delay_seconds: 15,
    test_admin_phones: ['79220079019'],
    max_msg_dm_win_template: '🎉 Поздравляем! Вы выиграли «{prize_name}»! Ваш промокод: {promo_code} (действует 48ч).',
    max_msg_dm_reminder_template: '🔥 {first_name}, ваш выигрыш «{prize_name}» сгорит через 24 часа! Успейте заказать!',
    test_mode_only_admins: false,
    keyword: 'КРУТИТЬ',
    require_group_member: true,
    require_post_like: true,
    require_messages_allowed: true,
    daily_free_spins: 1,
    free_spins_period: 'per_day',
    extra_spin_order_sum: 1200,
    prize_valid_hours: 48,
    contest_post_id: null,
    require_messages_allowed: true,
    free_spins_period: 'per_day',
    wheel_bg_image_url: null,
    draw_user_avatar_in_center: true,
    remind_unused_prize: true,
    remind_before_expire_hours: 24,
    msg_dm_win_template: '🎉 Поздравляем! Вы выиграли «{prize_name}»! Ваш промокод: {promo_code} (действует 48ч).',
    msg_dm_reminder_template: '🔥 {first_name}, ваш выигрыш «{prize_name}» сгорит через 24 часа! Успейте заказать!',
    sectors_config: [
      { id: 1, title: 'Скидка 10%', full: 'Скидка 10% на заказ от 1000 ₽', type: 'promo', val: 'FORTUNA10', weight: 40, color: '#E53935' },
      { id: 2, title: 'Калифорния', full: 'Ролл Калифорния в подарок к заказу от 1200 ₽', type: 'promo', val: 'W_CALIF', weight: 25, color: '#FB8C00' },
      { id: 3, title: '+150 бонусов', full: '150 бонусов iiko на ваш счёт', type: 'points', val: '150', weight: 20, color: '#43A047' },
      { id: 4, title: 'Пепперони', full: 'Пицца Пепперони в подарок от 1500 ₽', type: 'promo', val: 'W_PIZZA', weight: 12, color: '#1E88E5' },
      { id: 5, title: 'СУПЕРПРИЗ', full: 'Сет 1.5 кг в подарок к заказу от 2000 ₽', type: 'promo', val: 'W_SUPER', weight: 3, color: '#8E24AA' }
    ]
  },
  broadcast: {
    is_active: true,
    vk_enabled: true,
    max_enabled: false,
    channel_target: 'vk',
    max_send_mode: 'bridge_only',
    max_daily_limit: 100,
    max_delay_seconds: 15,
    test_admin_phones: ['79220079019'],
    max_broadcast_text: '🍣 {first_name}, соскучились по свежим роллам? Дарим порцию запечённых мидий к любому заказу от 1100 ₽ по промокоду МИДИИ!',
    max_happy_hours_template: '🍣 {first_name}, только сегодня с 14:00 до 17:00 скидка 20% на все сеты по промокоду ОБЕД!',
    test_mode_only_admins: false,
    segment_verification: 'all',
    segment_bonus_min: 0,
    segment_days_last_order: 14,
    segment_avg_check_min: 1000,
    exclude_last_touched_days: 7,
    broadcast_text: '🍣 {first_name}, соскучились по свежим роллам? Только сегодня дарим порцию запечённых мидий к любому заказу от 1100 ₽ по промокоду МИДИИ!',
    broadcast_photo_url: null,
    attachment_photo: null,
    happy_hours_auto: true,
    happy_hours_lookback_hours: 2,
    happy_hours_batch_size: 150,
    happy_hours_days_of_week: ['Пн', 'Вт', 'Ср', 'Чт'],
    happy_hours_check_time: '14:00',
    happy_hours_lookback_hours: 2,
    min_orders_threshold: 8,
    happy_hours_batch_size: 150,
    happy_hours_template: '🍣 {first_name}, только сегодня с 14:00 до 17:00 скидка 20% на все сеты по промокоду ОБЕД!'
  },
  referral: {
    is_active: true,
    vk_enabled: true,
    max_enabled: false,
    max_send_mode: 'bridge_only',
    max_daily_limit: 100,
    max_delay_seconds: 15,
    test_admin_phones: ['79220079019'],
    max_msg_ambassador_info: 'Ваша ссылка друга: https://vezuroll.ru/?ref={referral_code}.\nПригласите друга: он получит 250 ₽, а вы — 300 бонусов после его первой доставки!',
    max_msg_friend_welcome: 'Привет! Ваш друг дарит вам скидку на первый заказ от 1000 ₽! Промокод активирован 🍣',
    max_msg_referrer_reward_paid: '🎉 Ура! Ваш друг {friend_name} только что получил свой заказ! Вам начислено +{referrer_reward_points} бонусов в iiko!',
    test_mode_only_admins: false,
    friend_reward_type: 'iiko_points',
    friend_bonus_points: 250,
    friend_min_order_sum: 1000,
    referrer_reward_points: 300,
    max_referrals_per_user_month: 10,
    antifraud_strict_new_customer: true,
    antifraud_prevent_same_phone_address: true,
    trigger_command: 'пригласить друга, рефералка, друг',
    friend_gift_product_id: null,
    antifraud_prevent_same_phone_address: true,
    cert_bg_image_url: null,
    generate_invite_image: true,
    msg_ambassador_info: 'Ваша персональная ссылка: https://vk.com/write-186688777?ref={referral_code}.\nПригласите друга: он получит 250 ₽, а вы — 300 бонусов после его первой доставки!',
    msg_friend_welcome: 'Привет! Ваш друг дарит вам {friend_bonus_points} бонусов на первый заказ от 1000 ₽! Промокод уже активирован 🍣',
    msg_referrer_reward_paid: '🎉 Ура! Ваш друг {friend_name} только что получил свой первый заказ! Вам начислено +{referrer_reward_points} бонусов в iiko!'
  }
})

// Метаданные ботов
const botMeta = {
  shop: {
    title: 'Интерактивный Каталог и Повтор Заказа (VkShopBot)',
    subtitle: 'Каталог в ЛС, 1-клик повтор прошлого заказа из iiko, статус доставки',
    icon: 'ri-shopping-bag-3-line',
    color: 'primary',
    tabs: [
      { title: 'Главное меню (ВК)', icon: 'ri-menu-line' },
      { title: 'Витрина и Карусель', icon: 'ri-slideshow-line' },
      { title: 'Повтор заказа', icon: 'ri-repeat-line' },
      { title: 'Канал MAX (Личный №)', icon: 'ri-chat-voice-line' },
      { title: 'Конверсия и Аналитика', icon: 'ri-bar-chart-box-line' }
    ]
  },
  retention: {
    title: 'Триггерный Бот Реактивации Гостей (VkRetentionBot)',
    subtitle: 'Win-Back RFM цепочки: Новичок (7д), Засыпающий (21д), VIP (45д) + Будильник бонусов',
    icon: 'ri-user-heart-line',
    color: 'success',
    tabs: [
      { title: 'Цепочки RFM (ВК)', icon: 'ri-route-line' },
      { title: 'Будильник Бонусов', icon: 'ri-alarm-warning-line' },
      { title: 'Лимиты и Тайминг', icon: 'ri-time-line' },
      { title: 'Канал MAX (Личный №)', icon: 'ri-chat-voice-line' },
      { title: 'Аналитика ROI', icon: 'ri-funds-line' }
    ]
  },
  nps: {
    title: 'Бот NPS-Контроля Качества и Фото-Отзывов (VkReviewNpsBot)',
    subtitle: 'Опрос через 45 мин после доставки, перехват негатива 1-3 ⭐, баллы за 4-5 ⭐',
    icon: 'ri-star-smile-line',
    color: 'warning',
    tabs: [
      { title: 'Опрос и Тайминг', icon: 'ri-question-answer-line' },
      { title: 'Ветка Позитива (4-5 ⭐)', icon: 'ri-thumb-up-line' },
      { title: 'Перехват Негатива (1-3 ⭐)', icon: 'ri-alarm-line' },
      { title: 'Канал MAX (Личный №)', icon: 'ri-chat-voice-line' },
      { title: 'Дашборд Качества', icon: 'ri-dashboard-line' }
    ]
  },
  wheel: {
    title: 'Колесо Фортуны / Подарок за Заказ (VkWheelOfFortuneBot)',
    subtitle: 'Генерация рулетки в комментариях/ЛС, вероятности секторов, секретные промокоды на 48ч',
    icon: 'ri-pie-chart-2-line',
    color: 'error',
    tabs: [
      { title: 'Конструктор Секторов', icon: 'ri-pie-chart-line' },
      { title: 'Условия и VIP-Спины', icon: 'ri-shield-user-line' },
      { title: 'Генератор Рулетки', icon: 'ri-image-edit-line' },
      { title: 'Канал MAX (Личный №)', icon: 'ri-chat-voice-line' },
      { title: 'Дожим в Заказ (48ч)', icon: 'ri-hourglass-2-line' }
    ]
  },
  broadcast: {
    title: 'Таргетированные Рассылки и «Счастливые Часы» (VkSmartBroadcastBot)',
    subtitle: 'Сегментированные рассылки в ЛС и авто-активация спецпредложений при спаде на кухне',
    icon: 'ri-broadcast-line',
    color: 'info',
    tabs: [
      { title: 'Фильтры Аудитории', icon: 'ri-filter-3-line' },
      { title: 'Счастливые Часы (Кухня)', icon: 'ri-restaurant-line' },
      { title: 'Канал MAX (Личный №)', icon: 'ri-chat-voice-line' },
      { title: 'История Рассылок', icon: 'ri-history-line' }
    ]
  },
  referral: {
    title: 'Реферальный Бот: «Приведи Друга» (VkReferralBot)',
    subtitle: 'Персональные ссылки, бонусы после первого доставленного заказа друга, строгий антифрод',
    icon: 'ri-gift-line',
    color: 'secondary',
    tabs: [
      { title: 'Правила и Антифрод', icon: 'ri-shield-keyhole-line' },
      { title: 'Карточка-Приглашение', icon: 'ri-ticket-line' },
      { title: 'Канал MAX (Личный №)', icon: 'ri-chat-voice-line' },
      { title: 'Таблица Рефералов', icon: 'ri-group-line' }
    ]
  }
}

const currentMeta = computed(() => botMeta[props.botType] || botMeta.shop)
const currentConfig = computed(() => configs.value[props.botType] || {})

// Загрузка конфигурации с сервера
const fetchConfig = async () => {
  if (!props.connectionId) return
  try {
    const res = await axios.get(`/api/v1/vk/marketing-bots/config/${props.connectionId}`)
    if (res.data) {
      Object.keys(res.data).forEach(key => {
        if (configs.value[key] && res.data[key]) {
          configs.value[key] = { ...configs.value[key], ...res.data[key] }
        }
      })
    }
  } catch (e) {
    console.error('Ошибка загрузки конфига маркетинг-ботов:', e)
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    activeTab.value = 0
    fetchConfig()
    loadProducts()
    loadAnalytics()
  }
})

watch(activeTab, (newTab) => {
  // При переключении на вкладку аналитики подгружаем свежие данные
  if (newTab >= 2) {
    loadAnalytics()
  }
})

// Сохранение
const saveConfig = async () => {
  if (!props.connectionId) {
    toast.error('Ошибка: не выбрано подключение сообщества ВК')
    return
  }
  saving.value = true
  try {
    const payload = configs.value[props.botType]
    const res = await axios.post(`/api/v1/vk/marketing-bots/save/${props.botType}/${props.connectionId}`, payload)
    if (res.data && res.data.status === 'success') {
      toast.success(`Настройки "${currentMeta.value.title}" успешно сохранены!`)
      emit('saved', { botType: props.botType, config: { ...configs.value[props.botType] } })
      emit('update:modelValue', false)
    } else {
      toast.error(res.data?.message || 'Ошибка сохранения настроек')
    }
  } catch (e) {
    console.error('Ошибка сохранения бота:', e)
    const errMsg = e.response?.data?.message || e.response?.data?.detail || 'Ошибка при сохранении настроек'
    toast.error(errMsg)
  } finally {
    saving.value = false
  }
}

// Загрузка графики с компьютера и автоматическая синхронизация с VK API
const uploadingImage = ref(false)

const handleFileUpload = async (event, botKey, urlField, vkAttachField = null) => {
  const file = event?.target?.files?.[0] || (Array.isArray(event) ? event[0] : event)
  if (!file) return

  uploadingImage.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('bot_type', botKey)

    const res = await axios.post(
      `/api/v1/vk/marketing-bots/upload-image/${props.connectionId}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    if (res.data && res.data.file_url) {
      configs.value[botKey][urlField] = res.data.file_url
      if (vkAttachField && res.data.vk_attachment) {
        configs.value[botKey][vkAttachField] = res.data.vk_attachment
      }
      toast.success('Изображение успешно загружено и синхронизировано с ВК!')
    }
  } catch (err) {
    console.error('Ошибка загрузки файла:', err)
    toast.error(err.response?.data?.detail || 'Ошибка при загрузке изображения')
  } finally {
    uploadingImage.value = false
  }
}

// Загрузка доступных товаров для ручного режима карусели
const availableProducts = ref([])
const loadProducts = async () => {
  try {
    const res = await axios.get('/api/v1/vk/marketing-bots/products-list')
    if (res.data?.products) {
      availableProducts.value = res.data.products
    }
  } catch (e) {
    console.error('Ошибка загрузки товаров:', e)
  }
}

// Загрузка живой аналитики и логов из БД
const analyticsData = ref(null)
const loadingAnalytics = ref(false)

const loadAnalytics = async () => {
  if (!props.connectionId) return
  loadingAnalytics.value = true
  try {
    const res = await axios.get(`/api/v1/vk/marketing-bots/analytics/${props.botType}/${props.connectionId}`)
    analyticsData.value = res.data
  } catch (e) {
    console.error('Ошибка загрузки аналитики:', e)
  } finally {
    loadingAnalytics.value = false
  }
}

// Пересчет аудитории для рассылки
const countingAudience = ref(false)
const audienceCount = ref(null)
const startingBroadcast = ref(false)

const countAudience = async () => {
  if (!props.connectionId) return
  countingAudience.value = true
  try {
    const res = await axios.post(`/api/v1/vk/marketing-bots/broadcast/count-audience/${props.connectionId}`, configs.value.broadcast)
    audienceCount.value = res.data.audience_count
    toast.info(`Найдено подходящих получателей: ${audienceCount.value}`)
  } catch (e) {
    toast.error('Ошибка подсчета аудитории')
  } finally {
    countingAudience.value = false
  }
}

const runBroadcast = async () => {
  if (!confirm('Запустить отправку рассылки по выбранному сегменту клиентов?')) return
  startingBroadcast.value = true
  try {
    const res = await axios.post(`/api/v1/vk/marketing-bots/broadcast/start/${props.connectionId}`, configs.value.broadcast)
    toast.success(res.data.message || 'Рассылка успешно запущена!')
    loadAnalytics()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка запуска рассылки')
  } finally {
    startingBroadcast.value = false
  }
}

// Генерация превью рулетки через Pillow
const generatingWheel = ref(false)
const wheelPreviewUrl = ref('')

const generateWheelPreview = async () => {
  if (!props.connectionId) return
  generatingWheel.value = true
  try {
    const res = await axios.post(`/api/v1/vk/marketing-bots/wheel/preview-image/${props.connectionId}`, {
      sectors_config: configs.value.wheel.sectors_config
    })
    if (res.data?.image_url) {
      wheelPreviewUrl.value = res.data.image_url
      toast.success('Превью рулетки успешно сгенерировано!')
    }
  } catch (e) {
    toast.error('Ошибка генерации превью рулетки')
  } finally {
    generatingWheel.value = false
  }
}

// Реальная отправка тестового сообщения в ВК администратору
const sendTest = async (channel = 'vk') => {
  if (!props.connectionId) {
    toast.error('Не выбрано подключение')
    return
  }
  if (channel === 'max') {
    testingMax.value = true
  } else {
    testingVk.value = true
  }
  try {
    const adminId = configs.value[props.botType]?.test_admin_vk_ids?.[0] || null
    const adminPhonesList = configs.value[props.botType]?.test_admin_phones
    const adminPhone = Array.isArray(adminPhonesList) && adminPhonesList.length > 0 ? adminPhonesList[0] : (adminPhonesList || '79220079019')

    const res = await axios.post(`/api/v1/vk/marketing-bots/test-send/${props.botType}/${props.connectionId}`, {
      channel,
      admin_vk_id: adminId,
      admin_phone: adminPhone
    })
    if (res.data && res.data.status === 'success') {
      toast.success(res.data.message || `Тестовое сообщение успешно отправлено в ${channel === 'max' ? 'MAX (с личного номера)' : 'ВКонтакте'}!`)
    } else {
      toast.error(res.data?.detail || res.data?.message || 'Ошибка отправки теста')
    }
  } catch (e) {
    console.error('Ошибка отправки теста:', e)
    const errText = e.response?.data?.detail || `Не удалось отправить тестовое сообщение в ${channel === 'max' ? 'MAX' : 'ВК'}`
    toast.error(errText)
  } finally {
    testingVk.value = false
    testingMax.value = false
  }
}

// Сброс к эталонным заводским шаблонам
const resetToDefaults = () => {
  if (confirm(`Сбросить все тексты и настройки бота "${currentMeta.value.title}" к эталонным заводским шаблонам?`)) {
    fetchConfig()
    toast.info('Настройки перезагружены из БД')
  }
}

// Добавление новой кнопки меню в VkShopBot
const addMenuButton = () => {
  if (!configs.value.shop.menu_buttons) configs.value.shop.menu_buttons = []
  configs.value.shop.menu_buttons.push({
    id: Date.now(),
    text: 'Новая кнопка',
    color: 'primary',
    action: 'actions_text',
    active: true
  })
}

const removeMenuButton = (index) => {
  configs.value.shop.menu_buttons.splice(index, 1)
}

// Добавление сектора в VkWheelOfFortuneBot
const addWheelSector = () => {
  if (!configs.value.wheel.sectors_config) configs.value.wheel.sectors_config = []
  configs.value.wheel.sectors_config.push({
    id: Date.now(),
    title: 'Подарок',
    full: 'Подарок к заказу от 1000 ₽',
    type: 'promo',
    val: 'GIFT' + Math.floor(Math.random() * 100),
    weight: 10,
    color: '#00897B'
  })
}

const removeWheelSector = (index) => {
  configs.value.wheel.sectors_config.splice(index, 1)
}

const totalWheelWeight = computed(() => {
  const sectors = configs.value.wheel.sectors_config || []
  return sectors.reduce((acc, s) => acc + Number(s.weight || 0), 0)
})

// Форматирование превью сообщений (замена плейсхолдеров)

const previewImageUrl = computed(() => {
  const b = props.botType
  if (b === 'shop') return configs.value.shop.welcome_photo_url
  if (b === 'retention') return configs.value.retention.newbie_photo_url || configs.value.retention.sleeping_photo_url
  if (b === 'wheel') return wheelPreviewUrl.value || configs.value.wheel.wheel_bg_image_url
  if (b === 'broadcast') return configs.value.broadcast.broadcast_photo_url
  if (b === 'referral') return configs.value.referral.cert_bg_image_url
  return null
})

const previewText = computed(() => {
  const b = props.botType
  if (b === 'shop') {
    return (configs.value.shop.welcome_message_verified || '').replace('{first_name}', 'Вячеслав')
  } else if (b === 'retention') {
    return (configs.value.retention.sleeping_message_template || '').replace('{first_name}', 'Вячеслав').replace('{promo_code}', configs.value.retention.sleeping_promo_code)
  } else if (b === 'nps') {
    return (configs.value.nps.msg_ask_rating || '').replace('{order_number}', '1048')
  } else if (b === 'wheel') {
    return `🎉 Вы выиграли в Колесе Фортуны!\nВаш приз: Ролл «Калифорния» в подарок к заказу от 1200 ₽!\nПромокод: FORTUNA10 (действует 48 часов) 🍣`
  } else if (b === 'broadcast') {
    return (configs.value.broadcast.broadcast_text || '').replace('{first_name}', 'Вячеслав')
  } else if (b === 'referral') {
    return (configs.value.referral.msg_ambassador_info || '').replace('{referral_code}', 'VR-03921')
  }
  return 'Сообщение бота...'
})
</script>

<template>
  <VDialog
    :model-value="modelValue"
    max-width="1280px"
    scrollable
    persistent
    @update:model-value="emit('update:modelValue', $event)"
  >
    <VCard class="vk-modal-card">
      <!-- HEADER МОДАЛЬНОГО ОКНА -->
      <VCardItem class="modal-header border-b py-3 px-6">
        <div class="d-flex align-center justify-space-between w-100 flex-wrap gap-2">
          <!-- Левая часть: Иконка и Название -->
          <div class="d-flex align-center gap-3">
            <VAvatar :color="currentMeta.color" variant="tonal" size="48" class="rounded-lg elevation-1">
              <VIcon :icon="currentMeta.icon" size="28" />
            </VAvatar>
            <div>
              <div class="d-flex align-center gap-2">
                <span class="text-h6 font-weight-bold">{{ currentMeta.title }}</span>
                <VChip
                  :color="currentConfig.is_active ? 'success' : 'secondary'"
                  size="small"
                  variant="flat"
                  class="font-weight-medium"
                >
                  <VIcon start :icon="currentConfig.is_active ? 'ri-checkbox-circle-fill' : 'ri-pause-circle-line'" size="14" />
                  {{ currentConfig.is_active ? 'Активен' : 'Выключен' }}
                </VChip>
              </div>
              <div class="text-caption text-medium-emphasis">{{ currentMeta.subtitle }}</div>
            </div>
          </div>

          <!-- Правая часть: Каналы ВК и MAX + Главный рубильник + Закрыть -->
          <div class="d-flex align-center gap-3 flex-wrap">
            <div class="d-flex align-center gap-2 bg-light px-3 py-1 rounded border">
              <span class="text-caption font-weight-medium text-no-wrap"><VIcon icon="ri-vk-line" size="14" color="primary" /> ВК:</span>
              <VSwitch
                v-model="currentConfig.vk_enabled"
                color="primary"
                density="compact"
                hide-details
              />
            </div>

            <div class="d-flex align-center gap-2 bg-light px-3 py-1 rounded border">
              <span class="text-caption font-weight-medium text-no-wrap"><VIcon icon="ri-chat-voice-line" size="14" color="success" /> MAX (Личный №):</span>
              <VSwitch
                v-model="currentConfig.max_enabled"
                color="success"
                density="compact"
                hide-details
              />
            </div>

            <div class="d-flex align-center gap-2 bg-light px-3 py-1 rounded border">
              <span class="text-caption font-weight-medium text-no-wrap">Тест (админы):</span>
              <VSwitch
                v-model="currentConfig.test_mode_only_admins"
                color="warning"
                density="compact"
                hide-details
              />
            </div>

            <!-- Поле ввода ID администраторов при активном тест-режиме -->
            <div v-if="currentConfig.test_mode_only_admins" style="min-width: 220px;">
              <VCombobox
                v-model="currentConfig.test_admin_vk_ids"
                multiple
                chips
                closable-chips
                density="compact"
                label="VK ID админов для теста"
                placeholder="Ввод ID + Enter"
                hide-details
                variant="outlined"
              />
            </div>

            <div class="d-flex align-center gap-2 bg-light px-3 py-1 rounded border">
              <span class="text-caption font-weight-bold text-no-wrap">Статус бота:</span>
              <VSwitch
                v-model="currentConfig.is_active"
                color="success"
                density="compact"
                hide-details
              />
            </div>

            <VBtn
              icon="ri-close-line"
              variant="text"
              size="small"
              @click="emit('update:modelValue', false)"
            />
          </div>
        </div>
      </VCardItem>

      <!-- BODY: ДВЕ КОЛОНКИ (ТАБЫ С НАСТРОЙКАМИ И СМАРТФОН-ПРЕВЬЮ) -->
      <VCardText class="pa-0 modal-body">
        <VRow no-gutters class="fill-height">
          <!-- ЛЕВАЯ КОЛОНКА: ВКЛАДКИ И КОНСТРУКТОРЫ -->
          <VCol cols="12" md="7" lg="8" class="border-e d-flex flex-column" style="max-height: 75vh; overflow-y: auto;">
            <!-- ПАНЕЛЬ ВКЛАДОК (ГАРАНТИРОВАННОЕ ПЕРЕКЛЮЧЕНИЕ VBTN) -->
            <div class="d-flex flex-wrap gap-2 pa-3 border-b bg-surface sticky-tabs">
              <VBtn
                v-for="(tab, idx) in currentMeta.tabs"
                :key="idx"
                :variant="activeTab === idx ? 'flat' : 'tonal'"
                :color="activeTab === idx ? currentMeta.color : 'secondary'"
                size="small"
                :prepend-icon="tab.icon"
                @click="activeTab = idx"
              >
                {{ tab.title }}
              </VBtn>
            </div>

            <div class="pa-6">
              <!-- ==================== БОТ 1: VK SHOP BOT ==================== -->
              <div v-if="botType === 'shop'">
                <!-- Вкладка 1.1: Главное меню и Приветствие -->
                <div v-if="activeTab === 0" class="d-flex flex-column gap-5">
                  <VAlert type="info" variant="tonal" density="compact" class="text-caption">
                    Клиент открывает диалог с группой и сразу видит интерактивное меню с кнопками. Вы можете настроить цвет кнопок по стандартам ВКонтакте.
                  </VAlert>

                  <VTextField
                    v-model="configs.shop.trigger_keywords"
                    label="Слова-триггеры для открытия меню (через запятую)"
                    density="comfortable"
                    prepend-inner-icon="ri-key-line"
                    variant="outlined"
                    hint="Например: меню, начать, start, каталог, заказать, роллы"
                    persistent-hint
                  />

                  <VTextarea
                    v-model="configs.shop.welcome_message_verified"
                    label="Приветствие для верифицированного клиента (с подстановкой имени)"
                    variant="outlined"
                    rows="2"
                    density="comfortable"
                    hint="Поддерживаемые теги: {first_name}, {last_name}, {bonus_balance}"
                    persistent-hint
                  />

                  <VTextarea
                    v-model="configs.shop.welcome_message_guest"
                    label="Приветствие для нового гостя (без привязанного телефона)"
                    variant="outlined"
                    rows="2"
                    density="comfortable"
                    hint="Текст, который видит человек, ещё не зарегистрированный в доставке"
                    persistent-hint
                  />

                  <!-- Загрузка приветственного баннера -->
                  <div class="d-flex align-center gap-4 pa-3 rounded border bg-var-theme-background">
                    <VAvatar v-if="configs.shop.welcome_photo_url" rounded="lg" size="64" :image="configs.shop.welcome_photo_url" class="border" />
                    <VAvatar v-else rounded="lg" size="64" color="primary" variant="tonal">
                      <VIcon icon="ri-image-add-line" size="28" />
                    </VAvatar>
                    <div class="flex-grow-1">
                      <VFileInput
                        label="Загрузить баннер приветствия (JPG, PNG, WEBP)"
                        accept="image/*"
                        prepend-icon="ri-upload-cloud-line"
                        density="compact"
                        hide-details
                        :loading="uploadingImage"
                        @change="e => handleFileUpload(e, 'shop', 'welcome_photo_url', 'welcome_photo_vk_id')"
                      />
                      <div v-if="configs.shop.welcome_photo_url" class="d-flex align-center gap-2 mt-1">
                        <span class="text-caption text-success">✓ Файл загружен в /media/img/vk_bots/shop/</span>
                        <VBtn size="x-small" color="error" variant="text" @click="configs.shop.welcome_photo_url = null">Удалить</VBtn>
                      </div>
                    </div>
                  </div>

                  <div class="d-flex gap-4">
                    <VSwitch
                      v-model="configs.shop.show_on_start"
                      label="Показывать меню при нажатии «Начать»"
                      color="primary"
                      density="comfortable"
                    />
                    <VSwitch
                      v-model="configs.shop.attach_keyboard_always"
                      label="Прикреплять меню к каждому ответу"
                      color="primary"
                      density="comfortable"
                    />
                  </div>

                  <div class="d-flex align-center justify-space-between mt-2">
                    <span class="text-subtitle-2 font-weight-bold">Кнопки главного меню в диалоге ВКонтакте</span>
                    <VBtn size="small" variant="tonal" color="primary" prepend-icon="ri-add-line" @click="addMenuButton">
                      Добавить кнопку
                    </VBtn>
                  </div>

                  <VTable density="compact" class="border rounded">
                    <thead>
                      <tr>
                        <th style="width: 50px;">Вкл</th>
                        <th>Текст на кнопке</th>
                        <th style="width: 140px;">Цвет ВК</th>
                        <th style="width: 170px;">Действие</th>
                        <th style="width: 40px;"></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(btn, idx) in configs.shop.menu_buttons" :key="btn.id || idx">
                        <td>
                          <VCheckbox v-model="btn.active" density="compact" hide-details />
                        </td>
                        <td>
                          <VTextField v-model="btn.text" density="compact" variant="plain" hide-details />
                        </td>
                        <td>
                          <VSelect
                            v-model="btn.color"
                            density="compact"
                            variant="outlined"
                            hide-details
                            :items="[
                              { title: 'Синяя (Primary)', value: 'primary' },
                              { title: 'Зелёная (Positive)', value: 'positive' },
                              { title: 'Красная (Negative)', value: 'negative' },
                              { title: 'Белая (Secondary)', value: 'secondary' }
                            ]"
                          />
                        </td>
                        <td>
                          <VSelect
                            v-model="btn.action"
                            density="compact"
                            variant="outlined"
                            hide-details
                            :items="[
                              { title: 'Карусель товаров', value: 'carousel' },
                              { title: 'Повтор заказа iiko', value: 'repeat_order' },
                              { title: 'Текст акций', value: 'actions_text' },
                              { title: 'Статус доставки', value: 'status_iiko' },
                              { title: 'Баланс бонусов', value: 'bonus_balance' },
                              { title: 'Позвать оператора', value: 'operator' }
                            ]"
                          />
                        </td>
                        <td>
                          <VBtn icon="ri-delete-bin-line" size="x-small" variant="text" color="error" @click="removeMenuButton(idx)" />
                        </td>
                      </tr>
                    </tbody>
                  </VTable>
                </div>

                <!-- Вкладка 1.2: Витрина и Карусель товаров -->
                <div v-else-if="activeTab === 1" class="d-flex flex-column gap-4">
                  <VSelect
                    v-model="configs.shop.carousel_source_mode"
                    label="Источник товаров для карусели ВКонтакте"
                    variant="outlined"
                    density="comfortable"
                    :items="[
                      { title: 'Авто-выбор: Топ-10 хитов продаж по базе iiko за 30 дней', value: 'auto_top_sales' },
                      { title: 'Ручной список избранных позиций', value: 'featured_manual' }
                    ]"
                  />

                  <!-- Ручной выбор товаров для карусели из БД -->
                  <div v-if="configs.shop.carousel_source_mode === 'featured_manual'">
                    <VAutocomplete
                      v-model="configs.shop.featured_product_ids"
                      :items="availableProducts"
                      item-title="name"
                      item-value="id"
                      multiple
                      chips
                      closable-chips
                      label="Выберите блюда из меню для карусели (до 10 шт)"
                      variant="outlined"
                      density="comfortable"
                      hint="Товары будут отображаться в карусели в выбранном порядке"
                      persistent-hint
                    >
                      <template #chip="{ props, item }">
                        <VChip v-bind="props" color="primary" size="small">
                          {{ item.raw.name }} ({{ item.raw.price }} ₽)
                        </VChip>
                      </template>
                    </VAutocomplete>
                  </div>

                  <VSwitch
                    v-model="configs.shop.hide_stop_list_items"
                    label="Автоматически скрывать блюда из стоп-листа iiko"
                    color="primary"
                    density="comfortable"
                    hint="Блюдо мгновенно исчезает из карусели, если закончились ингредиенты"
                    persistent-hint
                  />

                  <VRow>
                    <VCol cols="12" md="6">
                      <VSelect
                        v-model="configs.shop.card_button_1_mode"
                        label="Основная кнопка карточки товара"
                        variant="outlined"
                        density="comfortable"
                        :items="[
                          { title: 'Добавить в корзину ВК', value: 'add_to_vk_cart' },
                          { title: 'Перейти к заказу на сайте', value: 'link_to_site' }
                        ]"
                      />
                    </VCol>
                    <VCol cols="12" md="6">
                      <VSelect
                        v-model="configs.shop.card_button_2_mode"
                        label="Вторая кнопка карточки"
                        variant="outlined"
                        density="comfortable"
                        :items="[
                          { title: 'Ссылка на карточку на сайте', value: 'link_to_site_product' },
                          { title: 'Подробнее о составе', value: 'show_modifiers' }
                        ]"
                      />
                    </VCol>
                  </VRow>
                </div>

                <!-- Вкладка 1.3: Повтор заказа и Оформление -->
                <div v-else-if="activeTab === 2" class="d-flex flex-column gap-4">
                  <VSwitch
                    v-model="configs.shop.enable_repeat_order"
                    label="Включить функцию «Повторить прошлый заказ в 1 клик»"
                    color="success"
                    density="comfortable"
                    hint="Бот находит прошлые заказы гостя по номеру телефона и предлагает повторить"
                    persistent-hint
                  />

                  <VRow>
                    <VCol cols="12" md="6">
                      <VSelect
                        v-model="configs.shop.repeat_order_lookback_count"
                        label="Сколько прошлых заказов предлагать на выбор"
                        variant="outlined"
                        density="comfortable"
                        :items="[
                          { title: 'Только последний (1 заказ)', value: 1 },
                          { title: 'До 3 последних заказов', value: 3 }
                        ]"
                      />
                    </VCol>
                    <VCol cols="12" md="6">
                      <VSelect
                        v-model="configs.shop.order_creation_mode"
                        label="Режим создания заказа"
                        variant="outlined"
                        density="comfortable"
                        :items="[
                          { title: 'Прямая отправка в iikoCloud + БД', value: 'direct_iiko_and_db' },
                          { title: 'Черновик на подтверждение оператору', value: 'operator_confirmation' }
                        ]"
                      />
                    </VCol>
                  </VRow>

                  <div class="pa-3 rounded border bg-var-theme-background">
                    <VSwitch
                      v-model="configs.shop.allow_bonus_payment_in_bot"
                      label="Разрешить списание бонусов iiko при заказе через ВК"
                      color="primary"
                      density="comfortable"
                      hide-details
                    />
                    <div v-if="configs.shop.allow_bonus_payment_in_bot" class="mt-3">
                      <div class="text-caption font-weight-medium mb-1">
                        Максимальный % оплаты чека бонусами: {{ configs.shop.max_bonus_payment_percent }}%
                      </div>
                      <VSlider
                        v-model="configs.shop.max_bonus_payment_percent"
                        min="5"
                        max="100"
                        step="5"
                        thumb-label
                        color="primary"
                      />
                    </div>
                  </div>

                  <VRow>
                    <VCol cols="12" md="6">
                      <VTextField
                        v-model="configs.shop.min_order_sum"
                        type="number"
                        label="Минимальная сумма заказа через ВК (₽)"
                        variant="outlined"
                        density="comfortable"
                      />
                    </VCol>
                    <VCol cols="12" md="6">
                      <VTextField
                        v-model="configs.shop.first_vk_order_discount_percent"
                        type="number"
                        label="Скидка на 1-й заказ через ВК (%)"
                        variant="outlined"
                        density="comfortable"
                      />
                    </VCol>
                  </VRow>

                  <VTextarea
                    v-model="configs.shop.status_check_template"
                    label="Шаблон ответа на кнопку «Где мой заказ?»"
                    variant="outlined"
                    rows="2"
                    density="comfortable"
                    hint="Теги: {order_number}, {status_human}, {courier_name}"
                    persistent-hint
                  />
                </div>

                <!-- Вкладка 1.4: Мессенджер MAX (Личный №) -->
                <div v-else-if="activeTab === 3">
                  <VkMarketingBotMaxSettings bot-type="shop" v-model="configs.shop" />
                </div>

                <!-- Вкладка 1.5: Конверсия и статистика -->
                <div v-else-if="activeTab === 4" class="d-flex flex-column gap-4">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <div class="d-flex align-center gap-2">
                      <span class="text-subtitle-2 font-weight-bold">Канал:</span>
                      <VBtnToggle v-model="selectedAnalyticsChannel" mandatory density="compact" color="primary" variant="outlined">
                        <VBtn value="all" size="small">🌐 Все каналы</VBtn>
                        <VBtn value="vk" size="small">ВКонтакте</VBtn>
                        <VBtn value="max" size="small">MAX (Личный №)</VBtn>
                      </VBtnToggle>
                    </div>
                  </div>
                  <VRow>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="primary" class="pa-4 text-center">
                        <div class="text-caption">Заказов за 30 дней</div>
                        <div class="text-h4 font-weight-bold mt-1">{{ activeMetrics?.orders_count ?? '0' }}</div>
                      </VCard>
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="success" class="pa-4 text-center">
                        <div class="text-caption">Сумма выручки</div>
                        <div class="text-h4 font-weight-bold mt-1">{{ Math.round(activeMetrics?.total_revenue || 0).toLocaleString() }} ₽</div>
                      </VCard>
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="info" class="pa-4 text-center">
                        <div class="text-caption">Конверсия в заказ</div>
                        <div class="text-h4 font-weight-bold mt-1">{{ activeMetrics?.conversion_rate ?? '0' }}%</div>
                      </VCard>
                    </VCol>
                  </VRow>

                  <div class="d-flex align-center justify-space-between mt-2">
                    <span class="text-subtitle-2 font-weight-bold">Последние события диалогов магазина</span>
                    <VBtn size="small" variant="text" prepend-icon="ri-refresh-line" :loading="loadingAnalytics" @click="loadAnalytics">Обновить</VBtn>
                  </div>

                  <VTable density="compact" class="border rounded">
                    <thead>
                      <tr>
                        <th>Время</th>
                        <th>Аккаунт</th>
                        <th>Событие</th>
                        <th>Текст</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="!activeLogs || activeLogs.length === 0">
                        <td colspan="5" class="text-center py-4 text-medium-emphasis">События пока не зафиксированы</td>
                      </tr>
                      <tr v-for="log in activeLogs" :key="log.id">
                        <td class="text-no-wrap text-caption">{{ log.created_at ? new Date(log.created_at).toLocaleString('ru-RU') : '-' }}</td>
                        <td>{{ log.account_id || '-' }}</td>
                        <td><VChip size="x-small" color="primary" label>{{ log.event_type }}</VChip></td>
                        <td class="text-truncate" style="max-width: 250px;">{{ log.text || '-' }}</td>
                        <td><VChip size="x-small" :color="log.status === 'error' ? 'error' : 'success'" variant="tonal">{{ log.status }}</VChip></td>
                      </tr>
                    </tbody>
                  </VTable>
                </div>
              </div>

              <!-- ==================== БОТ 2: VK RETENTION BOT ==================== -->
              <div v-else-if="botType === 'retention'">
                <!-- Вкладка 2.1: Цепочки RFM -->
                <div v-if="activeTab === 0" class="d-flex flex-column gap-5">
                  <!-- Этап 1: Новичок -->
                  <VCard variant="outlined" class="pa-4 border">
                    <div class="d-flex align-center justify-space-between mb-3">
                      <div class="d-flex align-center gap-2">
                        <VChip color="primary" size="small" label>ЭТАП 1</VChip>
                        <span class="font-weight-bold">Новичок после первого заказа</span>
                      </div>
                      <VSwitch v-model="configs.retention.newbie_enabled" color="primary" density="compact" hide-details />
                    </div>
                    <VRow>
                      <VCol cols="12" sm="4">
                        <VTextField v-model="configs.retention.newbie_days" type="number" label="Дней после 1-го заказа" density="compact" variant="outlined" />
                      </VCol>
                      <VCol cols="12" sm="4">
                        <VSelect
                          v-model="configs.retention.newbie_gift_mode"
                          label="Тип подарка"
                          density="compact"
                          variant="outlined"
                          :items="[
                            { title: 'Промокод на скидку', value: 'promo_code' },
                            { title: 'Сгораемые бонусы iiko', value: 'expiring_iiko_points' },
                            { title: 'Промокод + Бонусы', value: 'both' }
                          ]"
                        />
                      </VCol>
                      <VCol cols="12" sm="4">
                        <VTextField v-model="configs.retention.newbie_promo_code" label="Промокод скидки" density="compact" variant="outlined" />
                      </VCol>
                    </VRow>
                    <VTextarea v-model="configs.retention.newbie_message_template" label="Текст сообщения" rows="2" density="compact" variant="outlined" class="mt-2" />
                    <!-- Картинка этапа 1 -->
                    <div class="d-flex align-center gap-3 mt-2 pa-2 rounded border bg-var-theme-background">
                      <VAvatar v-if="configs.retention.newbie_photo_url" rounded="lg" size="48" :image="configs.retention.newbie_photo_url" class="border" />
                      <div class="flex-grow-1">
                        <VFileInput
                          label="Баннер для новичка (необязательно)"
                          accept="image/*"
                          prepend-icon="ri-image-add-line"
                          density="compact"
                          hide-details
                          @change="e => handleFileUpload(e, 'retention', 'newbie_photo_url', 'newbie_attachment_photo')"
                        />
                      </div>
                      <VBtn v-if="configs.retention.newbie_photo_url" size="x-small" color="error" variant="text" @click="configs.retention.newbie_photo_url = null; configs.retention.newbie_attachment_photo = null">Удалить</VBtn>
                    </div>
                  </VCard>

                  <!-- Этап 2: Засыпающий -->
                  <VCard variant="outlined" class="pa-4 border">
                    <div class="d-flex align-center justify-space-between mb-3">
                      <div class="d-flex align-center gap-2">
                        <VChip color="warning" size="small" label>ЭТАП 2</VChip>
                        <span class="font-weight-bold">Засыпающий гость</span>
                      </div>
                      <VSwitch v-model="configs.retention.sleeping_enabled" color="warning" density="compact" hide-details />
                    </div>
                    <VRow>
                      <VCol cols="12" sm="4">
                        <VTextField v-model="configs.retention.sleeping_days" type="number" label="Дней без заказов" density="compact" variant="outlined" />
                      </VCol>
                      <VCol cols="12" sm="4">
                        <VSelect
                          v-model="configs.retention.sleeping_gift_mode"
                          label="Тип подарка"
                          density="compact"
                          variant="outlined"
                          :items="[
                            { title: 'Сгораемые бонусы iiko', value: 'expiring_iiko_points' },
                            { title: 'Промокод на скидку', value: 'promo_code' },
                            { title: 'Промокод + Бонусы', value: 'both' }
                          ]"
                        />
                      </VCol>
                      <VCol cols="12" sm="4">
                        <VTextField v-model="configs.retention.sleeping_promo_code" label="Промокод / Название бонуса" density="compact" variant="outlined" />
                      </VCol>
                    </VRow>
                    <VTextarea v-model="configs.retention.sleeping_message_template" label="Текст сообщения" rows="2" density="compact" variant="outlined" class="mt-2" />
                    <!-- Картинка этапа 2 -->
                    <div class="d-flex align-center gap-3 mt-2 pa-2 rounded border bg-var-theme-background">
                      <VAvatar v-if="configs.retention.sleeping_photo_url" rounded="lg" size="48" :image="configs.retention.sleeping_photo_url" class="border" />
                      <div class="flex-grow-1">
                        <VFileInput
                          label="Баннер засыпающего (необязательно)"
                          accept="image/*"
                          prepend-icon="ri-image-add-line"
                          density="compact"
                          hide-details
                          @change="e => handleFileUpload(e, 'retention', 'sleeping_photo_url', 'sleeping_attachment_photo')"
                        />
                      </div>
                      <VBtn v-if="configs.retention.sleeping_photo_url" size="x-small" color="error" variant="text" @click="configs.retention.sleeping_photo_url = null; configs.retention.sleeping_attachment_photo = null">Удалить</VBtn>
                    </div>
                  </VCard>

                  <!-- Этап 3: Потерянный VIP -->
                  <VCard variant="outlined" class="pa-4 border">
                    <div class="d-flex align-center justify-space-between mb-3">
                      <div class="d-flex align-center gap-2">
                        <VChip color="error" size="small" label>ЭТАП 3</VChip>
                        <span class="font-weight-bold">Потерянный VIP-клиент</span>
                      </div>
                      <VSwitch v-model="configs.retention.lost_vip_enabled" color="error" density="compact" hide-details />
                    </div>
                    <VRow>
                      <VCol cols="12" sm="3">
                        <VTextField v-model="configs.retention.lost_vip_days" type="number" label="Дней без заказов" density="compact" variant="outlined" />
                      </VCol>
                      <VCol cols="12" sm="3">
                        <VTextField v-model="configs.retention.lost_vip_min_spent" type="number" label="Мин. LTV заказов (₽)" density="compact" variant="outlined" />
                      </VCol>
                      <VCol cols="12" sm="3">
                        <VSelect
                          v-model="configs.retention.lost_vip_gift_mode"
                          label="Тип подарка"
                          density="compact"
                          variant="outlined"
                          :items="[
                            { title: 'Блюдо + Бонусы (Both)', value: 'both' },
                            { title: 'Промокод на блюдо', value: 'promo_code' },
                            { title: 'Бонусы iiko', value: 'expiring_iiko_points' }
                          ]"
                        />
                      </VCol>
                      <VCol cols="12" sm="3">
                        <VTextField v-model="configs.retention.lost_vip_promo_code" label="VIP-промокод" density="compact" variant="outlined" />
                      </VCol>
                    </VRow>
                    <VTextarea v-model="configs.retention.lost_vip_message_template" label="Текст сообщения" rows="2" density="compact" variant="outlined" class="mt-2" />
                    <!-- Картинка этапа 3 -->
                    <div class="d-flex align-center gap-3 mt-2 pa-2 rounded border bg-var-theme-background">
                      <VAvatar v-if="configs.retention.lost_vip_photo_url" rounded="lg" size="48" :image="configs.retention.lost_vip_photo_url" class="border" />
                      <div class="flex-grow-1">
                        <VFileInput
                          label="Баннер VIP-клиента (необязательно)"
                          accept="image/*"
                          prepend-icon="ri-image-add-line"
                          density="compact"
                          hide-details
                          @change="e => handleFileUpload(e, 'retention', 'lost_vip_photo_url', 'lost_vip_attachment_photo')"
                        />
                      </div>
                      <VBtn v-if="configs.retention.lost_vip_photo_url" size="x-small" color="error" variant="text" @click="configs.retention.lost_vip_photo_url = null; configs.retention.lost_vip_attachment_photo = null">Удалить</VBtn>
                    </div>
                  </VCard>
                </div>

                <!-- Вкладка 2.2: Бонусный Будильник iiko -->
                <div v-else-if="activeTab === 1" class="d-flex flex-column gap-4">
                  <VSwitch
                    v-model="configs.retention.enable_expiring_bonuses"
                    label="Включить «Бонусный Будильник» (начисление сгораемых бонусов iiko)"
                    color="success"
                    density="comfortable"
                  />
                  <VRow>
                    <VCol cols="6">
                      <VTextField v-model="configs.retention.expiring_bonus_amount" type="number" label="Сумма подарочных бонусов" variant="outlined" density="comfortable" suffix="бонусов" />
                    </VCol>
                    <VCol cols="6">
                      <VTextField v-model="configs.retention.expiring_bonus_hours" type="number" label="Срок действия бонусов" variant="outlined" density="comfortable" suffix="часов (72ч)" />
                    </VCol>
                  </VRow>

                  <div class="d-flex align-center gap-4">
                    <VSwitch
                      v-model="configs.retention.send_burn_reminder"
                      label="Отправлять напоминание в ВК перед сгоранием"
                      color="warning"
                      density="comfortable"
                    />
                    <VTextField
                      v-if="configs.retention.send_burn_reminder"
                      v-model="configs.retention.burn_reminder_hours_before"
                      type="number"
                      label="За сколько часов напоминать"
                      style="max-width: 200px;"
                      density="compact"
                      variant="outlined"
                      suffix="ч"
                    />
                  </div>
                  <VTextarea
                    v-model="configs.retention.burn_reminder_template"
                    label="Шаблон напоминания о сгорании"
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  />
                </div>

                <!-- Вкладка 2.3: Лимиты и Безопасность -->
                <div v-else-if="activeTab === 2" class="d-flex flex-column gap-4">
                  <VRow>
                    <VCol cols="6">
                      <VTextField v-model="configs.retention.run_time_local" label="Время ежедневного запуска" variant="outlined" density="comfortable" hint="Например 16:30" persistent-hint />
                    </VCol>
                    <VCol cols="6">
                      <VTextField v-model="configs.retention.max_messages_per_day" type="number" label="Максимум сообщений в день (лимит спама)" variant="outlined" density="comfortable" />
                    </VCol>
                  </VRow>
                  <VRow>
                    <VCol cols="6">
                      <VTextField v-model="configs.retention.send_window_start" label="Начало окна отправки" variant="outlined" density="comfortable" />
                    </VCol>
                    <VCol cols="6">
                      <VTextField v-model="configs.retention.send_window_end" label="Конец окна отправки" variant="outlined" density="comfortable" />
                    </VCol>
                  </VRow>
                  <VTextField v-model="configs.retention.min_cooldown_days_between_touches" type="number" label="Кулдаун между рассылками одному клиенту (дней)" variant="outlined" density="comfortable" />
                </div>

                <!-- Вкладка 2.4: Аналитика ROI -->
                <div v-else-if="activeTab === 3" class="d-flex flex-column gap-4">
                  <VRow>
                    <VCol cols="6" sm="3">
                      <VCard variant="tonal" color="primary" class="pa-3 text-center">
                        <div class="text-caption">Кандидаты 7д</div>
                        <div class="text-h5 font-weight-bold">{{ analyticsData?.metrics?.newbie_candidates ?? 0 }}</div>
                      </VCard>
                    </VCol>
                    <VCol cols="6" sm="3">
                      <VCard variant="tonal" color="warning" class="pa-3 text-center">
                        <div class="text-caption">Кандидаты 21д</div>
                        <div class="text-h5 font-weight-bold">{{ analyticsData?.metrics?.sleeping_candidates ?? 0 }}</div>
                      </VCard>
                    </VCol>
                    <VCol cols="6" sm="3">
                      <VCard variant="tonal" color="error" class="pa-3 text-center">
                        <div class="text-caption">VIP 45д</div>
                        <div class="text-h5 font-weight-bold">{{ analyticsData?.metrics?.lost_vip_candidates ?? 0 }}</div>
                      </VCard>
                    </VCol>
                    <VCol cols="6" sm="3">
                      <VCard variant="tonal" color="success" class="pa-3 text-center">
                        <div class="text-caption">Выручка возврата</div>
                        <div class="text-h5 font-weight-bold">{{ Math.round(analyticsData?.metrics?.total_revenue_returned || 0).toLocaleString() }} ₽</div>
                      </VCard>
                    </VCol>
                  </VRow>

                  <div class="d-flex align-center justify-space-between mt-2">
                    <span class="text-subtitle-2 font-weight-bold">Журнал отправленных реактиваций</span>
                    <VBtn size="small" variant="text" prepend-icon="ri-refresh-line" :loading="loadingAnalytics" @click="loadAnalytics">Обновить</VBtn>
                  </div>

                  <VTable density="compact" class="border rounded">
                    <thead>
                      <tr>
                        <th>Время</th>
                        <th>VK ID</th>
                        <th>Триггер</th>
                        <th>Промокод</th>
                        <th>Выручка заказа</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="!activeLogs || activeLogs.length === 0">
                        <td colspan="5" class="text-center py-4 text-medium-emphasis">Сообщений пока не отправлялось</td>
                      </tr>
                      <tr v-for="log in activeLogs" :key="log.id">
                        <td class="text-caption text-no-wrap">{{ log.sent_at ? new Date(log.sent_at).toLocaleString('ru-RU') : '-' }}</td>
                        <td>{{ log.vk_id }}</td>
                        <td><VChip size="x-small" color="primary" label>{{ log.trigger_type }}</VChip></td>
                        <td><code>{{ log.promo_code || '-' }}</code></td>
                        <td><span class="font-weight-bold text-success">{{ log.conversion_revenue ? log.conversion_revenue + ' ₽' : '-' }}</span></td>
                      </tr>
                    </tbody>
                  </VTable>
                </div>
              </div>

              <!-- ==================== БОТ 3: VK REVIEW NPS BOT ==================== -->
              <div v-else-if="botType === 'nps'">
                <!-- Вкладка 3.1: Опрос и тайминг -->
                <div v-if="activeTab === 0" class="d-flex flex-column gap-4">
                  <VRow>
                    <VCol cols="12" sm="4">
                      <VTextField v-model="configs.nps.delay_minutes_after_delivery" type="number" label="Задержка после ДОСТАВЛЕН (мин)" variant="outlined" density="comfortable" />
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VTextField v-model="configs.nps.min_order_amount_for_nps" type="number" label="Мин. сумма чека (₽)" variant="outlined" density="comfortable" />
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VSelect
                        v-model="configs.nps.positive_rating_threshold"
                        label="Порог высокой оценки"
                        variant="outlined"
                        density="comfortable"
                        :items="[
                          { title: '4 и 5 звёзд (позитив)', value: 4 },
                          { title: 'Только 5 звёзд (позитив)', value: 5 }
                        ]"
                      />
                    </VCol>
                  </VRow>
                  <VTextarea
                    v-model="configs.nps.msg_ask_rating"
                    label="Текст первого сообщения с оценкой 1-5"
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                    hint="Теги: {order_number}, {first_name}"
                    persistent-hint
                  />
                  <VTextField v-model="configs.nps.points_for_rating" type="number" label="Баллы iiko за сам факт выставления оценки" variant="outlined" density="comfortable" suffix="бонусов" />
                </div>

                <!-- Вкладка 3.2: Ветка Позитива (4-5) -->
                <div v-else-if="activeTab === 1" class="d-flex flex-column gap-4">
                  <VTextarea
                    v-model="configs.nps.msg_positive"
                    label="Сообщение при оценке 4 или 5 звёзд"
                    rows="3"
                    variant="outlined"
                    density="comfortable"
                  />
                  <VRow>
                    <VCol cols="6">
                      <VTextField v-model="configs.nps.points_for_photo_review" type="number" label="Бонус за фото-отзыв на стене" variant="outlined" density="comfortable" suffix="бонусов (100)" />
                    </VCol>
                    <VCol cols="6">
                      <VTextField v-model="configs.nps.required_review_hashtag" label="Обязательный хэштег фото-отзыва" variant="outlined" density="comfortable" />
                    </VCol>
                  </VRow>
                  <div class="d-flex align-center justify-space-between flex-wrap gap-4">
                    <VSwitch v-model="configs.nps.require_photo_attachment" label="Требовать обязательное фото блюда в отзыве" color="primary" density="comfortable" hide-details />
                    <VTextField v-model="configs.nps.max_paid_reviews_per_month" type="number" label="Лимит оплачиваемых отзывов в месяц на 1 гостя" style="max-width: 250px;" density="compact" variant="outlined" />
                  </div>
                </div>

                <!-- Вкладка 3.3: Ветка Негатива (1-3) -->
                <div v-else-if="activeTab === 2" class="d-flex flex-column gap-4">
                  <VAlert type="warning" variant="tonal" density="compact" class="text-caption">
                    При оценке 1, 2 или 3 звезды бот НЕ публикует ничего в группу, а мгновенно создает обращение в Мультичат и тегает управляющего.
                  </VAlert>
                  <VTextarea
                    v-model="configs.nps.msg_negative"
                    label="Сообщение извинения при оценке 1-3 звезды"
                    rows="3"
                    variant="outlined"
                    density="comfortable"
                  />
                  <VTextarea
                    v-model="configs.nps.msg_negative_thank_you"
                    label="Финальный ответ после приёма претензии гостя"
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  />
                  <VSwitch v-model="configs.nps.auto_tag_multichat" label="Автоматически назначать тег «ЖАЛОБА / КОНТРОЛЬ КАЧЕСТВА» в Мультичате" color="error" density="comfortable" />
                  <VRow>
                    <VCol cols="12" sm="8">
                      <VCombobox
                        v-model="configs.nps.alert_admin_vk_ids"
                        multiple
                        chips
                        closable-chips
                        label="VK ID руководства для мгновенного алерта в ЛС"
                        placeholder="Ввод ID + Enter"
                        variant="outlined"
                        density="comfortable"
                        hint="При негативе бот сразу отправит текст жалобы этим администраторам"
                        persistent-hint
                      />
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VTextField
                        v-model="configs.nps.auto_apology_promo_code"
                        label="Извинительный промокод"
                        variant="outlined"
                        density="comfortable"
                        hint="Если хотите дарить авто-бонус"
                        persistent-hint
                      />
                    </VCol>
                  </VRow>
                </div>

                <!-- Вкладка 3.4: Дашборд -->
                <div v-else-if="activeTab === 3" class="d-flex flex-column gap-4">
                  <VRow>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="warning" class="pa-4 text-center">
                        <div class="text-caption">Средний рейтинг доставки</div>
                        <div class="text-h3 font-weight-bold mt-1">{{ analyticsData?.metrics?.average_rating || '5.0' }} ⭐</div>
                      </VCard>
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="success" class="pa-4 text-center">
                        <div class="text-caption">Позитивных оценок (4-5)</div>
                        <div class="text-h3 font-weight-bold mt-1">{{ analyticsData?.metrics?.positive_count || 0 }} 👍</div>
                      </VCard>
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="error" class="pa-4 text-center">
                        <div class="text-caption">Претензий (1-3)</div>
                        <div class="text-h3 font-weight-bold mt-1">{{ analyticsData?.metrics?.negative_count || 0 }} ⚠️</div>
                      </VCard>
                    </VCol>
                  </VRow>

                  <div class="d-flex align-center justify-space-between mt-2">
                    <span class="text-subtitle-2 font-weight-bold">Последние оценки и отзывы гостей</span>
                    <VBtn size="small" variant="text" prepend-icon="ri-refresh-line" :loading="loadingAnalytics" @click="loadAnalytics">Обновить</VBtn>
                  </div>

                  <VTable density="compact" class="border rounded">
                    <thead>
                      <tr>
                        <th>Время</th>
                        <th>Заказ №</th>
                        <th>VK ID</th>
                        <th>Оценка</th>
                        <th>Текст отзыва / претензии</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="!analyticsData?.reviews || analyticsData.reviews.length === 0">
                        <td colspan="6" class="text-center py-4 text-medium-emphasis">Оценок пока не зафиксировано</td>
                      </tr>
                      <tr v-for="rev in (analyticsData?.reviews || [])" :key="rev.id">
                        <td class="text-caption text-no-wrap">{{ rev.created_at ? new Date(rev.created_at).toLocaleString('ru-RU') : '-' }}</td>
                        <td>{{ rev.order_id || '-' }}</td>
                        <td>{{ rev.vk_id }}</td>
                        <td>
                          <VChip size="x-small" :color="rev.rating >= 4 ? 'success' : 'error'">
                            {{ rev.rating }} ⭐
                          </VChip>
                        </td>
                        <td class="text-truncate" style="max-width: 250px;">{{ rev.feedback_text || 'Без текста' }}</td>
                        <td>
                          <VChip size="x-small" :color="rev.is_resolved ? 'success' : 'warning'" variant="tonal">
                            {{ rev.is_resolved ? 'Решено' : 'В работе' }}
                          </VChip>
                        </td>
                      </tr>
                    </tbody>
                  </VTable>
                </div>
              </div>

              <!-- ==================== БОТ 4: VK WHEEL OF FORTUNE ==================== -->
              <div v-else-if="botType === 'wheel'">
                <!-- Вкладка 4.1: Конструктор Секторов -->
                <div v-if="activeTab === 0" class="d-flex flex-column gap-4">
                  <div class="d-flex align-center justify-space-between">
                    <div>
                      <span class="text-subtitle-2 font-weight-bold">Секторы колеса рулетки (8–12)</span>
                      <div class="text-caption" :class="totalWheelWeight === 100 ? 'text-success' : 'text-error font-weight-bold'">
                        Сумма вероятностей: {{ totalWheelWeight }}% {{ totalWheelWeight !== 100 ? '(должна быть строго 100%)' : '✅' }}
                      </div>
                    </div>
                    <VBtn size="small" variant="tonal" color="primary" prepend-icon="ri-add-line" @click="addWheelSector">
                      Добавить сектор
                    </VBtn>
                  </div>

                  <VTable density="compact" class="border rounded">
                    <thead>
                      <tr>
                        <th>Название</th>
                        <th>Полное описание</th>
                        <th style="width: 100px;">Тип</th>
                        <th style="width: 100px;">Промокод</th>
                        <th style="width: 75px;">Вес %</th>
                        <th style="width: 80px;">Цвет</th>
                        <th style="width: 40px;"></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(sec, idx) in configs.wheel.sectors_config" :key="sec.id || idx">
                        <td><VTextField v-model="sec.title" density="compact" variant="plain" hide-details /></td>
                        <td><VTextField v-model="sec.full" density="compact" variant="plain" hide-details /></td>
                        <td>
                          <VSelect v-model="sec.type" density="compact" variant="plain" hide-details :items="[{title:'Промокод', value:'promo'}, {title:'Баллы', value:'points'}]" />
                        </td>
                        <td><VTextField v-model="sec.val" density="compact" variant="plain" hide-details /></td>
                        <td><VTextField v-model="sec.weight" type="number" density="compact" variant="plain" hide-details /></td>
                        <td><input type="color" v-model="sec.color" style="border:none; width:32px; height:24px; cursor:pointer;" /></td>
                        <td><VBtn icon="ri-delete-bin-line" size="x-small" variant="text" color="error" @click="removeWheelSector(idx)" /></td>
                      </tr>
                    </tbody>
                  </VTable>
                </div>

                <!-- Вкладка 4.2: Условия и VIP-Спины -->
                <div v-else-if="activeTab === 1" class="d-flex flex-column gap-4">
                  <VRow>
                    <VCol cols="12" sm="6">
                      <VTextField v-model="configs.wheel.keyword" label="Слово для прокрутки (в комментах и ЛС)" variant="outlined" density="comfortable" hint="По умолчанию: КРУТИТЬ" persistent-hint />
                    </VCol>
                    <VCol cols="12" sm="6">
                      <VTextField v-model="configs.wheel.contest_post_id" type="number" label="ID конкурсного поста на стене" variant="outlined" density="comfortable" hint="Оставьте пустым для работы под всеми постами и в ЛС" persistent-hint />
                    </VCol>
                  </VRow>

                  <div class="d-flex flex-column gap-2 pa-3 rounded border bg-var-theme-background">
                    <span class="text-subtitle-2 font-weight-bold">Обязательные проверки для участия:</span>
                    <div class="d-flex flex-wrap gap-4">
                      <VSwitch v-model="configs.wheel.require_group_member" label="Подписка на сообщество" color="primary" density="compact" hide-details />
                      <VSwitch v-model="configs.wheel.require_post_like" label="Лайк на конкурсный пост" color="primary" density="compact" hide-details />
                      <VSwitch v-model="configs.wheel.require_messages_allowed" label="Разрешение сообщений от группы" color="primary" density="compact" hide-details />
                    </div>
                  </div>

                  <VRow>
                    <VCol cols="12" sm="4">
                      <VTextField v-model="configs.wheel.daily_free_spins" type="number" label="Бесплатных попыток" variant="outlined" density="comfortable" />
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VSelect
                        v-model="configs.wheel.free_spins_period"
                        label="Период попыток"
                        variant="outlined"
                        density="comfortable"
                        :items="[
                          { title: 'В сутки (каждый день)', value: 'per_day' },
                          { title: 'Раз в неделю', value: 'per_week' },
                          { title: 'Один раз за конкурс', value: 'once_per_contest' }
                        ]"
                      />
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VTextField v-model="configs.wheel.extra_spin_order_sum" type="number" label="VIP-спин за заказ от (₽)" variant="outlined" density="comfortable" hint="Авто-начисление +1 спина при доставке" persistent-hint />
                    </VCol>
                  </VRow>
                </div>

                <!-- Вкладка 4.3: Генератор Рулетки -->
                <div v-else-if="activeTab === 2" class="d-flex flex-column gap-4 text-center">
                  <VAlert type="info" variant="tonal" density="compact" class="text-caption text-start">
                    Картинка Колеса Фортуны генерируется на сервере с помощью Python Pillow и прикрепляется к комментарию бота.
                  </VAlert>
                  <!-- Загрузчик фонового шаблона -->
                  <div class="d-flex align-center gap-3 pa-3 rounded border bg-var-theme-background text-start">
                    <VAvatar v-if="configs.wheel.wheel_bg_image_url" rounded="lg" size="48" :image="configs.wheel.wheel_bg_image_url" class="border" />
                    <div class="flex-grow-1">
                      <VFileInput
                        label="Фоновый шаблон рулетки (необязательно, PNG 600x600)"
                        accept="image/*"
                        prepend-icon="ri-image-add-line"
                        density="compact"
                        hide-details
                        @change="e => handleFileUpload(e, 'wheel', 'wheel_bg_image_url')"
                      />
                    </div>
                    <VBtn v-if="configs.wheel.wheel_bg_image_url" size="x-small" color="error" variant="text" @click="configs.wheel.wheel_bg_image_url = null">Удалить</VBtn>
                  </div>

                  <VSwitch
                    v-model="configs.wheel.draw_user_avatar_in_center"
                    label="Вписывать круглую аватарку победителя в центр рулетки при генерации ответа"
                    color="primary"
                    density="comfortable"
                    class="text-start"
                  />

                  <div class="d-flex flex-column align-center gap-3">
                    <div class="pa-4 bg-light rounded d-flex justify-center border w-100">
                      <img v-if="wheelPreviewUrl" :src="wheelPreviewUrl" style="max-width: 220px; max-height: 220px; object-fit: contain;" class="rounded" />
                      <svg v-else viewBox="0 0 200 200" width="160" height="160">
                        <circle cx="100" cy="100" r="95" fill="#f8f9fa" stroke="#e0e0e0" stroke-width="4" />
                        <path d="M100,100 L100,5 A95,95 0 0,1 195,100 Z" fill="#E53935" />
                        <path d="M100,100 L195,100 A95,95 0 0,1 100,195 Z" fill="#FB8C00" />
                        <path d="M100,100 L100,195 A95,95 0 0,1 5,100 Z" fill="#43A047" />
                        <path d="M100,100 L5,100 A95,95 0 0,1 100,5 Z" fill="#1E88E5" />
                        <circle cx="100" cy="100" r="24" fill="#ffffff" stroke="#333" stroke-width="3" />
                        <polygon points="95,10 105,10 100,2" fill="#212121" />
                      </svg>
                    </div>

                    <VBtn
                      variant="tonal"
                      color="primary"
                      prepend-icon="ri-magic-line"
                      size="small"
                      :loading="generatingWheel"
                      @click="generateWheelPreview"
                    >
                      🎨 Сгенерировать превью рулетки через Pillow (PNG)
                    </VBtn>
                  </div>
                </div>

                <!-- Вкладка 4.4: Мессенджер MAX (Личный №) -->
                <div v-else-if="activeTab === 3">
                  <VkMarketingBotMaxSettings bot-type="wheel" v-model="configs.wheel" />
                </div>

                <!-- Вкладка 4.5: Дожим в Заказ -->
                <div v-else-if="activeTab === 4" class="d-flex flex-column gap-4">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <div class="d-flex align-center gap-2">
                      <span class="text-subtitle-2 font-weight-bold">Канал:</span>
                      <VBtnToggle v-model="selectedAnalyticsChannel" mandatory density="compact" color="error" variant="outlined">
                        <VBtn value="all" size="small">🌐 Все каналы</VBtn>
                        <VBtn value="vk" size="small">ВКонтакте</VBtn>
                        <VBtn value="max" size="small">MAX (Личный №)</VBtn>
                      </VBtnToggle>
                    </div>
                  </div>
                  <VRow>
                    <VCol cols="12" sm="6">
                      <VTextField v-model="configs.wheel.prize_valid_hours" type="number" label="Срок жизни приза" variant="outlined" density="comfortable" suffix="часов (48ч)" />
                    </VCol>
                    <VCol cols="12" sm="6">
                      <div class="d-flex align-center gap-2">
                        <VSwitch v-model="configs.wheel.remind_unused_prize" label="Авто-напоминание в ЛС" color="warning" density="compact" hide-details />
                        <VTextField v-if="configs.wheel.remind_unused_prize" v-model="configs.wheel.remind_before_expire_hours" type="number" label="За сколько ч." style="max-width: 140px;" density="compact" variant="outlined" suffix="ч" />
                      </div>
                    </VCol>
                  </VRow>

                  <VTextarea
                    v-model="configs.wheel.msg_dm_win_template"
                    label="Шаблон сообщения победителю в ЛС при выигрыше"
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                    hint="Теги: {first_name}, {prize_name}, {promo_code}, {valid_until}"
                    persistent-hint
                  />

                  <VTextarea
                    v-if="configs.wheel.remind_unused_prize"
                    v-model="configs.wheel.msg_dm_reminder_template"
                    label="Шаблон напоминания о сгорании приза в ЛС"
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                    hint="Теги: {first_name}, {prize_name}, {promo_code}"
                    persistent-hint
                  />

                  <div class="d-flex align-center justify-space-between mt-2">
                    <span class="text-subtitle-2 font-weight-bold">История прокруток и выданных призов</span>
                    <VBtn size="small" variant="text" prepend-icon="ri-refresh-line" :loading="loadingAnalytics" @click="loadAnalytics">Обновить</VBtn>
                  </div>

                  <VTable density="compact" class="border rounded">
                    <thead>
                      <tr>
                        <th>Время</th>
                        <th>VK ID</th>
                        <th>Приз</th>
                        <th>Промокод</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="!analyticsData?.spins || analyticsData.spins.length === 0">
                        <td colspan="5" class="text-center py-4 text-medium-emphasis">Кручений пока не зафиксировано</td>
                      </tr>
                      <tr v-for="spin in (analyticsData?.spins || [])" :key="spin.id">
                        <td class="text-caption text-no-wrap">{{ spin.created_at ? new Date(spin.created_at).toLocaleString('ru-RU') : '-' }}</td>
                        <td>{{ spin.vk_id }}</td>
                        <td class="font-weight-medium">{{ spin.prize_name }}</td>
                        <td><code>{{ spin.promo_code }}</code></td>
                        <td>
                          <VChip size="x-small" :color="spin.is_used ? 'success' : 'warning'">
                            {{ spin.is_used ? 'Использован' : 'Активен' }}
                          </VChip>
                        </td>
                      </tr>
                    </tbody>
                  </VTable>
                </div>
              </div>

              <!-- ==================== БОТ 5: VK SMART BROADCAST ==================== -->
              <div v-else-if="botType === 'broadcast'">
                <!-- Вкладка 5.1: Фильтры Аудитории -->
                <div v-if="activeTab === 0" class="d-flex flex-column gap-4">
                  <VRow>
                    <VCol cols="12" sm="3">
                      <VSelect
                        v-model="configs.broadcast.segment_verification"
                        label="Аудитория"
                        variant="outlined"
                        density="comfortable"
                        :items="[
                          { title: 'Все диалоги', value: 'all' },
                          { title: 'Только с телефоном iiko', value: 'only_phone' },
                          { title: 'Без телефона', value: 'no_phone' }
                        ]"
                      />
                    </VCol>
                    <VCol cols="12" sm="3">
                      <VTextField v-model="configs.broadcast.segment_days_last_order" type="number" label="Дней без заказа от" variant="outlined" density="comfortable" />
                    </VCol>
                    <VCol cols="12" sm="3">
                      <VTextField v-model="configs.broadcast.segment_avg_check_min" type="number" label="Мин. средний чек (₽)" variant="outlined" density="comfortable" />
                    </VCol>
                    <VCol cols="12" sm="3">
                      <VTextField v-model="configs.broadcast.segment_bonus_min" type="number" label="Мин. бонусов iiko" variant="outlined" density="comfortable" />
                    </VCol>
                  </VRow>
                  <VTextField v-model="configs.broadcast.exclude_last_touched_days" type="number" label="Защита от спама: исключить получавших рассылку за последние N дней" variant="outlined" density="comfortable" />

                  <VTextarea
                    v-model="configs.broadcast.broadcast_text"
                    label="Текст рассылки"
                    rows="3"
                    variant="outlined"
                    density="comfortable"
                    hint="Теги: {first_name}"
                    persistent-hint
                  />

                  <!-- Загрузка фото рассылки -->
                  <div class="d-flex align-center gap-4 pa-3 rounded border bg-var-theme-background">
                    <VAvatar v-if="configs.broadcast.broadcast_photo_url" rounded="lg" size="64" :image="configs.broadcast.broadcast_photo_url" class="border" />
                    <VAvatar v-else rounded="lg" size="64" color="secondary" variant="tonal">
                      <VIcon icon="ri-image-add-line" size="28" />
                    </VAvatar>
                    <div class="flex-grow-1">
                      <VFileInput
                        label="Загрузить баннер рассылки (JPG, PNG, WEBP)"
                        accept="image/*"
                        prepend-icon="ri-upload-cloud-line"
                        density="compact"
                        hide-details
                        :loading="uploadingImage"
                        @change="e => handleFileUpload(e, 'broadcast', 'broadcast_photo_url', 'attachment_photo')"
                      />
                      <div v-if="configs.broadcast.broadcast_photo_url" class="d-flex align-center gap-2 mt-1">
                        <span class="text-caption text-success">✓ Загружен ({{ configs.broadcast.attachment_photo || 'локально' }})</span>
                        <VBtn size="x-small" color="error" variant="text" @click="configs.broadcast.broadcast_photo_url = null; configs.broadcast.attachment_photo = null">Удалить</VBtn>
                      </div>
                    </div>
                  </div>

                  <div class="d-flex align-center justify-space-between pa-3 bg-light rounded border flex-wrap gap-2">
                    <div class="d-flex align-center gap-2">
                      <VBtn size="small" variant="tonal" color="info" prepend-icon="ri-calculator-line" :loading="countingAudience" @click="countAudience">
                        📊 Пересчитать аудиторию
                      </VBtn>
                      <span v-if="audienceCount !== null" class="font-weight-bold text-caption text-primary">
                        Подходит: {{ audienceCount }} чел.
                      </span>
                    </div>
                    <VBtn color="primary" variant="flat" size="small" prepend-icon="ri-send-plane-fill" :loading="startingBroadcast" @click="runBroadcast">
                      Запустить рассылку
                    </VBtn>
                  </div>
                </div>

                <!-- Вкладка 5.2: Счастливые Часы -->
                <div v-else-if="activeTab === 1" class="d-flex flex-column gap-4">
                  <VSwitch
                    v-model="configs.broadcast.happy_hours_auto"
                    label="Включить авто-дозагрузку кухни при спаде заказов в будни"
                    color="success"
                    density="comfortable"
                  />
                  <VSelect
                    v-model="configs.broadcast.happy_hours_days_of_week"
                    multiple
                    chips
                    label="Дни недели для проверки просадки кухни"
                    variant="outlined"
                    density="comfortable"
                    :items="['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']"
                  />
                  <VRow>
                    <VCol cols="12" sm="3">
                      <VTextField v-model="configs.broadcast.happy_hours_check_time" label="Время проверки" variant="outlined" density="comfortable" hint="Например 14:00" persistent-hint />
                    </VCol>
                    <VCol cols="12" sm="3">
                      <VTextField v-model="configs.broadcast.happy_hours_lookback_hours" type="number" label="За последние N часов" variant="outlined" density="comfortable" suffix="ч" />
                    </VCol>
                    <VCol cols="12" sm="3">
                      <VTextField v-model="configs.broadcast.min_orders_threshold" type="number" label="Порог заказов" variant="outlined" density="comfortable" hint="Если заказов меньше этого числа" persistent-hint />
                    </VCol>
                    <VCol cols="12" sm="3">
                      <VTextField v-model="configs.broadcast.happy_hours_batch_size" type="number" label="Пачка отправки (чел)" variant="outlined" density="comfortable" />
                    </VCol>
                  </VRow>
                  <VTextarea
                    v-model="configs.broadcast.happy_hours_template"
                    label="Шаблон спецпредложения «Счастливые Часы»"
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  />
                </div>

                <!-- Вкладка 5.3: Мессенджер MAX (Личный №) -->
                <div v-else-if="activeTab === 2">
                  <VkMarketingBotMaxSettings bot-type="broadcast" v-model="configs.broadcast" />
                </div>

                <!-- Вкладка 5.4: История -->
                <div v-else-if="activeTab === 3" class="d-flex flex-column gap-3">
                  <div class="d-flex align-center justify-space-between">
                    <span class="text-subtitle-2 font-weight-bold">История запущенных кампаний рассылок</span>
                    <VBtn size="small" variant="text" prepend-icon="ri-refresh-line" :loading="loadingAnalytics" @click="loadAnalytics">Обновить</VBtn>
                  </div>

                  <VTable density="compact" class="border rounded">
                    <thead>
                      <tr>
                        <th>Дата</th>
                        <th>Название / Текст</th>
                        <th>Получателей</th>
                        <th>Доставлено</th>
                        <th>Ошибок</th>
                        <th>Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="!analyticsData?.campaigns || analyticsData.campaigns.length === 0">
                        <td colspan="6" class="text-center py-4 text-medium-emphasis">Кампаний пока не создано</td>
                      </tr>
                      <tr v-for="c in (analyticsData?.campaigns || [])" :key="c.id">
                        <td class="text-caption text-no-wrap">{{ c.created_at ? new Date(c.created_at).toLocaleString('ru-RU') : '-' }}</td>
                        <td class="text-truncate" style="max-width: 280px;">{{ c.title || c.message_text || c.broadcast_text || '-' }}</td>
                        <td>{{ c.total_recipients || 0 }}</td>
                        <td><span class="text-success font-weight-bold">{{ c.sent_count || 0 }}</span></td>
                        <td><span :class="c.error_count > 0 ? 'text-error font-weight-bold' : ''">{{ c.error_count || 0 }}</span></td>
                        <td>
                          <VChip size="x-small" :color="c.status === 'completed' ? 'success' : 'info'" label>{{ c.status }}</VChip>
                        </td>
                      </tr>
                    </tbody>
                  </VTable>
                </div>
              </div>

              <!-- ==================== БОТ 6: VK REFERRAL BOT ==================== -->
              <div v-else-if="botType === 'referral'">
                <!-- Вкладка 6.1: Правила и Антифрод -->
                <div v-if="activeTab === 0" class="d-flex flex-column gap-4">
                  <VCard variant="outlined" class="pa-4 border">
                    <span class="font-weight-bold text-subtitle-2 mb-2 d-block">Что получает приглашённый друг (новый гость):</span>
                    <VRow>
                      <VCol cols="6">
                        <VTextField v-model="configs.referral.friend_bonus_points" type="number" label="Бонусов на 1-й заказ" variant="outlined" density="comfortable" suffix="₽" />
                      </VCol>
                      <VCol cols="6">
                        <VTextField v-model="configs.referral.friend_min_order_sum" type="number" label="Мин. сумма первого заказа" variant="outlined" density="comfortable" suffix="₽" />
                      </VCol>
                    </VRow>
                    <VSwitch v-model="configs.referral.antifraud_strict_new_customer" label="Строгий антифрод: у друга должно быть строго 0 прошлых заказов в БД" color="primary" density="compact" />
                  </VCard>

                  <VCard variant="outlined" class="pa-4 border">
                    <span class="font-weight-bold text-subtitle-2 mb-2 d-block">Что получает пригласивший клиент (амбассадор):</span>
                    <VRow>
                      <VCol cols="6">
                        <VTextField v-model="configs.referral.referrer_reward_points" type="number" label="Награда за друга" variant="outlined" density="comfortable" suffix="бонусов iiko" />
                      </VCol>
                      <VCol cols="6">
                        <VTextField v-model="configs.referral.max_referrals_per_user_month" type="number" label="Лимит друзей в месяц" variant="outlined" density="comfortable" />
                      </VCol>
                    </VRow>
                    <div class="d-flex align-center gap-2 mt-2">
                      <VChip color="success" size="small" label>Правило начисления:</VChip>
                      <span class="text-caption font-weight-medium">Строго после статуса первого заказа друга «ДОСТАВЛЕН»</span>
                    </div>
                  </VCard>
                </div>

                <!-- Вкладка 6.2: Карточка и Тексты -->
                <div v-else-if="activeTab === 1" class="d-flex flex-column gap-4">
                  <VSwitch v-model="configs.referral.generate_invite_image" label="Генерировать персональную карточку-сертификат через Pillow для отправки другу" color="primary" density="comfortable" />

                  <!-- Загрузчик фона сертификата -->
                  <div class="d-flex align-center gap-3 pa-3 rounded border bg-var-theme-background">
                    <VAvatar v-if="configs.referral.cert_bg_image_url" rounded="lg" size="48" :image="configs.referral.cert_bg_image_url" class="border" />
                    <div class="flex-grow-1">
                      <VFileInput
                        label="Фоновый шаблон сертификата (необязательно, JPG/PNG)"
                        accept="image/*"
                        prepend-icon="ri-image-add-line"
                        density="compact"
                        hide-details
                        @change="e => handleFileUpload(e, 'referral', 'cert_bg_image_url')"
                      />
                    </div>
                    <VBtn v-if="configs.referral.cert_bg_image_url" size="x-small" color="error" variant="text" @click="configs.referral.cert_bg_image_url = null">Удалить</VBtn>
                  </div>
                  <VTextarea v-model="configs.referral.msg_ambassador_info" label="Сообщение с ссылкой для амбассадора" rows="2" variant="outlined" density="comfortable" />
                  <VTextarea v-model="configs.referral.msg_friend_welcome" label="Приветствие друга при переходе по ссылке" rows="2" variant="outlined" density="comfortable" />
                  <VTextarea v-model="configs.referral.msg_referrer_reward_paid" label="Уведомление амбассадору о начислении бонусов за друга" rows="2" variant="outlined" density="comfortable" />
                </div>

                <!-- Вкладка 6.3: Мессенджер MAX (Личный №) -->
                <div v-else-if="activeTab === 2">
                  <VkMarketingBotMaxSettings bot-type="referral" v-model="configs.referral" />
                </div>

                <!-- Вкладка 6.4: Таблица Рефералов -->
                <div v-else-if="activeTab === 3" class="d-flex flex-column gap-3">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <div class="d-flex align-center gap-2">
                      <span class="text-subtitle-2 font-weight-bold">Канал:</span>
                      <VBtnToggle v-model="selectedAnalyticsChannel" mandatory density="compact" color="secondary" variant="outlined">
                        <VBtn value="all" size="small">🌐 Все каналы</VBtn>
                        <VBtn value="vk" size="small">ВКонтакте</VBtn>
                        <VBtn value="max" size="small">MAX (Личный №)</VBtn>
                      </VBtnToggle>
                    </div>
                  </div>
                  <VRow>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="primary" class="pa-3 text-center">
                        <div class="text-caption">Амбассадоров</div>
                        <div class="text-h4 font-weight-bold mt-1">{{ analyticsData?.metrics?.ambassadors_count || 0 }}</div>
                      </VCard>
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="info" class="pa-3 text-center">
                        <div class="text-caption">Приглашено друзей</div>
                        <div class="text-h4 font-weight-bold mt-1">{{ analyticsData?.metrics?.invited_friends || 0 }}</div>
                      </VCard>
                    </VCol>
                    <VCol cols="12" sm="4">
                      <VCard variant="tonal" color="success" class="pa-3 text-center">
                        <div class="text-caption">Заказов выполнено</div>
                        <div class="text-h4 font-weight-bold mt-1">{{ analyticsData?.metrics?.completed_orders || 0 }}</div>
                      </VCard>
                    </VCol>
                  </VRow>

                  <div class="d-flex align-center justify-space-between mt-2">
                    <span class="text-subtitle-2 font-weight-bold">Реферальные приглашения и выплаты</span>
                    <VBtn size="small" variant="text" prepend-icon="ri-refresh-line" :loading="loadingAnalytics" @click="loadAnalytics">Обновить</VBtn>
                  </div>

                  <VTable density="compact" class="border rounded">
                    <thead>
                      <tr>
                        <th>Дата</th>
                        <th>Амбассадор (VK ID)</th>
                        <th>Код</th>
                        <th>Друг (VK ID)</th>
                        <th>Статус</th>
                        <th>Награда</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-if="!analyticsData?.links || analyticsData.links.length === 0">
                        <td colspan="6" class="text-center py-4 text-medium-emphasis">Приглашений пока не зарегистрировано</td>
                      </tr>
                      <tr v-for="l in (analyticsData?.links || [])" :key="l.id">
                        <td class="text-caption text-no-wrap">{{ l.created_at ? new Date(l.created_at).toLocaleString('ru-RU') : '-' }}</td>
                        <td>{{ l.referrer_vk_id || '-' }}</td>
                        <td><code>{{ l.referral_code }}</code></td>
                        <td>{{ l.invited_vk_id || 'Ожидает' }}</td>
                        <td>
                          <VChip size="x-small" :color="l.reward_granted ? 'success' : 'warning'">
                            {{ l.reward_granted ? 'Доставлен' : (l.status || 'Зарегистрирован') }}
                          </VChip>
                        </td>
                        <td>
                          <span v-if="l.reward_granted" class="text-success font-weight-bold">+{{ configs.referral.referrer_reward_points }} бонусов</span>
                          <span v-else class="text-medium-emphasis">0</span>
                        </td>
                      </tr>
                    </tbody>
                  </VTable>
                </div>
              </div>
            </div>
          </VCol>

          <!-- ПРАВАЯ КОЛОНКА: ИНТЕРАКТИВНЫЙ ЭМУЛЯТОР СМАРТФОНА (ДИАЛОГ ВК) -->
          <VCol cols="12" md="5" lg="4" class="bg-light d-flex align-center justify-center pa-6">
            <div class="smartphone-frame elevation-4">
              <!-- ВЕРХНЯЯ ГРАНЬ И ЧЁЛКА/ДИНАМИК -->
              <div class="phone-speaker-notch">
                <div class="phone-speaker"></div>
                <div class="phone-camera"></div>
              </div>

              <!-- СТАТУС БАР ТЕЛЕФОНА -->
              <div class="phone-status-bar d-flex justify-space-between align-center px-4">
                <span class="phone-time font-weight-bold">14:35</span>
                <div class="d-flex align-center gap-1">
                  <VIcon icon="ri-signal-tower-fill" size="12" />
                  <VIcon icon="ri-wifi-line" size="12" />
                  <VIcon icon="ri-battery-2-charge-line" size="14" />
                </div>
              </div>

              <!-- ШАПКА ДИАЛОГА ВКОНТАКТЕ -->
              <div class="vk-chat-header d-flex align-center gap-2 px-3 py-2 border-b">
                <VIcon icon="ri-arrow-left-s-line" size="22" color="primary" />
                <VAvatar size="32" image="https://vezuroll.ru/media/img/logo.png">
                  <span class="text-caption font-weight-bold">ВР</span>
                </VAvatar>
                <div class="flex-grow-1 overflow-hidden">
                  <div class="d-flex align-center gap-1">
                    <span class="text-caption font-weight-bold text-truncate">Везу Ролл</span>
                    <VIcon icon="ri-verified-badge-fill" size="13" color="primary" />
                  </div>
                  <div class="text-caption text-medium-emphasis" style="font-size: 10px !important;">бот • онлайн</div>
                </div>
                <VIcon icon="ri-more-2-fill" size="18" color="medium-emphasis" />
              </div>

              <!-- СОДЕРЖИМОЕ ДИАЛОГА (ЧАТ С БОТОМ) -->
              <div class="vk-chat-body pa-3 d-flex flex-column gap-3">
                <!-- Сообщение от бота -->
                <div class="d-flex align-end gap-2">
                  <VAvatar size="24" color="primary" variant="flat">
                    <VIcon icon="ri-robot-line" size="14" color="white" />
                  </VAvatar>
                  <div class="vk-message-bubble pa-3 rounded-lg elevation-1">
                    <img
                      v-if="previewImageUrl"
                      :src="previewImageUrl"
                      class="w-100 rounded mb-2"
                      style="max-height: 140px; object-fit: cover;"
                    />
                    <div class="text-caption message-content" style="white-space: pre-line;">{{ previewText }}</div>
                    
                    <!-- СПЕЦИФИЧЕСКИЕ ВИДЖЕТЫ ВНУТРИ СООБЩЕНИЯ -->
                    <!-- Бот 1: Превью карусели товаров -->
                    <div v-if="botType === 'shop'" class="mt-2 vk-mini-carousel pa-2 rounded border bg-surface">
                      <div class="d-flex align-center gap-2">
                        <div class="product-thumb rounded bg-light" style="width: 44px; height: 44px; display:flex; align-items:center; justify-content:center;">🍣</div>
                        <div class="flex-grow-1">
                          <div class="font-weight-bold text-caption">Сет «Филадельфия»</div>
                          <div class="text-caption text-primary font-weight-bold">1 290 ₽</div>
                        </div>
                      </div>
                      <div class="d-flex gap-1 mt-2">
                        <button class="vk-btn vk-btn-primary flex-grow-1">В корзину</button>
                        <button class="vk-btn vk-btn-secondary">Подробнее</button>
                      </div>
                    </div>

                    <!-- Бот 3: Кнопки звезд NPS -->
                    <div v-if="botType === 'nps'" class="mt-2 d-flex gap-1 justify-space-between">
                      <button class="vk-btn vk-btn-secondary flex-grow-1">⭐ 1</button>
                      <button class="vk-btn vk-btn-secondary flex-grow-1">⭐ 2</button>
                      <button class="vk-btn vk-btn-secondary flex-grow-1">⭐ 3</button>
                      <button class="vk-btn vk-btn-primary flex-grow-1">⭐ 4</button>
                      <button class="vk-btn vk-btn-positive flex-grow-1">⭐ 5</button>
                    </div>

                    <!-- Бот 4: Мини-виджет рулетки -->
                    <div v-if="botType === 'wheel'" class="mt-2 pa-2 rounded bg-surface border text-center">
                      <div class="font-weight-bold text-caption text-primary">🎡 Колесо Фортуны Везу Ролл</div>
                      <div class="text-caption mt-1" style="font-size: 11px;">Секретный код: <strong class="text-success">FORTUNA10</strong></div>
                    </div>

                    <!-- Бот 6: Купон реферала -->
                    <div v-if="botType === 'referral'" class="mt-2 pa-2 rounded bg-surface border text-center">
                      <div class="text-caption text-medium-emphasis">Билет амбассадора:</div>
                      <div class="font-weight-bold text-h6 text-primary my-1">VR-03921</div>
                      <div class="text-caption text-success">+250 ₽ другу / +300 бонусов вам</div>
                    </div>

                    <div class="text-caption text-disabled text-end mt-1" style="font-size: 9px !important;">14:35</div>
                  </div>
                </div>

                <!-- КЛАВИАТУРА ВКОНТАКТЕ ВНИЗУ ЧАТА (ДЛЯ SHOP BOT) -->
                <div v-if="botType === 'shop'" class="vk-keyboard mt-auto pt-2 border-t">
                  <div class="vk-keyboard-grid">
                    <button
                      v-for="btn in (configs.shop.menu_buttons || []).filter(b => b.active)"
                      :key="btn.id"
                      class="vk-btn"
                      :class="'vk-btn-' + btn.color"
                    >
                      {{ btn.text }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- НИЖНЯЯ ПАНЕЛЬ СМАРТФОНА -->
              <div class="phone-home-bar"></div>
            </div>
          </VCol>
        </VRow>
      </VCardText>

      <!-- FOOTER КНОПКИ ДЕЙСТВИЙ -->
      <VCardActions class="border-t px-6 py-3">
        <VBtn
          variant="tonal"
          color="primary"
          prepend-icon="ri-vk-line"
          :loading="testingVk"
          @click="sendTest('vk')"
        >
          Тест в ВК
        </VBtn>

        <VBtn
          variant="tonal"
          color="success"
          prepend-icon="ri-chat-voice-line"
          :loading="testingMax"
          @click="sendTest('max')"
        >
          Тест в MAX (с личного №)
        </VBtn>

        <VBtn
          variant="text"
          color="secondary"
          prepend-icon="ri-restart-line"
          @click="resetToDefaults"
        >
          Сбросить
        </VBtn>

        <VSpacer />

        <VBtn variant="text" @click="emit('update:modelValue', false)">
          Отмена
        </VBtn>

        <VBtn
          color="primary"
          variant="flat"
          prepend-icon="ri-save-line"
          :loading="saving"
          @click="saveConfig"
        >
          Сохранить настройки
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>

<style scoped>
.vk-modal-card {
  border-radius: 16px;
  overflow: hidden;
}

.sticky-tabs {
  position: sticky;
  top: 0;
  z-index: 2;
}

/* СТИЛИЗАЦИЯ КОРПУСА СМАРТФОНА */
.smartphone-frame {
  width: 320px;
  height: 580px;
  background-color: #ffffff;
  border-radius: 36px;
  border: 10px solid #1e2022;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.phone-speaker-notch {
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 12px;
  background: #1e2022;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  z-index: 10;
}

.phone-speaker {
  width: 38px;
  height: 4px;
  background: #3a3d40;
  border-radius: 2px;
}

.phone-camera {
  width: 6px;
  height: 6px;
  background: #282a2d;
  border-radius: 50%;
}

.phone-status-bar {
  padding-top: 14px;
  height: 34px;
  background-color: #f7f8fa;
  font-size: 11px;
  color: #333;
}

.vk-chat-header {
  background-color: #ffffff;
}

.vk-chat-body {
  background-color: #edeef0;
  flex-grow: 1;
  overflow-y: auto;
}

.vk-message-bubble {
  background-color: #ffffff;
  color: #000000;
  max-width: 85%;
  border-bottom-left-radius: 4px !important;
}

.message-content {
  font-size: 12px !important;
  line-height: 1.35;
}

/* КНОПКИ В СТИЛЕ ВКОНТАКТЕ */
.vk-btn {
  font-size: 11px;
  font-weight: 500;
  padding: 6px 10px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
  text-align: center;
}

.vk-btn:hover {
  opacity: 0.9;
}

.vk-btn-primary {
  background-color: #2688eb;
  color: #ffffff;
}

.vk-btn-positive {
  background-color: #4bb34b;
  color: #ffffff;
}

.vk-btn-negative {
  background-color: #e64646;
  color: #ffffff;
}

.vk-btn-secondary {
  background-color: #e5ebf1;
  color: #2688eb;
}

.vk-keyboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.phone-home-bar {
  width: 100px;
  height: 4px;
  background: #bbb;
  border-radius: 2px;
  margin: 6px auto;
}
</style>
