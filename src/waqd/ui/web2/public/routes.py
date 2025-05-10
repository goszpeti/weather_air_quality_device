from datetime import timedelta
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

import waqd

from waqd.base.system import RuntimeSystem
from ..templates import render_spa, sub_template
from .authentication import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    User,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_current_user,
    get_current_user_redirect,
)

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/login", response_class=HTMLResponse)
async def login(current_user: Annotated[User, Depends(get_current_user_redirect)]):
    content = sub_template(
        "login.html",
        {},
        current_path,
    )
    return render_spa(content, current_user, menu=False)


@rt.get("/logout", response_class=HTMLResponse)
async def logout():
    content = sub_template(
        "login.html",
        {},
        current_path,
    )
    toast = sub_template(
        "toast.html",
        {},
        current_path / "components",
    )
    response = render_spa(content, None, toast=toast)
    response.delete_cookie(
        "Authorization",
        samesite="none",
        secure=True,
    )
    return response


@rt.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request
):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
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
    response.set_cookie(
        key="Authorization",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60,
        expires=60 * 60,
        # domain=".localhost",
        samesite="none",
        secure=True,
    )
    return response


@rt.get("/about", response_class=HTMLResponse)
async def about(current_user: Annotated[User, Depends(get_current_user_redirect)]):
    content = sub_template(
        "about.html",
        {"version": waqd.__version__, "platform": RuntimeSystem().platform},
        current_path,
    )
    return render_spa(content, current_user)
