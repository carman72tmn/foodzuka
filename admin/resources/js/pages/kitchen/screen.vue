<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import { hasPermission } from '@/utils/auth'

const toast = useToast()

// Состояния экрана
const activeZoneIds = ref([]) // массив выбранных цехов (пустой = Все)
const zones = ref([])
const orders = ref([])
const loading = ref(false)
const intervalId = ref(null)
const previousOrdersCount = ref(0)

// Модальное окно техкарты блюда
const isRecipeDialogOpen = ref(false)
const recipeLoading = ref(false)
const selectedProductRecipe = ref(null)
const recipeHistory = ref([]) // стек истории для вложенных рецептов

// Раскрытие ингредиентов прямо на плитке заказа
const expandedItems = ref({})
const toggleItemIngredients = (itemId) => {
  expandedItems.value[itemId] = !expandedItems.value[itemId]
}

// Аудио для уведомления о новом заказе
const audioNotification = ref(null)

// Загрузка цехов (зон)
const fetchZones = async () => {
  try {
    const res = await axios.get('/api/v1/kitchen/zones')
    zones.value = res.data
    // По умолчанию сбрасываем фильтр (активны все цеха)
    activeZoneIds.value = []
  } catch (err) {
    console.error('Ошибка при загрузке зон приготовления:', err)
  }
}

// Загрузка заказов для повара
const fetchOrders = async (showLoader = false) => {
  if (showLoader) loading.value = true
  try {
    const params = {}
    if (activeZoneIds.value && activeZoneIds.value.length > 0) {
      params.zone_ids = activeZoneIds.value.join(',')
    }
    
    const res = await axios.get('/api/v1/kitchen/orders', { params })
    const newOrders = res.data
    
    // Проверяем, появились ли новые заказы для проигрывания звука
    if (newOrders.length > previousOrdersCount.value && previousOrdersCount.value > 0) {
      playNewOrderSound()
      toast.info('Поступил новый заказ на кухню!')
    }
    
    orders.value = newOrders
    previousOrdersCount.value = newOrders.length
  } catch (err) {
    console.error('Не удалось загрузить заказы для кухни:', err)
  } finally {
    if (showLoader) loading.value = false
  }
}

// Проигрывание звука
const playNewOrderSound = () => {
  try {
    if (!audioNotification.value) {
      audioNotification.value = new Audio('/media/sounds/notification.mp3') // Стандартный звук
    }
    audioNotification.value.play().catch(e => console.log('Браузер заблокировал автовоспроизведение звука. Требуется клик.'))
  } catch (e) {
    console.error('Ошибка воспроизведения звука:', e)
  }
}

// Изменение статуса приготовления позиции блюда
const changeItemStatus = async (itemId, newStatus) => {
  if (!hasPermission('kitchen_screen_edit')) {
    toast.error('У вас нет прав для управления заказами на кухне')
    return
  }
  
  try {
    await axios.post(`/api/v1/kitchen/items/${itemId}/status`, null, {
      params: { status_name: newStatus }
    })
    
    toast.success(newStatus === 'cooking' ? 'Начато приготовление блюда' : 'Блюдо приготовлено!')
    fetchOrders(false)
  } catch (err) {
    toast.error('Не удалось обновить статус блюда')
  }
}

// Управление заказами целиком
const startOrderCooking = async (orderId) => {
  if (!hasPermission('kitchen_screen_edit')) {
    toast.error('У вас нет прав для управления заказами')
    return
  }
  try {
    await axios.post(`/api/v1/kitchen/orders/${orderId}/start-cooking`)
    toast.success('Начато приготовление заказа!')
    fetchOrders(false)
  } catch (err) {
    toast.error('Не удалось начать приготовление заказа')
  }
}

const startOrderAssembling = async (orderId) => {
  if (!hasPermission('kitchen_screen_edit')) {
    toast.error('У вас нет прав для управления заказами')
    return
  }
  try {
    await axios.post(`/api/v1/kitchen/orders/${orderId}/assembling`)
    toast.success('Заказ передан на сборку')
    fetchOrders(false)
  } catch (err) {
    toast.error('Не удалось перевести заказ на сборку')
  }
}

