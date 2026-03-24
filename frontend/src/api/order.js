const API_URL = 'http://192.168.31.162:8000/api/v1'

export const createOrder = async (orderData) => {
  try {
    const response = await fetch(`${API_URL}/orders/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(orderData)
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to create order')
    }
    
    return await response.json()
  } catch (error) {
    console.error('Order creation error:', error)
    throw error
  }
}
