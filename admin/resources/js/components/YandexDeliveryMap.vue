<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'

const props = defineProps({
  zones: {
    type: Array,
    required: true,
  },
  customPolygons: {
    type: Array,
    default: () => [],
  },
  apiKey: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['polygonClick'])

const mapContainer = ref(null)
let ymapsInstance = null
let map = null
let geoObjects = []
let polygonObjects = new Map() // Для быстрого поиска по ID

const initMap = () => {
  if (!window.ymaps || map) return

  window.ymaps.ready(() => {
    map = new window.ymaps.Map(mapContainer.value, {
      center: [57.1522, 65.5272], // Тюмень по умолчанию
      zoom: 11,
      controls: ['zoomControl', 'typeSelector', 'fullscreenControl'],
    })

    renderAll()
  })
}

const renderAll = () => {
  if (!map) return

  // Очищаем старые объекты
  geoObjects.forEach(obj => map.geoObjects.remove(obj))
  geoObjects = []
  polygonObjects.clear()

  // 1. Рендерим стандартные зоны iiko
  props.zones.forEach(zone => {
    if (!zone.polygon_coordinates) return

    try {
      const coords = JSON.parse(zone.polygon_coordinates)
      if (!coords || !coords.length) return

      const baseColor = '#0066ff'
      const polygon = new window.ymaps.Polygon(
        [coords],
        {
          hintContent: `<strong>${zone.name}</strong><br/>${zone.delivery_cost} ₽`,
          balloonContent: `
            <div class="map-balloon">
              <div class="map-balloon-header" style="background-color: ${baseColor}">
                ${zone.name} (iiko)
              </div>
              <div class="map-balloon-content">
                <div class="d-flex justify-space-between mb-1">
                  <span>Мин. заказ:</span>
                  <strong>${zone.min_order_amount || 0} ₽</strong>
                </div>
                <div class="d-flex justify-space-between mb-1">
                  <span>Доставка:</span>
                  <strong class="${zone.delivery_cost === 0 ? 'text-success' : ''}">
                    ${zone.delivery_cost === 0 ? 'Бесплатно' : zone.delivery_cost + ' ₽'}
                  </strong>
                </div>
              </div>
            </div>
          `
        },
        {
          fillColor: baseColor + '22',
          strokeColor: baseColor,
          strokeOpacity: 0.8,
          strokeWidth: 2,
          zIndex: 0,
        },
      )

      map.geoObjects.add(polygon)
      geoObjects.push(polygon)
      polygonObjects.set(`iiko-${zone.id}`, polygon)
    } catch (e) {
      console.error('Error parsing zone coordinates:', e)
    }
  })

  // 2. Рендерим кастомные полигоны
  props.customPolygons.forEach(poly => {
    if (!poly.coordinates || !poly.coordinates.length) return

    const baseColor = poly.fill_color || (poly.delivery_zone_id ? '#4caf50' : '#ff9800')
    
    const polygon = new window.ymaps.Polygon(
      [poly.coordinates],
      {
        hintContent: `<strong>${poly.name}</strong><br/>${poly.delivery_cost} ₽`,
        balloonContent: `
          <div class="map-balloon">
            <div class="map-balloon-header" style="background-color: ${baseColor}">
              ${poly.name}
            </div>
            <div class="map-balloon-content">
              ${poly.description ? `<div class="mb-2 text-grey-darken-1">${poly.description}</div>` : ''}
              
              <div class="d-flex justify-space-between mb-1">
                <span>Время:</span>
                <strong>${poly.min_delivery_time || '?'}-${poly.max_delivery_time || '?'} мин.</strong>
              </div>
              
              <div class="d-flex justify-space-between mb-1">
                <span>Мин. заказ:</span>
                <strong>${poly.min_order_amount || 0} ₽</strong>
              </div>
              
              <div class="d-flex justify-space-between mb-1">
                <span>Доставка:</span>
                <strong class="${poly.delivery_cost === 0 ? 'text-success' : ''}">
                  ${poly.delivery_cost === 0 ? 'Бесплатно' : poly.delivery_cost + ' ₽'}
                </strong>
              </div>
              
              ${poly.free_delivery_threshold > 0 ? `
              <div class="d-flex justify-space-between mb-1 text-primary">
                <span>Бесплатно от:</span>
                <strong>${poly.free_delivery_threshold} ₽</strong>
              </div>
              ` : ''}

              <div class="d-flex justify-space-between mb-1 text-grey" style="font-size: 0.8em">
                <span>Приоритет:</span>
                <strong>${poly.priority || 0}</strong>
              </div>
              
              <div class="mt-2 pt-2 border-top">
                <small class="text-grey">
                  <i class="bx bx-link-alt"></i> 
                  ${poly.delivery_zone_id ? `Зона: ${props.zones.find(z => z.id === poly.delivery_zone_id)?.name || 'Неизвестно'}` : 'Не привязан к iiko'}
                </small>
              </div>
            </div>
          </div>
        `
      },
      {
        fillColor: baseColor + '44', // ~25% alpha
        strokeColor: baseColor,
        strokeOpacity: 0.9,
        strokeWidth: 2,
        zIndex: poly.priority || 1,
        // Эффекты при наведении
        hoverFillColor: baseColor + '66', // ~40% alpha
        hoverStrokeWidth: 4,
      },
    )

    polygon.events.add('click', () => {
      emit('polygonClick', poly)
    })

    map.geoObjects.add(polygon)
    geoObjects.push(polygon)
    polygonObjects.set(`custom-${poly.id}`, polygon)
  })

  // Если есть объекты, масштабируем карту
  if (geoObjects.length) {
    map.setBounds(map.geoObjects.getBounds(), { checkZoomRange: true, zoomMargin: 20 })
  }
}

const focusOnPolygon = (type, id) => {
  const poly = polygonObjects.get(`${type}-${id}`)

  if (poly && map) {
    map.setBounds(poly.geometry.getBounds(), { checkZoomRange: true, zoomMargin: 50 })
    poly.balloon.open()
  }
}

defineExpose({ focusOnPolygon })

const loadYandexScript = () => {
  if (window.ymaps) {
    initMap()
    return
  }

  const script = document.createElement('script')
  script.src = `https://api-maps.yandex.ru/2.1/?apikey=${props.apiKey}&lang=ru_RU`
  script.async = true
  script.onload = initMap
  document.head.appendChild(script)
}

watch([() => props.zones, () => props.customPolygons], () => {
  renderAll()
}, { deep: true })

onMounted(() => {
  if (props.apiKey) {
    loadYandexScript()
  }
})

onUnmounted(() => {
  if (map) {
    map.destroy()
    map = null
  }
})
</script>

<template>
  <div class="yandex-map-wrapper">
    <div ref="mapContainer" class="map-container"></div>
    <div v-if="!apiKey" class="no-api-key">
      <VAlert type="warning" variant="tonal">
        API ключ Яндекс.Карт не настроен. Пожалуйста, укажите его в настройках.
      </VAlert>
    </div>
  </div>
</template>

<style scoped>
.yandex-map-wrapper {
  position: relative;
  width: 100%;
  height: 500px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.map-container {
  width: 100%;
  height: 100%;
}

:deep(.map-balloon) {
  min-width: 200px;
  overflow: hidden;
  border-radius: 8px;
  font-family: 'Public Sans', sans-serif;
}

:deep(.map-balloon-header) {
  padding: 8px 12px;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

:deep(.map-balloon-content) {
  padding: 12px;
  background: white;
}

:deep(.border-top) {
  border-top: 1px solid #eee;
}

:deep(.justify-space-between) {
  display: flex;
  justify-content: space-between;
}

.no-api-key {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  text-align: center;
}
</style>
