from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import current_user_id, OllamaClient
from app.schemas.user import MessageCreate
from app.services.chat import ChatService
from app.services.user import UserService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/history")
async def history(
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_db),
):
    svc = ChatService(session, OllamaClient())
    return await svc.get_history(user_id)


@router.post("/send")
async def send(
    data: MessageCreate,
    user_id: int = Depends(current_user_id),
    session: AsyncSession = Depends(get_db),
):
    user_svc = UserService(session)
    user = await user_svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Age gate
    if not user.age_verified:
        raise HTTPException(status_code=403, detail="Age verification required")

    chat_svc = ChatService(session, OllamaClient())

    async def event_stream():
        async for chunk in chat_svc.stream_chat(user_id, data.message, user.tier.value):
            yield chunk

    return StreamingResponse(event_stream(), media_type="text/plain")
