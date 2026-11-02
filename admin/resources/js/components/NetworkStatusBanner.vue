<script setup>
import { computed, ref } from 'vue'
import { networkStatus, processOutboxQueue } from '@/utils/offlineCacheManager'
import { getAuthHeaders } from '@/utils/auth'

const syncInProgress = ref(false)
const showRestoredBanner = ref(false)

const isVisible = computed(() => {
  return !networkStatus.isOnline || networkStatus.mode === 'offline' || networkStatus.queueCount > 0 || showRestoredBanner.value
})

const handleManualRetry = async () => {
  syncInProgress.value = true
  try {
    await processOutboxQueue(getAuthHeaders)
  } finally {
    syncInProgress.value = false
  }
}
</script>

<template>
  <Transition name="banner-slide">
    <div
      v-if="isVisible"
      class="network-status-banner"
      :class="{
        'banner-offline': networkStatus.mode === 'offline' || !networkStatus.isOnline,
        'banner-direct': networkStatus.mode === 'direct_gateway',
        'banner-syncing': networkStatus.isSyncing,
        'banner-restored': showRestoredBanner
      }"
    >
      <div class="banner-inner">
        <div class="banner-left">
          <VIcon
            v-if="!networkStatus.isOnline || networkStatus.mode === 'offline'"
            icon="bx-wifi-off"
            class="me-2 banner-icon"
            size="20"
          />
          <VIcon
            v-else-if="networkStatus.mode === 'direct_gateway'"
            icon="bx-shield-quarter"
            class="me-2 banner-icon"
            size="20"
          />
          <VIcon
            v-else
            icon="bx-check-circle"
            class="me-2 banner-icon"
            size="20"
          />

          <span class="banner-title">
            <template v-if="!networkStatus.isOnline || networkStatus.mode === 'offline'">
              Автономный режим (нет связи с сервером). Отображаются данные из кэша за 4 часа.
            </template>
            <template v-else-if="networkStatus.mode === 'direct_gateway'">
              Резервный шлюз (Белые списки): прямой обмен данными с iiko и Т-Банком активен.
            </template>
            <template v-else>
              Связь восстановлена. Все данные синхронизированы.
            </template>
          </span>

          <span v-if="networkStatus.queueCount > 0" class="queue-badge ms-2">
            В очереди: {{ networkStatus.queueCount }}
          </span>
        </div>

        <div class="banner-actions">
          <VBtn
            v-if="networkStatus.queueCount > 0 || !networkStatus.isOnline"
            size="x-small"
            variant="elevated"
            color="white"
            class="text-dark font-weight-bold"
            :loading="syncInProgress || networkStatus.isSyncing"
            @click="handleManualRetry"
          >
            Повторить
          </VBtn>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.network-status-banner {
  position: sticky;
  top: 0;
  left: 0;
  right: 0;
  width: 100%;
  z-index: 99999;
  padding: 6px 16px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.banner-offline {
  background: #f59e0b;
  color: #78350f;
  border-bottom: 1px solid #d97706;
}

.banner-direct {
  background: #3b82f6;
  color: #ffffff;
  border-bottom: 1px solid #2563eb;
}

.banner-restored {
  background: #10b981;
  color: #ffffff;
  border-bottom: 1px solid #059669;
}

.banner-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
}

.banner-left {
  display: flex;
  align-items: center;
  flex: 1;
}

.banner-title {
  line-height: 1.2;
}

.queue-badge {
  background: rgba(0, 0, 0, 0.15);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
}

.banner-slide-enter-active,
.banner-slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.banner-slide-enter-from,
.banner-slide-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
