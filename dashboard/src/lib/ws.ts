import { useEffect, useRef, useState } from 'react'

export function useWebSocket(path: string) {
  const [lastMessage, setLastMessage] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => {
    const connect = () => {
      const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${proto}://${window.location.host}${path}`
      const ws = new WebSocket(url)
      wsRef.current = ws
      ws.onmessage = e => setLastMessage(e.data)
      ws.onclose = () => { retryRef.current = setTimeout(connect, 2000) }
    }
    connect()
    return () => {
      wsRef.current?.close()
      clearTimeout(retryRef.current)
    }
  }, [path])

  return { lastMessage }
}
