export interface Step {
  id: string
  stepNumber: number
  thought: string
  action: string | null
  actionReason: string | null
  screenshotUrl: string | null
  timestamp: number
  // 扩展信息
  rawToolCall: object | null  // LLM 原始 tool_call 响应
  skillInfo: {
    name: string | null
    stage: number | null
    enforced: boolean  // 是否被 skill 约束修改过
    originalAction: string | null
  } | null
}

export interface Task {
  id: string
  command: string
  steps: Step[]
  status: 'running' | 'completed' | 'failed'
  createdAt: number
  completedAt: number | null
  skillActivated: string | null  // 激活的技能名称
}

export interface AppState {
  tasks: Task[]
  selectedTaskId: string | null
  selectedStepIndex: number

  addTask: (command: string, skillName?: string | null) => Task
  addStepToTask: (taskId: string, step: Omit<Step, 'id' | 'stepNumber' | 'timestamp'>) => void
  updateTaskStatus: (taskId: string, status: Task['status']) => void
  selectTask: (taskId: string) => void
  selectStep: (index: number) => void
  setInputText: (text: string) => void
  inputText: string
}