const makeOrderReady = async (orderId) => {
  if (!hasPermission('kitchen_screen_edit')) {
    toast.error('У вас нет прав для управления заказами')
    return
  }
  try {
    await axios.post(`/api/v1/kitchen/orders/${orderId}/ready`)
    toast.success('Заказ полностью готов!')
    fetchOrders(false)
  } catch (err) {
    toast.error('Не удалось завершить заказ')
  }
}

// Открытие рецепта во всплывающем окне для повара
const viewRecipe = async (productId) => {
  if (!productId) return
  isRecipeDialogOpen.value = true
  recipeLoading.value = true
  selectedProductRecipe.value = null
  recipeHistory.value = [] // Сброс стека
  
  try {
    const res = await axios.get(`/api/v1/kitchen/recipes/${productId}`)
    selectedProductRecipe.value = res.data
  } catch (err) {
    toast.error('Не удалось загрузить техкарту блюда')
    isRecipeDialogOpen.value = false
  } finally {
    recipeLoading.value = false
  }
}

// Открытие техкарты заготовок или модификаторов по iiko ID
const viewRecipeByIikoId = async (iikoId) => {
  if (!iikoId) return
  recipeLoading.value = true
  
  // Пушим текущий рецепт в стек истории перед переходом
  if (selectedProductRecipe.value) {
    recipeHistory.value.push(selectedProductRecipe.value)
  }
  
  selectedProductRecipe.value = null
  isRecipeDialogOpen.value = true
  
  try {
    const res = await axios.get(`/api/v1/kitchen/recipes/by-iiko-id/${iikoId}`)
    selectedProductRecipe.value = res.data
  } catch (err) {
    toast.error('Техкарта для этой позиции отсутствует в БД')
    goBackRecipe()
  } finally {
    recipeLoading.value = false
  }
}

// Возврат к предыдущему рецепту в истории
const goBackRecipe = () => {
  if (recipeHistory.value.length > 0) {
    selectedProductRecipe.value = recipeHistory.value.pop()
  }
}

// Расчет времени ожидания (таймер)
const formatTimeLeft = (expectedTimeStr) => {
  if (!expectedTimeStr) return '—'
  const expected = new Date(expectedTimeStr)
  const now = new Date()
  const diffMs = expected - now
  const diffMins = Math.round(diffMs / 60000)
  
  if (diffMins < 0) {
    return `Опоздание: ${Math.abs(diffMins)} мин`
  } else {
    return `Осталось: ${diffMins} мин`
  }
}

const getTimeColor = (expectedTimeStr) => {
  if (!expectedTimeStr) return 'white'
  const expected = new Date(expectedTimeStr)
  const now = new Date()
  const diffMins = (expected - now) / 60000
  
  if (diffMins < 0) return '#FF5252' // Просрочено (красный)
  if (diffMins <= 10) return '#FFB300' // Срочно (оранжевый)
  return '#4CAF50' // Времени достаточно (зеленый)
}

const getStatusText = (status) => {
  const map = {
    new: 'Новый',
    unconfirmed: 'Не подтвержден',
    confirmed: 'Подтвержден',
    preparing: 'Подготовка',
    cooking: 'Готовится',
    assembling: 'На сборке',
    ready: 'Готов',
    ready_for_pickup: 'Готов к выдаче'
  }
  return map[status] || status
}

// Отслеживаем смену активных цехов
watch(activeZoneIds, () => {
  previousOrdersCount.value = 0
  fetchOrders(true)
}, { deep: true })

onMounted(async () => {
  await fetchZones()
  await fetchOrders(true)
  
  // Запуск автообновления каждые 10 секунд
  intervalId.value = setInterval(() => {
    fetchOrders(false)
  }, 10000)
})

onUnmounted(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
})
</script>

