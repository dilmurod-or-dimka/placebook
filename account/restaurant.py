from fastapi import APIRouter,Depends,status,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.unitofwork import DeleteAll

from account.models import users, restaurant
from database import get_async_session
from utils import verify_token

router = APIRouter(tags=['restaurant'])


@router.get('/get-all-restaurants')
async def get_all_restaurants(session: AsyncSession = Depends(get_async_session),
                              token: dict = Depends(verify_token)
        ):
   user_id = token.get('user_id')
   check_admin = await session.execute(select(users).where((users.c.id == user_id) & (users.c.is_admin == True)))
   if not check_admin.scalar():
       raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
   result = await session.execute(select(restaurant))
   restaurants = result.mappings().all()
   return list(restaurants)




