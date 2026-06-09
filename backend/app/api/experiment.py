from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.middleware.auth import require_api_key
import app.subsystems.gradient_experiment as experiment

router = APIRouter(prefix="/api/experiment", dependencies=[Depends(require_api_key)])


class GradientStateIn(BaseModel):
    label: str
    gradient_value: float = Field(ge=0.0, le=1.0)


class SequenceCreate(BaseModel):
    name: str
    description: str = ""
    states: list[GradientStateIn] = Field(min_length=2)


class AversionApply(BaseModel):
    state_id: int
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    decay: float = Field(default=0.7, ge=0.0, le=1.0)
    notes: Optional[str] = None


class ProbeRequest(BaseModel):
    state_id: int
    threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    notes: Optional[str] = None


@router.get("/sequences")
async def list_sequences():
    from app.db import get_pool
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, description, status, created_at FROM runtime.gradient_sequences ORDER BY created_at DESC"
        )
    return {"success": True, "data": [dict(r) for r in rows]}


@router.post("/sequences", status_code=201)
async def create_sequence(body: SequenceCreate):
    """
    Create a gradient sequence. States are provided in order (cool → terminal).
    Creates relational records, AGE nodes, and PRECEDES edges between adjacent states.
    """
    seq = await experiment.create_sequence(
        name=body.name,
        description=body.description,
        states=[s.model_dump() for s in body.states],
    )
    return {"success": True, "data": seq}


@router.get("/sequences/{sequence_id}")
async def get_sequence(sequence_id: int):
    seq = await experiment.get_sequence(sequence_id)
    if not seq:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return {"success": True, "data": seq}


@router.post("/sequences/{sequence_id}/aversion")
async def apply_aversion(sequence_id: int, body: AversionApply):
    """
    Apply a terminal aversive event to a state and backpropagate through
    existing PRECEDES edges. The weight flows along edges that already exist —
    no paths are hand-wired to ancestor states.
    """
    result = await experiment.apply_aversion(
        state_id=body.state_id,
        strength=body.strength,
        decay=body.decay,
        notes=body.notes,
    )
    return {"success": True, "data": result}


@router.post("/sequences/{sequence_id}/probe")
async def probe_state(sequence_id: int, body: ProbeRequest):
    """
    Probe a state: query its current w_aversion and record the observation.
    Every call is written to runtime.observations regardless of outcome.
    This is the 'approach' — test whether anticipation fires before the endpoint.
    """
    result = await experiment.probe_state(
        state_id=body.state_id,
        threshold=body.threshold,
        notes=body.notes,
    )
    return {"success": True, "data": result}


@router.get("/sequences/{sequence_id}/observations")
async def get_observations(
    sequence_id: int,
    exp: str = "001-gradient-aversion-backprop",
):
    """Full observation log for an experiment — all runs, all outcomes."""
    obs = await experiment.get_observations(experiment=exp)
    return {"success": True, "count": len(obs), "data": obs}
