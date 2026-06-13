from fastapi import status, HTTPException, Depends
from fastapi.security.oauth2 import OAuth2PasswordBearer
from ..core.database import get_db

from sqlalchemy.orm import Session

import jwt
from jwt.exceptions import InvalidTokenError
from datetime import timedelta, datetime, timezone

from ..schemas.user import TokenPayload
from ..models.user import User, UserType

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)

def create_token(payload: TokenPayload, expire, token_type: str):

    expiry_time = datetime.now(timezone.utc) + expire

    to_encode = payload.model_dump()
    to_encode["sub"] = str(to_encode["sub"])
    to_encode.update({
        "type": token_type,
        "exp": expiry_time
    })

    encoded_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_token

def create_access_token(payload: TokenPayload):
    return create_token(payload, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")

def create_refresh_token(payload: TokenPayload):
    return create_token(payload, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")

def verify_token(token: str, token_type: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            raise credentials_exception
        
        payload["sub"] = int(payload["sub"])
        token_data = TokenPayload(**payload)
    except InvalidTokenError:
        raise credentials_exception
    
    return token_data

def refresh_access_token(refresh_token: str):
    token_data = verify_token(refresh_token, "refresh")
    return create_access_token(token_data)

def get_current_user(access_token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token_data = verify_token(access_token, "access")

    current_user = db.query(User).filter(User.id == token_data.sub).first()
    if not current_user:
        raise credentials_exception
    
    return current_user

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            detail="Not enough permissions",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    return current_user

def get_optional_current_user(access_token: str | None = Depends(optional_oauth2_scheme), db: Session = Depends(get_db)):
    if not access_token:
        return None

    try:
        token_data = verify_token(access_token, "access")
        current_user = db.query(User).filter(User.id == token_data.sub).first()
        return current_user
    except:
        return None

def get_optional_current_admin(current_user: User | None = Depends(get_optional_current_user)):
    if current_user and current_user.user_type == UserType.ADMIN:
        return current_user
    return None