<template>
  <div class="cart-page fade-in">
    <!-- Back to Menu Button -->
    <div class="back-nav">
      <router-link to="/" class="back-link">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
        Вернуться в меню
      </router-link>
    </div>

    <h1 class="page-title">Оформление заказа</h1>

    <!-- Empty Cart state -->
    <div v-if="cartStore.items.length === 0" class="empty-cart-state">
      <div class="empty-icon">🛒</div>
      <h2>Ваша корзина пуста</h2>
      <p>Перейдите в меню, чтобы выбрать ваши любимые блюда</p>
      <router-link to="/" class="primary-btn mt-4">В меню</router-link>
    </div>

    <!-- Active Cart contents -->
    <div v-else class="cart-layout">
      <!-- Left side: Items & Delivery Details -->
      <div class="cart-main-pane">
        <!-- List of items -->
        <div class="cart-card items-card">
          <h2>Выбранные блюда</h2>
          
          <div class="items-list">
            <div v-for="item in cartStore.items" :key="item.cart_item_key" class="cart-item-row">
              <img 
                :src="item.image_url || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=150&auto=format&fit=crop'" 
                :alt="item.name" 
                class="item-img"
              />
              
              <div class="item-info">
                <h3>{{ item.name }}</h3>
                <span v-if="item.selected_size" class="item-size-badge">
                  Size: {{ item.selected_size.name }}
                </span>
                
                <!-- Display chosen modifiers -->
                <div v-if="item.selected_modifiers && item.selected_modifiers.length > 0" class="item-modifiers">
                  <span v-for="mod in item.selected_modifiers" :key="mod.id" class="mod-pill">
                    + {{ mod.name }} ({{ mod.price }} ₽)
                  </span>
                </div>
              </div>

              <!-- Quantity control -->
              <div class="item-qty-adjust">
                <div class="counter-btn-mini">
                  <button class="cnt-btn-s" @click="cartStore.removeItem(item.cart_item_key)">-</button>
                  <span class="qty-val">{{ item.quantity }}</span>
                  <button class="cnt-btn-s" @click="cartStore.incrementItem(item.cart_item_key)">+</button>
                </div>
              </div>

              <div class="item-total-price">
                {{ Math.round(item.price * item.quantity) }} ₽
              </div>
            </div>
          </div>
        </div>

        <!-- Рекомендации "Рекомендуем к заказу" -->
        <div v-if="upsellProducts.length > 0" class="cart-card upsell-card">
          <h2>Рекомендуем к заказу</h2>
          <div class="upsell-horizontal-scroll no-visible-scrollbar">
            <div v-for="item in upsellProducts" :key="item.id" class="upsell-item-card">
              <img :src="item.image_url" :alt="item.name" class="upsell-item-img" />
              <div class="upsell-item-details">
                <h3 class="upsell-item-name">{{ item.name }}</h3>
                <span class="upsell-item-price">{{ item.price }} ₽</span>
              </div>
              <button type="button" class="upsell-item-add-btn" @click="addUpsellToCart(item)">
                Добавить
              </button>
            </div>
          </div>
        </div>

        <!-- Delivery Address Details -->
        <div class="cart-card address-card">
          <h2>Способ получения</h2>
          
          <div class="mode-selector-tabs mt-3">
            <button 
              type="button"
              class="tab-btn" 
              :class="{ active: deliveryMode === 'delivery' }" 
              @click="setDeliveryMode('delivery')"
            >
              🚀 Доставка
            </button>
            <button 
              type="button"
              class="tab-btn" 
              :class="{ active: deliveryMode === 'pickup' }" 
              @click="setDeliveryMode('pickup')"
            >
              🛍️ Самовывоз
            </button>
          </div>

          <!-- Address Fields for Delivery -->
          <div v-if="deliveryMode === 'delivery'" class="address-fields mt-4">
            <div class="form-row">
              <div class="form-group flex-2">
                <label>Улица</label>
                <input type="text" v-model="address.street" required placeholder="Введите улицу">
              </div>
              <div class="form-group flex-1">
                <label>Дом</label>
                <input type="text" v-model="address.house" required placeholder="Дом">
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>Подъезд</label>
                <input type="text" v-model="address.entrance" placeholder="Подъезд">
              </div>
              <div class="form-group">
                <label>Домофон</label>
                <input type="text" v-model="address.doorphone" placeholder="Код">
              </div>
              <div class="form-group">
                <label>Этаж</label>
                <input type="text" v-model="address.floor" placeholder="Этаж">
              </div>
              <div class="form-group">
                <label>Кв. / Офис</label>
                <input type="text" v-model="address.flat" placeholder="Кв.">
              </div>
            </div>
          </div>

          <!-- Info for Pickup -->
          <div v-else class="pickup-info mt-4">
            <p>📍 Точка выдачи: <strong>г. Тюмень, ул. Ленина, д. 25</strong></p>
            <p class="pickup-time-notice">Заказ будет готов к выдаче через 20-30 минут после подтверждения.</p>
          </div>
        </div>

        <!-- Payment Method Details -->
        <div class="cart-card payment-card">
          <h2>Способ оплаты</h2>
          <div class="payment-options mt-3">
            <label class="pay-option">
              <input type="radio" v-model="paymentMethod" value="online" checked>
              <div class="pay-card-content">
                <span class="pay-icon">💳</span>
                <span class="pay-title">Картой на сайте</span>
              </div>
            </label>
            <label class="pay-option">
              <input type="radio" v-model="paymentMethod" value="cash">
              <div class="pay-card-content">
                <span class="pay-icon">💵</span>
                <span class="pay-title">Наличными</span>
              </div>
            </label>
            <label class="pay-option">
              <input type="radio" v-model="paymentMethod" value="terminal">
              <div class="pay-card-content">
                <span class="pay-icon">📠</span>
                <span class="pay-title">Картой курьеру</span>
              </div>
            </label>
          </div>
        </div>
      </div>

      <!-- Right side: Checkout Sidebar -->
      <div class="cart-sidebar">
        <div class="sidebar-summary">
          <h2>Сумма заказа</h2>

          <div class="summary-details mt-3">
            <div class="summary-row">
              <span>Стоимость блюд:</span>
              <span>{{ cartStore.totalPrice }} ₽</span>
            </div>
            <div class="summary-row" v-if="deliveryMode === 'delivery'">
              <span>Доставка:</span>
              <span class="green-text">Бесплатно</span>
            </div>
            <div class="summary-row" v-if="promoDiscount > 0">
              <span>Скидка по промокоду:</span>
              <span class="red-text">-{{ promoDiscount }} ₽</span>
            </div>
            
            <div class="summary-divider"></div>
            
            <div class="summary-row total-row">
              <span>Итого:</span>
              <span class="total-price">{{ getFinalTotal() }} ₽</span>
            </div>
          </div>

          <!-- Checkout Form -->
          <form class="checkout-form mt-4" @submit.prevent="submitOrder">
            <div class="form-group">
              <label>Ваше имя</label>
              <input type="text" v-model="form.name" required placeholder="Введите имя">
            </div>
            
            <div class="form-group">
              <label>Телефон</label>
              <input type="tel" v-model="form.phone" required placeholder="+7 (999) 000-00-00">
            </div>

            <div class="form-group">
              <label>Комментарий к заказу</label>
              <textarea v-model="form.comment" placeholder="Например: домофон не работает, приборы на 3 персоны" rows="2"></textarea>
            </div>

            <!-- Promo input with button -->
            <div class="form-group">
              <label>Промокод</label>
              <div class="promo-input-wrapper">
                <input type="text" v-model="form.promo_code" placeholder="Введите код">
                <button type="button" class="promo-apply-btn" @click="applyPromo">Применить</button>
              </div>
              <span v-if="promoMessage" class="promo-feedback" :class="{ error: isPromoError }">
                {{ promoMessage }}
              </span>
            </div>

            <!-- Submit Button -->
            <button type="submit" class="submit-order-btn mt-3" :disabled="isSubmitting">
              {{ isSubmitting ? 'Оформляем...' : `Оформить заказ на ${getFinalTotal()} ₽` }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useCartStore } from '../store/cart'
