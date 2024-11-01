from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pycparser.ply.yacc import token
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.sync import update

from account.models import *
from passlib.context import CryptContext

from database import get_async_session
from utils import generate_token

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

router = APIRouter(tags=['auth'])


@router.post('/register')
async def register(
        firstname,lastname,email,phone_number,password1,password2,
        session: AsyncSession = Depends(get_async_session)
):
    if password1 == password2:

        email_exists = await session.execute(select(users).where(users.c.email == email))
        email_exists_value = email_exists.scalar()

        phone_exists = await session.execute(select(users).where(users.c.phone_number == phone_number))
        phone_exists_value = phone_exists.scalar()

        user_exists = await session.execute(select(users.c.id))
        first_user = user_exists.scalar()
        if first_user is None:
            first_user = True
        else:
            first_user = False

        if phone_exists_value is not None:
            return {'success': False, 'message': 'Phone number already exists!'}
        if email_exists_value is not None:
            return {'success': False, 'message': 'Email already exists!'}

        hash_password = pwd_context.hash(password1)
        query = insert(users).values(
            firstname=firstname,
            lastname=lastname,
            email=email,
            phone_number=phone_number,
            is_admin=first_user,
            hashed_password=hash_password
        )
        await session.execute(query)
        await session.commit()
        return {'success': True, 'message': 'Account created successfully'}
    else:
        raise HTTPException(status_code=400, detail='Passwords are not the same !')


@router.post('/login')
async def login(email,
                password,
                session: AsyncSession = Depends(get_async_session)
        ):
    check_user = await session.execute(select(users).where(email == users.c.email))
    check_user_value = check_user.one_or_none()
    if check_user_value is None:
        raise HTTPException(status_code=400, detail='Email or password is not correct!')
    else:
        password_check = pwd_context.verify(password, check_user_value.hashed_password)
        if password_check:
            token = generate_token(check_user_value.id)
            return {'success': True, 'token': token}
        else:
            raise HTTPException(status_code=400, detail='Email or password is not correct!')