from datetime import timedelta, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

import waqd

from waqd.base.system import RuntimeSystem
from waqd.ui.web2.templates import base_template, render_main, sub_template
from waqd.ui.web2.authentication import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    PermissionChecker,
    Token,
    User,
    UserInDB,
    authenticate_user,
    create_access_token,
    get_db,
    get_current_user_with_exception,
    get_current_user_plain,
)

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/login", response_class=HTMLResponse)
async def login(current_user: Annotated[User, Depends(get_current_user_plain)]):
    if current_user:
        return RedirectResponse(url="/weather")
    content = sub_template(
        "login.html",
        {},
        current_path,
    )
    return render_main(content, current_user, menu=False)


@rt.get("/logout", response_class=HTMLResponse)
async def logout():
    content = sub_template(
        "login.html",
        {},
        current_path,
    )
    toast = sub_template(
        "toast_logout_success.html",
        {},
        current_path,
        component=True,
    )
    response = render_main(content, None, toast=toast)
    response.delete_cookie(
        "Authorization",
        samesite="lax",
        # samesite="none",
        # secure=True, # disable for the time being
    )
    return response


@rt.get("/toast/login_failed", response_class=HTMLResponse)
async def toast(id: str):
    return sub_template(
        "toast_login_failed.html",
        {"id": id},
        current_path / "components",
    )


@rt.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request
):
    user = authenticate_user(get_db(), form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response = JSONResponse(
        {"access_token": access_token, "token_type": "bearer"},
        status_code=status.HTTP_200_OK,
    )
    set_access_token_cookie(response, user.username, access_token)
    return response


@rt.get("/keepalive", response_class=JSONResponse)
async def keepalive(current_user: Annotated[User, Depends(get_current_user_with_exception)]):
    if current_user.token_expires - datetime.now() > timedelta(minutes=11):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": current_user.username}, expires_delta=access_token_expires
        )
        response = JSONResponse(
            {"access_token": access_token, "token_type": "bearer"},
            status_code=status.HTTP_200_OK,
        )
        set_access_token_cookie(response, current_user.username, access_token)
        return response


def set_access_token_cookie(
    response: JSONResponse, username: str, access_token: str, expires_seconds=3600
):
    if not access_token:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
    response.set_cookie(
        key="Authorization",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=expires_seconds,
        expires=expires_seconds,
        samesite="lax",  # disable for the time being
        # samesite="none",
        # secure=True,
    )
    return response


@rt.get("/about", response_class=HTMLResponse)
async def about(current_user: Annotated[User, Depends(get_current_user_plain)]):
    content = sub_template(
        "about.html",
        {"version": waqd.__version__, "platform": RuntimeSystem().platform},
        current_path,
    )
    return render_main(content, current_user)