import { createOrder } from '../api/order'
import { fetchProducts } from '../api/catalog'

const cartStore = useCartStore()
const products = ref([])
const isSubmitting = ref(false)
const deliveryMode = ref(localStorage.getItem('delivery_mode') || 'delivery')
const paymentMethod = ref('online')

// Promo state
const promoDiscount = ref(0)
const promoMessage = ref('')
const isPromoError = ref(false)

const form = reactive({
  name: '',
  phone: '',
  comment: '',
  promo_code: ''
})

const address = reactive({
  street: '',
  house: '',
  entrance: '',
  doorphone: '',
  floor: '',
  flat: ''
})

onMounted(async () => {
  try {
    products.value = await fetchProducts()
  } catch (e) {
    console.error('Error loading products for upsell', e)
  }
  
  // Listen to delivery mode changes in header
  window.addEventListener('delivery-mode-changed', (e) => {
    deliveryMode.value = e.detail
  })
})

const upsellProducts = computed(() => {
  if (!products.value.length) return []
  
  // Исключаем товары, которые уже есть в корзине
  const cartProductIds = cartStore.items.map(item => item.product_id)
  
  return products.value.filter(p => {
    if (cartProductIds.includes(p.id)) return false
    if (!p.is_available) return false
    
    const name = p.name.toLowerCase()
    return name.includes('соус') || 
           name.includes('сок') || 
           name.includes('напиток') || 
           name.includes('кока') || 
           name.includes('кола') || 
           name.includes('спрайт') || 
           name.includes('фанта') || 
           name.includes('чизкейк') || 
           name.includes('картофель фри')
  }).slice(0, 5)
})

