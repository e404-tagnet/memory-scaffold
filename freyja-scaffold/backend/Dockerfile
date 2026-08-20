FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir uvicorn fastapi httpx sqlalchemy[asyncio] aiosqlite \
    pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] \
    python-multipart stripe elevenlabs redis

# Copy app
COPY app/ ./app/
RUN mkdir -p /app/data /app/logs /app/static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
