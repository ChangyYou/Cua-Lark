import { useState } from 'react'
import { useAppStore } from '../stores/appStore'
import styles from './StepPanel.module.css'

export default function StepPanel() {
  const { tasks, selectedTaskId, selectedStepIndex, selectStep } = useAppStore()
  const [expandedToolCalls, setExpandedToolCalls] = useState<Set<string>>(new Set())

  const selectedTask = tasks.find(t => t.id === selectedTaskId)

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const toggleToolCall = (stepId: string) => {
    const newSet = new Set(expandedToolCalls)
    if (newSet.has(stepId)) {
      newSet.delete(stepId)
    } else {
      newSet.add(stepId)
    }
    setExpandedToolCalls(newSet)
  }

  if (!selectedTask) {
    return (
      <div className={styles['step-panel']}>
        <div className={styles['no-task-selected']}>
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M13 3L4 14h7l-1 7 9-11h-7l1-7z"/>
          </svg>
          <p>选择左侧任务<br/>查看执行详情</p>
        </div>
      </div>
    )
  }

  if (selectedTask.steps.length === 0) {
    return (
      <div className={styles['step-panel']}>
        <div className={styles['no-steps']}>
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          <p>任务执行中...<br/>步骤数据将实时更新</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles['step-panel']}>
      {selectedTask.steps.map((step, index) => {
        const isExpanded = expandedToolCalls.has(step.id)

        return (
          <div
            key={step.id}
            className={`${styles['step-card']} ${index === selectedStepIndex ? styles['active'] : ''}`}
            onClick={() => selectStep(index)}
          >
            <div className={styles['step-header']}>
              <span className={styles['step-number']}>步骤 {step.stepNumber}</span>
              <span className={styles['step-action-type']}>{step.action || '思考'}</span>
              <span className={styles['step-time']}>{formatTime(step.timestamp)}</span>
            </div>

            <div className={styles['step-content']}>
              <div className={styles['thought-section']}>
                <div className={styles['thought-label']}>决策</div>
                <div className={styles['thought-text']}>{step.thought}</div>
              </div>

              {step.skillInfo && step.skillInfo.name && (
                <div className={`${styles['skill-badge']} ${step.skillInfo.enforced ? styles['enforced'] : ''}`}>
                  <svg viewBox="0 0 24 24" fill="currentColor" width="10" height="10">
                    <path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3z"/>
                  </svg>
                  {step.skillInfo.name}
                  {step.skillInfo.stage !== null && ` · 阶段 ${step.skillInfo.stage}`}
                </div>
              )}

              {step.skillInfo && step.skillInfo.enforced && (
                <div className={styles['enforced-info']}>
                  Skill 约束修改: {step.skillInfo.original_action} → {step.action}
                </div>
              )}

              {step.rawToolCall && (
                <div className={styles['tool-call-section']}>
                  <div
                    className={styles['tool-call-header']}
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleToolCall(step.id)
                    }}
                  >
                    <span className={styles['tool-call-title']}>
                      <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 9h-2v6h2v-6zm-4-3h2v9h2V8H5v3zm8 12h-2v-3h-2v3h-2v-3h-2v3h6v-6h2v3z"/>
                      </svg>
                      LLM 原始响应 (tool_call)
                    </span>
                    <span className={styles['tool-call-toggle']}>
                      {isExpanded ? '收起 ▲' : '展开 ▼'}
                    </span>
                  </div>
                  {isExpanded && (
                    <div className={styles['tool-call-content']}>
                      {JSON.stringify(step.rawToolCall, null, 2)}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}