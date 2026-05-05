export interface StepResponse {
  thought: string
  action: string | null
  action_reason: string | null
  screenshot_base64: string | null
  done: boolean
  error?: string
  // 扩展字段
  raw_tool_call?: object | null
  skill_info?: {
    name: string | null
    stage: number | null
    enforced: boolean
    original_action: string | null
  } | null
}

export interface StreamEvent {
  type: 'step' | 'done' | 'error'
  data: StepResponse | string
}

export async function* executeCommandStream(command: string) {
  const response = await fetch('/api/v1/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ command }),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  if (!reader) throw new Error('No response body')

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed.startsWith('data: ')) continue

      try {
        const event = JSON.parse(trimmed.slice(6)) as StreamEvent
        yield event
      } catch (e) {
        console.warn('Failed to parse event:', trimmed.slice(0, 100))
      }
    }
  }

  if (buffer.trim()) {
    const trimmed = buffer.trim()
    if (trimmed.startsWith('data: ')) {
      try {
        const event = JSON.parse(trimmed.slice(6)) as StreamEvent
        yield event
      } catch (e) {
        console.warn('Failed to parse final event:', trimmed.slice(0, 100))
      }
    }
  }
}