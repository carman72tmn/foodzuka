import httpx
from typing import Optional, Dict, Any, List
from shapely.geometry import Point, Polygon
import json
import logging
from sqlmodel import Session, select
from app.models.yandex_settings import YandexSettings
from app.models.company import DeliveryZone

logger = logging.getLogger(__name__)

class YandexService:
    def __init__(self):
        self.base_url_geocoder = "https://geocode-maps.yandex.ru/1.x/"
        self.base_url_matrix = "https://api.routing.yandex.net/v2/distancematrix"
        
    async def get_settings(self, session: Session) -> Optional[YandexSettings]:
        """Получение активных настроек Яндекс"""
        return session.exec(select(YandexSettings).where(YandexSettings.is_active == True)).first()

    async def geocode_address(self, address: str, api_key: str) -> Optional[Dict[str, float]]:
        """
        Преобразование адреса в координаты (Lat/Lng)
        """
        try:
            params = {
                "apikey": api_key,
                "geocode": address,
                "format": "json",
                "results": 1
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url_geocoder, params=params)
                response.raise_for_status()
                data = response.json()
                
                feature_member = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
                if not feature_member:
                    return None
                
                pos = feature_member[0].get("GeoObject", {}).get("Point", {}).get("pos", "")
                if not pos:
                    return None
                
                # Яндекс возвращает "lon lat"
                lon, lat = map(float, pos.split())
                return {"lat": lat, "lng": lon}
        except Exception as e:
            logger.error(f"Yandex Geocoding error: {str(e)}")
            return None

    def is_point_in_zone(self, lat: float, lng: float, zone: DeliveryZone) -> bool:
        """
        Проверка вхождения точки в зону доставки.
        Сначала проверяет кастомные полигоны (загруженные вручную), затем стандартный полигон iiko.
        """
        # 1. Проверка кастомных полигонов
        if hasattr(zone, "custom_polygons") and zone.custom_polygons:
            for custom_poly in zone.custom_polygons:
                if not custom_poly.is_active or not custom_poly.coordinates:
                    continue
                try:
                    # coordinates в CustomPolygon хранятся как [[lat, lng], ...]
                    poly = Polygon(custom_poly.coordinates)
                    if poly.contains(Point(lat, lng)):
                        return True
                except Exception as e:
                    logger.error(f"Custom polygon {custom_poly.id} check error: {str(e)}")

        # 2. Проверка стандартного полигона iiko
        if not zone.polygon_coordinates:
            return False
            
        try:
            # Парсим координаты полигона. Ожидается JSON список [[lat, lng], [lat, lng], ...]
            coords = json.loads(zone.polygon_coordinates)
            if not coords or len(coords) < 3:
                return False
                
            polygon = Polygon(coords)
            point = Point(lat, lng)
            
            return polygon.contains(point)
        except Exception as e:
            logger.error(f"Zone check error for zone {zone.name}: {str(e)}")
            return False

    async def resolve_zone_for_point(self, lat: float, lng: float, session: Session) -> Optional[DeliveryZone]:
        """
        Поиск зоны доставки для заданных координат
        """
        zones = session.exec(select(DeliveryZone).where(DeliveryZone.is_active == True)).all()
        
        # Сначала проверяем зоны с приоритетом
        sorted_zones = sorted(zones, key=lambda x: x.priority, reverse=True)
        
        for zone in sorted_zones:
            if self.is_point_in_zone(lat, lng, zone):
                return zone
        return None

    async def test_geocoder_key(self, api_key: str) -> bool:
        """Проверка ключа геокодера"""
        res = await self.geocode_address("Москва, Красная площадь, 1", api_key)
        return res is not None

yandex_service = YandexService()
