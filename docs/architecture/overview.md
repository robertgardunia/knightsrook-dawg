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

### ADR-003 — Documentation as first-class artifact
**Status:** Accepted
**Context:** DAWG is a research project producing new concepts and running novel experiments. Understanding evaporates when not written down. Null results are as important as positive ones — a null result must be earned (see `project:dawg:reconstruction-gate`), and that proof must be on record.
**Decision:** Every experiment gets a design doc in `docs/experiments/` before it runs. Results are appended to that doc regardless of outcome. Concepts get their own file in `docs/concepts/` when they stabilize. Every significant architectural decision gets an ADR here. A pre-commit hook enforces that no code touching `app/subsystems/` or `db/init/` is committed without a corresponding experiment or ADR document.
**Consequences:** No experiment runs without a doc. No concept is treated as settled without a doc. More upfront writing; zero lost context across sessions.

### ADR-004 — Adaptive vector DB schema: multi-dimensional signals, no collapsed score
**Status:** Accepted
**Context:** Spec §4.3 requires retrieval to return a structured multi-signal surface, not a ranked list. Collapsing signals into a single score reintroduces the RAG pattern DAWG is designed to supersede, and discards the disagreement structure between signals — which is itself information.
**Decision:** `substrate.entries` stores individual weight signals (`w_use`, `w_provenance`, `w_impact`, `w_centrality`) as separate columns. Recency is computed on retrieval from `last_accessed` via exponential decay (half-life: 168 hours). No `score` or `rank` column exists. All retrieval endpoints surface raw signals; consumers decide how to use them.
**Consequences:** Retrieval responses are richer and require consumers to handle multi-dimensional data. Signals not yet meaningful in early milestones (`w_impact` in v0.1, `w_centrality` in v0.1) are reserved at 0.0 and documented as deferred.
