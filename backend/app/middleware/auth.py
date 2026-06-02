from fastapi import Request, HTTPException
from app.config import settings


async def require_api_key(request: Request) -> None:
    if not settings.API_KEY:
        return
    key = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not key:
        key = request.query_params.get("api_key", "")
    if key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
