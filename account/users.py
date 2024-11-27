from typing import List

from sqlalchemy import select, insert

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import current_user

from account.models import users
from database import get_async_session
from scheme import UserInfo
from utils import verify_token

router = APIRouter(tags=['users'])


@router.get('/get_user_info',response_model=UserInfo)
async def get_user_info(
        session: AsyncSession=Depends(get_async_session),
        token: dict=Depends(verify_token)
):
    current_user_id = token['user_id']
    user_info = await session.execute(select(users).where(users.c.id == current_user_id))
    result = user_info.mappings().one_or_none()
    return result

