import os
import shutil
import random
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from pycparser.ply.yacc import resultlimit
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse

from account.models import food_categories, MenuItem
from config import PHOTO_DIR
from database import  get_async_session
from utils import verify_token, check_permissions, admin_check

router = APIRouter(tags=['menu'])


@router.post('/add-food-category')
async def add_food_category(
        restaurant_id: int,
        category_name: str,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    current_user_id = token.get('user_id')

    has_permission = await check_permissions(current_user_id, restaurant_id, session)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add a category!"
        )

    # Add the category
    await session.execute(
        insert(food_categories).values(
            restaurant_id=restaurant_id,
            name=category_name
        )
    )
    await session.commit()

    return {"success": True, "message": f"Category '{category_name}' added to restaurant {restaurant_id}."}



@router.get('/get-food-categories')
async def get_food_categories(session: AsyncSession = Depends(get_async_session)
                ):

    categories = await session.execute(select(food_categories))
    result = categories.mappings().all()
    return result


@router.post('/add-food-to-category')
async def add_food_to_category(
    food_category_id: int,
    name: str,
    price: float,
    description: str,
    image: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    token: dict = Depends(verify_token)
):
    current_user_id = token.get('user_id')

    res_id = await session.execute(
        select(food_categories.c.restaurant_id)
        .where(food_categories.c.id == food_category_id)
    )
    restaurant_id = res_id.scalar()
    if not restaurant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Food category not found!"
        )

    has_permission = await check_permissions(current_user_id, restaurant_id, session)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to add a food item!"
        )

    file_extension = image.filename.split('.')[-1]
    if file_extension not in ('jpg', 'jpeg', 'png'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats are: jpg, jpeg, png."
        )

    while True:
        random_number = random.randint(10000, 99999)
        image_filename = f"{random_number}_{name}.{file_extension}"
        image_path = Path(f"./media/photos/{image_filename}")
        if not image_path.exists():
            break

    with image_path.open("wb") as buffer:
        buffer.write(await image.read())

    image_url = str(image_path)
    result = await session.execute(
        insert(MenuItem).values(
            food_categories_id=food_category_id,
            name=name,
            description=description,
            price=price,
            image_url=image_url
        ).returning(MenuItem.c.id)
    )
    food_item_id = result.scalar()
    await session.commit()

    return {"message": "Food item added successfully!", "food_item_id": food_item_id}


@router.get('/get-food-items')
async def get_food_items(
                         food_category_id: int,
session: AsyncSession = Depends(get_async_session),
                         ):
    food = await session.execute(select(MenuItem).where(MenuItem.c.food_categories_id == food_category_id))
    result = food.mappings().all()
    return result


@router.get('/add-food-by-id')
async def add_food_by_id(menu_id: int, session: AsyncSession = Depends(get_async_session),
                         ):

    check_menu_id = await session.execute(select(MenuItem).where(MenuItem.c.id == menu_id))
    if not check_menu_id.scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Menu not found!")

    result = await session.execute(select(MenuItem).where(MenuItem.c.id == menu_id))
    result_item = result.mappings().first()
    return result_item


@router.get('/get-food-photo')
async def get_food_photo(
        food_id: int,
        download: bool = Query(False),
        session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(MenuItem.c.image_url).where(MenuItem.c.id == food_id))
    photo_url = result.scalar()

    if not photo_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="food item not found!")

    photo_path = Path(photo_url)

    if not photo_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo file not found.")

    if download:
        return FileResponse(photo_path, media_type='image/jpeg', filename=photo_path.name)
    else:
        return FileResponse(photo_path, media_type='image/jpeg', headers={"Content-Disposition": "inline"})


