from http.client import HTTPException
from pyexpat.errors import messages

from alembic.util import status
from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.functions import current_user

from account.models import users
from database import get_async_session
from utils import verify_token, admin_check

router = APIRouter(tags=['admin'])


@router.get('/get-all-users')
async def get_all_users(
        token:dict= Depends(verify_token),
        session: AsyncSession = Depends(get_async_session)):
    current_user_id = token.get('user_id')
    is_admin = admin_check(current_user_id)
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
    is_admin = admin_check(current_user_id)
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)

    user_check  = await session.execute(select(users).where(users.c.id == user_id))
    if not user_check.scalar():
        raise HTTPException(status_code=status.HTTP_401_NOT_FOUND)

    try:
        delet_user = await session.execute(delete(users).where(users.c.id == user_id))
        await session.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        return {"message": str(e)}