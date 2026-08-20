from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=128)
    email: str | None = Field(None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tier: Literal["basic", "premium"]
    age_verified: bool
    verification_status: Literal["pending", "verified", "rejected"]
    created_at: datetime


class UserLogin(BaseModel):
    username: str
    password: str


class MessageBase(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1)


class MessageRead(MessageBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    model_used: str | None = None


class ChatResponse(BaseModel):
    content: str
    model: str


class CheckoutSession(BaseModel):
    tier: Literal["premium"]
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str


class TierUpgrade(BaseModel):
    tier: Literal["premium"]
