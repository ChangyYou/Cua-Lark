import { useRef, useEffect, KeyboardEvent } from 'react'
import styles from './InputBox.module.css'

interface InputBoxProps {
  onExecute: (command: string) => void
  disabled?: boolean
  inputText: string
  onInputChange: (text: string) => void
}

const exampleCommands = [
  '帮我给张三发送消息：明天开会',
  '打开飞书搜索',
  '帮我预约一个视频会议'
]

export default function InputBox({ onExecute, disabled, inputText, onInputChange }: InputBoxProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [inputText])

  const handleSend = () => {
    const trimmed = inputText.trim()
    if (!trimmed || disabled) return
    onExecute(trimmed)
    onInputChange('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={styles['input-box']}>
      <div className={styles['input-wrapper']}>
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={e => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入指令，让 Agent 帮你操控飞书..."
          disabled={disabled}
          rows={1}
        />
        <button
          className={styles['send-button']}
          onClick={handleSend}
          disabled={disabled || !inputText.trim()}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
          </svg>
        </button>
      </div>

      {!disabled && (
        <>
          <p className={styles['hint']}>按 Enter 发送，Shift + Enter 换行</p>
          <div className={styles['examples']}>
            {exampleCommands.map((cmd, i) => (
              <button
                key={i}
                className={styles['example-btn']}
                onClick={() => onInputChange(cmd)}
              >
                {cmd}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}