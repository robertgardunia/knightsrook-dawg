import EventStream from './panels/EventStream'
import StateInspector from './panels/StateInspector'
import ManualProbe from './panels/ManualProbe'

export default function App() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', height: '100vh', gap: 1, background: '#0a0a0a' }}>
      <EventStream />
      <StateInspector />
      <ManualProbe />
    </div>
  )
}
