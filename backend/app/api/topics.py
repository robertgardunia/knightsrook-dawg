from fastapi import APIRouter, Depends
from app.db import get_pool
from app.middleware.auth import require_api_key

router = APIRouter(prefix="/api/topics", dependencies=[Depends(require_api_key)])


@router.get("")
async def list_topics():
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM runtime.topics ORDER BY created_at DESC")
    return {"success": True, "data": [dict(r) for r in rows]}


@router.post("")
async def create_topic(body: dict):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO runtime.topics (key, value) VALUES ($1, $2) RETURNING *",
            body.get("key"),
            body.get("value"),
        )
    return {"success": True, "data": dict(row)}
