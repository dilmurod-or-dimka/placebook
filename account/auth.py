import random
from fastapi import APIRouter, Depends, HTTPException,status
from pydantic import EmailStr
from sqlalchemy import select, insert,update
from sqlalchemy.ext.asyncio import AsyncSession

from account.models import *
from passlib.context import CryptContext
from scheme import LoginModel
from database import get_async_session
from utils import generate_token, send_mail_for_forget_password

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
async def login(user:LoginModel,
                session: AsyncSession = Depends(get_async_session)
        ):
    check_user = await session.execute(select(users).where(user.email == users.c.email))
    check_user_value = check_user.one_or_none()
    if check_user_value is None:
        raise HTTPException(status_code=400, detail='Email or password is not correct!')
    else:
        password_check = pwd_context.verify(user.password, check_user_value.hashed_password)
        if password_check:
            token = generate_token(check_user_value.id)
            change_activation_code = await session.execute(update(users).where(users.c.email == user.email).values(activation_code=0))
            return {'success': True, 'token': token}
        else:
            raise HTTPException(status_code=400, detail='Email or password is not correct!')





@router.get('/forget-password/{email}')
async def forget_password(
        email: str,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        user_query = select(users).where(users.c.email == email)
        user_data = await session.execute(user_query)
        user = user_data.fetchone()

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Invalid Email address")

        code = random.randint(99999, 999999)

        update_query = update(users).where(users.c.email == email).values(
            activation_code=code
        )
        await session.execute(update_query)
        await session.commit()

        await send_mail_for_forget_password(email, code)

        return {"detail": "Check your email"}
    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)


@router.post('/reset-password/{email}')
async def reset_password(
        email: str,
        code: int,
        new_password: str,
        confirm_password: str,
        session: AsyncSession = Depends(get_async_session)
):
    try:
        if new_password != confirm_password:
            raise HTTPException(detail="Passwords do not match!", status_code=status.HTTP_400_BAD_REQUEST)

        user_query = select(users).where(users.c.email == email)
        user_data = await session.execute(user_query)
        user = user_data.fetchone()

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Invalid Email address")

        acivation_code = await session.execute(select(users.c.activation_code).where(users.c.email == email))
        active_code = acivation_code.scalar()

        if active_code==0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="You have not generated code yet")

        if code == active_code:
            update_query = update(users).where(users.c.email == email).values(
                hashed_password=pwd_context.hash(new_password),
                activation_code=0
            )
            await session.execute(update_query)
            await session.commit()
            return {"detail": "Password changed successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid code")

    except Exception as e:
        raise HTTPException(detail=f'{e}', status_code=status.HTTP_400_BAD_REQUEST)
