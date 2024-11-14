from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException, File, UploadFile, Query
import os
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.sync import update
from sqlalchemy.orm.unitofwork import DeleteAll
from starlette.responses import FileResponse

from account.models import users, restaurant
from config import PHOTO_DIR
from database import get_async_session
from scheme import RestaurantModel
from utils import verify_token

router = APIRouter(tags=['restaurant'])

@router.post('/add-restaurant')
async def add_restaurant(
        name: str,
        address: str,
        phone_number: str,
        number_of_people: int,
        description: str,
        photo: UploadFile = File(...),
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

    file_extension = photo.filename.split('.')[-1]
    if file_extension not in ('jpg', 'jpeg', 'png'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid photo format. Use jpg, jpeg, or png.")

    photo_filename = f"{name}_{phone_number}.{file_extension}"
    photo_path = PHOTO_DIR / photo_filename

    with open(photo_path, "wb") as file:
        file.write(await photo.read())

    query = restaurant.insert().values(
        name=name,
        address=address,
        phone_number=phone_number,
        number_of_people=number_of_people,
        description=description,
        photo_url=str(photo_path)
    )

    await session.execute(query)
    await session.commit()

    return {"message": "Restaurant added successfully"}


@router.get('/get-all-restaurants', response_model=List[RestaurantModel])
async def get_restaurants(session: AsyncSession = Depends(get_async_session),
                          ):
    restaurants = await session.execute(select(restaurant))
    restaurants_item = restaurants.mappings().all()
    return restaurants_item


@router.get('/get-restaurant-by-id')
async def get_restaurant(resraurant_id: int,
                         session: AsyncSession = Depends(get_async_session)
                         ):
    restaurant_item = await session.execute(select(restaurant).where(restaurant.c.id == resraurant_id))
    return restaurant_item.mappings().one()


@router.get('/get-restaurant-photo')
async def get_restaurant_photo(
        restaurant_id: int,
        download: bool = Query(False),
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(restaurant.c.photo_url).where(restaurant.c.id == restaurant_id))
    photo_url = result.scalar()

    if not photo_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Restaurant not found or photo not available.")

    photo_path = Path(photo_url)

    if not photo_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo file not found.")

    if download:
        return FileResponse(photo_path, media_type='image/jpeg', filename=photo_path.name)
    else:
        return FileResponse(photo_path, media_type='image/jpeg', headers={"Content-Disposition": "inline"})


@router.put('/update-restaurant')
async def update_restaurant(
        restaurant_id: int,
        name: Optional[str] = None,
        address: Optional[str] = None,
        phone_number: Optional[str] = None,
        number_of_people: Optional[int] = None,
        description: Optional[str] = None,
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

    if not fields_to_update:
        raise HTTPException(status_code=400, detail="Please provide at least one field to update.")

        # Perform the update operation on the database
    async with session.begin():
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

    image_path = await session.execute(select(restaurant.c.photo_url).where(restaurant.c.id == restaurant_id))

    delete_restaurant = await session.execute(delete(restaurant).where(restaurant.c.id == restaurant_id))
    await session.commit()

    return {"message": "Restaurant deleted successfully"}
