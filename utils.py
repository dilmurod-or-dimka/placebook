import secrets
from datetime import datetime, timedelta
from sqlalchemy import select

from fastapi import Depends,HTTPException
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from watchfiles import awatch
from math import radians, sin, cos, sqrt, atan2

from account.models import users, restaurant_owner
from config import SECRET
from database import get_async_session

algorithm = 'HS256'
security = HTTPBearer()


def generate_token(user_id:int):
    jti_access = secrets.token_urlsafe(32)
    jti_refresh = secrets.token_urlsafe(32)

    payload_access = {
        "type": 'access',
        "user_id": user_id,
        "jti_access": jti_access,
        "exp": datetime.utcnow()+ timedelta(minutes=30),
    }

    payload_refresh = {
        'type':'refresh',
        'jti_refresh': jti_refresh,
        'user_id': user_id,
        'exp': datetime.utcnow()+ timedelta(days=1)
    }
    access_token = jwt.encode(payload_access, SECRET, algorithm=algorithm)
    refresh_token = jwt.encode(payload_refresh, SECRET, algorithm=algorithm)
    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token is expired!')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Token invalid!')


async def admin_check(admin_id,session):
    checking_admin = await session.execute(select(users).where((users.c.id == admin_id) & (users.c.is_admin == True)))
    return bool(checking_admin.scalar())


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


async def check_permissions(user_id: int, restaurant_id: int, session: AsyncSession) -> bool:
    is_admin = await admin_check(user_id, session)
    if is_admin:
        return True

    result = await session.execute(
        select(restaurant_owner.c.owner_id)
        .where(restaurant_owner.c.restaurant_id == restaurant_id)
    )
    owners = [row.owner_id for row in result.mappings()]
    return user_id in owners
