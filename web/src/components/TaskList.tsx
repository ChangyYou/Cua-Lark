import { useAppStore } from '../stores/appStore'
import styles from './TaskList.module.css'

export default function TaskList() {
  const { tasks, selectedTaskId, selectTask } = useAppStore()

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running': return '执行中'
      case 'completed': return '完成'
      case 'failed': return '失败'
      default: return status
    }
  }

  const runningCount = tasks.filter(t => t.status === 'running').length

  return (
    <div className={styles['task-list']}>
      <div className={styles['task-list-header']}>
        <span>任务历史</span>
        {tasks.length > 0 && <span className={styles['task-count']}>{tasks.length}</span>}
      </div>
      <div className={styles['task-list-content']}>
        {tasks.length === 0 ? (
          <div className={styles['empty-tasks']}>
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M13 3L4 14h7l-1 7 9-11h-7l1-7z"/>
            </svg>
            <p>暂无任务记录<br/>在下方输入指令开始</p>
          </div>
        ) : (
          tasks.map(task => (
            <div
              key={task.id}
              className={`${styles['task-item']} ${task.id === selectedTaskId ? styles['selected'] : ''}`}
              onClick={() => selectTask(task.id)}
            >
              <div className={styles['task-item-header']}>
                <span className={`${styles['task-status-dot']} ${styles[task.status]}`} />
                <span className={styles['task-status-text']}>{getStatusText(task.status)}</span>
              </div>
              <div className={styles['task-command']}>{task.command}</div>
              <div className={`${styles['task-skill']} ${task.skillActivated ? '' : styles['none']}`}>
                <svg viewBox="0 0 24 24" fill="currentColor" width="10" height="10">
                  <path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3z"/>
                </svg>
                {task.skillActivated || '通用执行'}
              </div>
              <div className={styles['task-meta']}>
                <span className={styles['task-steps-count']}>{task.steps.length} 步</span>
                <span>{formatTime(task.createdAt)}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}