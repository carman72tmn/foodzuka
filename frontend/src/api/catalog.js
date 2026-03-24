// API fetching logic for the frontend menu

const API_URL = 'http://192.168.31.162:8000/api/v1'

export const fetchCategories = async () => {
  try {
    const res = await fetch(`${API_URL}/categories/`)
    if (!res.ok) throw new Error('API Error fetching categories')
    return await res.json()
  } catch (error) {
    console.error("Failed to fetch categories, using mock", error)
    return [
      { id: 1, name: "Суши и Роллы", iiko_id: "fake_iiko_1", is_deleted: false },
      { id: 2, name: "Пицца", iiko_id: "fake_iiko_2", is_deleted: false },
      { id: 3, name: "Супы", iiko_id: "fake_iiko_3", is_deleted: false }
    ]
  }
}

export const fetchProducts = async () => {
  try {
    const res = await fetch(`${API_URL}/products/`)
    if (!res.ok) throw new Error('API Error fetching products')
    const data = await res.json()
    // Depending on backend, might be { items: [...] } or just [...]
    return Array.isArray(data) ? data : data.items || data
  } catch (error) {
    console.error("Failed to fetch products from API, using mock data", error)
    // Fallback to mock data for layout purposes if API is down
    return [
      { id: 1, name: "Ролл Филадельфия", price: 550, description: "Лосось, сливочный сыр, огурец", category_id: 1, image_url: "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?q=80&w=400&auto=format&fit=crop" },
      { id: 2, name: "Пицца Пепперони", price: 650, description: "Пепперони, моцарелла, томатный соус", category_id: 2, image_url: "https://images.unsplash.com/photo-1628840042765-356cda07504e?q=80&w=400&auto=format&fit=crop" },
      { id: 3, name: "Том Ям", price: 450, description: "Креветки, кокосовое молоко, лемонграсс", category_id: 3, image_url: "https://images.unsplash.com/photo-1548943487-a2e4142f8c5c?q=80&w=400&auto=format&fit=crop" },
      { id: 4, name: "Калифорния", price: 480, description: "Краб, авокадо, огурец, тобико", category_id: 1, image_url: "https://images.unsplash.com/photo-1553621042-f6e147245754?q=80&w=400&auto=format&fit=crop" }
    ]
  }
}
