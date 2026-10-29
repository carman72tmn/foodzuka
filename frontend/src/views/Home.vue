<template>
  <div class="home-page fade-in">
    <!-- Hero Banner Carousel / Banners -->
    <div class="banners-carousel">
      <div class="banner-card orange-gradient">
        <div class="banner-content">
          <h3>СКИДКА -10% НА САМОВЫВОЗ!</h3>
          <p>По промокоду: <strong>SAM</strong></p>
        </div>
        <div class="banner-badge">🔥 Акция</div>
      </div>
      <div class="banner-card purple-gradient">
        <div class="banner-content">
          <h3>ДЕНЬ РОЖДЕНИЯ? СКИДКА -15%!</h3>
          <p>По промокоду: <strong>DR15</strong></p>
        </div>
        <div class="banner-badge">🎂 Поздравляем</div>
      </div>
      <div class="banner-card green-gradient">
        <div class="banner-content">
          <h3>ПОДАРОК К ЗАКАЗУ ЗА 0 ₽!</h3>
          <p>Выбирайте вкусные подарки в корзине</p>
        </div>
        <div class="banner-badge">🎁 Подарки</div>
      </div>
    </div>

    <!-- Category Selector (Horizontal Scroll) -->
    <div class="categories-nav no-visible-scrollbar">
      <button 
        class="category-tab" 
        :class="{ active: selectedCategory === null }"
        @click="selectedCategory = null"
      >
        🍽️ Все меню
      </button>
      <button 
        v-for="cat in visibleCategories" 
        :key="cat.id"
        class="category-tab"
        :class="{ active: selectedCategory === cat.id }"
        @click="selectedCategory = cat.id"
      >
        {{ getCategoryEmoji(cat.name) }} {{ cat.name }}
      </button>
    </div>

    <!-- Catalog Section -->
    <div class="catalog-container">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Загружаем вкусное меню...</p>
      </div>

      <div v-else class="catalog-grid-wrapper">
        <div v-for="category in displayCategories" :key="category.id" class="category-section">
          <h2 class="category-title">
            <span class="emoji">{{ getCategoryEmoji(category.name) }}</span>
            {{ category.name }}
          </h2>

          <div class="product-grid mt-4">
            <div 
              v-for="product in getProductsByCategory(category.id)" 
              :key="product.id" 
              class="product-card group"
              :class="{ 'stopped-card': isProductStopped(product) }"
            >
              <!-- Card Top: Image + Info (Click opens modal) -->
              <div class="card-top" @click="openProductModal(product)">
                <div class="image-container">
                  <img 
                    :src="product.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=400&auto=format&fit=crop'" 
                    :alt="product.name"
                    class="product-img"
                  />
                  <!-- Wrapper for all tags on the image -->
                  <div class="badges-wrapper">
                    <div v-if="product.is_popular" class="popular-tag">Хит</div>
                    <div 
                      v-for="tag in getProductTags(product)" 
                      :key="tag" 
                      class="custom-tag"
                      :class="getTagColorClass(tag)"
                    >
                      {{ tag }}
                    </div>
                  </div>
                  <!-- Discount badge -->
                  <div v-if="hasDiscount(product)" class="discount-badge">
                    Скидка {{ getDiscountPercent(product) }}%
                  </div>
                </div>
                
                <div class="info-container">
                  <h3 class="product-name">{{ product.name }}</h3>
                  <span class="product-weight">
                    {{ getProductWeight(product) }}
                  </span>
                  <p class="product-desc">{{ product.description }}</p>
                </div>
              </div>

              <!-- Card Middle: Sizes/Variants selector -->
              <div v-if="product.sizes && product.sizes.length > 1" class="variants-container">
                <div class="size-tabs">
                  <button 
                    v-for="size in product.sizes" 
                    :key="size.id"
                    class="size-tab-btn"
                    :class="{ active: getSelectedSize(product).id === size.id }"
                    @click.stop="setSelectedSize(product.id, size)"
                  >
                    {{ size.name }}
                  </button>
                </div>
              </div>

              <!-- Card Bottom: Price & Button -->
              <div class="card-footer">
                <div class="price-container">
                  <span v-if="product.old_price" class="old-price">{{ getProductOldPrice(product) }} ₽</span>
                  <span class="current-price">{{ getProductPrice(product) }} ₽</span>
                </div>

                <!-- Add Button / Counter -->
                <div class="action-btn-container">
                  <span v-if="isProductStopped(product)" class="stopped-status-label">Нет в наличии</span>
                  
                  <!-- Case: already in cart -->
                  <div v-else-if="getCartQty(product) > 0" class="counter-btn">
                    <button class="cnt-btn" @click="decrementQty(product)" aria-label="Меньше">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" x2="19" y1="12" y2="12"></line></svg>
                    </button>
                    <span class="qty-num">{{ getCartQty(product) }}</span>
                    <button class="cnt-btn" @click="incrementQty(product)" aria-label="Больше">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="5" y2="19"></line><line x1="5" x2="19" y1="12" y2="12"></line></svg>
                    </button>
                  </div>
                  <!-- Case: add to cart -->
                  <button v-else class="add-to-cart-btn" @click="addToCart(product)" aria-label="Добавить в корзину">
                    <span class="btn-price">{{ getProductPrice(product) }} ₽</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="plus-icon">
                      <line x1="12" x2="12" y1="5" y2="19"></line>
                      <line x1="5" x2="19" y1="12" y2="12"></line>
                    </svg>
                  </button>
                </div>
                
                <!-- Stop list message -->
                <div v-if="isProductStopped(product)" class="stopped-msg-banner">
                  В данном заведении временно данная позиция находится в стоп-листе
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Floating Bottom Cart Bar -->
    <div v-if="cartStore.totalItems > 0" class="floating-cart-bar fade-in">
      <div class="cart-bar-content" @click="$router.push('/cart')">
        <div class="cart-bar-left">
          <div class="bag-icon-wrapper">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <path d="M16 10a4 4 0 0 1-8 0"></path>
            </svg>
            <span class="badge">{{ cartStore.totalItems }}</span>
          </div>
          <span class="cart-bar-price">{{ cartStore.totalPrice }} ₽</span>
        </div>
        <div class="cart-bar-right">
          <span>Перейти в корзину</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </div>
      </div>
    </div>

    <!-- Product Detail Modal (Radix style) -->
    <div v-if="modalProduct" class="modal-overlay" @click="closeProductModal">
      <div class="modal-content-wrapper scrollbar-thin" @click.stop>
        <!-- Close Button -->
        <button class="modal-close-btn" @click="closeProductModal" aria-label="Закрыть">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" x2="6" y1="6" y2="18"></line>
            <line x1="6" x2="18" y1="6" y2="18"></line>
          </svg>
        </button>

        <div class="modal-body">
          <!-- Left pane: Image -->
          <div class="modal-image-pane">
            <img 
              :src="modalProduct.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=600&auto=format&fit=crop'" 
              :alt="modalProduct.name"
            />
          </div>

          <!-- Right pane: Scrollable info -->
          <div class="modal-info-pane scrollbar-thin">
            <!-- Basic Details -->
            <div class="modal-section basic-info">
              <h2>{{ modalProduct.name }}</h2>
              <span class="weight-label">{{ getModalProductWeight() }}</span>
              <p class="desc-text">{{ modalProduct.description }}</p>

              <!-- Size selector in modal -->
              <div v-if="modalProduct.sizes && modalProduct.sizes.length > 1" class="modal-sizes mt-3">
                <div class="size-tabs">
                  <button 
                    v-for="size in modalProduct.sizes" 
                    :key="size.id"
                    class="size-tab-btn"
                    :class="{ active: modalSelectedSize.id === size.id }"
                    @click="modalSelectedSize = size"
                  >
                    {{ size.name }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Modifiers ("В комплект не входят!") -->
            <div v-if="modalProduct.modifier_groups && modalProduct.modifier_groups.length > 0" class="modal-section modifiers-section">
              <template v-for="group in modalProduct.modifier_groups" :key="group.id">
                <div v-if="group.modifiers.some(m => m.is_visible !== false)" class="modifier-group">
                  <h3>{{ group.name }} <span class="group-limit" v-if="group.max_amount > 1">(до {{ group.max_amount }} шт)</span></h3>
                  
                  <div class="modifiers-grid">
                    <template v-for="mod in group.modifiers" :key="mod.id">
                      <div 
                        v-if="mod.is_visible !== false"
                        class="modifier-card"
                        :class="{ selected: isModifierSelected(mod) }"
                        @click="toggleModifier(mod, group)"
                      >
                        <img 
                          :src="getModifierImage(mod)" 
                          :alt="mod.name"
                          class="mod-img"
                        />
                        <div class="mod-info">
                          <p class="mod-name">{{ mod.name }}</p>
                          <span class="mod-price">+{{ mod.price }} ₽</span>
                        </div>
                        <div v-if="isModifierSelected(mod)" class="mod-check">
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>
              </template>
            </div>

            <!-- KBJU Card -->
            <div v-if="hasKBJU(modalProduct)" class="modal-section kbju-section">
              <div class="kbju-grid">
                <div class="kbju-box">
                  <span class="value">{{ modalProduct.calories || '—' }}</span>
                  <span class="label">ККал</span>
                </div>
                <div class="kbju-box">
                  <span class="value">{{ modalProduct.proteins || '—' }}г</span>
                  <span class="label">Белки</span>
                </div>
                <div class="kbju-box">
                  <span class="value">{{ modalProduct.carbohydrates || '—' }}г</span>
                  <span class="label">Углеводы</span>
                </div>
                <div class="kbju-box">
                  <span class="value">{{ modalProduct.fats || '—' }}г</span>
                  <span class="label">Жиры</span>
                </div>
              </div>
              <span class="kbju-disclaimer">*на 100 грамм готового блюда</span>
            </div>

            <!-- Блок допродаж "С этим часто покупают" -->
            <div v-if="upsellProducts.length > 0" class="upsell-section">
              <h3 class="upsell-title">С этим часто покупают:</h3>
              <div class="upsell-list no-visible-scrollbar">
                <div v-for="item in upsellProducts" :key="item.id" class="upsell-item">
                  <img :src="item.image_url" :alt="item.name" class="upsell-img" />
                  <div class="upsell-info">
                    <p class="upsell-name">{{ item.name }}</p>
                    <span class="upsell-price">{{ item.price }} ₽</span>
                  </div>
                  <button class="upsell-add-btn" @click.stop="addUpsellToCart(item)" title="Добавить">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="12" x2="12" y1="5" y2="19"></line>
                      <line x1="5" x2="19" y1="12" y2="12"></line>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

          </div>
        </div>

        <!-- Sticky Footer Modal Actions -->
        <div class="modal-footer">
          <div v-if="isProductStopped(modalProduct)" class="modal-stopped-banner">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
              <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon>
              <line x1="12" x2="12" y1="8" y2="12"></line>
              <line x1="12" x2="12.01" y1="16" y2="16"></line>
            </svg>
            В данном заведении временно данная позиция находится в стоп-листе
          </div>
          <button v-else class="modal-add-btn" @click="addModalItemToCart">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
              <line x1="12" x2="12" y1="5" y2="19"></line>
              <line x1="5" x2="19" y1="12" y2="12"></line>
            </svg>
            Добавить за {{ getModalTotalPrice() }} ₽
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useCartStore } from '../store/cart'
import { fetchProducts, fetchCategories } from '../api/catalog'

