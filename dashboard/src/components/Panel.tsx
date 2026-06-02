import type { ReactNode } from 'react'

export default function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', background: '#161616', overflow: 'hidden' }}>
      <div style={{
        padding: '8px 12px',
        background: '#1e1e1e',
        borderBottom: '1px solid #2a2a2a',
        fontSize: 11,
        color: '#666',
        letterSpacing: 2,
        textTransform: 'uppercase',
      }}>
        {title}
      </div>
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', padding: 8 }}>
        {children}
      </div>
    </div>
  )
}