const addUpsellToCart = (product) => {
  const size = product.sizes && product.sizes.length > 0
    ? (product.sizes.find(s => s.is_default) || product.sizes[0])
    : null
  cartStore.addItem(product, size, [])
}

const setDeliveryMode = (mode) => {
  deliveryMode.value = mode
  localStorage.setItem('delivery_mode', mode)
}

const applyPromo = () => {
  if (!form.promo_code) return
  // Dummy promo codes logic for layout purposes. In production, бэкенд calculates it.
  const code = form.promo_code.toUpperCase()
  if (code === 'SAM' && deliveryMode.value === 'pickup') {
    promoDiscount.value = Math.round(cartStore.totalPrice * 0.1)
    promoMessage.value = 'Промокод применен: Скидка 10% на самовывоз!'
    isPromoError.value = false
  } else if (code === 'DR15') {
    promoDiscount.value = Math.round(cartStore.totalPrice * 0.15)
    promoMessage.value = 'Промокод применен: Скидка 15% в День Рождения!'
    isPromoError.value = false
  } else {
    promoDiscount.value = 0
    promoMessage.value = 'Промокод недействителен для данных условий'
    isPromoError.value = true
  }
}

const getFinalTotal = () => {
  return Math.max(cartStore.totalPrice - promoDiscount.value, 0)
}