const cartStore = useCartStore()
const products = ref([])
const categories = ref([])
const loading = ref(true)
const selectedCategory = ref(null)

// Track size choices on the cards: { [productId]: selectedSizeObject }
const cardSelectedSizes = reactive({})

// Modal States
const modalProduct = ref(null)
const modalSelectedSize = ref(null)
const modalSelectedModifiers = ref([])

onMounted(async () => {
  try {
    const [prodsData, catsData] = await Promise.all([
      fetchProducts(),
      fetchCategories()
    ])
    products.value = prodsData
    categories.value = catsData

    // Initialize default sizes for products
    products.value.forEach(product => {
      if (product.sizes && product.sizes.length > 0) {
        // Choose default size or first size
        const defaultSize = product.sizes.find(s => s.is_default) || product.sizes[0]
        cardSelectedSizes[product.id] = defaultSize
      }
    })
  } catch (err) {
    console.error('Error loading catalog data', err)
  } finally {
    loading.value = false
  }
})

// Categories emoji mapper
const getCategoryEmoji = (name) => {
  const normalized = name.toLowerCase()
  if (normalized.includes('ролл') || normalized.includes('суши')) return '🍣'
  if (normalized.includes('пицца')) return '🍕'
  if (normalized.includes('суп') || normalized.includes('том ям')) return '🍲'
  if (normalized.includes('салат')) return '🥗'
  if (normalized.includes('закус') || normalized.includes('фри')) return '🍟'
  if (normalized.includes('напит') || normalized.includes('сок')) return '🥤'
  if (normalized.includes('десерт') || normalized.includes('слад')) return '🍰'
  if (normalized.includes('сет') || normalized.includes('комбо')) return '🍱'
  if (normalized.includes('вок') || normalized.includes('wok')) return '🍜'
  return '🍽️'
}

