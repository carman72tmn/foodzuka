<template>
  <div class="app-container" :data-theme="currentTheme">
    <!-- Header -->
    <header class="header">
      <!-- Left: Menu Toggle & City -->
      <div class="header-left">
        <button class="icon-btn menu-btn" @click="isSidebarOpen = true" aria-label="Открыть меню">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" x2="20" y1="12" y2="12"></line>
            <line x1="4" x2="20" y1="6" y2="6"></line>
            <line x1="4" x2="20" y1="18" y2="18"></line>
          </svg>
        </button>
        
        <div class="city-selector">
          <div class="city-title">
            <span class="city-name">Тюмень</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="m6 9 6 6 6-6"></path>
            </svg>
          </div>
          <span class="wait-time">~ 35-85 мин</span>
        </div>
      </div>

      <!-- Center: Delivery Switcher (Pill) -->
      <div class="delivery-switcher">
        <button 
          class="switch-btn" 
          :class="{ active: deliveryMode === 'delivery' }" 
          @click="setDeliveryMode('delivery')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="switch-icon">
            <rect x="1" y="3" width="15" height="13" rx="2" ry="2"></rect>
            <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon>
            <circle cx="5.5" cy="18.5" r="2.5"></circle>
            <circle cx="18.5" cy="18.5" r="2.5"></circle>
          </svg>
          Доставка
        </button>
        <button 
          class="switch-btn" 
          :class="{ active: deliveryMode === 'pickup' }" 
          @click="setDeliveryMode('pickup')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="switch-icon">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          Самовывоз
        </button>
      </div>

      <!-- Right: Palette (Customization), Profile, Cart -->
      <div class="header-right">
        <!-- Palette button to open theme customizer -->
        <button class="icon-btn theme-toggle-btn" @click="isThemePanelOpen = true" aria-label="Настройка оформления">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 14.7255 3.09032 17.1962 4.85857 19C5.02941 19.1708 5.2842 19.1915 5.4801 19.0526C6.67108 18.2078 8.11894 17.7059 9.68421 17.7059C9.85862 17.7059 10 17.8473 10 18.0217V19.6842C10 20.9632 11.0368 22 12.3158 22H12Z"></path>
            <circle cx="7.5" cy="10.5" r="1.5" fill="currentColor"></circle>
            <circle cx="11.5" cy="7.5" r="1.5" fill="currentColor"></circle>
            <circle cx="16.5" cy="9.5" r="1.5" fill="currentColor"></circle>
          </svg>
        </button>

        <button class="icon-btn profile-btn" aria-label="Личный кабинет">
          <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <router-view></router-view>
    </main>

    <!-- Sidebar Menu Drawer -->
    <div class="drawer-overlay" :class="{ open: isSidebarOpen }" @click="isSidebarOpen = false"></div>
    <div class="sidebar-drawer" :class="{ open: isSidebarOpen }">
      <div class="drawer-header">
        <div class="logo">vezuroll.ru</div>
        <button class="close-btn" @click="isSidebarOpen = false" aria-label="Закрыть">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" x2="6" y1="6" y2="18"></line>
            <line x1="6" x2="18" y1="6" y2="18"></line>
          </svg>
        </button>
      </div>

      <nav class="drawer-nav">
        <router-link to="/" class="nav-item" @click="isSidebarOpen = false">🍣 Меню заказа</router-link>
        <a href="#" class="nav-item" @click="isSidebarOpen = false">📋 Доставка и оплата</a>
        <a href="#" class="nav-item" @click="isSidebarOpen = false">🔥 Акции и события</a>
        <a href="#" class="nav-item" @click="isSidebarOpen = false">🔗 Универсальная ссылка</a>
      </nav>

      <div class="drawer-footer">
        <div class="work-time">
          <strong>Тюмень</strong>
          <span>с 10:15 до 22:45</span>
        </div>
        <a href="tel:88005507216" class="phone-link">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
          </svg>
          8 (800) 550-72-16
        </a>
        <div class="apps-download">
          <p>Скачайте наше мобильное приложение</p>
          <div class="app-buttons">
            <a href="#" class="app-btn-mock">App Store</a>
            <a href="#" class="app-btn-mock">Google Play</a>
          </div>
        </div>
        <p class="copyright">Разработано vezuroll &copy; 2026</p>
      </div>
    </div>

    <!-- Theme Customization Drawer -->
    <div class="drawer-overlay" :class="{ open: isThemePanelOpen }" @click="isThemePanelOpen = false"></div>
    <div class="theme-drawer" :class="{ open: isThemePanelOpen }">
      <div class="drawer-header">
        <h3>Оформление</h3>
        <button class="close-btn" @click="isThemePanelOpen = false" aria-label="Закрыть">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" x2="6" y1="6" y2="18"></line>
            <line x1="6" x2="18" y1="6" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="theme-panel-content">
        <!-- Mode Switch: Light/Dark -->
        <div class="setting-group">
          <h4>Режим</h4>
          <div class="mode-toggles">
            <button 
              class="mode-toggle-btn" 
              :class="{ active: currentTheme === 'light' }" 
              @click="setTheme('light')"
            >
              ☀️ Светлая
            </button>
            <button 
              class="mode-toggle-btn" 
              :class="{ active: currentTheme === 'dark' }" 
              @click="setTheme('dark')"
            >
              🌙 Темная
            </button>
          </div>
        </div>

        <!-- Brand Accent Color -->
        <div class="setting-group">
          <h4>Цвет акцента</h4>
          <div class="accent-selectors">
            <button 
              v-for="color in accentColors" 
              :key="color.id"
              class="accent-color-dot"
              :style="{ backgroundColor: color.hex }"
              :class="{ active: currentAccent === color.id }"
              :title="color.name"
              @click="setAccent(color.id)"
            >
              <svg v-if="currentAccent === color.id" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const isSidebarOpen = ref(false)
