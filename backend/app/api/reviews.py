from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from app.core.database import get_session
from app.models.review import OrderReview
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.mailing_cascade import OrderReviewResponse

router = APIRouter(prefix="/mailings/reviews", tags=["Order Reviews"])

@router.get("", response_model=List[OrderReviewResponse])
def get_reviews(
    rating: Optional[int] = Query(None, description="Фильтр по оценке (1-5)"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_session)
):
    """
    Получить журнал отзывов гостей.
    Обогащает данные именами клиентов и номерами заказов.
    """
    statement = select(OrderReview, Customer.name, Customer.phone, Order.external_number)\
        .outerjoin(Customer, OrderReview.customer_id == Customer.id)\
        .outerjoin(Order, OrderReview.order_id == Order.id)
        
    if rating is not None:
        statement = statement.where(OrderReview.rating == rating)
        
    statement = statement.order_by(OrderReview.created_at.desc()).limit(limit).offset(offset)
    
    results = db.exec(statement).all()
    
    reviews_list = []
    for review, cust_name, cust_phone, order_num in results:
        reviews_list.append(OrderReviewResponse(
            id=review.id,
            order_id=review.order_id,
            customer_id=review.customer_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            customer_name=cust_name or "Гость",
            customer_phone=cust_phone or "---",
            order_number=order_num or str(review.order_id) if review.order_id else "---"
        ))
        
    return reviews_list

@router.get("/stats")
def get_reviews_stats(db: Session = Depends(get_session)):
    """
    Получить статистику оценок гостей (средний балл и распределение).
    """
    # Средний балл
    avg_rating_query = select(func.avg(OrderReview.rating))
    avg_rating = db.exec(avg_rating_query).one() or 0.0
    
    # Всего отзывов
    total_query = select(func.count(OrderReview.id))
    total_count = db.exec(total_query).one() or 0
    
    # Распределение оценок
    dist_query = select(OrderReview.rating, func.count(OrderReview.id))\
        .group_by(OrderReview.rating)
    dist_results = db.exec(dist_query).all()
    
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating, count in dist_results:
        if rating in distribution:
            distribution[rating] = count
            
    return {
        "average_rating": round(float(avg_rating), 2),
        "total_count": total_count,
        "distribution": distribution
    }
