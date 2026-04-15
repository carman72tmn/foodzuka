import httpx
import logging
import re
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class SpamConfig(BaseSettings):
    CLEANTALK_AUTH_KEY: Optional[str] = None
    KASPERSKY_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

config = SpamConfig()

class BaseSpamProvider(ABC):
    """Базовый класс для провайдеров проверки номеров"""
    
    def __init__(self, headers: Dict[str, str]):
        self.headers = headers

    @abstractmethod
    async def check(self, phone: str) -> Dict[str, Any]:
        """Возвращает {'score': int, 'info': str}"""
        pass

    def clean_phone(self, phone: str) -> str:
        clean = re.sub(r"\D", "", phone)
        if clean.startswith("8") and len(clean) == 11:
            clean = "7" + clean[1:]
        elif len(clean) == 10:
            clean = "7" + clean
        return clean

class NeberiTrubkuProvider(BaseSpamProvider):
    """Провайдер NeberiTrubku.ru - общественная база спама"""
    
    async def check(self, phone: str) -> Dict[str, Any]:
        clean_p = self.clean_phone(phone)
        if not clean_p or len(clean_p) < 10:
            return {"score": 0, "info": "Invalid phone"}
            
        try:
            url = f"https://www.neberitrubku.ru/nomer-telefona/{clean_p}"
            async with httpx.AsyncClient(headers=self.headers, timeout=5.0) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    text = response.text.lower()
                    if any(x in text for x in ["опасный", "мошенничество", "danger"]):
                        return {"score": 100, "info": "NeberiTrubku: Критическая угроза (Мошенники)"}
                    if any(x in text for x in ["отрицательный", "нежелательный", "negative"]):
                        return {"score": 80, "info": "NeberiTrubku: Высокий риск спама"}
                    if any(x in text for x in ["нейтральный", "neutral"]):
                        return {"score": 40, "info": "NeberiTrubku: Средний риск"}
                    if any(x in text for x in ["положительный", "positive"]):
                        return {"score": 0, "info": "NeberiTrubku: Безопасно"}
            return {"score": 0, "info": "NeberiTrubku: Нет данных"}
        except Exception as e:
            logger.warning(f"NeberiTrubku error: {e}")
            return {"score": 0, "info": "NeberiTrubku: Ошибка доступа"}

class VoxlinkProvider(BaseSpamProvider):
    """Провайдер Voxlink - информация об операторе и регионе"""
    
    async def check(self, phone: str) -> Dict[str, Any]:
        clean_p = self.clean_phone(phone)
        try:
            url = f"http://num.voxlink.ru/get/?num={clean_p}"
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    op = data.get("operator", "?")
                    reg = data.get("region", "?")
                    return {"score": 0, "info": f"Voxlink: {op} ({reg})"}
            return {"score": 0, "info": "Voxlink: Нет данных"}
        except Exception as e:
            return {"score": 0, "info": "Voxlink: Ошибка"}

class CleanTalkProvider(BaseSpamProvider):
    """Провайдер CleanTalk - профессиональный антиспам API"""
    
    async def check(self, phone: str) -> Dict[str, Any]:
        if not config.CLEANTALK_AUTH_KEY:
            return {"score": 0, "info": "CleanTalk: Нет ключа API"}
            
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post("https://api.cleantalk.org/", data={
                    "method_name": "spam_check",
                    "auth_key": config.CLEANTALK_AUTH_KEY,
                    "phone": self.clean_phone(phone)
                })
                if res.status_code == 200:
                    data = res.json()
                    # Упрощенная логика анализа ответа CleanTalk
                    if data.get("data", {}).get(self.clean_phone(phone), {}).get("appears") == 1:
                        return {"score": 90, "info": "CleanTalk: Номер в базе спама"}
            return {"score": 0, "info": "CleanTalk: Чисто"}
        except Exception as e:
            return {"score": 0, "info": "CleanTalk: Ошибка"}

class KasperskyProvider(BaseSpamProvider):
    """Провайдер Kaspersky Who Calls"""
    
    async def check(self, phone: str) -> Dict[str, Any]:
        # Пока Kaspersky API требует сложной интеграции или ключа, 
        # реализуем как высокоприоритетную заглушку или поиск через web (если возможно)
        return {"score": 0, "info": "Kaspersky: Данные уточняются"}

class SpamService:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.providers: List[BaseSpamProvider] = [
            NeberiTrubkuProvider(self.headers),
            VoxlinkProvider(self.headers),
            CleanTalkProvider(self.headers),
            KasperskyProvider(self.headers)
        ]

    async def check_phone(self, phone: str) -> Dict[str, Any]:
        """Агрегированная проверка по всем источникам"""
        if not phone:
            return {"score": 0, "info": "Номер не указан"}
            
        results = await asyncio.gather(*[p.check(phone) for p in self.providers], return_exceptions=True)
        
        max_score = 0
        info_parts = []
        
        for res in results:
            if isinstance(res, dict):
                max_score = max(max_score, res.get("score", 0))
                if res.get("info"):
                    info_parts.append(res["info"])
            else:
                logger.error(f"Provider error: {res}")
                
        return {
            "score": max_score,
            "info": " | ".join(info_parts) if info_parts else "Нет данных"
        }

spam_service = SpamService()