const visibleCategories = computed(() => {
  return categories.value.filter(c => c.is_active && !c.hide_category_only && !c.hide_category_and_products && !c.parent_id)
})

const displayCategories = computed(() => {
  const visible = visibleCategories.value
  if (selectedCategory.value === null) return visible
  return visible.filter(c => c.id === selectedCategory.value)
})

const getProductsByCategory = (catId) => {
  const categoryIds = [catId]
  const subCats = categories.value.filter(c => c.parent_id === catId)
  subCats.forEach(sc => {
    categoryIds.push(sc.id)
    const subSubCats = categories.value.filter(c => c.parent_id === sc.id)
    subSubCats.forEach(ssc => categoryIds.push(ssc.id))
  })

  return products.value
    .filter(p => p.is_available && categoryIds.includes(p.category_id))
    .sort((a, b) => (a.sort_order - b.sort_order) || a.name.localeCompare(b.name))
}

const upsellProducts = computed(() => {
  if (!products.value.length) return []
  return products.value.filter(p => {
    if (modalProduct.value && p.id === modalProduct.value.id) return false
    if (!p.is_available) return false
    const cat = categories.value.find(c => c.id === p.category_id)
    if (!cat) return false
    const catName = cat.name.toLowerCase()
    const pName = p.name.toLowerCase()
    return catName.includes('напит') || 
           catName.includes('сок') || 
           catName.includes('десерт') || 
           catName.includes('соус') || 
           pName.includes('соус')
  }).slice(0, 5)
})

