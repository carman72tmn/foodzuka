<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'
import { hasPermission } from '@/utils/auth'

const toast = useToast()

// Состояние
const search = ref('')
const selectedCategory = ref(null)
const selectedZone = ref(null)
const hasRecipeFilter = ref(null)
const categories = ref([])
const zones = ref([])
const products = ref([])
const loading = ref(false)

// Диалог рецепта
const isRecipeDialogOpen = ref(false)
const recipeLoading = ref(false)
const selectedProduct = ref(null)
const recipeForm = ref({
  ingredients: [],
  technology: '',
  appearance: '',
  critical_points: '',
  kitchen_zone_id: null
})

// Диалог зон
const isZoneDialogOpen = ref(false)
const isEditingZone = ref(false)
const activeZoneTab = ref(0)
const zoneForm = ref({
  id: null,
  name: '',
  color: '#2196F3',
  description: ''
})

// Для печати
const isPrinting = ref(false)
const printRecipeData = ref(null)

// Загрузка справочников
const fetchCategories = async () => {
  try {
    const res = await axios.get('/api/v1/categories')
    categories.value = res.data
  } catch (err) {
    console.error('Ошибка загрузки категорий:', err)
  }
}

const fetchZones = async () => {
  try {
    const res = await axios.get('/api/v1/kitchen/zones')
    zones.value = res.data
  } catch (err) {
    console.error('Ошибка загрузки зон:', err)
  }
}

const fetchProducts = async () => {
  loading.value = true
  try {
    const params = {}
    if (search.value) params.search = search.value
    if (selectedCategory.value) params.category_id = selectedCategory.value
    if (selectedZone.value) params.kitchen_zone_id = selectedZone.value
    if (hasRecipeFilter.value !== null) params.has_recipe = hasRecipeFilter.value
    
    const res = await axios.get('/api/v1/kitchen/recipes/products', { params })
    products.value = res.data
  } catch (err) {
    toast.error('Не удалось загрузить блюда')
  } finally {
    loading.value = false
  }
}

// Открытие техкарты
const openRecipe = async (product) => {
  selectedProduct.value = product
  recipeLoading.value = true
  isRecipeDialogOpen.value = true
  
  try {
    const res = await axios.get(`/api/v1/kitchen/recipes/${product.id}`)
    const data = res.data
    recipeForm.value = {
      ingredients: data.ingredients || [],
      technology: data.technology || '',
      appearance: data.appearance || '',
      critical_points: data.critical_points || '',
      kitchen_zone_id: data.kitchen_zone_id
    }
  } catch (err) {
    toast.error('Ошибка при загрузке техкарты')
    isRecipeDialogOpen.value = false
  } finally {
    recipeLoading.value = false
  }
}

// Ингредиенты
const addIngredient = () => {
  recipeForm.value.ingredients.push({
    name: '',
    gross: 0,
    net: 0,
    output: 0
  })
}

const removeIngredient = (index) => {
  recipeForm.value.ingredients.splice(index, 1)
}

const totalGross = computed(() => {
  return recipeForm.value.ingredients.reduce((sum, item) => sum + Number(item.gross || 0), 0)
})

const totalNet = computed(() => {
  return recipeForm.value.ingredients.reduce((sum, item) => sum + Number(item.net || 0), 0)
})

const totalOutput = computed(() => {
  return recipeForm.value.ingredients.reduce((sum, item) => sum + Number(item.output || 0), 0)
})

// Сохранение техкарты
const saveRecipe = async () => {
  if (!hasPermission('kitchen_recipes_edit')) {
    toast.error('Недостаточно прав для редактирования техкарт')
    return
  }
  
  recipeLoading.value = true
  try {
    await axios.put(`/api/v1/kitchen/recipes/${selectedProduct.value.id}`, recipeForm.value)
    toast.success('Техкарта успешно сохранена')
    isRecipeDialogOpen.value = false
    fetchProducts()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Ошибка сохранения техкарты')
  } finally {
    recipeLoading.value = false
  }
}

// Управление зонами
const editZone = (zone) => {
  isEditingZone.value = true
  zoneForm.value = { ...zone }
  isZoneDialogOpen.value = true
}

const openCreateZone = () => {
  isEditingZone.value = false
  zoneForm.value = {
    id: null,
    name: '',
    color: '#2196F3',
    description: ''
  }
  isZoneDialogOpen.value = true
}

