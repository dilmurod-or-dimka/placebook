import secrets
from datetime import datetime, timedelta

from fastapi import Depends,HTTPException
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import SECRET

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