const addUpsellToCart = (product) => {
  const size = product.sizes && product.sizes.length > 0
    ? (product.sizes.find(s => s.is_default) || product.sizes[0])
    : null
  cartStore.addItem(product, size, [])
}

const isProductStopped = (product) => {
  if (!product) return false
  return !!(product.is_on_stop_list || product.is_stopped)
}

// Card Sizes Helpers
const getSelectedSize = (product) => {
  if (!product) return { id: 'default', price: 0, name: '' }
  if (cardSelectedSizes[product.id]) {
    return cardSelectedSizes[product.id]
  }
  if (product.sizes && product.sizes.length > 0) {
    const def = product.sizes.find(s => s.is_default) || product.sizes[0]
    cardSelectedSizes[product.id] = def
    return def
  }
  return { id: 'default', price: product.price, name: '' }
}

const setSelectedSize = (productId, size) => {
  cardSelectedSizes[productId] = size
}

const getProductPrice = (product) => {
  if (product.sizes && product.sizes.length > 0) {
    return Math.round(getSelectedSize(product).price)
  }
  return Math.round(product.price)
}

const getProductOldPrice = (product) => {
  // If size selected, old_price is usually proportional or we show product old price
  if (product.old_price) return Math.round(product.old_price)
  return null
}

const getProductTags = (product) => {
  if (!product.tags) return []
  return product.tags.split(',').map(t => t.trim()).filter(Boolean)
}

