<script setup>
import { onMounted } from 'vue'
import { useTheme } from 'vuetify'
import { useRouter } from 'vue-router'
import { appTimezone, appOffset } from '@/utils/date'
import { syncVkLinking, loginWithVkMiniApp } from '@/utils/auth'
import PwaInstallBanner from '@/components/PwaInstallBanner.vue'

const { global: globalTheme } = useTheme()
const router = useRouter()

onMounted(async () => {
  // Проверяем среду VK Mini App и выполняем авто-логин
  const urlParams = new URLSearchParams(window.location.search)
  const isVk = urlParams.has('vk_app_id') || urlParams.has('vk_user_id')
  
  if (isVk) {
    console.log('[VK Mini App] VK launch parameters detected. Attempting auto-login (Employee)...')
    try {
      const queryParams = window.location.search
      const result = await loginWithVkMiniApp(queryParams)
      
      if (result.status === 'success') {
        console.log('[VK Mini App] Auto-login successful for employee:', result.username)
        // Сохраняем параметры запуска на всякий случай
        localStorage.setItem('vk_launch_params', queryParams)
        if (result.is_courier) {
          router.push('/pers/dashboard')
        } else {
          router.push('/admin/dashboard')
        }
      } else if (result.status === 'not_linked') {
        console.log('[VK Mini App] Account not linked. Redirecting to login with link mode (Employee)...')
        localStorage.setItem('vk_launch_params', queryParams)
        router.push({
          path: '/login',
          query: { vk_link_mode: '1', vk_user_id: result.vk_user_id }
        })
        return // Прерываем дальнейшее монтирование / обычный логин
      }
    } catch (err) {
      console.error('[VK Mini App] Auto-login error (Employee):', err)
    }
  }

  // Загрузка настроек iiko для синхронизации часового пояса
  try {
    const response = await fetch('/api/v1/iiko/settings/')
    if (response.ok) {
      const data = await response.json()
      
      if (data && data.timezone_name) {
        appTimezone.value = data.timezone_name
        localStorage.setItem('app_timezone', data.timezone_name)
      }
      
      if (data && data.manual_timezone) {
        const offsetMatch = data.manual_timezone.match(/([+-])(\d+)/)
        if (offsetMatch) {
          const sign = offsetMatch[1] === '-' ? -1 : 1
          const hours = parseInt(offsetMatch[2])
          
          appOffset.value = sign * hours
          localStorage.setItem('app_offset', appOffset.value.toString())
        }
      } else {
        appOffset.value = 0
        localStorage.setItem('app_offset', '0')
      }
    }
  } catch (error) {
    console.error('Failed to load iiko settings for timezone (Employee):', error)
  }

  // Синхронизация привязки VK при входе в приложение
  try {
    await syncVkLinking()
  } catch (error) {
    console.error('Failed to sync VK linking (Employee):', error)
  }
})
</script>

<template>
  <VApp>
    <RouterView />
    <PwaInstallBanner />
  </VApp>
</template>

<style>
/* Можно добавить специфичные стили для панели сотрудников */
</style>
