from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Tier
from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, data: UserCreate) -> User:
        existing = await self.session.scalar(
            select(User).where(User.username == data.username)
        )
        if existing:
            raise ValueError("Username already taken")

        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        if user and verify_password(password, user.password_hash):
            return user
        return None

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def upgrade_tier(self, user_id: int, tier: Tier) -> User:
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.tier = tier
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def verify_age(self, user_id: int) -> User:
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        user.age_verified = True
        user.verification_status = "verified"
        await self.session.commit()
        await self.session.refresh(user)
        return user
