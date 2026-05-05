import { useAppStore } from '../stores/appStore'
import { executeCommandStream } from '../api/agent'
import TaskList from '../components/TaskList'
import StepPanel from '../components/StepPanel'
import ScreenshotPanel from '../components/ScreenshotPanel'
import InputBox from '../components/InputBox'
import '../styles/main-layout.css'

export default function MainLayout() {
  const {
    tasks,
    addTask,
    addStepToTask,
    updateTaskStatus,
    selectedTaskId,
    inputText,
    setInputText,
  } = useAppStore()

  const isRunning = tasks.some(t => t.status === 'running')
  const selectedTask = tasks.find(t => t.id === selectedTaskId)
  const currentStep = selectedTask?.steps.length || 0

  const handleExecute = async (command: string) => {
    if (isRunning) return

    const task = addTask(command, null)

    try {
      for await (const event of executeCommandStream(command)) {
        if (event.type === 'step') {
          const data = event.data as {
            thought: string
            action: string | null
            action_reason: string | null
            screenshot_base64: string | null
            raw_tool_call?: object | null
            skill_info?: {
              name: string | null
              stage: number | null
              enforced: boolean
              original_action: string | null
            } | null
          }
          addStepToTask(task.id, {
            thought: data.thought,
            action: data.action,
            actionReason: data.action_reason,
            screenshotUrl: data.screenshot_base64
              ? `data:image/png;base64,${data.screenshot_base64}`
              : null,
            rawToolCall: data.raw_tool_call || null,
            skillInfo: data.skill_info || null,
          })
        } else if (event.type === 'done') {
          updateTaskStatus(task.id, 'completed')
          break
        } else if (event.type === 'error') {
          updateTaskStatus(task.id, 'failed')
          break
        }
      }
    } catch (error) {
      console.error('Execution error:', error)
      updateTaskStatus(task.id, 'failed')
    }
  }

  return (
    <div className="main-layout">
      <header className="main-header">
        <h1>CUA-Lark Agent</h1>
        <div className="header-center">
          {selectedTask && (
            <div className="progress-badge">
              步骤 {currentStep}/{selectedTask.steps.length || '-'}
            </div>
          )}
        </div>
        <div className="header-status">
          <span className={`status-dot ${isRunning ? 'running' : ''}`} />
          <span>{isRunning ? '执行中...' : '等待指令'}</span>
        </div>
      </header>

      <main className="main-content">
        <TaskList />
        <StepPanel />
        <ScreenshotPanel />
      </main>

      <div className="input-area">
        <InputBox
          onExecute={handleExecute}
          disabled={isRunning}
          inputText={inputText}
          onInputChange={setInputText}
        />
      </div>
    </div>
  )
}