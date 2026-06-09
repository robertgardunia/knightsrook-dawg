import EventStream from './panels/EventStream'
import StateInspector from './panels/StateInspector'
import ManualProbe from './panels/ManualProbe'
import ExperimentView from './panels/ExperimentView'

export default function App() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr',
      gridTemplateRows: '1fr 2fr',
      height: '100vh',
      gap: 1,
      background: '#0a0a0a',
    }}>
      <EventStream />
      <StateInspector />
      <ManualProbe />
      <div style={{ gridColumn: '1 / -1' }}>
        <ExperimentView />
      </div>
    </div>
  )
}
