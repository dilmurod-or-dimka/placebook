import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from sqlalchemy import select

from fastapi import Depends,HTTPException
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from watchfiles import awatch
from math import radians, sin, cos, sqrt, atan2
from celery import Celery

from account.models import users, restaurant_owner
from config import SECRET, MAIL_USERNAME, MAIL_PORT, MAIL_SERVER,MAIL_PASSWORD, MAIL_FROM
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




def get_email_template_dashboard(user_email, code):
    email = EmailMessage()
    email['Subject'] = f'Verify email'
    email['From'] = MAIL_USERNAME
    email['To'] = user_email

    email.set_content(
        f"""
        <div>
            <h1 style="color: black;"> Hi!😊 </h1>
            <h1 style="color: black;">Enter the verification code below to activate your account: </h1>
            <h1 style="margin: 0; padding-right: 2px; width: 90px ; background-color: green; color: white;"> {code} </h1>
        </div>
        """,
        subtype='html'
    )
    return email

async def send_mail_for_forget_password(email: str, code: int):
    email = get_email_template_dashboard(email, code)
    with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT) as server:
        server.login(MAIL_FROM, MAIL_PASSWORD)
        server.send_message(email)


