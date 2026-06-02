import { useEffect, useState } from 'react'
import { fetchTopics } from '../lib/api'
import Panel from '../components/Panel'

interface Topic { key: string; value: string; created_at: string }

export default function StateInspector() {
  const [topics, setTopics] = useState<Topic[]>([])

  useEffect(() => {
    const load = () => fetchTopics().then(setTopics).catch(() => {})
    load()
    const id = setInterval(load, 5000)
    return () => clearInterval(id)
  }, [])

  return (
    <Panel title="State Inspector">
      <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #2a2a2a', color: '#666' }}>
            <th style={{ textAlign: 'left', padding: '4px 6px' }}>key</th>
            <th style={{ textAlign: 'left', padding: '4px 6px' }}>value</th>
          </tr>
        </thead>
        <tbody>
          {topics.length === 0 && (
            <tr><td colSpan={2} style={{ padding: 4, color: '#444' }}>no topics</td></tr>
          )}
          {topics.map((t, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #1e1e1e' }}>
              <td style={{ padding: '3px 6px', color: '#9cdcfe' }}>{t.key}</td>
              <td style={{ padding: '3px 6px', color: '#ce9178' }}>{t.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  )
}
