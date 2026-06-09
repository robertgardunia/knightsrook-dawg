"""
Gradient Experiment subsystem — v0.2.

Creates gradient sequences in both the relational store and the AGE graph.
Applies aversion events and backpropagates aversion weight through existing
PRECEDES edges — the burn's weight flows along edges that already exist, not
along a path we hand-wire after the fact. This is the non-cheating constraint.

All observations are written to runtime.observations regardless of outcome.
Null results are kept. Nothing is deleted.

Experiment design: docs/experiments/001-gradient-aversion-backprop.md
"""
import json
from typing import Any

from app.db import get_pool
from app.events import publish


# ── AGE type conversion ──────────────────────────────────────────────────────────
# asyncpg returns agtype values as strings, ints, or floats depending on the
# AGE version and whether codecs are registered. These helpers normalise them.

def _agint(val: Any) -> int:
    if isinstance(val, int):
        return val
    return int(str(val).strip().strip('"'))


def _agfloat(val: Any) -> float:
    if isinstance(val, (int, float)):
        return float(val)
    return float(str(val).strip().strip('"'))


# ── Sequence creation ─────────────────────────────────────────────────────────────

async def create_sequence(
    name: str,
    description: str,
    states: list[dict],  # [{label, gradient_value}, ...]  ordered cool→terminal
) -> dict[str, Any]:
    """
    Creates a gradient sequence:
    1. Relational records in runtime.gradient_sequences / gradient_states
    2. One AGE node per state (GradientState label, state_id property = relational id)
    3. PRECEDES edges between adjacent states (position i → position i+1)

    Safe Cypher interpolation note: only integer / float values from our own DB
    are interpolated into Cypher strings. Never interpolate user input.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            seq = await conn.fetchrow(
                "INSERT INTO runtime.gradient_sequences (name, description) VALUES ($1, $2) RETURNING *",
                name, description,
            )
            seq_id = seq["id"]

            state_rows = []
            for i, s in enumerate(states):
                row = await conn.fetchrow(
                    """
                    INSERT INTO runtime.gradient_states
                        (sequence_id, position, label, gradient_value)
                    VALUES ($1, $2, $3, $4)
                    RETURNING *
                    """,
                    seq_id, i, s.get("label"), float(s["gradient_value"]),
                )
                state_rows.append(row)

            # Mirror each state as an AGE node; store the AGE vertex id back
            for row in state_rows:
                sid = row["id"]
                pos = row["position"]
                gval = float(row["gradient_value"])
                result = await conn.fetchrow(
                    f"""
                    SELECT (node_id)::text AS node_id
                    FROM cypher('graph', $$
                        CREATE (n:GradientState {{
                            state_id: {sid},
                            sequence_id: {seq_id},
                            position: {pos},
                            gradient_value: {gval}
                        }})
                        RETURN id(n) AS node_id
                    $$) AS (node_id agtype)
                    """,
                )
                node_id = _agint(result["node_id"])
                await conn.execute(
                    "UPDATE runtime.gradient_states SET graph_node_id = $1 WHERE id = $2",
                    node_id, sid,
                )

            # Create PRECEDES edges: i → i+1 for the whole sequence
            for i in range(len(state_rows) - 1):
                a_id = state_rows[i]["id"]
                b_id = state_rows[i + 1]["id"]
                await conn.execute(
                    f"""
                    SELECT 1 FROM cypher('graph', $$
                        MATCH (a:GradientState {{state_id: {a_id}}}),
                              (b:GradientState {{state_id: {b_id}}})
                        CREATE (a)-[:PRECEDES {{weight: 1.0}}]->(b)
                        RETURN 1
                    $$) AS (result agtype)
                    """,
                )

    await publish("experiment.sequence.created", {"sequence_id": seq_id, "name": name})
    return await get_sequence(seq_id)


# ── Aversion + backpropagation ─────────────────────────────────────────────────

async def apply_aversion(
    state_id: int,
    strength: float = 1.0,
    decay: float = 0.7,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Applies a terminal aversive event to a state then backpropagates through
    the PRECEDES edges that already exist in the AGE graph. The weight flows
    along existing edges — nothing is hand-wired to ancestor states.

    Aversion weight per ancestor = strength * (decay ^ hops).
    Uses GREATEST so a state reached by multiple paths keeps the strongest signal.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Record the event
            await conn.execute(
                """
                INSERT INTO runtime.aversion_events
                    (state_id, aversion_strength, backprop_decay, notes)
                VALUES ($1, $2, $3, $4)
                """,
                state_id, strength, decay, notes,
            )

            # Set terminal state's aversion directly
            await conn.execute(
                "UPDATE runtime.gradient_states SET w_aversion = $1 WHERE id = $2",
                strength, state_id,
            )

            # Traverse backward through PRECEDES edges from the terminal state
            ancestors = await conn.fetch(
                f"""
                SELECT
                    (anc_state_id)::text AS anc_state_id,
                    (hops)::text         AS hops
                FROM cypher('graph', $$
                    MATCH path = (anc:GradientState)-[:PRECEDES*1..100]->(term:GradientState)
                    WHERE term.state_id = {state_id}
                    RETURN anc.state_id AS anc_state_id, length(path) AS hops
                $$) AS (anc_state_id agtype, hops agtype)
                """,
            )

            backprop = {}
            for row in ancestors:
                anc_id = _agint(row["anc_state_id"])
                hops = _agint(row["hops"])
                weight = strength * (decay ** hops)
                backprop[anc_id] = weight
                await conn.execute(
                    """
                    UPDATE runtime.gradient_states
                    SET w_aversion = GREATEST(w_aversion, $1)
                    WHERE id = $2
                    """,
                    weight, anc_id,
                )

    await publish("experiment.aversion.applied", {
        "state_id": state_id,
        "strength": strength,
        "decay": decay,
        "propagated_to": len(backprop),
    })
    return {
        "terminal_state_id": state_id,
        "strength": strength,
        "decay": decay,
        "backpropagated": {str(k): round(v, 4) for k, v in sorted(backprop.items())},
    }


# ── Probing ───────────────────────────────────────────────────────────────────────

async def probe_state(
    state_id: int,
    threshold: float = 0.1,
    experiment: str = "001-gradient-aversion-backprop",
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Queries the current aversion weight for a state and records the observation.
    This is 'the approach' — does the precursor surface the aversion before the
    endpoint is reached? Every probe call is written to runtime.observations.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM runtime.gradient_states WHERE id = $1",
            state_id,
        )
        if not row:
            return {"error": f"state {state_id} not found"}

        aversion = float(row["w_aversion"])
        anticipation_fired = aversion > threshold
        raw = {
            "state_id": state_id,
            "position": row["position"],
            "label": row["label"],
            "gradient_value": float(row["gradient_value"]),
            "w_aversion": aversion,
        }

        await conn.execute(
            """
            INSERT INTO runtime.observations
                (experiment, query_state_id, aversion_surfaced,
                 anticipation_fired, threshold, raw_result, notes)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
            """,
            experiment, state_id, aversion, anticipation_fired,
            threshold, json.dumps(raw), notes,
        )

    return {
        "state_id": state_id,
        "label": row["label"],
        "position": row["position"],
        "gradient_value": float(row["gradient_value"]),
        "w_aversion": aversion,
        "anticipation_fired": anticipation_fired,
        "threshold": threshold,
    }


# ── Query helpers ──────────────────────────────────────────────────────────────

async def get_sequence(sequence_id: int) -> dict[str, Any] | None:
    pool = get_pool()
    async with pool.acquire() as conn:
        seq = await conn.fetchrow(
            "SELECT * FROM runtime.gradient_sequences WHERE id = $1", sequence_id,
        )
        if not seq:
            return None
        states = await conn.fetch(
            "SELECT * FROM runtime.gradient_states WHERE sequence_id = $1 ORDER BY position",
            sequence_id,
        )
    return {
        "id": seq["id"],
        "name": seq["name"],
        "description": seq["description"],
        "status": seq["status"],
        "created_at": seq["created_at"].isoformat(),
        "states": [
            {
                "id": s["id"],
                "position": s["position"],
                "label": s["label"],
                "gradient_value": float(s["gradient_value"]),
                "w_aversion": float(s["w_aversion"]),
                "graph_node_id": s["graph_node_id"],
            }
            for s in states
        ],
    }


async def get_observations(
    experiment: str = "001-gradient-aversion-backprop",
) -> list[dict[str, Any]]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM runtime.observations WHERE experiment = $1 ORDER BY observed_at ASC",
            experiment,
        )
    return [
        {
            "id": r["id"],
            "query_state_id": r["query_state_id"],
            "aversion_surfaced": r["aversion_surfaced"],
            "anticipation_fired": r["anticipation_fired"],
            "threshold": r["threshold"],
            "raw_result": dict(r["raw_result"]) if r["raw_result"] else None,
            "observed_at": r["observed_at"].isoformat(),
            "notes": r["notes"],
        }
        for r in rows
    ]
