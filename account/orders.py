from pyexpat.errors import messages
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete, insert, update, Nullable
from sqlalchemy.ext.asyncio import AsyncSession

from account.bot import send_to_telegram
from account.models import Reservation, users, restaurant
from database import get_async_session
from scheme import OrderInput
from utils import verify_token, admin_check

router = APIRouter(tags=['Orders'])


@router.get('/orders')
async def get_orders(
        session: AsyncSession = Depends(get_async_session),
        token: dict = Depends(verify_token),
):
    user_id = token['user_id']
    check_admin = await admin_check(user_id, session)  # Assuming admin_check is async
    if not check_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You do not have permission to perform this action.")

    result = await session.execute(select(Reservation))
    orders = result.mappings().all()  # Get the list of orders

    if not orders:  # Check if orders list is empty
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='You do not have orders yet')

    return orders


@router.post('/make-order', response_model=dict)
async def make_order(
    order_data: OrderInput,
    token: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_async_session),
):
    user_id = token['user_id']
    first_name = await session.execute(select(users.c.firstname).where(users.c.id == user_id))
    last_name = await session.execute(select(users.c.lastname).where(users.c.id == user_id))
    frname = first_name.scalar()
    ltname = last_name.scalar()

    # Validate the restaurant
    restaurant_check = await session.execute(select(restaurant).where(restaurant.c.id == order_data.restaurant_id))
    if not restaurant_check.scalar():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found."
        )

    chatid = await session.execute(select(restaurant).where(order_data.restaurant_id == restaurant.c.id))
    chat_id = chatid.mappings().all()
    for chat in chat_id:
        phone = chat.phone_number
        date = order_data.reservation_time
        guests = order_data.number_of_people
        chatt_id = chat.chat_id
    send_to_telegram(frname, ltname, phone, date, guests,chatt_id)

    selected_restaurant = await session.execute(
        select(restaurant.c.seats_left).where(restaurant.c.id == order_data.restaurant_id)
    )
    left_seats = selected_restaurant.scalar()
    if left_seats - order_data.number_of_people <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No seats left")

    order_values = {
        "user_id": user_id,
        "restaurant_id": order_data.restaurant_id,
        "num_people": order_data.number_of_people,
        "reservation_time": order_data.reservation_time,
        "is_active": True,
    }

    # Update restaurant seats
    await session.execute(
        update(restaurant)
        .where(restaurant.c.id == order_data.restaurant_id)
        .values(seats_left=restaurant.c.seats_left - order_data.number_of_people)
    )

    # Insert the reservation
    await session.execute(insert(Reservation).values(order_values))
    await session.commit()

    return {"message": "Order created successfully", "order": order_values}


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
