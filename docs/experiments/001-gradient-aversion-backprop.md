# Experiment 001 — Gradient Aversion Backpropagation

**Status:** Designed, not yet run
**Gate relevance:** Direct — this is the make-or-break reconstruction gate test at minimal scale
**Design authored:** 2026-06-03
**Reference:** `project:dawg:first-experiment-gradient`, `project:dawg:reconstruction-gate`

---

## Hypothesis

A terminal aversive event applied to the endpoint of a gradient sequence will, through
associative reinforcement along pre-existing graph edges, cause its aversive weight to migrate
backward onto precursor states — such that a later partial approach (querying a precursor state)
surfaces the aversion before the endpoint is reached.

**The flinch to look for is anticipation**: the system responds to the *precursor* of the bad
stimulus, having only ever been hurt at the endpoint. Nobody labeled the precursor dangerous.
The danger must have back-propagated itself.

## Why This Is the Gate Test

Binary pain (burned/not-burned) cannot be learned from. The signal arrives exactly when it is too
late to use; there is nothing to anticipate with. A gradient gives earlier, milder states for the
terminal consequence to attach backward onto. After the burn, the rising-heat precursor inherits
the aversive weight; next time, the warmth alone surfaces the burn association.

If this works: there is a root. The canopy has something real to grow from.
If this does not work after genuine effort: there is no project.

---

## The Non-Cheating Constraint

Do **not** hand-wire the backpropagation ("on burn, raise weight of previous N states"). The
gradient states are associated by sequence/co-occurrence; the burn's weight must flow along
**edges that already exist** via associative reinforcement (spec §4.5). This is simultaneously a
test of whether the graph dynamics do the work they claimed.

---

## Setup

### Gradient sequence
A sequence of N states (N ≥ 5 recommended) with scalar gradient values progressing from cool to
terminal.

Example: `[0.1, 0.3, 0.5, 0.7, 0.9, 1.0]`
Labels: `[ambient, warm, warmer, hot, very_hot, burn]`

### Graph edges (prerequisite — v0.2)
Before the aversion event runs, sequence-adjacent states must be connected by AGE graph edges.
Edge weights start uniform. Associative reinforcement propagates through them during backprop.

### Aversion event
Apply a single aversion event (strength=1.0) to the terminal state (`burn`). Do not touch any
precursor state weights directly.

### Backpropagation mechanism
Associative reinforcement propagates one hop at a time through existing edges, multiplied by a
decay factor per hop (default: 0.7). After propagation:

| State       | Position | Expected w_aversion |
|-------------|----------|---------------------|
| burn        | N        | 1.00 (direct)       |
| very_hot    | N-1      | 0.70                |
| hot         | N-2      | 0.49                |
| warmer      | N-3      | 0.34                |
| warm        | N-4      | 0.24                |
| ambient     | N-5      | 0.17                |

---

## What Constitutes a Pass

**Anticipation fires** when querying a precursor state (e.g., `hot`) returns `w_aversion`
meaningfully above baseline, **without that state having been directly touched by an aversion
event**.

Pass criteria:
- At least the 2 states immediately preceding the endpoint show elevated `w_aversion`
- The aversion gradient decreases with distance from the endpoint (closer = stronger)
- Earliest states (e.g., `ambient`) show near-zero aversion — the backprop decays to nothing

**Anticipation threshold:** `w_aversion > 0.10` for precursors within 3 hops.
**Decay gradient check:** each hop should be ~30% weaker than the previous.

---

## What Constitutes a Fail

- `w_aversion` on precursor states remains 0.0 after backpropagation
- `w_aversion` is uniform across all states (propagation did not decay)
- Precursors show elevated aversion but the decay gradient is inverted or flat

A null result must be **earned**. A weak first attempt, bad decay parameters, or an
under-specified reconstruction step does not constitute demonstrated failure. Try parameter
variation and alternative propagation strategies before concluding the approach fails.

---

## Data to Record

Every run logs to `runtime.observations`. Required fields per observation:

| Field | Value |
|-------|-------|
| `experiment` | `"001-gradient-aversion-backprop"` |
| `query_state_id` | which state was queried |
| `aversion_surfaced` | the `w_aversion` value returned |
| `anticipation_fired` | boolean (threshold applied) |
| `threshold` | threshold used for this observation |
| `raw_result` | full JSON of the query response |
| `notes` | parameter set, run number, anything unusual |

Also record:
- `runtime.aversion_events` for every burn event applied
- Snapshot of `runtime.gradient_states.w_aversion` before and after each backprop run

---

## Experiment Sequence (do not skip ahead)

1. **This experiment** — aversion backprop alone. Gate-relevant. Run this clean first.
2. **Opposing drive + emergent choice** — only after (1) passes cleanly. Add a second pull and
   watch choice emerge from the tension. Do not install during the gate test.
3. **Curiosity/experimentation** — deferred. Unlocked by the continuum but downstream of (2).

---

## Current Status

| Step | Status |
|------|--------|
| Schema designed (`runtime.gradient_states`, `runtime.observations`, etc.) | ✅ Done |
| Graph layer (v0.2 — AGE nodes + PRECEDES edges) | ✅ Done |
| Backpropagation subsystem (`gradient_experiment.apply_aversion`) | ✅ Done |
| API routes (`POST /api/experiment/sequences`, `/aversion`, `/probe`) | ✅ Done |
| First run | ⬜ Ready — rebuild Docker and run |
| Results recorded | ⬜ |
| Pass/fail determination | ⬜ |

---

## Post-Run Log

_(append entries here after each run — date, parameters, result, notes)_
