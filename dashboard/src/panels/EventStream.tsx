import { useEffect, useRef, useState } from 'react'
import { useWebSocket } from '../lib/ws'
import Panel from '../components/Panel'

export default function EventStream() {
  const [events, setEvents] = useState<string[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const { lastMessage } = useWebSocket('/ws/events')

  useEffect(() => {
    if (!lastMessage) return
    setEvents(prev => [...prev.slice(-200), lastMessage])
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [lastMessage])

  return (
    <Panel title="Event Stream">
      <div style={{ fontFamily: 'monospace', fontSize: 11, overflowY: 'auto', flex: 1 }}>
        {events.length === 0 && (
          <div style={{ color: '#444', padding: 4 }}>waiting for events…</div>
        )}
        {events.map((e, i) => (
          <div key={i} style={{ padding: '2px 0', borderBottom: '1px solid #1e1e1e', color: '#9cdcfe' }}>{e}</div>
        ))}
        <div ref={bottomRef} />
      </div>
    </Panel>
  )
}