const submitOrder = async () => {
  if (cartStore.items.length === 0) return
  isSubmitting.value = true

  try {
    // Collect address fields into single string or pass separately
    let fullAddress = 'Самовывоз'
    if (deliveryMode.value === 'delivery') {
      const parts = [
        `ул. ${address.street}`,
        `д. ${address.house}`,
        address.entrance ? `под. ${address.entrance}` : '',
        address.doorphone ? `код ${address.doorphone}` : '',
        address.floor ? `эт. ${address.floor}` : '',
        address.flat ? `кв. ${address.flat}` : ''
      ].filter(Boolean)
      fullAddress = parts.join(', ')
    }

    const orderData = {
      telegram_user_id: 1, // Dummy ID
      branch_id: 1,
      customer_name: form.name,
      customer_phone: form.phone,
      delivery_address: fullAddress,
      comment: form.comment || null,
      promo_code: form.promo_code || null,
      bonus_spent: 0,
      items: cartStore.items.map(item => ({
        product_id: item.id,
        quantity: item.quantity,
        product_size_id: item.selected_size ? item.selected_size.id : null,
        modifiers: item.selected_modifiers ? item.selected_modifiers.map(m => ({
          modifier_id: m.id,
          quantity: m.quantity || 1
        })) : []
      }))
    }

    await createOrder(orderData)
    alert('Заказ успешно создан! Наш оператор свяжется с вами для подтверждения.')
    cartStore.clearCart()
    
    // Clear forms
    form.name = ''
    form.phone = ''
    form.comment = ''
    form.promo_code = ''
    address.street = ''
    address.house = ''
    address.entrance = ''
    address.doorphone = ''
    address.floor = ''
    address.flat = ''
    promoDiscount.value = 0
    promoMessage.value = ''
  } catch (error) {
    alert('Ошибка создания заказа: ' + error.message)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.cart-page {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 4rem;
}

.back-nav {
  margin-bottom: 1.5rem;
}

.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-weight: 600;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.back-link:hover {
  color: var(--color-accent);
}

.page-title {
  font-size: 2.2rem;
  font-weight: 800;
  margin-bottom: 2rem;
  color: var(--text-primary);
}

.empty-cart-state {
  text-align: center;
  padding: 5rem 2rem;
  background-color: var(--bg-main);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-gray-border);
}

.empty-icon {
  font-size: 3.5rem;
  margin-bottom: 1rem;
}

.empty-cart-state h2 {
  margin-bottom: 8px;
}

.empty-cart-state p {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

/* Cart Layout grid */
.cart-layout {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 30px;
  align-items: start;
}

@media (max-width: 992px) {
  .cart-layout {
    grid-template-columns: 1fr;
  }
}

.cart-main-pane {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.cart-card {
  background-color: var(--bg-main);
  border-radius: var(--radius-xl);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-gray-border);
}

.cart-card h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  border-bottom: 1px solid var(--color-gray-border);
  padding-bottom: 10px;
}

/* Cart item list */
.items-list {
  display: flex;
  flex-direction: column;
  margin-top: 10px;
}

.cart-item-row {
  display: flex;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid var(--color-gray-border);
  gap: 16px;
}

.cart-item-row:last-child {
  border-bottom: none;
}

.item-img {
  width: 70px;
  height: 70px;
  border-radius: var(--radius-md);
  object-fit: cover;
}

.item-info {
  flex-grow: 1;
}

.item-info h3 {
  font-size: 1rem;
  font-weight: 600;
}

.item-size-badge {
  font-size: 0.75rem;
  color: var(--text-secondary);
  background-color: var(--bg-tetriary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  display: inline-block;
  margin-top: 4px;
}

.item-modifiers {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.mod-pill {
  font-size: 0.7rem;
  color: var(--color-accent);
  background-color: rgba(var(--color-accent-rgb), 0.08);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.item-qty-adjust {
  width: 100px;
}

.counter-btn-mini {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px;
  background-color: var(--counter-bg);
  border-radius: var(--radius-full);
}

.cnt-btn-s {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-full);
  border: none;
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
}

.cnt-btn-s:hover {
  color: var(--color-accent);
}

.qty-val {
  font-weight: 700;
  font-size: 0.85rem;
  color: var(--text-primary);
}

.item-total-price {
  font-weight: 700;
  font-size: 1.05rem;
  min-width: 70px;
  text-align: right;
  color: var(--text-primary);
}

/* Mode selector */
.mode-selector-tabs {
  display: flex;
  background-color: var(--bg-tetriary);
  padding: 4px;
  border-radius: var(--radius-full);
  gap: 2px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--text-secondary);
  background: transparent;
  border-radius: var(--radius-full);
  border: none;
  cursor: pointer;
  transition: all 0.25s;
}

.tab-btn.active {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

/* Address Fields */
.address-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.flex-2 { flex: 2; }
.flex-1 { flex: 1; }

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.form-group label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.form-group input, .form-group textarea {
  width: 100%;
  background-color: var(--bg-tetriary);
  border: 1px solid var(--color-gray-border);
  color: var(--text-primary);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.form-group input:focus, .form-group textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.pickup-info {
  background-color: var(--bg-tetriary);
  padding: 14px;
  border-radius: var(--radius-md);
  border: 1px dashed var(--color-gray-border);
}

.pickup-time-notice {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-top: 6px;
}

/* Payment Options */
.payment-options {
  display: flex;
  gap: 12px;
  flex-direction: row;
}

@media (max-width: 576px) {
  .payment-options {
    flex-direction: column;
  }
}

.pay-option {
  flex: 1;
  cursor: pointer;
}

.pay-option input {
  display: none;
}

.pay-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  border: 2px solid var(--color-gray-border);
  border-radius: var(--radius-lg);
  background-color: var(--bg-secondary);
  transition: all 0.25s;
}

.pay-option input:checked + .pay-card-content {
  border-color: var(--color-accent);
  background-color: rgba(var(--color-accent-rgb), 0.05);
}

.pay-icon {
  font-size: 1.5rem;
  margin-bottom: 6px;
}

.pay-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-primary);
}

/* Sidebar summary */
.cart-sidebar {
  position: sticky;
  top: 100px;
}

.sidebar-summary {
  background-color: var(--bg-main);
  border-radius: var(--radius-xl);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-gray-border);
}

