from pydantic import BaseModel
from sqlalchemy import select, func, desc
from typing import List

from fastapi import FastAPI, APIRouter, Depends, HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession

import account.auth
import account.admin
import account.restaurant
import account.orders
import account.users
import account.menu
import account.review_and_comment
from account.models import restaurant, Review, locations_of_restaurant
from database import get_async_session
from scheme import HomePageModel
from send_sms import send_sms
from utils import calculate_distance

SECRET_KEY = "ca1ed94261ae6da2f2d81a487e7017c420ed69dd0f81e59817ab768bdc000cbb"
app = FastAPI( docs_url=f"/docs/{SECRET_KEY}",)
router = APIRouter(tags=["home"])



@router.get('/most-popular',response_model=List[HomePageModel])
async def most_popular(session: AsyncSession = Depends(get_async_session)):
    query = select(restaurant)

    subquery = (
        select(
            Review.c.restaurant_id,
            func.avg(Review.c.rating).label("average_rating")
        )
        .group_by(Review.c.restaurant_id)
        .subquery()
    )
    query = (
        select(restaurant, subquery.c.average_rating)
        .join(subquery, restaurant.c.id == subquery.c.restaurant_id)
        .order_by(subquery.c.average_rating.desc())
    )
    result = await session.execute(query)
    restaurants = result.mappings().all()
    return restaurants


@router.get('/nearby_restaurants', summary="Get restaurants nearby")
async def nearby_restaurants(
        coordinates:str,
        session: AsyncSession = Depends(get_async_session)
) -> List[dict]:
    location_query = (
        select(restaurant.c.id, restaurant.c.name, restaurant.c.description, locations_of_restaurant.c.latitude,
               locations_of_restaurant.c.longitude)
        .join(locations_of_restaurant, restaurant.c.id == locations_of_restaurant.c.restaurant_id)
    )
    results = await session.execute(location_query)
    restaurants = results.mappings().all()
    try:
        latitude, longitude = map(float, coordinates.split(','))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid coordinates format. Expected 'latitude,longitude'."
        )

    restaurant_distances = []
    for r in restaurants:
        distance = calculate_distance(latitude, longitude, r["latitude"], r["longitude"])
        restaurant_distances.append({
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "distance": f"{round(distance, 2)} km"
        })

    sorted_restaurants = sorted(restaurant_distances, key=lambda x: x["distance"])
    return sorted_restaurants


class NewestRestaurantsResponse(BaseModel):
    newest_restaurants: List[HomePageModel]

@router.get('/newest-restaurants', summary="Get newest restaurants", response_model=NewestRestaurantsResponse)
async def newest_restaurants(session: AsyncSession = Depends(get_async_session)):
    query = (
        select(
            restaurant.c.id,
            restaurant.c.name,
            restaurant.c.address,
            restaurant.c.phone_number,
            restaurant.c.number_of_people,
            restaurant.c.description,
        )
        .order_by(desc(restaurant.c.id))
        .limit(2)
    )

    result = await session.execute(query)
    restaurants = result.mappings().all()

    return {"newest_restaurants": restaurants}



@app.post("/send-sms/")
async def send_sms_endpoint(phone_number: str, message: str):
    try:
        result = await send_sms(phone_number, message)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




app.include_router(router)
app.include_router(account.auth.router)
app.include_router(account.users.router)
app.include_router(account.admin.router)
app.include_router(account.restaurant.router)
app.include_router(account.menu.router)
app.include_router(account.orders.router)
app.include_router(account.review_and_comment.app)