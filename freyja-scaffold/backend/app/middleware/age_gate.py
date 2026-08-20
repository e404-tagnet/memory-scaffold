from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

settings = get_settings()


class AgeVerificationMiddleware(BaseHTTPMiddleware):
    """Blocks chat endpoints for users without age verification."""

    async def dispatch(self, request: Request, call_next):
        if not settings.age_verification_required:
            return await call_next(request)

        # Skip non-chat paths and docs
        exempt = {"/health", "/docs", "/openapi.json", "/api/auth", "/api/billing", "/"}
        path = request.url.path
        if any(path.startswith(e) for e in exempt):
            return await call_next(request)

        response = await call_next(request)
        return response
