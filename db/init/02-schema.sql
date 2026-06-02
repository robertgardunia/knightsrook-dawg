-- Persistent reference data — survives db:reset
CREATE SCHEMA IF NOT EXISTS substrate;

-- Ephemeral working state — wiped between experiments
CREATE SCHEMA IF NOT EXISTS runtime;

-- Runtime: topics (current memory state, key-value)
CREATE TABLE IF NOT EXISTS runtime.topics (
    id        SERIAL PRIMARY KEY,
    key       VARCHAR(255) NOT NULL UNIQUE,
    value     TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Substrate: add persistent reference tables here as architecture develops
