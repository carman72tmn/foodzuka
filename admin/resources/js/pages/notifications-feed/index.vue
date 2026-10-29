<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

const router = useRouter()
const toast = useToast()

// Состояние
const loading = ref(false)
const markingAll = ref(false)
const selectedCategory = ref('all')
const unreadOnly = ref(false)
const searchQuery = ref('')
const items = ref([])
const counts = ref({
  all: 0,
  unread: 0,
  new_order: 0,
  order_status: 0,
  tbank_payment: 0,
  vk_message: 0,
  max_message: 0
})

let pollInterval = null

// Категории табов
const categories = [
  { id: 'all', label: 'Все события', icon: 'bx-layer', color: 'primary' },
  { id: 'new_order', label: 'Новые заказы', icon: 'bx-cart-add', color: 'success' },
  { id: 'order_status', label: 'Статусы заказов', icon: 'bx-transfer-alt', color: 'warning' },
  { id: 'tbank_payment', label: 'Оплаты Т-Банк', icon: 'bx-credit-card', color: 'info' },
  { id: 'vk_message', label: 'Сообщения ВК', icon: 'ri-vk-line', color: 'primary' },
  { id: 'max_message', label: 'Сообщения MAX', icon: 'ri-chat-voice-line', color: 'success' },
]

// Загрузка данных
const fetchFeed = async (silent = false) => {
  if (!silent) loading.value = true
  try {
    const params = {
      category: selectedCategory.value,
      unread_only: unreadOnly.value,
      search: searchQuery.value || undefined,
      limit: 100
    }
    const res = await axios.get('/api/v1/notifications/feed', { params })
    if (res.data) {
      items.value = res.data.items || []
      counts.value = res.data.counts || counts.value
    }
  } catch (e) {
    if (!silent) {
      console.error('Ошибка загрузки ленты уведомлений:', e)
      toast.error('Не удалось загрузить уведомления')
    }
  } finally {
    if (!silent) loading.value = false
  }
}

// Отметить одно уведомление прочитанным
const markAsRead = async (item) => {
  if (item.is_read) return
  item.is_read = true
  if (counts.value.unread > 0) counts.value.unread--

  if (item.db_id) {
    try {
      await axios.post(`/api/v1/notifications/${item.db_id}/read`)
    } catch (e) {
      console.warn('Ошибка отметки прочтения:', e)
    }
  }
}

// Отметить все прочитанными
const markAllAsRead = async () => {
  markingAll.value = true
  try {
    await axios.post('/api/v1/notifications/read-all')
    items.value.forEach(x => { x.is_read = true })
    counts.value.unread = 0
    toast.success('Все уведомления отмечены прочитанными')
  } catch (e) {
    toast.error('Ошибка отметки прочитанных')
  } finally {
    markingAll.value = false
  }
}

// Умный переход внутри SPA без потери префикса
const navigateTo = (url) => {
  if (!url) return
  let target = url.trim()
  
  if (target.startsWith('http://') || target.startsWith('https://')) {
    window.location.href = target
    return
  }

  if (target.startsWith('/admin/')) {
    target = target.substring(6)
  } else if (target === '/admin') {
    target = '/orders'
  }

  if (target.startsWith('/pers/')) {
    target = target.substring(5)
  } else if (target === '/pers') {
    target = '/'
  }

  if (!target.startsWith('/')) {
    target = '/' + target
  }

  router.push(target)
}

// Переход по кнопке действия или клику на строку-плашку
const handleActionClick = (item) => {
  markAsRead(item)
  if (item.url) {
    navigateTo(item.url)
  }
}

// Форматирование даты
const formatTime = (isoStr) => {
  if (!isoStr) return ''
  try {
    const date = new Date(isoStr)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return 'Только что'
    if (diffMins < 60) return `${diffMins} мин назад`

    const isToday = date.toDateString() === now.toDateString()
    const timeStr = date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })

    if (isToday) return `Сегодня в ${timeStr}`
    return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' }) + ' ' + timeStr
  } catch {
    return isoStr
  }
}

// Следим за фильтрами
watch([selectedCategory, unreadOnly], () => {
  fetchFeed()
})

let searchDebounce = null
watch(searchQuery, () => {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    fetchFeed()
  }, 400)
})

