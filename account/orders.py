from typing import List

from alembic.util import status
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select, delete,insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.testing.pickleable import Order

from account.models import *
from utils import get_async_session, verify_token, admin_check

router = APIRouter(tags=['Orders'])

@router.get('/orders')
async def get_orders(session:AsyncSession=Depends(get_async_session),
                     token:dict=Depends(verify_token)
        ):
    user_id = token['user_id']
    is_admin = admin_check(user_id)
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_401_NOT_FOUND)

    result = await session.execute(select(Reservation))
    result_item = result.mappings().all()
    return result_item