const isThemePanelOpen = ref(false)
const deliveryMode = ref(localStorage.getItem('delivery_mode') || 'delivery')

// Theme state
const currentTheme = ref(localStorage.getItem('theme_mode') || 'light')
const currentAccent = ref(localStorage.getItem('theme_accent') || 'orange')

const accentColors = [
  { id: 'orange', name: 'Оранжевый', hex: '#ff6b35' },
  { id: 'red', name: 'Красный', hex: '#e4022c' },
  { id: 'green', name: 'Зеленый', hex: '#5f9d55' },
  { id: 'blue', name: 'Синий', hex: '#1d77ed' },
  { id: 'purple', name: 'Фиолетовый', hex: '#7745bb' }
]

onMounted(() => {
  // Apply saved theme & accent to document
  applyThemeToDOM()
})

const setDeliveryMode = (mode) => {
  deliveryMode.value = mode
  localStorage.setItem('delivery_mode', mode)
  // Dispatch custom event to notify components
  window.dispatchEvent(new CustomEvent('delivery-mode-changed', { detail: mode }))
}

const setTheme = (theme) => {
  currentTheme.value = theme
  localStorage.setItem('theme_mode', theme)
  applyThemeToDOM()
}

const setAccent = (accent) => {
  currentAccent.value = accent
  localStorage.setItem('theme_accent', accent)
  applyThemeToDOM()
}

const applyThemeToDOM = () => {
  const root = document.documentElement
  root.setAttribute('data-theme', currentTheme.value)
  root.setAttribute('data-accent', currentAccent.value)
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-layout);
  transition: background-color 0.3s;
}

/* Header Styles */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 5%;
  background-color: var(--bg-main);
  border-bottom: 1px solid var(--color-gray-border);
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Icon Buttons */
.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  background-color: transparent;
  transition: background-color 0.2s, color 0.2s;
  border: none;
  cursor: pointer;
}

.icon-btn:hover {
  background-color: var(--bg-tetriary);
  color: var(--color-accent);
}

