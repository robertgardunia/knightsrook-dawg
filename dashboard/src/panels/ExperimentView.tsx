import { useCallback, useEffect, useState } from 'react'
import Panel from '../components/Panel'
import {
  applyAversion,
  fetchObservations,
  fetchSequence,
  fetchSequenceList,
  probeState,
  type GradientSequence,
  type Observation,
  type SequenceSummary,
} from '../lib/api'

// ── Color scale: dark → amber → red based on w_aversion ─────────────────────

function hexToRgb(hex: string): [number, number, number] {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)]
}

function lerp(a: string, b: string, t: number): string {
  const [ar, ag, ab] = hexToRgb(a)
  const [br, bg, bb] = hexToRgb(b)
  return `rgb(${Math.round(ar + (br - ar) * t)},${Math.round(ag + (bg - ag) * t)},${Math.round(ab + (bb - ab) * t)})`
}

function aversionColor(v: number): string {
  if (v <= 0.001) return '#2a2a2a'
  if (v >= 0.999) return '#ef4444'
  if (v < 0.3) return lerp('#2a2a2a', '#b45309', v / 0.3)
  return lerp('#b45309', '#ef4444', (v - 0.3) / 0.7)
}

// ── SVG gradient visualization ──────────────────────────────────────────────

const VW = 900
const VH = 150
const PAD = 50
const R = 18
const NODE_Y = 60

function GradientViz({ seq }: { seq: GradientSequence }) {
  const states = seq.states
  const drawW = VW - PAD * 2

  const nx = (gv: number) => PAD + gv * drawW

  return (
    <svg
      viewBox={`0 0 ${VW} ${VH}`}
      style={{ width: '100%', display: 'block', marginBottom: 8 }}
    >
      {/* Axis line */}
      <line x1={PAD - 10} y1={NODE_Y} x2={VW - PAD + 10} y2={NODE_Y}
        stroke="#1e1e1e" strokeWidth={1} />

      {/* PRECEDES edges */}
      {states.slice(0, -1).map((s, i) => {
        const x1 = nx(s.gradient_value) + R + 2
        const x2 = nx(states[i + 1].gradient_value) - R - 2
        const y = NODE_Y
        return (
          <g key={`e${i}`}>
            <line x1={x1} y1={y} x2={x2 - 5} y2={y}
              stroke="#333" strokeWidth={1.5} />
            <polygon points={`${x2},${y} ${x2 - 7},${y - 3.5} ${x2 - 7},${y + 3.5}`}
              fill="#333" />
          </g>
        )
      })}

      {/* Nodes */}
      {states.map((s) => {
        const x = nx(s.gradient_value)
        const isTerminal = s.position === states.length - 1
        const fill = aversionColor(s.w_aversion)
        const textFill = s.w_aversion > 0.15 ? '#fff' : '#888'

        return (
          <g key={s.id}>
            {/* Node circle */}
            <circle cx={x} cy={NODE_Y} r={R}
              fill={fill}
              stroke={isTerminal ? '#ef4444' : '#3a3a3a'}
              strokeWidth={isTerminal ? 2.5 : 1} />

            {/* w_aversion inside node if non-zero */}
            {s.w_aversion > 0.001 && (
              <text x={x} y={NODE_Y + 3.5} textAnchor="middle"
                fill={textFill} fontSize={8} fontFamily="monospace" fontWeight="bold">
                {s.w_aversion.toFixed(2)}
              </text>
            )}

            {/* Anticipation indicator */}
            {s.w_aversion > 0.1 && !isTerminal && (
              <circle cx={x + R - 4} cy={NODE_Y - R + 4} r={4}
                fill="#22c55e" />
            )}

            {/* Label below */}
            <text x={x} y={NODE_Y + R + 13} textAnchor="middle"
              fill="#666" fontSize={9} fontFamily="monospace">
              {s.label ?? `s${s.position}`}
            </text>

            {/* Gradient value */}
            <text x={x} y={NODE_Y + R + 24} textAnchor="middle"
              fill="#444" fontSize={8} fontFamily="monospace">
              g={s.gradient_value.toFixed(1)}
            </text>
          </g>
        )
      })}

      {/* Legend */}
      <text x={PAD} y={VH - 4} fill="#333" fontSize={7.5} fontFamily="monospace">
        fill = w_aversion (dark=0 → amber → red=1) · ● green dot = anticipation fired (w&gt;0.1) · ⬤ red border = terminal
      </text>
    </svg>
  )
}

// ── Observation table ────────────────────────────────────────────────────────