const getTagColorClass = (tag) => {
  const t = tag.toLowerCase()
  if (t === 'новинка' || t === 'new') return 'tag-new'
  if (t === 'острое' || t === 'острая') return 'tag-spicy'
  if (t === 'веган' || t === 'vegan' || t === 'постное') return 'tag-vegan'
  return 'tag-default'
}

const hasDiscount = (product) => {
  const price = getProductPrice(product)
  const oldPrice = getProductOldPrice(product)
  return oldPrice && oldPrice > price
}

const getDiscountPercent = (product) => {
  const price = getProductPrice(product)
  const oldPrice = getProductOldPrice(product)
  if (!oldPrice || oldPrice <= price) return 0
  return Math.round(((oldPrice - price) / oldPrice) * 100)
}

const getProductWeight = (product) => {
  if (product.sizes && product.sizes.length > 0) {
    const size = getSelectedSize(product)
    const weightStr = size.weight_grams ? ` (${size.weight_grams} г)` : ''
    return `${size.name}${weightStr}`.trim()
  }
  return product.weight_grams ? `${product.weight_grams} г` : ''
}

// Cart actions from card
const getCartKeyForCard = (product) => {
  const size = getSelectedSize(product)
  const sizeId = size ? size.id : 'default'
  return `${product.id}_${sizeId}_`
}

const getCartQty = (product) => {
  const key = getCartKeyForCard(product)
  const cartItem = cartStore.items.find(item => item.cart_item_key === key)
  return cartItem ? cartItem.quantity : 0
}

const addToCart = (product) => {
  const size = getSelectedSize(product)
  cartStore.addItem(product, size, [])
}

const incrementQty = (product) => {
  const key = getCartKeyForCard(product)
  cartStore.incrementItem(key)
}

const decrementQty = (product) => {
  const key = getCartKeyForCard(product)
  cartStore.removeItem(key)
}

// Modal Logics
const openProductModal = (product) => {
  modalProduct.value = product
  modalSelectedSize.value = getSelectedSize(product)
  modalSelectedModifiers.value = []
  document.body.style.overflow = 'hidden'
}

const closeProductModal = () => {
  modalProduct.value = null
  modalSelectedSize.value = null
  modalSelectedModifiers.value = []
  document.body.style.overflow = ''
}

const getModalProductWeight = () => {
  if (!modalProduct.value) return ''
  if (modalProduct.value.sizes && modalProduct.value.sizes.length > 0 && modalSelectedSize.value) {
    const s = modalSelectedSize.value
    const weightStr = s.weight_grams ? ` (${s.weight_grams} г)` : ''
    return `${s.name}${weightStr}`.trim()
  }
  return modalProduct.value.weight_grams ? `${modalProduct.value.weight_grams} г` : ''
}

const hasKBJU = (p) => {
  return p.calories || p.proteins || p.fats || p.carbohydrates
}

const getModifierImage = (mod) => {
  // Return standard image or placeholder
  return mod.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=150&auto=format&fit=crop'
}

const isModifierSelected = (mod) => {
  return modalSelectedModifiers.value.some(m => m.id === mod.id)
}

const toggleModifier = (mod, group) => {
  const index = modalSelectedModifiers.value.findIndex(m => m.id === mod.id)
  if (index > -1) {
    modalSelectedModifiers.value.splice(index, 1)
  } else {
    // Check group limit
    const groupMods = modalSelectedModifiers.value.filter(m => m.group_id === group.id)
    if (groupMods.length < (group.max_amount || 1)) {
      modalSelectedModifiers.value.push({ ...mod, group_id: group.id })
    } else if (group.max_amount === 1) {
      // Toggle off the other one if max is 1
      const otherModIndex = modalSelectedModifiers.value.findIndex(m => m.group_id === group.id)
      if (otherModIndex > -1) {
        modalSelectedModifiers.value.splice(otherModIndex, 1)
      }
      modalSelectedModifiers.value.push({ ...mod, group_id: group.id })
    }
  }
}

