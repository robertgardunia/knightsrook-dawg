import time
from fastapi import APIRouter, Depends
from app.db import get_pool
from app.middleware.auth import require_api_key

router = APIRouter(dependencies=[Depends(require_api_key)])
_start = time.time()


@router.get("/health")
async def health():
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok", "db": "ok", "uptime": round(time.time() - _start, 1)}
