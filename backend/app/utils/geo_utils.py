import json
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict, Any

def parse_geojson(content: str) -> List[Dict[str, Any]]:
    """
    Парсит содержимое GeoJSON и извлекает полигоны.
    Возвращает список словарей с 'name' и 'coordinates' [[lat, lng], ...].
    """
    try:
        data = json.loads(content)
        polygons = []
        
        features = data.get("features", [])
        if not features and data.get("type") == "Feature":
            features = [data]
            
        for feature in features:
            geom = feature.get("geometry", {})
            if not geom:
                continue
                
            if geom.get("type") == "Polygon":
                name = feature.get("properties", {}).get("name") or feature.get("properties", {}).get("description") or "Unnamed Polygon"
                # В GeoJSON координаты [lng, lat]
                coords = [[p[1], p[0]] for p in geom.get("coordinates", [[]])[0]]
                polygons.append({"name": name, "coordinates": coords})
            elif geom.get("type") == "MultiPolygon":
                name = feature.get("properties", {}).get("name") or "Unnamed MultiPolygon"
                for i, poly in enumerate(geom.get("coordinates", [])):
                    coords = [[p[1], p[0]] for p in poly[0]]
                    polygons.append({"name": f"{name} {i+1}", "coordinates": coords})
                    
        return polygons
    except Exception as e:
        print(f"Error parsing GeoJSON: {e}")
        return []

def parse_kml(content: str) -> List[Dict[str, Any]]:
    """
    Парсит содержимое KML и извлекает полигоны.
    Возвращает список словарей с 'name' и 'coordinates' [[lat, lng], ...].
    """
    polygons = []
    try:
        # KML может быть с пространством имен или без
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            # Возможно, есть декларация кодировки, которая мешает
            if isinstance(content, str):
                content = content.encode("utf-8")
            root = ET.fromstring(content)

        # Пространства имен
        ns = {"kml": "http://www.opengis.net/kml/2.2"}
        
        # Если в корне нет namespace, попробуем искать напрямую
        placemarks = root.findall(".//kml:Placemark", ns)
        if not placemarks:
            placemarks = root.findall(".//Placemark")
            ns = {} # Сбрасываем ns если нашли без него

        for placemark in placemarks:
            name_elem = placemark.find("kml:name", ns) if ns else placemark.find("name")
            name = (name_elem.text.strip() if name_elem is not None and name_elem.text else "Unnamed Polygon")
            
            # Поиск Polygon
            poly_elem = placemark.find(".//kml:Polygon", ns) if ns else placemark.find(".//Polygon")
            if poly_elem is not None:
                coord_elem = poly_elem.find(".//kml:coordinates", ns) if ns else poly_elem.find(".//coordinates")
                if coord_elem is not None and coord_elem.text:
                    # В KML координаты: lng,lat,alt или lng,lat
                    raw_coords = coord_elem.text.strip().split()
                    coords = []
                    for rc in raw_coords:
                        parts = rc.split(",")
                        if len(parts) >= 2:
                            try:
                                coords.append([float(parts[1]), float(parts[0])])
                            except ValueError:
                                continue
                    if coords:
                        polygons.append({"name": name, "coordinates": coords})
    except Exception as e:
        print(f"Error parsing KML: {e}")
        
    return polygons

def is_point_in_polygon(lat: float, lng: float, polygon: List[List[float]]) -> bool:
    """
    Алгоритм Ray Casting для проверки вхождения точки в полигон.
    polygon - список [lat, lng].
    """
    if not polygon:
        return False
        
    n = len(polygon)
    inside = False
    
    # Нормализация: если последняя точка не совпадает с первой, добавим её (необязательно для ray casting, но полезно)
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if lat > min(p1x, p2x):
            if lat <= max(p1x, p2x):
                if lng <= max(p1y, p2y):
                    if p1x != p2x:
                        xints = (lat - p1x) * (p2y - p1y) / (p2x - p1x) + p1y
                    if p1y == p2y or lng <= xints:
                        inside = not inside
        p1x, p1y = p2x, p2y
        
    return inside
