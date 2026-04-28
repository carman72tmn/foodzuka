import { onMounted } from 'vue'
import { appTimezone, appOffset } from '@/utils/date'
import UpgradeToPro from '@/components/UpgradeToPro.vue'

onMounted(async () => {
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

<template>
  <VApp>
    <RouterView />
    <UpgradeToPro />
  </VApp>
</template>
