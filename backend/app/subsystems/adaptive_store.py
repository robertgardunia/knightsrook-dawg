"""
Adaptive Vector DB — v0.1 skeleton.

Multi-dimensional weight signals per entry; retrieval returns a multi-signal surface,
never a collapsed single score. The consumer decides how to use the signal breakdown.

v0.1 signals:
  recency    — computed on retrieval via exponential decay from last_accessed
  use        — raw access count
  provenance — 0.0=incidentally captured, 1.0=deliberately entered

v0.2+ will add: graph co-retrieval edges, associative reinforcement, embedding similarity.
v0.3+ will add: impact tracking (consequence of past retrievals).
v0.4+ will add: drift detection, versioned snapshots, rollback.
"""
import math
from datetime import datetime, timezone
from typing import Any

from app.db import get_pool
from app.events import publish

RECENCY_HALF_LIFE_HOURS = 168.0  # recency halves every 7 days


def _recency_score(last_accessed: datetime | None, created_at: datetime) -> float:
    reference = last_accessed or created_at
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    hours = (datetime.now(timezone.utc) - reference).total_seconds() / 3600.0
    return math.exp(-math.log(2) / RECENCY_HALF_LIFE_HOURS * hours)


def _to_surface_entry(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "key": row["key"],
        "content": row["content"],
        "signals": {
            "recency": _recency_score(row["last_accessed"], row["created_at"]),
            "use": row["w_use"],
            "provenance": row["w_provenance"],
            "impact": row["w_impact"],       # 0.0 until v0.3
            "centrality": row["w_centrality"],  # 0.0 until v0.2
        },
        "version": row["version"],
        "created_at": row["created_at"].isoformat(),
        "last_accessed": row["last_accessed"].isoformat() if row["last_accessed"] else None,
        "meta": dict(row["meta"]),
    }


async def create_entry(
    key: str,
    content: str,
    provenance: float = 0.5,
    meta: dict | None = None,
) -> dict[str, Any]:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO substrate.entries (key, content, w_provenance, meta)
            VALUES ($1, $2, $3, $4)
            RETURNING *
            """,
            key, content, provenance, meta or {},
        )
        await conn.execute(
            """
            INSERT INTO substrate.entry_events (entry_id, event_type, payload)
            VALUES ($1, 'created', $2::jsonb)
            """,
            row["id"], f'{{"key": "{key}", "provenance": {provenance}}}',
        )
    await publish("store.entry.created", {"id": row["id"], "key": key})
    return _to_surface_entry(row)


async def record_access(entry_id: int) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE substrate.entries
            SET w_use = w_use + 1,
                last_accessed = NOW(),
                version = version + 1
            WHERE id = $1
            """,
            entry_id,
        )
        await conn.execute(
            """
            INSERT INTO substrate.entry_events (entry_id, event_type, payload)
            VALUES ($1, 'accessed', '{}')
            """,
            entry_id,
        )


async def retrieve(query: str | None = None, limit: int = 50) -> dict[str, Any]:
    """
    Returns a multi-signal surface — not a ranked list.

    v0.1: text-match search via ILIKE; embedding similarity deferred to v0.2.
    The consumer is responsible for deciding how to use the per-entry signal breakdown.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        if query:
            rows = await conn.fetch(
                """
                SELECT * FROM substrate.entries
                WHERE content ILIKE $1 OR key ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                f"%{query}%", limit,
            )
        else:
            rows = await conn.fetch(
                "SELECT * FROM substrate.entries ORDER BY created_at DESC LIMIT $1",
                limit,
            )

    return {
        "query": query,
        "count": len(rows),
        "surface": [_to_surface_entry(r) for r in rows],
        "retrieval_note": "v0.1: text-match only; embedding similarity deferred to v0.2",
    }


async def get_entry(entry_id: int) -> dict[str, Any] | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM substrate.entries WHERE id = $1", entry_id)
    return _to_surface_entry(row) if row else None


async def get_events(entry_id: int) -> list[dict[str, Any]]:
    """Full event log for one entry — the data trail."""
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM substrate.entry_events
            WHERE entry_id = $1
            ORDER BY occurred_at ASC
            """,
            entry_id,
        )
    return [
        {
            "id": r["id"],
            "event_type": r["event_type"],
            "payload": dict(r["payload"]),
            "occurred_at": r["occurred_at"].isoformat(),
        }
        for r in rows
    ]
