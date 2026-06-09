from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.middleware.auth import require_api_key
import app.subsystems.adaptive_store as store

router = APIRouter(prefix="/api/store", dependencies=[Depends(require_api_key)])


class EntryCreate(BaseModel):
    key: str
    content: str
    provenance: float = Field(default=0.5, ge=0.0, le=1.0)
    meta: dict = Field(default_factory=dict)


@router.post("/entries", status_code=201)
async def create_entry(body: EntryCreate):
    entry = await store.create_entry(
        key=body.key,
        content=body.content,
        provenance=body.provenance,
        meta=body.meta,
    )
    return {"success": True, "data": entry}


@router.get("/entries")
async def retrieve_entries(q: str | None = None, limit: int = 50):
    """
    Returns a multi-signal surface — not a ranked list.
    Each entry carries per-signal scores; the consumer decides how to weight them.
    """
    surface = await store.retrieve(query=q, limit=min(limit, 200))
    return {"success": True, "data": surface}


@router.get("/entries/{entry_id}")
async def get_entry(entry_id: int):
    entry = await store.get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await store.record_access(entry_id)
    return {"success": True, "data": entry}


@router.get("/entries/{entry_id}/events")
async def get_entry_events(entry_id: int):
    """Full event log for one entry — the complete data trail."""
    events = await store.get_events(entry_id)
    return {"success": True, "count": len(events), "data": events}
