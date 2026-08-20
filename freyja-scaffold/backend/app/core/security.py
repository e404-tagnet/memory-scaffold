from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> int:
    """Resolve user_id from Bearer header or cookie session."""
    token = None

    # 1. Bearer header
    if credentials:
        token = credentials.credentials
    # 2. Cookie fallback
    else:
        token = request.cookies.get(settings.session_cookie_name)

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return int(user_id)


class OllamaClient:
    """Async client for Ollama chat completions."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool = True,
        temperature: float = 0.7,
    ):
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature},
        }
        async with httpx.AsyncClient(timeout=None) as client:
            if stream:
                async with client.stream("POST", url, json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        yield line
            else:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                yield resp.text
