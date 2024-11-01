from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from account.models import users
from database import get_async_session

router = APIRouter(tags=['admin'])


@router.get('/get-all-users')
async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(users))
    usrs = result.mappings().all()
    return usrs