const saveZone = async () => {
  try {
    if (isEditingZone.value) {
      await axios.put(`/api/v1/kitchen/zones/${zoneForm.value.id}`, zoneForm.value)
      toast.success('Зона приготовления обновлена')
    } else {
      await axios.post('/api/v1/kitchen/zones', zoneForm.value)
      toast.success('Зона приготовления создана')
    }
    isZoneDialogOpen.value = false
    fetchZones()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Ошибка сохранения зоны')
  }
}

const deleteZone = async (id) => {
  if (!confirm('Вы уверены, что хотите удалить эту зону?')) return
  try {
    await axios.delete(`/api/v1/kitchen/zones/${id}`)
    toast.success('Зона удалена')
    fetchZones()
  } catch (err) {
    toast.error('Не удалось удалить зону')
  }
}

// Импорт из iiko
const importLoading = ref(false)
const importFromIiko = async () => {
  if (!confirm('Вы действительно хотите запустить импорт техкарт и цехов из iiko Office? Это обновит локальные техкарты и цеха.')) return
  importLoading.value = true
  try {
    const res = await axios.post('/api/v1/kitchen/recipes/import-iiko')
    toast.success(res.data.message || 'Импорт завершен успешно!')
    fetchZones()
    fetchProducts()
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Не удалось импортировать данные из iiko Office')
  } finally {
    importLoading.value = false
  }
}

// Печать техкарты
const printRecipe = async (product) => {
  try {
    const res = await axios.get(`/api/v1/kitchen/recipes/${product.id}`)
    printRecipeData.value = res.data
    isPrinting.value = true
    
    // Ждем рендера и вызываем печать
    setTimeout(() => {
      window.print()
      isPrinting.value = false
      printRecipeData.value = null
    }, 500)
  } catch (err) {
    toast.error('Не удалось сгенерировать печатную форму')
  }
}

// Получить имя зоны
const getZoneName = (zoneId) => {
  const z = zones.value.find(item => item.id === zoneId)
  return z ? z.name : '—'
}

const getZoneColor = (zoneId) => {
  const z = zones.value.find(item => item.id === zoneId)
  return z ? z.color : '#E0E0E0'
}

onMounted(() => {
  fetchCategories()
  fetchZones()
  fetchProducts()
})
</script>

