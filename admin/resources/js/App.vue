<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { appTimezone, appOffset } from '@/utils/date'
import { loginWithVkMiniApp } from '@/utils/auth'
import PwaInstallBanner from '@/components/PwaInstallBanner.vue'

const router = useRouter()

onMounted(async () => {
  // Проверяем среду VK Mini App и выполняем авто-логин
  const urlParams = new URLSearchParams(window.location.search)
  const isVk = urlParams.has('vk_app_id') || urlParams.has('vk_user_id')
  
  if (isVk) {
    console.log('[VK Mini App] VK launch parameters detected. Attempting auto-login (Admin)...')
    try {
      const queryParams = window.location.search
      const result = await loginWithVkMiniApp(queryParams)
      
      if (result.status === 'success') {
        console.log('[VK Mini App] Auto-login successful for admin:', result.username)
        localStorage.setItem('vk_launch_params', queryParams)
        if (result.is_courier) {
          router.push('/pers/dashboard')
        } else {
          router.push('/admin/dashboard')
        }
      } else if (result.status === 'not_linked') {
        console.log('[VK Mini App] Account not linked. Redirecting to login with link mode (Admin)...')
        localStorage.setItem('vk_launch_params', queryParams)
        router.push({
          path: '/login',
          query: { vk_link_mode: '1', vk_user_id: result.vk_user_id }
        })
        return // Прерываем дальнейшее монтирование
      }
    } catch (err) {
      console.error('[VK Mini App] Auto-login error (Admin):', err)
    }
  }

  try {
    const response = await fetch('/api/v1/iiko/settings/')
    if (response.ok) {
      const data = await response.json()
      
      // Обработка имени пояса (IANA)
      if (data && data.timezone_name) {
        console.log('[App] Loaded timezone:', data.timezone_name)
        appTimezone.value = data.timezone_name
        localStorage.setItem('app_timezone', data.timezone_name)
      }
      
      // Обработка ручного смещения (например, +05:00 или +5)
      if (data && data.manual_timezone) {
        const offsetMatch = data.manual_timezone.match(/([+-])(\d+)/)
        if (offsetMatch) {
          const sign = offsetMatch[1] === '-' ? -1 : 1
          const hours = parseInt(offsetMatch[2])
          appOffset.value = sign * hours
          console.log('[App] Loaded offset:', appOffset.value)
          localStorage.setItem('app_offset', appOffset.value.toString())
        }
      } else {
        console.log('[App] No manual offset found, using 0')
        appOffset.value = 0
        localStorage.setItem('app_offset', '0')
      }
    }
  } catch (error) {
    console.error('Failed to load iiko settings for timezone:', error)
  }
})
</script>

<template>
  <VApp>
    <RouterView />
    <PwaInstallBanner />
  </VApp>
</template>
