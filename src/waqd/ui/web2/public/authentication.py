from typing import Annotated, Optional

from datetime import datetime, timedelta, timezone

from fastapi.responses import RedirectResponse
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param

import waqd.app as base_app
from ....settings import USER_DEFAULT_PW

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "89c9b9a1d10f4dd9bf6edc95c4add1a7ddd0d198912ce2deffcce4f571cb319f"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class PyUser(User):
    id: int
    permissions: list[str] = []


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")
        header_scheme, header_param = get_authorization_scheme_param(header_authorization)
        cookie_scheme, cookie_param = get_authorization_scheme_param(cookie_authorization)

        if header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param

        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param
        else:
            authorization = False

        if not authorization or scheme.lower() != "bearer":
            return None

        # if self.auto_error:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Not authenticated",
        #         headers={"WWW-Authenticate": "Bearer"},
        #     )
        # else:
        #     return None
        return param


oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl="/token",
    scopes={
        "me": "diagnostics about the current user",
        "bgp": "capabilities about bgp route lookup",
    },
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except InvalidTokenError:
        return None
    return get_user(fake_users_db, username=token_data.username)


async def get_current_user_api(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = get_current_user(token)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_redirect(token: Annotated[str, Depends(oauth2_scheme)]):
    user = get_current_user(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login"}
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


fake_users_db = {
    "johndoe": {
        "id": 0,
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
        "permissions": [],
    },
    "local_admin": {
        "id": 1,
        "username": "local_admin",
        "full_name": "Default Admin",
        "hashed_password": get_password_hash(base_app.settings.get_string(USER_DEFAULT_PW)),
        "disabled": False,
        "permissions": ["users:admin"],
    },
}


class PermissionChecker:
    def __init__(self, required_permissions: list[str]) -> None:
        self.required_permissions = required_permissions

    def __call__(self, user: PyUser = Depends(get_current_user)) -> bool:
        for r_perm in self.required_permissions:
            if r_perm not in user.permissions:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Permissions"
                )
        return True
