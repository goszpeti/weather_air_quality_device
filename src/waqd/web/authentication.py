from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.openapi.models import OAuthFlows, OAuthFlowPassword
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

import waqd.app as base_app

from waqd.settings import USER_API_KEY, USER_DEFAULT_PW, USER_SESSION_SECRET

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    expires: datetime | None = None


class UserInDB(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    hashed_password: str
    permissions: list[str] = []


class User(UserInDB):
    token_expires: datetime


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str | None = None,
        scopes: dict | None = None,
        auto_error: bool = True,
    ):
        flows = OAuthFlows(password=OAuthFlowPassword(tokenUrl=tokenUrl))
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        header_authorization: str = request.headers.get("Authorization", "")
        cookie_authorization: str = request.cookies.get("Authorization", "")
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


def get_user_from_token(db, token: TokenData):
    if token.username in db:
        user_dict = db[token.username]
        user_dict["token_expires"] = token.expires
        return User(**user_dict)


def get_user_from_name(db, username: str):
    if username in db:
        user_dict = db[username]
        user_dict["token_expires"] = datetime.now()
        return User(**user_dict)


def authenticate_user(db, username: str, password: str):
    user = get_user_from_name(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, base_app.settings.get_string(USER_SESSION_SECRET), algorithm=ALGORITHM
    )
    return encoded_jwt

@lru_cache(maxsize=None)
def get_current_user(token):
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, base_app.settings.get_string(USER_SESSION_SECRET), algorithms=[ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(
            username=username, expires=datetime.fromtimestamp(payload.get("exp", 0))
        )
    except InvalidTokenError:
        return None
    return get_user_from_token(get_db(), token_data)


async def get_current_user_with_exception(token: Annotated[str, Depends(oauth2_scheme)]):
    if token == base_app.settings.get_string(USER_API_KEY):
        user = get_user_from_name(get_db(), "local_admin")
    else:
        user = get_current_user(token)
    if user is None:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        raise credentials_exception
    return user


async def get_current_user_with_redirect(
    request: Request, token: Annotated[str, Depends(oauth2_scheme)]
):
    for open_routes in ["/public/", "/static/"]:
        if request.url.path.startswith(open_routes):
            return None
    user = get_current_user(token)
    if user is None:
        from .main import RequiresLoginException

        raise RequiresLoginException(status.HTTP_303_SEE_OTHER)
    return user


async def get_current_user_plain(token: Annotated[str, Depends(oauth2_scheme)]):
    user = get_current_user(token)
    return user


@lru_cache(maxsize=None)
def get_db():
    return {
        "remote_user": {
            "username": "remote_user",
            "email": "johndoe@example.com",
            "hashed_password": get_password_hash(base_app.settings.get_string(USER_DEFAULT_PW)),
            "disabled": False,
            "permissions": [],
        },
        "local_admin": {
            "username": "local_admin",
            "hashed_password": get_password_hash(base_app.settings.get_string(USER_DEFAULT_PW)),
            "disabled": False,
            "permissions": ["users:admin", "users:local"],
        },
    }

class PermissionChecker:
    def __init__(self, required_permissions: list[str]) -> None:
        self.required_permissions = required_permissions

    def __call__(self, user: User = Depends(get_current_user_plain), exception=True) -> bool:
        if self.check_permissions(user):
            return True
        if exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Permissions")
        return False

    def get_permissions(self, user: User) -> list[str]:
        return user.permissions

    def check_permissions(self, user: UserInDB) -> bool:
        for r_perm in self.required_permissions:
            if r_perm not in user.permissions:
                return False
        return True

user_exception_check = Depends(get_current_user_with_exception)
user_redirect_check = Depends(get_current_user_with_redirect)
user_plain_check = Depends(get_current_user_plain)

local_check = Depends(PermissionChecker(required_permissions=["users:local"]))
admin_check = Depends(PermissionChecker(required_permissions=["users:admin"]))
