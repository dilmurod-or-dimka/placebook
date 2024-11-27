from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, insert, update, Nullable
from sqlalchemy.ext.asyncio import AsyncSession

from account.models import Reservation, users, restaurant
from database import get_async_session
from utils import verify_token, admin_check

router = APIRouter(tags=['Orders'])


@router.get('/orders', response_model=List[dict])
async def get_orders(
    session: AsyncSession = Depends(get_async_session),
    token: dict = Depends(verify_token),
):
    user_id = token['user_id']
    check_admin = await admin_check(user_id,session)
    if not check_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="You do not have permission to perform this action.")
    result = await session.execute(select(Reservation))
    if result.scalar() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail='You do not have orders yet')
    orders = result.mappings().all()
    return orders


@router.post('/make-order', response_model=dict)
async def make_order(
    restaurant_id: int,
    date: str,
    number_of_people:int,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session),
):
    user_id = token['user_id']
    selected_date = datetime.strptime(date, "%Y-%m-%d" )

    # check_user = await session.execute(select(Reservation).where(Reservation.c.user_id == user_id))
    # if check_user.scalar():
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='You already have an order')

    restaurant_check = await session.execute(select(restaurant).where(restaurant.c.id == restaurant_id))
    if not restaurant_check.scalar():raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                                         detail="Restaurant not found."
        )
    selected_restaurant = await session.execute(select(restaurant.c.seats_left).where(restaurant.c.id == restaurant_id))
    left_seats = selected_restaurant.scalar()
    if left_seats - number_of_people <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail='No seats left')

    order_data = {
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "num_people": number_of_people,
        "reservation_time": selected_date,
        "is_active": True,
    }
    await session.execute(
        update(restaurant)
        .where(restaurant.c.id == restaurant_id)
        .values(seats_left=restaurant.c.seats_left - number_of_people)
    )
    await session.execute(insert(Reservation).values(order_data))
    await session.commit()

    return {"message": "Order created successfully", "order": order_data}


@router.delete('/delete-order', response_model=dict)
async def delete_order(
    order_id: int,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session),
):
    user_id = token['user_id']

    check_order_owner = await session.execute(select(Reservation).where(Reservation.c.user_id == user_id))
    if not check_order_owner.scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Order not found.")
    order_check = await session.execute(select(Reservation).where(Reservation.c.id == order_id))
    if not order_check.scalar():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )

    await session.execute(delete(Reservation).where(Reservation.c.id == order_id))
    await session.commit()

    return {"message": "Order deleted successfully", "order_id": order_id}


@router.get('/my-orders', response_model=List[dict])
async def get_user_orders(
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session),
):
    user_id = token['user_id']

    result = await session.execute(select(Reservation).where(Reservation.c.user_id == user_id))
    orders = result.mappings().all()
    # if not result.scalar():
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No orders found.")

    return orders