function ObsTable({ obs, states }: { obs: Observation[]; states: GradientSequence['states'] }) {
  const stateMap = Object.fromEntries(states.map(s => [s.id, s]))
  const recent = [...obs].reverse().slice(0, 30)

  return (
    <div style={{ flex: 1, overflowY: 'auto' }}>
      <div style={{ color: '#444', fontSize: 9, letterSpacing: 1, textTransform: 'uppercase', marginBottom: 4 }}>
        observations ({obs.length} total)
      </div>
      <table style={{ width: '100%', fontSize: 10, borderCollapse: 'collapse', fontFamily: 'monospace' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #2a2a2a', color: '#555' }}>
            <th style={{ textAlign: 'left', padding: '2px 6px' }}>state</th>
            <th style={{ textAlign: 'right', padding: '2px 6px' }}>w_aversion</th>
            <th style={{ textAlign: 'center', padding: '2px 6px' }}>fired</th>
            <th style={{ textAlign: 'right', padding: '2px 6px' }}>threshold</th>
            <th style={{ textAlign: 'right', padding: '2px 6px' }}>time</th>
          </tr>
        </thead>
        <tbody>
          {recent.map((o) => {
            const state = o.query_state_id != null ? stateMap[o.query_state_id] : null
            const fired = o.anticipation_fired
            return (
              <tr key={o.id} style={{ borderBottom: '1px solid #1e1e1e' }}>
                <td style={{ padding: '2px 6px', color: '#9cdcfe' }}>
                  {state ? `${state.label ?? `s${state.position}`} (pos ${state.position})` : '—'}
                </td>
                <td style={{ padding: '2px 6px', textAlign: 'right',
                  color: aversionColor(o.aversion_surfaced ?? 0) === '#2a2a2a' ? '#555' : aversionColor(o.aversion_surfaced ?? 0) }}>
                  {o.aversion_surfaced?.toFixed(4) ?? '—'}
                </td>
                <td style={{ padding: '2px 6px', textAlign: 'center',
                  color: fired ? '#22c55e' : '#444', fontWeight: fired ? 'bold' : 'normal' }}>
                  {fired == null ? '—' : fired ? '✓' : '–'}
                </td>
                <td style={{ padding: '2px 6px', textAlign: 'right', color: '#555' }}>
                  {o.threshold?.toFixed(2) ?? '—'}
                </td>
                <td style={{ padding: '2px 6px', textAlign: 'right', color: '#555' }}>
                  {new Date(o.observed_at).toLocaleTimeString()}
                </td>
              </tr>
            )
          })}
          {obs.length === 0 && (
            <tr><td colSpan={5} style={{ padding: 6, color: '#333' }}>no observations yet — run probe all</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

// ── Button style ──────────────────────────────────────────────────────────────

const btn = (extra?: object): React.CSSProperties => ({
  background: '#1e3a5f',
  color: '#9cdcfe',
  border: 'none',
  padding: '4px 10px',
  cursor: 'pointer',
  fontSize: 10,
  fontFamily: 'monospace',
  ...extra,
})

// ── Main panel ────────────────────────────────────────────────────────────────

export default function ExperimentView() {
  const [seqList, setSeqList] = useState<SequenceSummary[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [seq, setSeq] = useState<GradientSequence | null>(null)
  const [obs, setObs] = useState<Observation[]>([])
  const [probing, setProbing] = useState(false)
  const [burning, setBurning] = useState(false)

  const reload = useCallback((id: number) => {
    fetchSequence(id).then(setSeq).catch(() => {})
    fetchObservations(id).then(setObs).catch(() => {})
  }, [])

  // Load sequence list
  useEffect(() => {
    fetchSequenceList()
      .then(list => {
        setSeqList(list)
        if (list.length > 0) setSelectedId(list[0].id)
      })
      .catch(() => {})
  }, [])

  // Poll selected sequence
  useEffect(() => {
    if (!selectedId) return
    reload(selectedId)
    const id = setInterval(() => reload(selectedId), 4000)
    return () => clearInterval(id)
  }, [selectedId, reload])

  const handleProbeAll = async () => {
    if (!seq || probing) return
    setProbing(true)
    for (const s of seq.states) {
      await probeState(seq.id, s.id, 0.1).catch(() => {})
    }
    reload(seq.id)
    setProbing(false)
  }

  const handleBurnTerminal = async () => {
    if (!seq || burning || seq.states.length === 0) return
    const terminal = seq.states[seq.states.length - 1]
    setBurning(true)
    await applyAversion(seq.id, terminal.id, 1.0, 0.7).catch(() => {})
    reload(seq.id)
    setBurning(false)
  }

  return (
    <Panel title="Experiment 001 — Gradient Aversion Backpropagation">
      {/* Controls */}
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 10, flexWrap: 'wrap' }}>
        <select
          value={selectedId ?? ''}
          onChange={e => setSelectedId(Number(e.target.value))}
          style={{ background: '#1a1a1a', border: '1px solid #2a2a2a', color: '#eee', padding: '3px 6px', fontSize: 10, fontFamily: 'monospace' }}
        >
          {seqList.length === 0 && <option value="">no sequences</option>}
          {seqList.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        <button onClick={handleProbeAll} disabled={probing || !seq} style={btn()}>
          {probing ? '…probing' : 'probe all'}
        </button>

        <button onClick={handleBurnTerminal} disabled={burning || !seq} style={btn({ background: '#3a1a1a', color: '#fca5a5' })}>
          {burning ? '…' : 'burn terminal'}
        </button>

        {seq && (
          <span style={{ color: '#444', fontSize: 9, fontFamily: 'monospace', marginLeft: 'auto' }}>
            {seq.states.length} states · {seq.name}
          </span>
        )}

        {!seq && selectedId && (
          <span style={{ color: '#555', fontSize: 9, fontFamily: 'monospace' }}>
            no sequences — create one via POST /api/experiment/sequences
          </span>
        )}
      </div>

      {/* Gradient viz */}
      {seq && seq.states.length > 0
        ? <GradientViz seq={seq} />
        : (
          <div style={{ color: '#333', fontSize: 10, fontFamily: 'monospace', padding: '16px 0', textAlign: 'center' }}>
            waiting for sequence data…
          </div>
        )
      }

      {/* Observations */}
      {seq && <ObsTable obs={obs} states={seq.states} />}
    </Panel>
  )
}
