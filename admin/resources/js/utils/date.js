import { ref } from 'vue'

// Глобальная настройка часового пояса (обновляется при загрузке приложения)
export const appTimezone = ref(localStorage.getItem('app_timezone') || 'Asia/Yekaterinburg')
// Смещение в часах (например, +5 или -3)
export const appOffset = ref(parseInt(localStorage.getItem('app_offset') || '0'))

const parseAsUTC = val => {
  if (!val) return val

  if (typeof val === 'string' && !val.includes('Z') && !val.match(/[+-]\d{2}:?\d{2}$/)) {
    // Если есть пробел между датой и временем, заменяем на T
    let normalized = val.trim().replace(' ', 'T')

    // Если нет Z и нет смещения в конце, добавляем Z (считаем что это UTC от iiko)
    if (!normalized.includes('Z') && !normalized.match(/[+-]\d{2}:?\d{2}$/)) {
      normalized = `${normalized}Z`
    }

    return normalized
  }

  return val
}

export const formatDate = val => {
  if (!val) return '-'

  try {
    let date = new Date(parseAsUTC(val))
    
    // Если задано ручное смещение, корректируем время перед форматированием
    if (appOffset.value !== 0) {
      date = new Date(date.getTime() + appOffset.value * 3600000)
      return new Intl.DateTimeFormat('ru-RU', {
        timeZone: 'UTC',
      }).format(date)
    }

    return new Intl.DateTimeFormat('ru-RU', {
      timeZone: appTimezone.value,
    }).format(date)
  } catch (e) {
    console.error('Date format error:', e, val)
    return val
  }
}

export const formatDateTime = (val, options = {}) => {
  if (!val) return '-'

  try {
    const utcVal = parseAsUTC(val)
    let date = new Date(utcVal)

    // Если задано ручное смещение, корректируем время
    if (appOffset.value !== 0) {
      date = new Date(date.getTime() + appOffset.value * 3600000)

      return new Intl.DateTimeFormat('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'UTC',
        ...options,
      }).format(date)
    }

    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: appTimezone.value,
      ...options,
    }).format(date)
  } catch (e) {
    console.error('DateTime format error:', e, val)

    return val
  }
}