const getModalTotalPrice = () => {
  if (!modalProduct.value) return 0
  const sizePrice = modalSelectedSize.value ? parseFloat(modalSelectedSize.value.price) : parseFloat(modalProduct.value.price)
  const modsPrice = modalSelectedModifiers.value.reduce((sum, m) => sum + parseFloat(m.price), 0)
  return Math.round(sizePrice + modsPrice)
}

const addModalItemToCart = () => {
  if (!modalProduct.value) return
  if (modalSelectedSize.value) {
    cardSelectedSizes[modalProduct.value.id] = modalSelectedSize.value
  }
  cartStore.addItem(modalProduct.value, modalSelectedSize.value, [...modalSelectedModifiers.value])
  closeProductModal()
}
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Banners Carousel */
.banners-carousel {
  display: flex;
  gap: 20px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.banners-carousel::-webkit-scrollbar {
  height: 4px;
}
.banners-carousel::-webkit-scrollbar-thumb {
  background: var(--color-gray-border);
  border-radius: 4px;
}

.banner-card {
  min-width: 280px;
  flex: 1;
  border-radius: var(--radius-xl);
  padding: 1.5rem;
  color: white;
  position: relative;
  overflow: hidden;
  height: 140px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s;
  cursor: pointer;
}

.banner-card:hover {
  transform: translateY(-2px);
}

.banner-badge {
  position: absolute;
  top: 15px;
  right: 15px;
  background-color: rgba(255, 255, 255, 0.2);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.banner-content h3 {
  font-size: 1.15rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 4px;
}

.banner-content p {
  font-size: 0.85rem;
  opacity: 0.9;
}

/* Gradients */
.orange-gradient {
  background: linear-gradient(135deg, #ff6b35 0%, #ff8c5f 100%);
}
.purple-gradient {
  background: linear-gradient(135deg, #7745bb 0%, #9e75db 100%);
}
.green-gradient {
  background: linear-gradient(135deg, #5f9d55 0%, #7dbd73 100%);
}

/* Category navigation */
.categories-nav {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-gray-border);
}

.category-tab {
  padding: 10px 20px;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--color-gray-border);
  border-radius: var(--radius-full);
  font-size: 0.9rem;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.category-tab:hover {
  background-color: var(--bg-tetriary);
}

.category-tab.active {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--text-inverse);
  box-shadow: 0 4px 12px rgba(var(--color-accent-rgb), 0.25);
}

/* Catalog section */
.category-section {
  margin-bottom: 3rem;
}

.category-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Card design matching dovezuka.ru */
.product-card {
  background-color: var(--bg-product-card);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-gray-border);
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.2s;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-accent);
}

.card-top {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.image-container {
  aspect-ratio: 1/1;
  width: 100%;
  position: relative;
  overflow: hidden;
  background-color: var(--bg-tetriary);
}

.product-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s;
}

.product-card:hover .product-img {
  transform: scale(1.05);
}

.badges-wrapper {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 2;
}

.popular-tag {
  background-color: var(--color-accent);
  color: var(--text-inverse);
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.custom-tag {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.tag-new {
  background-color: #5f9d55;
  color: #ffffff;
}

.tag-spicy {
  background-color: #d32f2f;
  color: #ffffff;
}

.tag-vegan {
  background-color: #2e7d32;
  color: #ffffff;
}

.tag-default {
  background-color: #616161;
  color: #ffffff;
}

.discount-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background-color: #d32f2f;
  color: #ffffff;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  padding: 4px 10px;
  border-radius: var(--radius-md);
  box-shadow: 0 2px 8px rgba(211, 47, 47, 0.4);
  animation: pulse-badge 2s infinite;
  z-index: 2;
}

@keyframes pulse-badge {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

.info-container {
  padding: 12px 14px 8px 14px;
  display: flex;
  flex-direction: column;
}

.product-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.25;
  margin-bottom: 4px;
}

.product-weight {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 500;
  margin-bottom: 6px;
}

.product-desc {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Variant selectors */
.variants-container {
  padding: 0 14px 10px 14px;
}

.size-tabs {
  display: flex;
  background-color: var(--bg-tetriary);
  padding: 3px;
  border-radius: var(--radius-full);
  width: 100%;
  gap: 2px;
}

.size-tab-btn {
  flex: 1;
  padding: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  border-radius: var(--radius-full);
  border: none;
  background: transparent;
  cursor: pointer;
  white-space: nowrap;
}

.size-tab-btn.active {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

/* Card bottom */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px 14px 14px;
  margin-top: auto;
}

.price-container {
  display: flex;
  flex-direction: column;
}

.old-price {
  font-size: 0.8rem;
  color: var(--text-secondary);
  text-decoration: line-through;
  line-height: 1;
}

.current-price {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-primary);
}

.action-btn-container {
  width: 120px;
}

.add-to-cart-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background-color: var(--counter-bg);
  border-radius: var(--radius-full);
  color: var(--text-primary);
  font-weight: 700;
  font-size: 0.85rem;
  border: none;
  cursor: pointer;
  transition: all 0.25s ease;
}

.add-to-cart-btn:hover {
  background-color: var(--color-accent);
  color: var(--text-inverse);
}

.add-to-cart-btn .plus-icon {
  margin-left: 4px;
}

/* Counter */
.counter-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 6px;
  background-color: var(--color-accent);
  color: var(--text-inverse);
  border-radius: var(--radius-full);
}

