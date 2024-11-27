from pyexpat.errors import messages
from typing import List
from fastapi import APIRouter,status,HTTPException
from fastapi.params import Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from account.models import users, restaurant,restaurant_owner
from database import get_async_session
from scheme import UserInfo, OwnerInfo
from utils import verify_token, admin_check

router = APIRouter(tags=['admin'])


@router.get('/get-all-users')
async def get_all_users(
        token: dict = Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)):
    current_user_id = token.get('user_id')
    is_admin = await admin_check(current_user_id,session)
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
    result = await session.execute(select(users))
    usrs = result.mappings().all()
    return usrs


@router.delete('/delete-user')
async def delete_user(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    current_user_id = token.get('user_id')
    is_admin = await admin_check(current_user_id,session)
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    user_check = await session.execute(select(users).where(users.c.id == user_id))
    if not user_check.scalar():
        raise HTTPException(status_code=status.HTTP_401_NOT_FOUND)

    try:
        delet_user = await session.execute(delete(users).where(users.c.id == user_id))
        await session.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        return {"message": str(e)}


@router.post('/add-owner')
async def add_owner(
        user_id: int,
        restaurant_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    # Extract current user ID and check admin status
    current_user_id = token.get('user_id')
    is_admin = await admin_check(current_user_id, session)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can assign restaurant owners."
        )

    # Check if the user exists
    user_query = await session.execute(select(users).where(users.c.id == user_id))
    user = user_query.scalar()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    restaurant_query = await session.execute(select(restaurant).where(restaurant.c.id == restaurant_id))
    restauran = restaurant_query.scalar()
    if not restauran:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found."
        )

    owner_query = await session.execute(
        select(restaurant_owner)
        .where(restaurant_owner.c.restaurant_id == restaurant_id)
        .where(restaurant_owner.c.owner_id == user_id)
    )
    existing_owner = owner_query.scalar()
    if existing_owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {user_id} is already an owner of restaurant {restaurant_id}."
        )

    await session.execute(
        restaurant_owner.insert().values(
            restaurant_id=restaurant_id,
            owner_id=user_id
        )
    )
    await session.commit()

    return {
        'success': True,
        "message": f"User {user_id} is now an owner of restaurant {restaurant_id}."
    }


@router.get('/get-all-owners')
async def get_all_owners(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    current_user_id = token.get('user_id')

    # Check if the user is an admin
    is_admin = await admin_check(current_user_id, session)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission!"
        )

    # Query to fetch owner and restaurant details
    query = (
        select(
            users.c.id.label("id"),
            restaurant_owner.c.restaurant_id
        )
        .select_from(restaurant_owner)
        .join(users, restaurant_owner.c.owner_id == users.c.id)
    )
    result = await session.execute(query)
    owners = result.mappings().all()

    return owners


@router.delete('/delete-owner')
async def delete_owner(
        restaurant_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    current_user_id = token.get('user_id')

    is_admin = await admin_check(current_user_id, session)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission!"
        )

    delete_result = await session.execute(
        delete(restaurant_owner)
        .where(restaurant_owner.c.restaurant_id == restaurant_id)
    )
    await session.commit()

    # Check if a row was actually deleted
    if delete_result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No owner found for restaurant {restaurant_id}."
        )

    return {
        "success": True,
        "message": f"Owner has been removed from restaurant {restaurant_id}."
    }


@router.get('/get-owners-by-restaurant/{restaurant_id}', response_model=List[OwnerInfo])
async def get_owners_by_restaurant(
        restaurant_id: int,
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token)
):
    current_user_id = token.get('user_id')

    # Check if the user is an admin
    is_admin = await admin_check(current_user_id, session)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission!"
        )

    check_restaurnt = await session.execute(select(restaurant_owner).where(restaurant_owner.c.restaurant_id == restaurant_id))
    if not check_restaurnt.scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail='This restaurant does not have an owner')

    query = (
        select(
            users.c.id.label("id"),
            users.c.firstname,
            users.c.lastname,
            users.c.email,
            users.c.phone_number,
        )
        .select_from(restaurant_owner)
        .join(users, restaurant_owner.c.owner_id == users.c.id)
        .where(restaurant_owner.c.restaurant_id == restaurant_id)
    )
    result = await session.execute(query)
    owners = result.mappings().all()
    return owners

