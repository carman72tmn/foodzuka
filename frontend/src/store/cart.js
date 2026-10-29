import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: JSON.parse(localStorage.getItem('cart_items') || '[]'),
  }),
  getters: {
    totalItems: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),
    totalPrice: (state) => state.items.reduce((sum, item) => sum + (item.price * item.quantity), 0)
  },
  actions: {
    addItem(product, selectedSize = null, selectedModifiers = []) {
      // 1. Generate a unique key for this configuration
      // Modifiers sorted by ID to ensure order doesn't affect key uniqueness
      const sortedModIds = [...selectedModifiers].map(m => m.id).sort().join('-')
      const sizeId = selectedSize ? selectedSize.id : 'default'
      const cartItemKey = `${product.id}_${sizeId}_${sortedModIds}`

      // 2. Check if this exact item configuration is already in the cart
      const existingItem = this.items.find(item => item.cart_item_key === cartItemKey)

      if (existingItem) {
        existingItem.quantity++
      } else {
        // Calculate price per single item: size price (or base price) + sum(modifier prices)
        const sizePrice = selectedSize ? parseFloat(selectedSize.price) : parseFloat(product.price)
        const modsPrice = selectedModifiers.reduce((sum, m) => sum + (parseFloat(m.price) * (m.quantity || 1)), 0)
        const price = sizePrice + modsPrice

        this.items.push({
          cart_item_key: cartItemKey,
          id: product.id,
          name: product.name,
          image_url: product.image_url,
          selected_size: selectedSize,
          selected_modifiers: selectedModifiers,
          price,
          quantity: 1
        })
      }
      this.saveToStorage()
    },
    removeItem(cartItemKey) {
      const index = this.items.findIndex(item => item.cart_item_key === cartItemKey)
      if (index > -1) {
        if (this.items[index].quantity > 1) {
          this.items[index].quantity--
        } else {
          this.items.splice(index, 1)
        }
      }
      this.saveToStorage()
    },
    incrementItem(cartItemKey) {
      const item = this.items.find(item => item.cart_item_key === cartItemKey)
      if (item) {
        item.quantity++
      }
      this.saveToStorage()
    },
    clearCart() {
      this.items = []
      this.saveToStorage()
    },
    saveToStorage() {
      localStorage.setItem('cart_items', JSON.stringify(this.items))
    }
  }
})