<template>
  <div>
    <!-- Основной контейнер, скрывается при печати -->
    <div class="no-print">
      <VRow class="mb-4 align-center">
        <VCol cols="12" md="4">
          <h1 class="text-h4 font-weight-bold">Технологические карты блюд</h1>
        </VCol>
        <VCol cols="12" md="8" class="text-right">
          <VBtn
            v-if="hasPermission('kitchen_zones_manage')"
            color="secondary"
            prepend-icon="bx-layer"
            class="mr-2"
            @click="activeZoneTab = 1"
          >
            Зоны приготовления
          </VBtn>
          <VBtn
            v-if="hasPermission('kitchen_recipes_edit')"
            color="warning"
            prepend-icon="bx-cloud-download"
            class="mr-2"
            :loading="importLoading"
            @click="importFromIiko"
          >
            Импорт из iiko Office
          </VBtn>
          <VBtn
            color="primary"
            prepend-icon="bx-refresh"
            @click="fetchProducts"
          >
            Обновить
          </VBtn>
        </VCol>
      </VRow>

      <!-- Вкладки: 0 - Каталог, 1 - Зоны приготовления -->
      <VTabs v-model="activeZoneTab" class="mb-4">
        <VTab :value="0">Каталог техкарт</VTab>
        <VTab v-if="hasPermission('kitchen_zones_manage')" :value="1">Настройка цехов (зон)</VTab>
      </VTabs>

      <VWindow v-model="activeZoneTab">
        <!-- Окно Каталога техкарт -->
        <VWindowItem :value="0">
          <VCard class="pa-4 mb-4">
            <VRow>
              <VCol cols="12" md="3">
                <VTextField
                  v-model="search"
                  label="Поиск по названию или артикулу"
                  prepend-inner-icon="bx-search"
                  clearable
                  @input="fetchProducts"
                />
              </VCol>
              <VCol cols="12" md="3">
                <VSelect
                  v-model="selectedCategory"
                  label="Категория"
                  :items="categories"
                  item-title="name"
                  item-value="id"
                  clearable
                  @update:model-value="fetchProducts"
                />
              </VCol>
              <VCol cols="12" md="3">
                <VSelect
                  v-model="selectedZone"
                  label="Зона приготовления"
                  :items="zones"
                  item-title="name"
                  item-value="id"
                  clearable
                  @update:model-value="fetchProducts"
                />
              </VCol>
              <VCol cols="12" md="3">
                <VSelect
                  v-model="hasRecipeFilter"
                  label="Наличие техкарты"
                  :items="[
                    { title: 'Все блюда', value: null },
                    { title: 'Есть техкарта', value: true },
                    { title: 'Нет техкарты', value: false }
                  ]"
                  item-title="title"
                  item-value="value"
                  @update:model-value="fetchProducts"
                />
              </VCol>
            </VRow>
          </VCard>

          <VDataTable
            :headers="[
              { title: 'Фото', key: 'image_url', sortable: false, width: '80px' },
              { title: 'Название блюда', key: 'name' },
              { title: 'Артикул', key: 'article' },
              { title: 'Зона приготовления', key: 'kitchen_zone_id' },
              { title: 'Статус техкарты', key: 'has_recipe', align: 'center' },
              { title: 'Действия', key: 'actions', sortable: false, align: 'right' }
            ]"
            :items="products"
            :loading="loading"
            class="elevation-1"
          >
            <template #item.image_url="{ item }">
              <VAvatar size="50" rounded="lg">
                <VImg :src="item.image_url || '/images/default-dish.jpg'" cover />
              </VAvatar>
            </template>
            
            <template #item.kitchen_zone_id="{ item }">
              <VChip
                v-if="item.kitchen_zone_id"
                :color="getZoneColor(item.kitchen_zone_id)"
                variant="flat"
                size="small"
                class="text-white"
              >
                {{ getZoneName(item.kitchen_zone_id) }}
              </VChip>
              <span v-else class="text-grey">Не назначена</span>
            </template>

            <template #item.has_recipe="{ item }">
              <VChip
                :color="item.has_recipe ? 'success' : 'warning'"
                size="small"
                variant="tonal"
              >
                {{ item.has_recipe ? 'Заполнена' : 'Не заполнена' }}
              </VChip>
            </template>

            <template #item.actions="{ item }">
              <VBtn
                color="info"
                variant="tonal"
                size="small"
                icon="bx-edit"
                class="mr-2"
                @click="openRecipe(item)"
                title="Редактировать техкарту"
              />
              <VBtn
                color="secondary"
                variant="tonal"
                size="small"
                icon="bx-printer"
                @click="printRecipe(item)"
                title="Печать техкарты"
              />
            </template>
          </VDataTable>
        </VWindowItem>

        <!-- Окно Зон приготовления -->
        <VWindowItem :value="1">
          <VCard class="pa-4 mb-4">
            <div class="d-flex justify-between align-center mb-4">
              <h2 class="text-h6 font-weight-bold">Список цехов на кухне</h2>
              <VBtn color="primary" prepend-icon="bx-plus" @click="openCreateZone">
                Добавить зону
              </VBtn>
            </div>

            <VDataTable
              :headers="[
                { title: 'Название цеха', key: 'name' },
                { title: 'Цвет метки', key: 'color' },
                { title: 'Описание', key: 'description' },
                { title: 'Действия', key: 'actions', sortable: false, align: 'right' }
              ]"
              :items="zones"
              class="elevation-1"
            >
              <template #item.color="{ item }">
                <div class="d-flex align-center">
                  <div :style="`background-color: ${item.color}; width: 24px; height: 24px; border-radius: 4px;`" class="mr-2" />
                  <code>{{ item.color }}</code>
                </div>
              </template>
              
              <template #item.actions="{ item }">
                <VBtn
                  color="info"
                  variant="tonal"
                  size="small"
                  icon="bx-edit"
                  class="mr-2"
                  @click="editZone(item)"
                />
                <VBtn
                  color="error"
                  variant="tonal"
                  size="small"
                  icon="bx-trash"
                  @click="deleteZone(item.id)"
                />
              </template>
            </VDataTable>
          </VCard>
        </VWindowItem>
      </VWindow>
    </div>

    <!-- 4. Диалог редактирования техкарты -->
    <VDialog v-model="isRecipeDialogOpen" max-width="1000px" persistent>
      <VCard :loading="recipeLoading">
        <VCardTitle class="pa-4 bg-primary text-white d-flex justify-space-between align-center">
          <span class="text-h6">Техкарта: {{ selectedProduct?.name }}</span>
          <VBtn icon="bx-x" color="white" variant="text" @click="isRecipeDialogOpen = false" />
        </VCardTitle>

        <VCardText class="pa-4">
          <VRow>
            <!-- Левая колонка: Описание, КБЖУ, Цех -->
            <VCol cols="12" md="4">
              <VCard variant="outlined" class="pa-3 mb-4">
                <h3 class="text-subtitle-1 font-weight-bold mb-3">Данные из iiko</h3>
                <div class="d-flex justify-center mb-3">
                  <VAvatar size="150" rounded="lg" class="border">
                    <VImg :src="selectedProduct?.image_url || '/images/default-dish.jpg'" cover />
                  </VAvatar>
                </div>
                <div class="text-body-2 mb-1"><strong>Артикул:</strong> {{ selectedProduct?.article || '—' }}</div>
                <div class="text-body-2 mb-1"><strong>Вес/Выход:</strong> {{ selectedProduct?.weight_grams || '—' }} г</div>
                <div class="text-body-2 mb-1"><strong>Калорийность:</strong> {{ selectedProduct?.calories || '—' }} ккал</div>
                <div class="text-body-2 mb-1"><strong>Белки:</strong> {{ selectedProduct?.proteins || '—' }} г</div>
                <div class="text-body-2 mb-1"><strong>Жиры:</strong> {{ selectedProduct?.fats || '—' }} г</div>
                <div class="text-body-2 mb-1"><strong>Углеводы:</strong> {{ selectedProduct?.carbohydrates || '—' }} г</div>
              </VCard>

              <!-- Зона приготовления -->
              <VSelect
                v-model="recipeForm.kitchen_zone_id"
                label="Цех приготовления (Зона)"
                :items="zones"
                item-title="name"
                item-value="id"
                placeholder="Выберите цех..."
                clearable
                class="mb-4"
              />
            </VCol>

            <!-- Правая колонка: Ингредиенты и технология -->
            <VCol cols="12" md="8">
              <!-- Ингредиенты -->
              <div class="d-flex justify-space-between align-center mb-2">
                <h3 class="text-subtitle-1 font-weight-bold">Ингредиенты (Состав)</h3>
                <VBtn
                  size="small"
                  color="success"
                  prepend-icon="bx-plus"
                  @click="addIngredient"
                >
                  Добавить строку
                </VBtn>
              </div>

              <VTable density="compact" class="border rounded mb-4">
                <thead>
                  <tr>
                    <th>Наименование сырья</th>
                    <th width="100">Брутто (г)</th>
                    <th width="100">Нетто (г)</th>
                    <th width="100">Выход (г)</th>
                    <th width="50"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(ing, index) in recipeForm.ingredients" :key="index">
                    <td>
                      <VTextField
                        v-model="ing.name"
                        density="compact"
                        hide-details
                        placeholder="Напр. Сыр Моцарелла"
                      />
                    </td>
                    <td>
                      <VTextField
                        v-model.number="ing.gross"
                        type="number"
                        density="compact"
                        hide-details
                      />
                    </td>
                    <td>
                      <VTextField
                        v-model.number="ing.net"
                        type="number"
                        density="compact"
                        hide-details
                      />
                    </td>
                    <td>
                      <VTextField
                        v-model.number="ing.output"
                        type="number"
                        density="compact"
                        hide-details
                      />
                    </td>
                    <td>
                      <VBtn
                        icon="bx-trash"
                        size="x-small"
                        color="error"
                        variant="text"
                        @click="removeIngredient(index)"
                      />
                    </td>
                  </tr>
                  <tr v-if="recipeForm.ingredients.length === 0">
                    <td colspan="5" class="text-center text-grey pa-4">
                      Список ингредиентов пуст. Нажмите "Добавить строку"
                    </td>
                  </tr>
                  <tr v-else class="font-weight-bold bg-light">
                    <td>Итого:</td>
                    <td>{{ totalGross }} г</td>
                    <td>{{ totalNet }} г</td>
                    <td>{{ totalOutput }} г</td>
                    <td></td>
                  </tr>
                </tbody>
              </VTable>

              <!-- Технология приготовления -->
              <VTextarea
                v-model="recipeForm.technology"
                label="Технология приготовления (Пошаговый процесс)"
                rows="4"
                auto-grow
                class="mb-3"
              />

              <!-- Требования к внешнему виду / подаче -->
              <VTextarea
                v-model="recipeForm.appearance"
                label="Требования к внешнему виду и подаче"
                rows="2"
                auto-grow
                class="mb-3"
              />

              <!-- Критические контрольные точки -->
              <VTextarea
                v-model="recipeForm.critical_points"
                label="Сроки хранения и ККТ"
                rows="2"
                auto-grow
              />
            </VCol>
          </VRow>
        </VCardText>

        <VCardActions class="pa-4 bg-light">
          <VSpacer />
          <VBtn color="secondary" variant="outlined" @click="isRecipeDialogOpen = false">
            Отмена
          </VBtn>
          <VBtn
            v-if="hasPermission('kitchen_recipes_edit')"
            color="primary"
            prepend-icon="bx-save"
            @click="saveRecipe"
          >
            Сохранить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- 5. Диалог добавления/редактирования зоны -->
    <VDialog v-model="isZoneDialogOpen" max-width="500px">
      <VCard>
        <VCardTitle class="pa-4 bg-primary text-white d-flex justify-space-between align-center">
          <span class="text-h6">{{ isEditingZone ? 'Редактировать цех' : 'Создать цех' }}</span>
          <VBtn icon="bx-x" color="white" variant="text" @click="isZoneDialogOpen = false" />
        </VCardTitle>

        <VCardText class="pa-4">
          <VTextField
            v-model="zoneForm.name"
            label="Название цеха/зоны"
            class="mb-4"
            required
          />
          
          <div class="mb-4">
            <label class="text-subtitle-2 mb-1 d-block">Цвет метки</label>
            <div class="d-flex align-center">
              <VColorPicker
                v-model="zoneForm.color"
                mode="hex"
                hide-inputs
                show-swatches
                class="mr-4"
              />
              <div>
                <VTextField
                  v-model="zoneForm.color"
                  label="Hex код"
                  density="compact"
                  style="width: 120px;"
                />
                <div :style="`background-color: ${zoneForm.color}; width: 120px; height: 40px; border-radius: 4px; border: 1px solid #ddd;`" class="mt-2" />
              </div>
            </div>
          </div>

          <VTextarea
            v-model="zoneForm.description"
            label="Описание цеха"
            rows="3"
          />
        </VCardText>

        <VCardActions class="pa-4 bg-light">
          <VSpacer />
          <VBtn color="secondary" variant="outlined" @click="isZoneDialogOpen = false">
            Отмена
          </VBtn>
          <VBtn color="primary" prepend-icon="bx-save" @click="saveZone">
            Сохранить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- 6. Печатная форма техкарты (A4) - Видна ТОЛЬКО при печати -->
    <div v-if="isPrinting && printRecipeData" class="print-container">
      <div class="print-header d-flex justify-space-between align-center border-bottom pb-3 mb-4">
        <div>
          <h2 class="print-title">{{ printRecipeData.product_name }}</h2>
          <span class="print-meta">Артикул: {{ printRecipeData.article || '—' }}</span>
        </div>
        <div class="print-logo text-right font-weight-bold">
          FoodZuka Kitchen
        </div>
      </div>

      <div class="print-body">
        <div class="d-flex mb-4">
          <!-- Левая сторона: БЖУ и КБЖУ в печатной карточке -->
          <div class="print-info-block border pa-3 mr-4 flex-grow-1">
            <h4 class="font-weight-bold border-bottom pb-1 mb-2">Характеристики блюда</h4>
            <table class="w-100 print-table-metrics">
              <tr>
                <td><strong>Выход блюда:</strong></td>
                <td class="text-right">{{ printRecipeData.weight_grams || '—' }} г</td>
              </tr>
              <tr>
                <td><strong>Калорийность:</strong></td>
                <td class="text-right">{{ printRecipeData.calories || '—' }} ккал</td>
              </tr>
              <tr>
                <td><strong>Белки:</strong></td>
                <td class="text-right">{{ printRecipeData.proteins || '—' }} г</td>
              </tr>
              <tr>
                <td><strong>Жиры:</strong></td>
                <td class="text-right">{{ printRecipeData.fats || '—' }} г</td>
              </tr>
              <tr>
                <td><strong>Углеводы:</strong></td>
                <td class="text-right">{{ printRecipeData.carbohydrates || '—' }} г</td>
              </tr>
              <tr>
                <td><strong>Цех приготовления:</strong></td>
                <td class="text-right">{{ getZoneName(printRecipeData.kitchen_zone_id) }}</td>
              </tr>
            </table>
          </div>

          <!-- Правая сторона: Фотография в печатной карточке -->
          <div class="print-photo border pa-2 text-center" style="width: 160px; height: 160px;">
            <img 
              :src="printRecipeData.image_url || '/images/default-dish.jpg'" 
              style="max-width: 100%; max-height: 100%; object-fit: cover;"
              alt="Фото блюда" 
            />
          </div>
        </div>

        <!-- Ингредиенты -->
        <div class="print-section mb-4">
          <h4 class="font-weight-bold border-bottom pb-1 mb-2">1. Рецептурный состав (Ингредиенты)</h4>
          <table class="print-table w-100 border text-left">
            <thead>
              <tr class="bg-light-grey">
                <th class="border pa-2">Наименование сырья</th>
                <th class="border pa-2 text-center" style="width: 100px;">Брутто (г)</th>
                <th class="border pa-2 text-center" style="width: 100px;">Нетто (г)</th>
                <th class="border pa-2 text-center" style="width: 100px;">Выход (г)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(ing, index) in printRecipeData.ingredients" :key="index">
                <td class="border pa-2">{{ ing.name }}</td>
                <td class="border pa-2 text-center">{{ ing.gross }}</td>
                <td class="border pa-2 text-center">{{ ing.net }}</td>
                <td class="border pa-2 text-center">{{ ing.output }}</td>
              </tr>
              <tr class="font-weight-bold bg-light-grey">
                <td class="border pa-2">Итого сырья (выход):</td>
                <td class="border pa-2 text-center">{{ printRecipeData.ingredients.reduce((sum, item) => sum + Number(item.gross || 0), 0) }} г</td>
                <td class="border pa-2 text-center">{{ printRecipeData.ingredients.reduce((sum, item) => sum + Number(item.net || 0), 0) }} г</td>
                <td class="border pa-2 text-center">{{ printRecipeData.ingredients.reduce((sum, item) => sum + Number(item.output || 0), 0) }} г</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Технология приготовления -->
        <div class="print-section mb-4">
          <h4 class="font-weight-bold border-bottom pb-1 mb-2">2. Технология приготовления</h4>
          <div class="print-text text-justify" style="white-space: pre-line;">
            {{ printRecipeData.technology || 'Технология приготовления не заполнена.' }}
          </div>
        </div>

        <!-- Подача -->
        <div class="print-section mb-4" v-if="printRecipeData.appearance">
          <h4 class="font-weight-bold border-bottom pb-1 mb-2">3. Требования к оформлению и подаче</h4>
          <div class="print-text text-justify" style="white-space: pre-line;">
            {{ printRecipeData.appearance }}
          </div>
        </div>

        <!-- ККТ -->
        <div class="print-section" v-if="printRecipeData.critical_points">
          <h4 class="font-weight-bold border-bottom pb-1 mb-2">4. Условия хранения и ККТ</h4>
          <div class="print-text text-justify" style="white-space: pre-line;">
            {{ printRecipeData.critical_points }}
          </div>
        </div>
      </div>

      <div class="print-footer border-top pt-3 mt-5 text-center text-grey text-caption">
        Технологическая карта создана автоматически в панели управления FoodZuka. Дата печати: {{ new Date().toLocaleDateString() }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Стили для печатной формы */
@media print {
  /* Скрываем всю админку и все элементы кроме печатной формы */
  .no-print {
    display: none !important;
  }
  
  /* Разворачиваем печатный контейнер */
  .print-container {
    display: block !important;
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    font-family: 'Outfit', 'Inter', sans-serif;
    color: #000;
    background: #fff;
    padding: 0;
    margin: 0;
    box-sizing: border-box;
  }

  .border-bottom {
    border-bottom: 2px solid #333 !important;
  }

  .border {
    border: 1px solid #333 !important;
  }

  .print-table {
    border-collapse: collapse;
    width: 100%;
  }

  .print-table th, .print-table td {
    border: 1px solid #333 !important;
    padding: 6px 10px;
    font-size: 11pt;
  }

  .bg-light-grey {
    background-color: #f2f2f2 !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }

  .print-text {
    font-size: 11pt;
    line-height: 1.5;
  }

  .print-table-metrics td {
    padding: 3px 0;
    font-size: 10.5pt;
  }
}

/* Стили отображения в браузере */
.print-container {
  display: none;
}

.text-justify {
  text-align: justify;
}

.w-100 {
  width: 100%;
}
</style>
