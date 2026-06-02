export interface Topic { key: string; value: string; created_at: string }

export async function fetchTopics(): Promise<Topic[]> {
  const res = await fetch('/api/topics')
  const data = await res.json()
  return data.data ?? []
}