<template>
  <div class="kds-screen bg-grey-darken-4 text-white min-h-screen pa-4">
    <!-- Шапка KDS -->
    <VRow class="mb-4 align-center border-bottom pb-3">
      <VCol cols="12" md="3" class="d-flex align-center">
        <VIcon icon="bx-restaurant" size="32" class="mr-2 text-primary" />
        <h1 class="text-h4 font-weight-bold">KDS Экран повара</h1>
      </VCol>
      <VCol cols="12" md="7" class="d-flex align-center justify-center flex-wrap">
        <!-- Кнопка сброса фильтра -->
        <VBtn
          :variant="activeZoneIds.length === 0 ? 'flat' : 'outlined'"
          color="primary"
          class="mr-3 font-weight-bold"
          density="comfortable"
          @click="activeZoneIds = []"
        >
          Все цеха
        </VBtn>

        <!-- Мультивыбор цехов -->
        <VChipGroup
          v-model="activeZoneIds"
          multiple
          column
          color="primary"
        >
          <VChip
            v-for="zone in zones"
            :key="zone.id"
            :value="zone.id"
            filter
            variant="flat"
            color="grey-darken-3"
            selected-class="bg-primary text-white"
            class="ma-1 font-weight-bold text-body-2"
          >
            <span :style="`background-color: ${zone.color}; width: 10px; height: 10px; border-radius: 50%; display: inline-block;`" class="mr-1" />
            {{ zone.name }}
          </VChip>
        </VChipGroup>
      </VCol>
      <VCol cols="12" md="2" class="text-right">
        <VBtn
          color="grey-darken-3"
          icon="bx-refresh"
          @click="fetchOrders(true)"
          class="text-white"
        />
      </VCol>
    </VRow>

    <!-- Список заказов (Сетка KDS) -->
    <div v-if="loading" class="d-flex justify-center align-center py-10">
      <VProgressCircular indeterminate size="64" color="primary" />
    </div>

    <div v-else-if="orders.length === 0" class="d-flex flex-column justify-center align-center py-16 text-grey">
      <VIcon icon="bx-receipt" size="100" class="mb-4" />
      <div class="text-h5">Нет активных заказов для выбранных цехов</div>
      <div class="text-body-1 mt-1">Ожидайте поступления новых заказов с сайта или iiko...</div>
    </div>

    <VRow v-else class="kds-grid">
      <VCol
        v-for="order in orders"
        :key="order.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
        class="kds-card-col"
      >
        <VCard color="grey-darken-3" class="kds-order-card elevation-4 rounded-lg d-flex flex-column h-100">
          <!-- Заголовок карточки заказа -->
          <div 
            class="pa-3 font-weight-bold d-flex justify-space-between align-center rounded-t-lg"
            :style="`background-color: ${getTimeColor(order.expected_time)}; color: black;`"
          >
            <div>
              <span class="text-h6">№ {{ order.external_number || order.id }}</span>
              <VChip size="x-small" variant="flat" color="black" class="ml-2 text-white font-weight-bold">
                {{ order.order_type || 'Доставка' }}
              </VChip>
            </div>
            <div class="text-body-2 font-weight-bold">
              {{ formatTimeLeft(order.expected_time) }}
            </div>
          </div>

          <!-- Контент карточки (блюда) -->
          <VCardText class="pa-3 flex-grow-1 d-flex flex-column overflow-y-auto">
            <!-- Время создания и статус -->
            <div class="d-flex justify-space-between align-center text-caption text-grey-lighten-1 mb-2">
              <div>Принят: {{ new Date(order.iiko_creation_time || order.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}</div>
              <VChip size="x-small" color="primary" variant="tonal" class="font-weight-bold">
                {{ getStatusText(order.status) }}
              </VChip>
            </div>

            <!-- Управляющие кнопки заказа целиком -->
            <div class="mb-3 pa-2 bg-grey-darken-4 rounded d-flex flex-wrap align-center justify-center gap-1">
              <!-- Начать готовить заказ -->
              <VBtn
                v-if="['new', 'unconfirmed', 'confirmed', 'preparing'].includes(order.status)"
                size="small"
                color="blue"
                variant="flat"
                prepend-icon="bx-play-circle"
                class="font-weight-bold text-white flex-grow-1 text-caption"
                @click="startOrderCooking(order.id)"
              >
                Начать готовить
              </VBtn>

              <!-- Передать на сборку -->
              <VBtn
                v-if="order.status === 'cooking'"
                size="small"
                color="orange"
                variant="flat"
                prepend-icon="bx-package"
                class="font-weight-bold text-white flex-grow-1 text-caption"
                @click="startOrderAssembling(order.id)"
              >
                На сборку
              </VBtn>

              <!-- Отметить собранным -->
              <VBtn
                v-if="order.status === 'assembling'"
                size="small"
                color="success"
                variant="flat"
                prepend-icon="bx-check-square"
                class="font-weight-bold text-black flex-grow-1 text-caption"
                @click="makeOrderReady(order.id)"
              >
                Собран
              </VBtn>

              <!-- Кнопка Готов Полностью (Быстрый перевод) -->
              <VBtn
                v-if="!['ready', 'ready_for_pickup'].includes(order.status)"
                size="small"
                color="green"
                variant="outlined"
                prepend-icon="bx-check-double"
                class="font-weight-bold text-green flex-grow-1 text-caption mt-1"
                @click="makeOrderReady(order.id)"
              >
                Готов полностью
              </VBtn>
            </div>

            <!-- Список блюд -->
            <div class="flex-grow-1">
              <div v-for="item in order.items" :key="item.id" class="kds-item-row border-bottom-dashed py-2">
                <div class="d-flex justify-space-between align-start">
                  <div class="kds-item-name-box">
                    <!-- Кликабельное название для просмотра техкарты -->
                    <span 
                      class="kds-item-name font-weight-bold text-body-1 cursor-pointer text-decoration-underline text-blue-lighten-4"
                      @click="viewRecipe(item.product_id)"
                      title="Посмотреть рецепт блюда"
                    >
                      {{ item.product_name }}
                    </span>
                    
                    <!-- Размер -->
                    <div v-if="item.size_name" class="text-caption text-primary font-weight-bold">
                      Размер: {{ item.size_name }}
                    </div>

                    <!-- Модификаторы -->
                    <div v-if="item.modifiers && item.modifiers.length > 0" class="kds-modifiers-box mt-1 pl-2 border-left-active">
                      <div 
                        v-for="(mod, mIdx) in item.modifiers" 
                        :key="mIdx" 
                        class="text-body-2 text-warning font-weight-bold cursor-pointer text-decoration-underline"
                        @click="viewRecipeByIikoId(mod.productId || mod.iiko_id)"
                        title="Посмотреть техкарту модификатора"
                      >
                        • {{ mod.name }} <span v-if="mod.quantity > 1">x{{ mod.quantity }}</span>
                      </div>
                    </div>

                    <!-- Ссылка/кнопка для развертывания состава, если ингредиенты есть -->
                    <div v-if="item.ingredients && item.ingredients.length > 0" class="mt-1">
                      <span 
                        class="text-caption text-blue-lighten-3 cursor-pointer d-inline-flex align-center font-weight-bold text-decoration-underline"
                        @click.stop="toggleItemIngredients(item.id)"
                      >
                        <VIcon size="14" class="mr-1">{{ expandedItems[item.id] ? 'bx-chevron-up' : 'bx-chevron-down' }}</VIcon>
                        Состав ({{ item.ingredients.length }})
                      </span>
                    </div>

                    <!-- Развернутый состав ингредиентов -->
                    <div v-if="expandedItems[item.id] && item.ingredients && item.ingredients.length > 0" class="kds-ingredients-inline mt-1 pl-3 border-left-active bg-grey-darken-4 pa-1 rounded">
                      <div 
                        v-for="(ing, ingIdx) in item.ingredients" 
                        :key="ingIdx" 
                        class="text-caption d-flex justify-space-between align-center py-0.5 text-grey-lighten-2"
                      >
                        <span 
                          v-if="ing.iiko_id" 
                          class="text-decoration-underline text-blue-lighten-4 cursor-pointer font-weight-bold"
                          @click.stop="viewRecipeByIikoId(ing.iiko_id)"
                          title="Открыть техкарту заготовки"
                        >
                          {{ ing.name }}
                        </span>
                        <span v-else>{{ ing.name }}</span>
                        <span class="text-white ml-2">{{ ing.net }}г</span>
                      </div>
                    </div>

                    <!-- Комментарий к блюду -->
                    <div v-if="item.comment" class="text-body-2 text-red-accent-2 font-weight-bold mt-1">
                      ⚠️ Прим: {{ item.comment }}
                    </div>
                  </div>

                  <div class="text-h6 font-weight-bold text-light-blue-accent-1 ml-2">
                    {{ item.quantity }} шт
                  </div>
                </div>

                <!-- Кнопки управления статусом блюда -->
                <div class="d-flex justify-end mt-2 pt-1">
                  <VBtn
                    v-if="item.kitchen_status === 'pending'"
                    size="small"
                    color="blue"
                    variant="flat"
                    prepend-icon="bx-play"
                    class="font-weight-bold text-white text-caption"
                    @click="changeItemStatus(item.id, 'cooking')"
                  >
                    Начать готовить
                  </VBtn>

                  <VBtn
                    v-else-if="item.kitchen_status === 'cooking'"
                    size="small"
                    color="success"
                    variant="flat"
                    prepend-icon="bx-check"
                    class="font-weight-bold text-black text-caption"
                    @click="changeItemStatus(item.id, 'ready')"
                  >
                    Готово
                  </VBtn>

                  <VChip
                    v-else-if="item.kitchen_status === 'ready'"
                    color="success"
                    variant="tonal"
                    size="small"
                    prepend-icon="bx-check-double"
                    class="font-weight-bold text-caption"
                  >
                    Приготовлено
                  </VChip>
                </div>
              </div>
            </div>

            <!-- Комментарий к заказу внизу карточки -->
            <div v-if="order.comment" class="mt-3 pa-2 rounded bg-grey-darken-4 text-body-2 border-left-comment">
              <strong>Комментарий к заказу:</strong><br />
              {{ order.comment }}
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Диалог просмотра техкарты поваром в KDS -->
    <VDialog v-model="isRecipeDialogOpen" max-width="700px">
      <VCard :loading="recipeLoading" color="grey-darken-3" class="text-white">
        <VCardTitle class="pa-4 bg-primary text-white d-flex justify-space-between align-center">
          <div class="d-flex align-center">
            <VBtn 
              v-if="recipeHistory.length > 0" 
              icon="bx-chevron-left" 
              color="white" 
              variant="text" 
              class="mr-2"
              @click="goBackRecipe"
            />
            <span class="text-h6">Рецепт: {{ selectedProductRecipe?.product_name }}</span>
          </div>
          <VBtn icon="bx-x" color="white" variant="text" @click="isRecipeDialogOpen = false" />
        </VCardTitle>

        <VCardText class="pa-4" v-if="selectedProductRecipe">
          <VRow>
            <!-- Фото и характеристики -->
            <VCol cols="12" sm="4" class="text-center">
              <VAvatar size="140" rounded="lg" class="border mb-3 bg-white">
                <VImg :src="selectedProductRecipe.image_url || '/images/default-dish.jpg'" cover />
              </VAvatar>
              <div class="text-body-1 font-weight-bold mb-1 text-white">Выход: {{ selectedProductRecipe.weight_grams || '—' }} г</div>
              <div class="text-caption text-grey-lighten-2">КБЖУ: {{ selectedProductRecipe.proteins || 0 }}/{{ selectedProductRecipe.fats || 0 }}/{{ selectedProductRecipe.carbohydrates || 0 }} ({{ selectedProductRecipe.calories || 0 }} ккал)</div>
            </VCol>

            <!-- Ингредиенты -->
            <VCol cols="12" sm="8">
              <h4 class="font-weight-bold mb-2 text-primary">Ингредиенты (Состав)</h4>
              <VTable density="compact" class="border rounded bg-grey-darken-4 text-white mb-3">
                <thead>
                  <tr class="text-grey-lighten-2">
                    <th class="text-left text-white">Сырье (заготовка/модификатор)</th>
                    <th class="text-right text-white">Нетто</th>
                    <th class="text-right text-white">Выход</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(ing, idx) in selectedProductRecipe.ingredients" :key="idx" class="text-white">
                    <td class="text-left text-white">
                      <!-- Если есть iiko_id, делаем ссылку кликабельной для вложенного рецепта -->
                      <span 
                        v-if="ing.iiko_id" 
                        class="text-decoration-underline text-blue-lighten-3 cursor-pointer font-weight-bold"
                        @click="viewRecipeByIikoId(ing.iiko_id)"
                        title="Посмотреть техкарту заготовки"
                      >
                        {{ ing.name }}
                      </span>
                      <span v-else>{{ ing.name }}</span>
                    </td>
                    <td class="text-right font-weight-bold text-white">{{ ing.net }} г</td>
                    <td class="text-right font-weight-bold text-white">{{ ing.output }} г</td>
                  </tr>
                  <tr v-if="selectedProductRecipe.ingredients.length === 0">
                    <td colspan="3" class="text-center text-grey">Ингредиенты не указаны</td>
                  </tr>
                </tbody>
              </VTable>
            </VCol>
          </VRow>

          <!-- Технология приготовления -->
          <div class="mt-4 pa-3 rounded bg-grey-darken-4 border-left-active">
            <h4 class="font-weight-bold mb-2 text-primary">Технология приготовления</h4>
            <div class="text-body-1 text-justify text-white" style="white-space: pre-line; line-height: 1.6;">
              {{ selectedProductRecipe.technology || 'Процесс приготовления не описан.' }}
            </div>
          </div>

          <!-- Сноски подачи/ККТ -->
          <div v-if="selectedProductRecipe.appearance" class="mt-3 pa-2 rounded bg-grey-darken-4 border-left-comment text-white">
            <strong>Оформление и подача:</strong> {{ selectedProductRecipe.appearance }}
          </div>
        </VCardText>
        <VCardActions class="pa-4">
          <VSpacer />
          <VBtn color="white" variant="text" @click="isRecipeDialogOpen = false">Закрыть</VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.kds-screen {
  min-height: 100vh;
  font-family: 'Outfit', 'Inter', sans-serif;
}

.border-bottom {
  border-bottom: 2px solid #424242;
}

.border-bottom-dashed {
  border-bottom: 1px dashed #555;
}

.border-left-active {
  border-left: 3.5px solid #FFB300;
}

.border-left-comment {
  border-left: 3.5px solid #2196F3;
}

.kds-grid {
  margin-top: 10px;
}

.kds-order-card {
  border: 1px solid #424242;
  transition: all 0.2s ease;
}

.kds-order-card:hover {
  transform: translateY(-2px);
}

.cursor-pointer {
  cursor: pointer;
}

.text-justify {
  text-align: justify;
}

.overflow-y-auto {
  max-height: 520px;
  overflow-y: auto;
}

.gap-1 {
  gap: 4px;
}

.gap-2 {
  gap: 8px;
}

/* Дополнительные стили для планшетов */
@media (max-width: 1024px) {
  .text-h4 {
    font-size: 1.8rem !important;
  }
  .kds-item-name {
    font-size: 1.05rem !important;
  }
  .v-btn--size-small {
    padding: 0 8px !important;
    height: 32px !important;
  }
}
</style>