.cnt-btn {
  width: 26px;
  height: 26px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  cursor: pointer;
}

.cnt-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.qty-num {
  font-weight: 700;
  font-size: 0.9rem;
}

/* Floating Bottom Cart Bar */
.floating-cart-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 40px);
  max-width: 500px;
  background-color: #1a1a1a;
  color: white;
  border-radius: var(--radius-xl);
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  z-index: 99;
}

.cart-bar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
}

.cart-bar-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.bag-icon-wrapper {
  position: relative;
}

.bag-icon-wrapper .badge {
  position: absolute;
  top: -6px;
  right: -8px;
  background-color: var(--color-accent);
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  border-radius: var(--radius-full);
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.cart-bar-price {
  font-weight: 700;
  font-size: 1.1rem;
}

.cart-bar-right {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  opacity: 0.9;
}

/* Modal details overlay & content */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.6);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-content-wrapper {
  background-color: var(--bg-main);
  border-radius: var(--radius-2xl);
  max-width: 900px;
  width: 100%;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
  animation: fadeIn 0.3s ease-out forwards;
}

.modal-close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background-color: rgba(0, 0, 0, 0.3);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
}

.modal-close-btn:hover {
  background-color: var(--color-accent);
}

.modal-body {
  display: flex;
  overflow: hidden;
  height: calc(85vh - 76px);
}

@media (max-width: 768px) {
  .modal-body {
    flex-direction: column;
    overflow-y: auto;
  }
  .modal-content-wrapper {
    max-height: 90vh;
  }
}

.modal-image-pane {
  flex: 1.2;
  background-color: var(--bg-tetriary);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.modal-image-pane img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-info-pane {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
  background-color: var(--color-cart-bg);
}

.modal-section {
  background-color: var(--bg-main);
  border-radius: var(--radius-lg);
  padding: 1.2rem;
  box-shadow: var(--shadow-sm);
}

.basic-info h2 {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 4px;
}

.weight-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 600;
  display: block;
  margin-bottom: 10px;
}

.desc-text {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.45;
}

/* Modifiers section */
.modifier-group h3 {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 12px;
}

.group-limit {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: normal;
}

.modifiers-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

