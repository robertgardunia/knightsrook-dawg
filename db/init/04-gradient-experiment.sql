-- Gradient Experiment Tables (runtime schema — wiped by db:reset).
-- See docs/experiments/001-gradient-aversion-backprop.md for the full experiment design.
-- All observations are recorded regardless of outcome — null results must be earned.

-- Named gradient sequences: one per experimental run
CREATE TABLE IF NOT EXISTS runtime.gradient_sequences (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    status      VARCHAR(32) NOT NULL DEFAULT 'active',
    -- status values: active | complete | archived
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Individual states in a gradient sequence (the continuum)
CREATE TABLE IF NOT EXISTS runtime.gradient_states (
    id              BIGSERIAL PRIMARY KEY,
    sequence_id     BIGINT NOT NULL REFERENCES runtime.gradient_sequences(id) ON DELETE CASCADE,
    position        INTEGER NOT NULL,               -- ordinal position (0-indexed, 0=coolest)
    label           VARCHAR(255),                   -- human label: 'warm', 'hot', 'burn'
    gradient_value  FLOAT NOT NULL,                 -- scalar value on the continuum
    w_aversion      FLOAT NOT NULL DEFAULT 0.0,     -- backpropagated aversion weight
    graph_node_id   BIGINT,                         -- AGE node id once mirrored to graph (v0.2)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(sequence_id, position)
);

CREATE INDEX IF NOT EXISTS idx_gradient_states_sequence ON runtime.gradient_states(sequence_id, position);

-- Terminal aversive events: the 'burn' moment applied to an endpoint state
CREATE TABLE IF NOT EXISTS runtime.aversion_events (
    id                  BIGSERIAL PRIMARY KEY,
    state_id            BIGINT NOT NULL REFERENCES runtime.gradient_states(id),
    aversion_strength   FLOAT NOT NULL DEFAULT 1.0,
    backprop_decay      FLOAT NOT NULL DEFAULT 0.7,     -- per-hop multiplicative decay factor
    applied_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes               TEXT
);

-- Observation log: every query result, regardless of outcome.
-- This is where the experiment data lives. Do not truncate.
CREATE TABLE IF NOT EXISTS runtime.observations (
    id                  BIGSERIAL PRIMARY KEY,
    experiment          VARCHAR(255) NOT NULL,
    query_state_id      BIGINT REFERENCES runtime.gradient_states(id),
    aversion_surfaced   FLOAT,              -- w_aversion value returned by the query
    anticipation_fired  BOOLEAN,            -- did it exceed the anticipation threshold?
    threshold           FLOAT,              -- threshold used for this observation
    raw_result          JSONB,              -- full query output
    observed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes               TEXT
);

CREATE INDEX IF NOT EXISTS idx_observations_experiment ON runtime.observations(experiment);
CREATE INDEX IF NOT EXISTS idx_observations_observed   ON runtime.observations(observed_at DESC);
