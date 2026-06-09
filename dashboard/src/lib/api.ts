export interface Topic { key: string; value: string; created_at: string }

export async function fetchTopics(): Promise<Topic[]> {
  const res = await fetch('/api/topics')
  const data = await res.json()
  return data.data ?? []
}

// ── Experiment API ─────────────────────────────────────────────────────────────

export interface GradientState {
  id: number
  position: number
  label: string
  gradient_value: number
  w_aversion: number
  graph_node_id: number | null
}

export interface GradientSequence {
  id: number
  name: string
  description: string
  status: string
  created_at: string
  states: GradientState[]
}

export interface SequenceSummary {
  id: number
  name: string
  status: string
}

export interface Observation {
  id: number
  query_state_id: number | null
  aversion_surfaced: number | null
  anticipation_fired: boolean | null
  threshold: number | null
  raw_result: Record<string, unknown> | null
  observed_at: string
  notes: string | null
}

export async function fetchSequenceList(): Promise<SequenceSummary[]> {
  const res = await fetch('/api/experiment/sequences')
  const data = await res.json()
  return data.data ?? []
}

export async function fetchSequence(id: number): Promise<GradientSequence> {
  const res = await fetch(`/api/experiment/sequences/${id}`)
  const data = await res.json()
  return data.data
}

export async function fetchObservations(sequenceId: number): Promise<Observation[]> {
  const res = await fetch(`/api/experiment/sequences/${sequenceId}/observations`)
  const data = await res.json()
  return data.data ?? []
}

export async function probeState(
  sequenceId: number,
  stateId: number,
  threshold = 0.1,
): Promise<unknown> {
  const res = await fetch(`/api/experiment/sequences/${sequenceId}/probe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state_id: stateId, threshold }),
  })
  return res.json()
}

export async function applyAversion(
  sequenceId: number,
  stateId: number,
  strength = 1.0,
  decay = 0.7,
): Promise<unknown> {
  const res = await fetch(`/api/experiment/sequences/${sequenceId}/aversion`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state_id: stateId, strength, decay }),
  })
  return res.json()
}
