from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.message_log import CustomerMessageLog, ShortLink
from app.models.broadcast import CustomerBroadcast
from datetime import datetime, timezone

# Роутер без префикса для коротких ссылок типа /lnk/{code}
router = APIRouter(tags=["Link Tracker"])

@router.get("/lnk/{code}")
def track_link_click(code: str, db: Session = Depends(get_session)):
    """
    Отслеживание кликов по коротким ссылкам.
    Помечает сообщение как кликнутое и перенаправляет гостя на целевой сайт.
    """
    short_link = db.get(ShortLink, code)
    if not short_link:
        raise HTTPException(status_code=404, detail="Короткая ссылка не найдена")
        
    # Находим лог сообщения
    log = db.get(CustomerMessageLog, short_link.message_log_id)
    if log:
        if log.status != "clicked":
            log.status = "clicked"
            log.clicked_at = datetime.now(timezone.utc)
            db.add(log)
            
            # Если это было сообщение рассылки, увеличим количество прочитанных/кликнутых
            if log.broadcast_id:
                broadcast = db.get(CustomerBroadcast, log.broadcast_id)
                if broadcast:
                    # Увеличим read_count в качестве метрики прочтения/клика
                    broadcast.read_count += 1
                    db.add(broadcast)
                    
            db.commit()
            
    return RedirectResponse(url=short_link.original_url)
