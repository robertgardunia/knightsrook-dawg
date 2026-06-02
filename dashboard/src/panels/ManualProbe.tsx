import { useState } from 'react'
import Panel from '../components/Panel'

export default function ManualProbe() {
  const [key, setKey] = useState('')
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const probe = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api/topics?key=${encodeURIComponent(key)}`)
      const data = await res.json()
      setResult(JSON.stringify(data, null, 2))
    } catch (e) {
      setResult(String(e))
    }
    setLoading(false)
  }

  return (
    <Panel title="Manual Probe">
      <div style={{ display: 'flex', gap: 6, marginBottom: 8 }}>
        <input
          value={key}
          onChange={e => setKey(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && probe()}
          placeholder="topic key…"
          style={{
            flex: 1,
            background: '#1a1a1a',
            border: '1px solid #2a2a2a',
            color: '#eee',
            padding: '4px 8px',
            fontFamily: 'monospace',
            fontSize: 11,
          }}
        />
        <button
          onClick={probe}
          disabled={loading}
          style={{ background: '#1e3a5f', color: '#9cdcfe', border: 'none', padding: '4px 12px', cursor: 'pointer', fontSize: 11 }}
        >
          {loading ? '…' : 'probe'}
        </button>
      </div>
      {result && (
        <pre style={{ fontSize: 11, overflowY: 'auto', flex: 1, margin: 0, color: '#ce9178', whiteSpace: 'pre-wrap' }}>
          {result}
        </pre>
      )}
    </Panel>
  )
}
