# knightsrook-dawg — Architecture Overview

## Purpose

Reconstructive memory substrate — where understanding persists and content is regenerated, not the reverse.

## Services

| Service | Tech | Port | Responsibility |
|---------|------|------|----------------|
| backend | FastAPI (Python 3.12) | 8000 | API, event bus, WebSocket stream |
| dashboard | React+Vite | 5311 (dev) / 80 (prod) | Observability — event stream, state inspector, manual probe |
| db | Postgres 16 + pgvector + AGE | 5432 | Vector storage + property graph |

## Data Model

Two schemas:
- **substrate** — persistent reference data; survives `db:reset`
- **runtime** — ephemeral working state; dropped and recreated between experiments

AGE graph named `graph` lives alongside relational tables. Every connection runs `LOAD 'age'; SET search_path = ag_catalog, "$user", public` on connect (wired into asyncpg pool `init`).

## Key Flows

_To be documented as subsystems are built._

## Architecture Decision Records

### ADR-001 — substrate/runtime schema separation
**Status:** Accepted
**Context:** Experiments need a clean wipe boundary — erase working state without destroying reference data.
**Decision:** Two Postgres schemas. `runtime` is dropped/recreated by `db:reset`. `substrate` is never touched by reset scripts.
**Consequences:** All tables must be schema-qualified. New tables require a conscious decision about which side of the boundary they belong on.

### ADR-002 — Per-connection AGE bootstrap
**Status:** Accepted
**Context:** Apache AGE requires `LOAD 'age'` and `SET search_path = ag_catalog` on every connection or Cypher queries fail with cryptic errors.
**Decision:** Wire both calls into asyncpg's pool `init` parameter so it's automatic and cannot be forgotten.
**Consequences:** All connections pay a small overhead per acquire. Non-negotiable for correctness.
