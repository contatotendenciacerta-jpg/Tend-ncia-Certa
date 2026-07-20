import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import AccessToken, LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=UserRole.SUBSCRIBER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado") from exc
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    invalid_credentials = HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")

    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise invalid_credentials
    if user.status != UserStatus.ACTIVE:
        raise invalid_credentials

    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=AccessToken)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessToken:
    invalid_token = HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token inválido")

    try:
        token_payload = decode_token(payload.refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise invalid_token from exc

    try:
        user_id = uuid.UUID(token_payload["sub"])
    except (KeyError, ValueError) as exc:
        raise invalid_token from exc

    user = db.get(User, user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise invalid_token

    return AccessToken(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
