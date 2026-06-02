<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import NavItems from '@/layouts/components/NavItems.vue'
import logo from '@images/logo.svg?raw'
import VerticalNavLayout from '@layouts/components/VerticalNavLayout.vue'
import Footer from '@/layouts/components/Footer.vue'
import UserProfile from '@/layouts/components/UserProfile.vue'
import NavbarThemeSwitcher from '@/layouts/components/NavbarThemeSwitcher.vue'
import ChatDrawer from '@/components/ChatDrawer.vue'
import { useChatStore } from '@/stores/chatStore.js'

import { formatDateTime } from '@/utils/date'

const chatStore = useChatStore()
const currentTime = ref('')

const updateTime = () => {
  currentTime.value = formatDateTime(new Date(), { 
    hour: '2-digit', 
    minute: '2-digit',
    day: undefined,
    month: undefined,
    year: undefined
  })
}

// Pull to refresh logic
const pullDistance = ref(0)
const isPulling = ref(false)
const refreshThreshold = 150
const startY = ref(0)

const handleTouchStart = e => {
  if (window.scrollY === 0) {
    startY.value = e.touches[0].pageY
    isPulling.value = true
  }
}

const handleTouchMove = e => {
  if (!isPulling.value) return
  const currentY = e.touches[0].pageY
  const diff = currentY - startY.value
  if (diff > 0) {
    pullDistance.value = Math.min(diff * 0.5, refreshThreshold + 50)
    if (pullDistance.value > 10) {
      if (e.cancelable) e.preventDefault()
    }
  } else {
    isPulling.value = false
    pullDistance.value = 0
  }
}

const handleTouchEnd = () => {
  if (pullDistance.value >= refreshThreshold) {
    window.location.reload()
  }
  isPulling.value = false
  pullDistance.value = 0
}

let timer = null

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 60000)

  window.addEventListener('touchstart', handleTouchStart, { passive: false })
  window.addEventListener('touchmove', handleTouchMove, { passive: false })
  window.addEventListener('touchend', handleTouchEnd)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('touchstart', handleTouchStart)
  window.removeEventListener('touchmove', handleTouchMove)
  window.removeEventListener('touchend', handleTouchEnd)
})
</script>

<template>
  <VerticalNavLayout>
    <!-- 👉 Pull to refresh indicator -->
    <div 
      v-if="pullDistance > 0"
      class="pull-to-refresh-indicator"
      :style="{ transform: `translateY(${pullDistance - 60}px)`, opacity: Math.min(pullDistance / refreshThreshold, 1) }"
    >
      <VProgressCircular
        :model-value="Math.min((pullDistance / refreshThreshold) * 100, 100)"
        :rotate="-90"
        :size="40"
        :width="4"
        :color="pullDistance >= refreshThreshold ? 'primary' : 'grey-lighten-1'"
      >
        <VIcon
          v-if="pullDistance < refreshThreshold"
          icon="bx-down-arrow-alt"
          size="24"
        />
        <VIcon
          v-else
          icon="bx-refresh"
          class="rotate-animation"
          size="24"
        />
      </VProgressCircular>
    </div>

    <!-- 👉 navbar -->
    <template #navbar="{ toggleVerticalOverlayNavActive, isNavCollapsed, toggleIsNavCollapsed }">
      <div class="d-flex h-100 align-center">
        <!-- 👉 Vertical nav toggle in overlay mode -->
        <IconBtn
          class="ms-n3 d-lg-none"
          @click="toggleVerticalOverlayNavActive(true)"
        >
          <VIcon icon="bx-menu" />
        </IconBtn>

        <!-- 👉 Vertical nav collapse/expand toggle on desktop -->
        <IconBtn
          class="ms-n3 d-none d-lg-block me-2 text-primary"
          @click="toggleIsNavCollapsed"
        >
          <VIcon :icon="isNavCollapsed ? 'bx-menu-alt-left' : 'bx-menu'" />
        </IconBtn>

        <!-- 👉 Search -->
        <div
          class="d-flex align-center cursor-pointer ms-lg-n3"
          style="user-select: none;"
        >
          <!-- 👉 Search Trigger button -->
          <IconBtn>
            <VIcon icon="bx-search" />
          </IconBtn>

          <span class="d-none d-md-flex align-center text-disabled ms-2">
            <span class="me-2">Поиск</span>
            <span class="meta-key">&#8984;K</span>
          </span>
        </div>

        <VSpacer />

        <IconBtn>
          <VIcon icon="bx-bell" />
        </IconBtn>

        <NavbarThemeSwitcher class="me-1" />

        <IconBtn
          class="me-2"
          @click="chatStore.isDrawerOpen = true"
        >
          <VBadge
            v-if="chatStore.unreadCount > 0"
            color="error"
            :content="chatStore.unreadCount"
            offset-x="2"
            offset-y="2"
          >
            <VIcon icon="bx-chat" />
          </VBadge>
          <VIcon
            v-else
            icon="bx-chat"
          />
        </IconBtn>

        <UserProfile />

        <div class="ms-4 font-weight-bold text-body-1 text-primary d-flex align-center">
          <VIcon icon="bx-time-five" size="20" class="me-1" />
          {{ currentTime }}
        </div>
      </div>
    </template>

    <template #vertical-nav-header="{ toggleIsOverlayNavActive, isNavCollapsed, toggleIsNavCollapsed }">
      <RouterLink
        to="/"
        class="app-logo app-title-wrapper"
      >
        <!-- eslint-disable vue/no-v-html -->
        <div
          class="d-flex"
          v-html="logo"
        />
        <!-- eslint-enable -->

        <h1 class="app-logo-title">
          FoodTech
        </h1>
      </RouterLink>

      <IconBtn
        class="d-none d-lg-block text-primary nav-pin-button"
        @click="toggleIsNavCollapsed"
      >
        <VIcon :icon="isNavCollapsed ? 'bx-radio-circle' : 'bx-radio-circle-marked'" />
      </IconBtn>

      <IconBtn
        class="d-block d-lg-none"
        @click="toggleIsOverlayNavActive(false)"
      >
        <VIcon icon="bx-x" />
      </IconBtn>
    </template>

    <template #vertical-nav-content>
      <NavItems />
    </template>

    <!-- 👉 Pages -->
    <slot />

    <!-- 👉 Footer -->
    <template #footer>
      <Footer />
    </template>

    <!-- 👉 Chat Drawer -->
    <ChatDrawer />
  </VerticalNavLayout>
</template>

<style lang="scss" scoped>
.meta-key {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 6px;
  block-size: 1.5625rem;
  line-height: 1.3125rem;
  padding-block: 0.125rem;
  padding-inline: 0.25rem;
}

.app-logo {
  display: flex;
  align-items: center;
  column-gap: 0.75rem;

  .app-logo-title {
    font-size: 1.25rem;
    font-weight: 500;
    line-height: 1.75rem;
    text-transform: uppercase;
  }
}

.pull-to-refresh-indicator {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  pointer-events: none;
  height: 60px;
  background: transparent;
}

.rotate-animation {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.app-logo-title {
  transition: opacity 0.2s ease-in-out, visibility 0.2s ease-in-out;
}

:global(.layout-vertical-nav-collapsed .layout-vertical-nav:not(.hovered)) {
  .app-logo-title {
    opacity: 0 !important;
    visibility: hidden !important;
    width: 0 !important;
    overflow: hidden;
  }
  .nav-pin-button {
    opacity: 0 !important;
    visibility: hidden !important;
  }
}
</style>