.city-selector {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.city-title {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
  cursor: pointer;
}

.city-title svg {
  color: var(--text-secondary);
}

.city-name:hover {
  color: var(--color-accent);
}

.wait-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 1px;
}

/* Center Switcher */
.delivery-switcher {
  display: flex;
  background-color: var(--bg-tetriary);
  padding: 4px;
  border-radius: var(--radius-full);
  gap: 2px;
}

.switch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
  border-radius: var(--radius-full);
  transition: all 0.25s ease;
  border: none;
  background: transparent;
  cursor: pointer;
}

.switch-btn.active {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  box-shadow: var(--shadow-sm);
}

.switch-icon {
  width: 14px;
  height: 14px;
}

.switch-btn.active .switch-icon {
  color: var(--color-accent);
}

.main-content {
  flex: 1;
  padding: 1.5rem 5% 4rem 5%;
}

/* Sidebar Drawer & Theme Drawer Common Overlay */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 200;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.drawer-overlay.open {
  opacity: 1;
  pointer-events: auto;
}

/* Drawers */
.sidebar-drawer, .theme-drawer {
  position: fixed;
  top: 0;
  bottom: 0;
  width: 320px;
  max-width: 85%;
  background-color: var(--bg-main);
  z-index: 210;
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-drawer {
  left: 0;
  transform: translateX(-100%);
}

.sidebar-drawer.open {
  transform: translateX(0);
}

.theme-drawer {
  right: 0;
  transform: translateX(100%);
}

.theme-drawer.open {
  transform: translateX(0);
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 1.5rem;
  border-bottom: 1px solid var(--color-gray-border);
}

.drawer-header .logo {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--color-accent);
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
}

.close-btn:hover {
  color: var(--text-primary);
}

/* Drawer Nav Items */
.drawer-nav {
  display: flex;
  flex-direction: column;
  padding: 1.5rem 1rem;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  color: var(--text-primary);
  text-decoration: none;
  font-weight: 500;
  border-radius: var(--radius-md);
  transition: background-color 0.2s, color 0.2s;
}

.nav-item:hover {
  background-color: var(--bg-tetriary);
  color: var(--color-accent);
}

.drawer-footer {
  margin-top: auto;
  padding: 1.5rem;
  border-top: 1px solid var(--color-gray-border);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.work-time {
  font-size: 0.85rem;
  display: flex;
  flex-direction: column;
}

.work-time strong {
  color: var(--text-primary);
}

.work-time span {
  color: var(--text-secondary);
}

.phone-link {
  display: flex;
  align-items: center;
  font-weight: 700;
  color: var(--color-accent);
  text-decoration: none;
  font-size: 1.1rem;
}

.apps-download p {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.app-buttons {
  display: flex;
  gap: 8px;
}

.app-btn-mock {
  flex: 1;
  text-align: center;
  padding: 8px;
  background-color: var(--bg-tetriary);
  color: var(--text-primary);
  font-size: 0.75rem;
  font-weight: 600;
  text-decoration: none;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-gray-border);
}

.app-btn-mock:hover {
  border-color: var(--color-accent);
}

.copyright {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
}

/* Theme Panel */
.theme-panel-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.setting-group h4 {
  font-size: 0.9rem;
  margin-bottom: 10px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.mode-toggles {
  display: flex;
  gap: 8px;
}

.mode-toggle-btn {
  flex: 1;
  padding: 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-gray-border);
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-toggle-btn.active {
  border-color: var(--color-accent);
  background-color: var(--bg-tetriary);
  color: var(--color-accent);
}

.accent-selectors {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.accent-color-dot {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid transparent;
  transition: transform 0.2s, border-color 0.2s;
  box-shadow: var(--shadow-sm);
}

.accent-color-dot:hover {
  transform: scale(1.1);
}

.accent-color-dot.active {
  border-color: var(--text-primary);
}

@media (max-width: 768px) {
  .header {
    padding: 0.8rem 3%;
  }
}
</style>
