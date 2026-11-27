


import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.db.session import get_db
from app.db.repositories import user_repository
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email address.",
        )

    return normalized


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    email = normalize_email(user_data.email)

    if user_repository.get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    try:
        user = user_repository.create_user(
            db,
            {
                "email": email,
                "hashed_password": hash_password(user_data.password),
                "is_active": True,
            },
        )
        return user

    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain an access token",
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    email = normalize_email(login_data.email)

    user = user_repository.get_user_by_email(db, email)

    if (
        user is None
        or not verify_password(login_data.password, user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    access_token = create_access_token(user.id)

    return TokenResponse(access_token=access_token)