from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import current_user_id, create_access_token
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.user import UserService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead)
async def signup(data: UserCreate, session: AsyncSession = Depends(get_db)):
    svc = UserService(session)
    try:
        user = await svc.create_user(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@router.post("/login")
async def login(
    data: UserLogin,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    svc = UserService(session)
    user = await svc.authenticate(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    response.set_cookie(
        key="freyja_session",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )
    return {"ok": True, "tier": user.tier.value, "age_verified": user.age_verified}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("freyja_session")
    return {"ok": True}


@router.get("/me", response_model=UserRead)
async def me(user_id: int = Depends(current_user_id), session: AsyncSession = Depends(get_db)):
    svc = UserService(session)
    user = await svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
