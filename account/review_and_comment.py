from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from account.models import Review
from database import get_async_session
from scheme import ReviewResponse, ReviewBase
from utils import verify_token

app = APIRouter(tags=['comments'])



@app.post("/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(review: ReviewBase,
                        token: dict = Depends(verify_token),
                        session: AsyncSession = Depends(get_async_session)):
    user_id = token.get('user_id')

    if not (1 <= review.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Insert the review
    new_review = Review.insert().values(
        user_id=user_id,
        restaurant_id=review.restaurant_id,
        rating=review.rating,
        comment=review.comment,
        created_at=datetime.utcnow()
    ).returning(*Review.columns)

    result = await session.execute(new_review)
    await session.commit()
    return result.fetchone()


@app.get("/reviews", response_model=List[ReviewResponse])
async def get_reviews(restaurant_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Review).where(Review.c.restaurant_id == restaurant_id)
    result = await session.execute(query)
    reviews = result.mappings().all()

    if not reviews:
        raise HTTPException(status_code=404, detail="No reviews found for this restaurant")

    return reviews


@app.delete("/reviews/{review_id}", status_code=204)
async def delete_review(review_id: int, session: AsyncSession = Depends(get_async_session)):
    query = delete(Review).where(Review.c.id == review_id)
    result = await session.execute(query)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Review not found")

    await session.commit()
    return {"detail": "Review deleted successfully"}