@media (max-width: 480px) {
  .modifiers-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.modifier-card {
  border-radius: var(--radius-md);
  border: 1px solid var(--color-gray-border);
  background-color: var(--bg-secondary);
  overflow: hidden;
  cursor: pointer;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
  user-select: none;
}

.modifier-card.selected {
  border-color: var(--color-accent);
  background-color: rgba(var(--color-accent-rgb), 0.05);
}

.mod-img {
  width: 100%;
  aspect-ratio: 1/1;
  object-fit: cover;
}

.mod-info {
  padding: 6px;
  display: flex;
  flex-direction: column;
  flex-grow: 1;
}

.mod-name {
  font-size: 0.7rem;
  font-weight: 600;
  line-height: 1.2;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  height: 24px;
}

.mod-price {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 4px;
}

.mod-check {
  position: absolute;
  top: 5px;
  right: 5px;
  background-color: var(--color-accent);
  color: white;
  width: 18px;
  height: 18px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* KBJU section */
.kbju-grid {
  display: flex;
  gap: 8px;
}

.kbju-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  background-color: var(--bg-tetriary);
  padding: 8px 4px;
  border-radius: var(--radius-sm);
}

.kbju-box .value {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-primary);
}

.kbju-box .label {
  font-size: 0.65rem;
  color: var(--text-secondary);
  margin-top: 2px;
}

.kbju-disclaimer {
  display: block;
  text-align: right;
  font-size: 0.65rem;
  color: var(--text-secondary);
  margin-top: 6px;
}

/* Sticky Modal Footer */
.modal-footer {
  padding: 16px 20px;
  background-color: var(--bg-main);
  border-top: 1px solid var(--color-gray-border);
  display: flex;
  justify-content: flex-end;
}

.modal-add-btn {
  width: 100%;
  max-width: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background-color: var(--color-accent);
  color: var(--text-inverse);
  font-weight: 700;
  font-size: 1rem;
  border-radius: var(--radius-full);
  border: none;
  cursor: pointer;
  transition: opacity 0.2s;
  box-shadow: 0 4px 12px rgba(var(--color-accent-rgb), 0.2);
}

.modal-add-btn:hover {
  opacity: 0.9;
}

/* Upsell Section Styles */
.upsell-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px dashed var(--color-gray-border);
}

.upsell-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.upsell-list {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
  scroll-behavior: smooth;
}

.upsell-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background-color: var(--bg-card);
  border: 1px solid var(--color-gray-border);
  border-radius: var(--radius-lg);
  min-width: 200px;
  max-width: 240px;
  flex-shrink: 0;
  position: relative;
}

.upsell-img {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: var(--radius-md);
  background-color: var(--bg-card);
}

.upsell-info {
  flex-grow: 1;
  min-width: 0;
}

.upsell-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin: 0 0 2px 0;
}

.upsell-price {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-accent);
}

.upsell-add-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background-color: var(--bg-main);
  border: 1px solid var(--color-gray-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-primary);
  transition: all 0.2s;
  padding: 0;
}

.upsell-add-btn:hover {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--text-inverse);
}

.loading-state {
  text-align: center;
  padding: 4rem;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-gray-border);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.mt-4 { margin-top: 1rem; }
.mt-3 { margin-top: 0.75rem; }

/* Stopped product styling */
.stopped-card {
  opacity: 0.65;
}

.stopped-status-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-secondary);
  background-color: var(--bg-tetriary);
  padding: 6px 12px;
  border-radius: var(--radius-full);
}

.stopped-msg-banner {
  width: 100%;
  margin-top: 8px;
  padding: 6px 10px;
  background-color: #fff1f0;
  border: 1px solid #ffa39e;
  color: #cf1322;
  font-size: 0.72rem;
  font-weight: 600;
  border-radius: var(--radius-md);
  line-height: 1.3;
  text-align: center;
}

.modal-stopped-banner {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  background-color: #fff1f0;
  border: 1px solid #ffa39e;
  color: #cf1322;
  font-weight: 700;
  font-size: 0.9rem;
  border-radius: var(--radius-full);
  text-align: center;
}
</style>