onMounted(() => {
  fetchFeed()
  // Фоновый опрос каждые 10 секунд
  pollInterval = setInterval(() => {
    fetchFeed(true)
  }, 10000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  clearTimeout(searchDebounce)
})
</script>

<template>
  <div class="notifications-feed-page">
    <!-- ШАПКА ЦЕНТРА УВЕДОМЛЕНИЙ -->
    <VCard class="mb-5 pa-4 border">
      <div class="d-flex align-center justify-space-between flex-wrap gap-3">
        <div class="d-flex align-center gap-3">
          <VAvatar color="primary" variant="tonal" size="48" class="rounded-lg">
            <VIcon icon="bx-bell" size="28" />
          </VAvatar>
          <div>
            <div class="d-flex align-center gap-2">
              <h2 class="text-h5 font-weight-bold mb-0">Центр уведомлений</h2>
              <VChip size="x-small" color="success" variant="flat" class="pulse-chip">
                <span class="live-dot me-1"></span> LIVE 10с
              </VChip>
              <VChip v-if="counts.unread > 0" size="small" color="error" variant="flat" class="font-weight-bold">
                {{ counts.unread }} непрочитанных
              </VChip>
            </div>
            <div class="text-caption text-medium-emphasis">
              Оперативная лента заказов, статусов доставки, оплат Т-Банка и сообщений ВКонтакте и MAX
            </div>
          </div>
        </div>

        <div class="d-flex align-center gap-3 flex-wrap">
          <VSwitch
            v-model="unreadOnly"
            label="Только непрочитанные"
            color="primary"
            density="compact"
            hide-details
          />

          <VBtn
            variant="tonal"
            color="secondary"
            size="small"
            prepend-icon="bx-check-double"
            :loading="markingAll"
            @click="markAllAsRead"
          >
            Прочитать все
          </VBtn>

          <VBtn
            variant="outlined"
            color="primary"
            size="small"
            icon="bx-refresh"
            :loading="loading"
            @click="fetchFeed(false)"
          />
        </div>
      </div>

      <!-- ПОИСК И СТРОКА ФИЛЬТРА -->
      <div class="mt-4">
        <VTextField
          v-model="searchQuery"
          placeholder="Быстрый поиск по номеру заказа, тексту, имени клиента или сумме..."
          prepend-inner-icon="bx-search"
          variant="outlined"
          density="compact"
          hide-details
          clearable
        />
      </div>

      <!-- ТАБЫ КАТЕГОРИЙ -->
      <div class="d-flex flex-wrap gap-2 mt-4 pt-3 border-t">
        <VBtn
          v-for="cat in categories"
          :key="cat.id"
          :variant="selectedCategory === cat.id ? 'flat' : 'tonal'"
          :color="selectedCategory === cat.id ? cat.color : 'secondary'"
          size="small"
          class="font-weight-medium"
          @click="selectedCategory = cat.id"
        >
          <VIcon start :icon="cat.icon" size="16" />
          {{ cat.label }}
          <VChip
            size="x-small"
            class="ms-2 font-weight-bold"
            :color="selectedCategory === cat.id ? 'surface' : cat.color"
            :variant="selectedCategory === cat.id ? 'flat' : 'tonal'"
          >
            {{ counts[cat.id] || 0 }}
          </VChip>
        </VBtn>
      </div>
    </VCard>

    <!-- ИНДИКАТОР ПУСТОГО СПИСКА -->
    <VCard v-if="items.length === 0 && !loading" class="pa-10 text-center border">
      <VAvatar color="secondary" variant="tonal" size="64" class="mb-3">
        <VIcon icon="bx-bell-off" size="36" />
      </VAvatar>
      <div class="text-h6 font-weight-medium">Уведомлений не найдено</div>
      <div class="text-caption text-medium-emphasis mt-1">
        В выбранной категории или по вашему запросу событий пока нет
      </div>
    </VCard>

    <!-- СПИСОК УВЕДОМЛЕНИЙ В ВИДЕ СТРОК-ПЛАШЕК -->
    <div v-else class="notifications-list d-flex flex-column gap-2">
      <div
        v-for="item in items"
        :key="item.id"
        class="notification-plaque d-flex align-center justify-space-between px-4 py-3 rounded-lg border bg-surface transition-all"
        :class="[
          'accent-border-' + item.badge_color,
          { 'is-unread': !item.is_read }
        ]"
        @click="handleActionClick(item)" style="cursor: pointer;"
      >
        <!-- ЛЕВАЯ ЧАСТЬ: Иконка + Бейдж + Текст -->
        <div class="d-flex align-center gap-3 flex-grow-1 text-truncate pe-3">
          <!-- Иконка категории -->
          <VAvatar
            :color="item.badge_color"
            variant="tonal"
            size="40"
            class="rounded-lg flex-shrink-0"
          >
            <VIcon :icon="item.icon" size="22" />
          </VAvatar>

          <!-- Бейдж категории -->
          <VChip
            :color="item.badge_color"
            variant="flat"
            size="small"
            class="font-weight-bold flex-shrink-0 text-center"
            style="min-width: 110px;"
          >
            {{ item.badge_text }}
          </VChip>

          <!-- Основной текст плашки -->
          <div class="d-flex flex-column text-truncate">
            <div class="d-flex align-center gap-2">
              <span class="font-weight-bold text-subtitle-2 text-truncate">{{ item.title }}</span>
              <span v-if="item.subtitle" class="text-caption text-medium-emphasis text-truncate d-none d-md-inline">
                • {{ item.subtitle }}
              </span>
            </div>
            <div class="text-caption text-truncate text-high-emphasis">
              {{ item.body }}
            </div>
          </div>
        </div>

        <!-- ПРАВАЯ ЧАСТЬ: Сумма + Время + Кнопка перехода + Индикатор -->
        <div class="d-flex align-center gap-3 flex-shrink-0">
          <!-- Сумма (если есть) -->
          <div v-if="item.amount" class="text-end d-none d-sm-block">
            <span class="font-weight-bold text-subtitle-1 text-success text-no-wrap">
              {{ Math.round(item.amount).toLocaleString('ru-RU') }} ₽
            </span>
          </div>

          <!-- Время -->
          <div class="text-caption text-medium-emphasis text-no-wrap" style="min-width: 85px;">
            {{ formatTime(item.created_at) }}
          </div>

          <!-- Кнопка действия -->
          <VBtn
            size="small"
            :color="item.badge_color"
            variant="tonal"
            class="text-caption px-3 font-weight-medium d-none d-sm-flex"
            @click.stop="handleActionClick(item)"
          >
            <span v-if="item.category === 'new_order' || item.category === 'order_status'">Заказ</span>
            <span v-else-if="item.category === 'tbank_payment'">Платеж</span>
            <span v-else-if="item.category === 'vk_message' || item.category === 'max_message'">В чат</span>
            <span v-else>Открыть</span>
            <VIcon end icon="bx-chevron-right" size="16" />
          </VBtn>

          <!-- Индикатор прочитанности (точка) -->
          <div
            class="read-indicator flex-shrink-0 cursor-pointer"
            :title="item.is_read ? 'Прочитано' : 'Нажмите, чтобы отметить прочитанным'"
            @click.stop="markAsRead(item)"
          >
            <span v-if="!item.is_read" class="unread-dot"></span>
            <VIcon v-else icon="bx-check" size="18" class="text-medium-emphasis" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notifications-feed-page {
  max-width: 1400px;
  margin: 0 auto;
}

/* Плашка уведомления */
.notification-plaque {
  border-left-width: 5px !important;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.notification-plaque:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.notification-plaque.is-unread {
  background-color: rgba(var(--v-theme-primary), 0.04) !important;
}

/* Цветные левые акценты */
.accent-border-success {
  border-left-color: rgb(var(--v-theme-success)) !important;
}
.accent-border-warning {
  border-left-color: rgb(var(--v-theme-warning)) !important;
}
.accent-border-info {
  border-left-color: rgb(var(--v-theme-info)) !important;
}
.accent-border-primary {
  border-left-color: rgb(var(--v-theme-primary)) !important;
}
.accent-border-secondary {
  border-left-color: rgba(var(--v-theme-on-surface), 0.38) !important;
}

/* Индикатор непрочитанного */
.unread-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(var(--v-theme-primary), 0.6);
}

.read-indicator {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Пульсирующая точка LIVE */
.live-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  background-color: #ffffff;
  border-radius: 50%;
  animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.3;
    transform: scale(0.7);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
