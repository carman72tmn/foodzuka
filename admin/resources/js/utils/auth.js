import { reactive } from 'vue'

export const authState = reactive({
  token: localStorage.getItem('access_token') || null,
  user: null,
})

export const login = async (username, password) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      username,
      password,
      grant_type: 'password',
    }),
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Ошибка авторизации')
  }

  const data = await response.json()
  authState.token = data.access_token
  localStorage.setItem('access_token', data.access_token)
  return data
}

export const logout = () => {
  authState.token = null
  authState.user = null
  localStorage.removeItem('access_token')
}

export const fetchMe = async () => {
  if (!authState.token) return null
  
  const response = await fetch('/api/v1/users/me', {
    headers: {
      'Authorization': `Bearer ${authState.token}`
    }
  })
  
  if (response.ok) {
    const data = await response.json()
    authState.user = data
    return data
  } else {
    logout()
    return null
  }
}
