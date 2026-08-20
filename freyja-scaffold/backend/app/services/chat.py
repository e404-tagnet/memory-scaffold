import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Message, User
from app.core.config import get_settings

settings = get_settings()


class ChatService:
    def __init__(self, session: AsyncSession, ollama_client):
        self.session = session
        self.ollama = ollama_client

    async def get_history(self, user_id: int) -> list[dict]:
        result = await self.session.execute(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.id.asc())
        )
        rows = result.scalars().all()
        return [{"role": r.role, "content": r.content} for r in rows]

    async def get_history_limited(self, user_id: int, tier: str) -> list[dict]:
        limit = (
            settings.premium_history_limit
            if tier == "premium"
            else settings.basic_history_limit
        )
        result = await self.session.execute(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(Message.id.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]

    async def save_message(self, user_id: int, role: str, content: str, model: str | None = None):
        msg = Message(user_id=user_id, role=role, content=content, model_used=model)
        self.session.add(msg)
        await self.session.commit()

    async def stream_chat(self, user_id: int, user_message: str, tier: str):
        """Yields content chunks. Caller must handle DB save for assistant response."""
        await self.save_message(user_id, "user", user_message)

        history = await self.get_history_limited(user_id, tier)
        messages = [{"role": "system", "content": settings.system_persona}] + history
        messages.append({"role": "user", "content": user_message})

        model = settings.default_model
        if tier == "premium" and settings.premium_models:
            model = settings.premium_models[0]

        full_reply = ""
        async for line in self.ollama.chat(model=model, messages=messages):
            chunk = json.loads(line)
            piece = chunk.get("message", {}).get("content", "")
            if piece:
                full_reply += piece
                yield piece

        await self.save_message(user_id, "assistant", full_reply, model=model)
