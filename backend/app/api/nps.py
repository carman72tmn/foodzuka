"""
API эндпоинты для управления Отзывами (NPS)
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.nps import NpsReview
from app.schemas import NpsReviewCreate, NpsReviewUpdate, NpsReviewResponse

router = APIRouter(prefix="/nps", tags=["NPS Reviews"])

@router.get("/", response_model=List[NpsReviewResponse])
async def get_reviews(
    skip: int = 0,
    limit: int = 100,
    is_processed: Optional[bool] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Список отзывов клиентов по завершенным заказам"""
    query = select(NpsReview).order_by(NpsReview.created_at.desc()).offset(skip).limit(limit)
    
    if is_processed is not None:
        query = query.where(NpsReview.is_processed == is_processed)
    
    if min_score is not None:
        query = query.where(NpsReview.score >= min_score)
        
    if max_score is not None:
        query = query.where(NpsReview.score <= max_score)
        
    reviews = session.exec(query).all()
    return reviews

@router.get("/{review_id}", response_model=NpsReviewResponse)
async def get_review(review_id: int, session: Session = Depends(get_session)):
    """Получение деталей конкретного отзыва"""
    review = session.get(NpsReview, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NPS Review not found")
    return review

@router.post("/", response_model=NpsReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: NpsReviewCreate,
    session: Session = Depends(get_session)
):
    """Создать отзыв клиента после заказа (обычно вызывается через telegram-бота)"""
    review = NpsReview(**review_data.model_dump())
    session.add(review)
    session.commit()
    session.refresh(review)
    return review

@router.patch("/{review_id}", response_model=NpsReviewResponse)
async def process_review(
    review_id: int,
    review_data: NpsReviewUpdate,
    session: Session = Depends(get_session)
):
    """Обработка отзыва менеджером (например закрытие негативного отзыва с комментарием)"""
    review = session.get(NpsReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    update_data = review_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)
        
    if update_data.get('is_processed') and not review.processed_at:
        review.processed_at = datetime.now(timezone.utc)

    session.add(review)
    session.commit()
    session.refresh(review)
    return review
