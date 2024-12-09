from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse, JSONResponse

from account.models import users, restaurant, restaurants_photos
from database import get_async_session
from scheme import RestaurantModel
from utils import verify_token, admin_check, serialize_row

router = APIRouter(tags=['restaurant'])


@router.post('/add-restaurant')
async def add_restaurant(
        name: str,
        address: str,
        phone_number: str,
        number_of_people: int,
        description: str,
        coodinates: str,
        chat_id:int,
        photo:str,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    check_admin = await session.execute(select(users).where((users.c.id == user_id) & (users.c.is_admin == True)))

    if not check_admin.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="User is not authorized.")

    check_phone_number = await session.execute(select(restaurant).where(restaurant.c.phone_number == phone_number))
    if check_phone_number.scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Restaurant with this phone number is already exists.")


    query = restaurant.insert().values(
        name=name,
        address=address,
        phone_number=phone_number,
        number_of_people=number_of_people,
        seats_left=number_of_people,
        description=description,
        coordinates=coodinates,
        chat_id=chat_id,
        photo=photo
    )

    await session.execute(query)
    await session.commit()

    return {"message": "Restaurant added successfully"}



@router.post('/add-photo-to-restaurant')
async def add_photos_to_restaurant(
    restaurant_id: int,
    name:str,
    session: AsyncSession = Depends(get_async_session),
    token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')

    # Check if the user is an admin
    if not await admin_check(user_id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add a photo to the restaurant."
        )

    # Check if the restaurant exists
    restaurant_result = await session.execute(
        select(restaurant).where(restaurant.c.id == restaurant_id)
    )
    existing_restaurant = restaurant_result.scalar_one_or_none()
    if not existing_restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found."
        )

    # Add the photo to the `restaurant_photos` table
    try:
        query = insert(restaurants_photos).values(
            restaurant_id=restaurant_id,
            photo_url=name
        )
        await session.execute(query)
        await session.commit()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add the photo to the database. Error: {str(e)}"
        )

    return {
        "message": "Photo added to restaurant successfully",
        "photo_url": str(name)
    }


@router.get('/get-all-restaurants')
async def get_restaurants(session: AsyncSession = Depends(get_async_session)):
    # Fetch restaurants from the database
    result = await session.execute(select(restaurant))
    restaurants = result.mappings().all()

    response_data = [serialize_row(row) for row in restaurants]

    return JSONResponse(content=response_data, media_type="application/json")


@router.get('/get-restaurant-by-id')
async def get_restaurant(resraurant_id: int,
                         session: AsyncSession = Depends(get_async_session)
                         ):
    restaurant_item = await session.execute(select(restaurant).where(restaurant.c.id == resraurant_id))
    result = restaurant_item.mappings().first()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant does not exist.")
    return result



@router.get('/get-photos-by-restaurant')
async def get_photos_by_restaurant(
    restaurant_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    # Fetch photos associated with the restaurant
    result = await session.execute(
        select(restaurants_photos.c.id, restaurants_photos.c.photo_url)
        .where(restaurants_photos.c.restaurant_id == restaurant_id)
    )
    photos = result.fetchall()

    if not photos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No photos found for this restaurant."
        )

    return {
        "restaurant_id": restaurant_id,
        "photos": [{"id": photo.id, "photo_url": photo.photo_url} for photo in photos]
    }


@router.put('/update-restaurant')
async def update_restaurant(
        restaurant_id: int,
        name: Optional[str] = None,
        address: Optional[str] = None,
        phone_number: Optional[str] = None,
        number_of_people: Optional[int] = None,
        description: Optional[str] = None,
        coordinates: Optional[str] = None,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    admin_check = await session.execute(select(users).where((users.c.id == user_id) & (users.c.is_admin == True)))
    if not admin_check.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    fields_to_update: Dict[str, Any] = {}
    if name:
        fields_to_update["name"] = name
    if address:
        fields_to_update["address"] = address
    if phone_number:
        fields_to_update["phone_number"] = phone_number
    if number_of_people:
        fields_to_update["number_of_people"] = number_of_people
    if description:
        fields_to_update["description"] = description
    if coordinates:
        fields_to_update["coordinates"] = coordinates

    if not fields_to_update:
        raise HTTPException(status_code=400, detail="Please provide at least one field to update.")

    stmt = (
        restaurant.update()
        .where(restaurant.c.id == restaurant_id)
        .values(**fields_to_update)
    )
    await session.execute(stmt)

    await session.commit()
    return {"message": "Restaurant updated successfully"}


@router.delete('/delete-restaurant')
async def delete_restaurant(
        restaurant_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    user_id = token.get('user_id')
    admin_check = await session.execute(select(users).where((users.c.id == user_id) & (users.c.is_admin == True)))
    if not admin_check.scalar():
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    check_restaurant = await session.execute(select(restaurant).where(restaurant.c.id == restaurant_id))
    if not check_restaurant.scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    await session.execute(delete(restaurant).where(restaurant.c.id == restaurant_id))
    await session.commit()

    return {"message": "Restaurant deleted successfully"}