.sidebar-summary h2 {
  font-size: 1.25rem;
  font-weight: 700;
  border-bottom: 1px solid var(--color-gray-border);
  padding-bottom: 10px;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.green-text {
  color: var(--success-color);
  font-weight: 600;
}

.red-text {
  color: var(--destructive-color);
  font-weight: 600;
}

.summary-divider {
  height: 1px;
  background-color: var(--color-gray-border);
  margin: 6px 0;
}

.total-row {
  color: var(--text-primary);
  font-weight: 700;
  font-size: 1rem;
}

.total-price {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-accent);
}

/* Promo input */
.promo-input-wrapper {
  display: flex;
  gap: 8px;
}

.promo-input-wrapper input {
  flex-grow: 1;
}

.promo-apply-btn {
  background-color: var(--bg-tetriary);
  color: var(--text-primary);
  padding: 10px 16px;
  font-weight: 600;
  font-size: 0.85rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-gray-border);
  cursor: pointer;
  transition: all 0.2s;
}

.promo-apply-btn:hover {
  background-color: var(--color-accent);
  color: var(--text-inverse);
  border-color: var(--color-accent);
}

.promo-feedback {
  font-size: 0.75rem;
  color: var(--success-color);
  margin-top: 4px;
}

.promo-feedback.error {
  color: var(--destructive-color);
}

/* Submit order button */
.submit-order-btn {
  width: 100%;
  padding: 14px;
  background-color: var(--color-accent);
  color: var(--text-inverse);
  font-weight: 700;
  font-size: 1rem;
  border-radius: var(--radius-full);
  border: none;
  cursor: pointer;
  box-shadow: 0 6px 20px rgba(var(--color-accent-rgb), 0.25);
  transition: opacity 0.2s;
}

.submit-order-btn:hover {
  opacity: 0.9;
}

.submit-order-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.primary-btn {
  background-color: var(--color-accent);
  color: var(--text-inverse);
  padding: 10px 24px;
  border-radius: var(--radius-full);
  font-weight: 700;
  text-decoration: none;
  display: inline-block;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(var(--color-accent-rgb), 0.2);
}

.primary-btn:hover {
  opacity: 0.9;
}

.mt-4 { margin-top: 1rem; }
.mt-3 { margin-top: 0.75rem; }

/* Upsell Card Styles */
.upsell-card {
  padding: 20px;
}

.upsell-horizontal-scroll {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding: 10px 0;
}

.upsell-item-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 140px;
  padding: 12px;
  background-color: var(--bg-card);
  border: 1px solid var(--color-gray-border);
  border-radius: var(--radius-lg);
  flex-shrink: 0;
  text-align: center;
}

.upsell-item-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: var(--radius-md);
  margin-bottom: 8px;
}

.upsell-item-details {
  flex-grow: 1;
  width: 100%;
}

.upsell-item-name {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.upsell-item-price {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--color-accent);
  display: block;
  margin-bottom: 8px;
}

.upsell-item-add-btn {
  width: 100%;
  padding: 6px;
  background-color: var(--bg-main);
  border: 1px solid var(--color-gray-border);
  border-radius: var(--radius-full);
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.upsell-item-add-btn:hover {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--text-inverse);
}
</style>
