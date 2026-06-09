-- v0.1: Adaptive Vector DB — substrate.entries with multi-dimensional weight signals.
-- Retrieval returns a multi-signal surface; no single collapsed score is stored here.
-- See docs/architecture/overview.md ADR-004.

-- Entries: the persistent adaptive memory store
CREATE TABLE IF NOT EXISTS substrate.entries (
    id              BIGSERIAL PRIMARY KEY,
    key             VARCHAR(512) NOT NULL UNIQUE,
    content         TEXT NOT NULL,
    embedding       vector(1536),               -- NULL until embedded (v0.2+)

    -- Recency: computed on retrieval as exponential decay from last_accessed.
    -- Not stored as a float — the timestamp IS the signal; staleness is derived.
    last_accessed   TIMESTAMPTZ,

    -- Weight signal: use — raw access count; never decays
    w_use           INTEGER NOT NULL DEFAULT 0,

    -- Weight signal: provenance — 0.0=incidentally captured, 1.0=deliberately entered
    w_provenance    FLOAT NOT NULL DEFAULT 0.5,

    -- Reserved signals (columns present; values 0.0 until populated in later milestones)
    w_impact        FLOAT NOT NULL DEFAULT 0.0,     -- v0.3: consequence of past retrievals
    w_centrality    FLOAT NOT NULL DEFAULT 0.0,     -- v0.2: graph topology measure

    -- Monotonic version counter — incremented on every update; foundation for v0.4 rollback
    version         INTEGER NOT NULL DEFAULT 1,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta            JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_entries_key         ON substrate.entries(key);
CREATE INDEX IF NOT EXISTS idx_entries_w_use       ON substrate.entries(w_use DESC);
CREATE INDEX IF NOT EXISTS idx_entries_created_at  ON substrate.entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_entries_last_access ON substrate.entries(last_accessed DESC NULLS LAST);

-- Event log: every operation on every entry, in order, forever.
-- This is the data trail. Do not truncate this table.
-- event_type values: created | accessed | weight_updated | impact_signal | rollback
CREATE TABLE IF NOT EXISTS substrate.entry_events (
    id          BIGSERIAL PRIMARY KEY,
    entry_id    BIGINT NOT NULL REFERENCES substrate.entries(id) ON DELETE CASCADE,
    event_type  VARCHAR(64) NOT NULL,
    payload     JSONB NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entry_events_entry_id ON substrate.entry_events(entry_id);
CREATE INDEX IF NOT EXISTS idx_entry_events_type     ON substrate.entry_events(event_type);
CREATE INDEX IF NOT EXISTS idx_entry_events_occurred ON substrate.entry_events(occurred_at DESC);
