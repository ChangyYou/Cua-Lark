import { useState } from 'react'
import { useAppStore } from '../stores/appStore'
import styles from './ScreenshotPanel.module.css'

export default function ScreenshotPanel() {
  const { tasks, selectedTaskId, selectedStepIndex, selectStep } = useAppStore()
  const [viewMode, setViewMode] = useState<'current' | 'list'>('current')

  const selectedTask = tasks.find(t => t.id === selectedTaskId)
  const screenshots = selectedTask?.steps.filter(s => s.screenshotUrl) || []
  const currentScreenshot = selectedTask?.steps[selectedStepIndex]?.screenshotUrl

  if (!selectedTask) {
    return (
      <div className={styles['screenshot-panel']}>
        <div className={styles['screenshot-header']}>截图</div>
        <div className={styles['screenshot-placeholder']}>
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
          </svg>
          <p>选择任务后<br/>查看对应截图</p>
        </div>
      </div>
    )
  }

  if (screenshots.length === 0) {
    return (
      <div className={styles['screenshot-panel']}>
        <div className={styles['screenshot-header']}>截图</div>
        <div className={styles['screenshot-placeholder']}>
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
          </svg>
          <p>暂无截图<br/>执行中的任务将显示截图</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles['screenshot-panel']}>
      <div className={styles['screenshot-header']}>
        <span>截图 <span className={styles['screenshot-count']}>{screenshots.length}</span></span>
        <div className={styles['view-toggle']}>
          <button
            className={`${styles['view-toggle-btn']} ${viewMode === 'current' ? styles['active'] : ''}`}
            onClick={() => setViewMode('current')}
          >
            当前
          </button>
          <button
            className={`${styles['view-toggle-btn']} ${viewMode === 'list' ? styles['active'] : ''}`}
            onClick={() => setViewMode('list')}
          >
            历史 ({screenshots.length})
          </button>
        </div>
      </div>

      {viewMode === 'current' ? (
        <div className={styles['screenshot-container']}>
          {currentScreenshot ? (
            <div className={styles['screenshot-wrapper']}>
              <img src={currentScreenshot} alt="当前截图" />
            </div>
          ) : (
            <div className={styles['screenshot-placeholder']}>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
              </svg>
              <p>当前步骤暂无截图</p>
            </div>
          )}
        </div>
      ) : (
        <div className={styles['screenshot-list']}>
          {screenshots.map((step) => {
            const stepIndex = selectedTask.steps.findIndex(s => s.id === step.id)
            return (
              <div
                key={step.id}
                className={`${styles['screenshot-thumbnail']} ${stepIndex === selectedStepIndex ? styles['active'] : ''}`}
                onClick={() => selectStep(stepIndex)}
              >
                <img src={step.screenshotUrl!} alt={`步骤 ${step.stepNumber}`} />
                <div className={styles['step-label']}>步骤 {step.stepNumber}</div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}