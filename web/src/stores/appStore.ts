import { create } from 'zustand'
import type { AppState, Task, Step } from './types'

const generateId = () => Math.random().toString(36).substring(2, 9)

export const useAppStore = create<AppState>((set, get) => ({
  tasks: [],
  selectedTaskId: null,
  selectedStepIndex: 0,
  inputText: '',

  addTask: (command: string, skillName: string | null = null) => {
    const task: Task = {
      id: generateId(),
      command,
      steps: [],
      status: 'running',
      createdAt: Date.now(),
      completedAt: null,
      skillActivated: skillName,
    }
    set(state => ({
      tasks: [task, ...state.tasks],
      selectedTaskId: task.id,
      selectedStepIndex: 0,
    }))
    return task
  },

  addStepToTask: (taskId: string, stepData: Omit<Step, 'id' | 'stepNumber' | 'timestamp'>) => {
    const state = get()
    const task = state.tasks.find(t => t.id === taskId)
    if (!task) return

    const newStepIndex = task.steps.length
    const newStep: Step = {
      ...stepData,
      id: generateId(),
      stepNumber: newStepIndex + 1,
      timestamp: Date.now(),
    }

    set(state => ({
      tasks: state.tasks.map(t =>
        t.id === taskId ? { ...t, steps: [...t.steps, newStep] } : t
      ),
      selectedStepIndex: newStepIndex,
    }))
  },

  updateTaskStatus: (taskId: string, status: Task['status']) => {
    set(state => ({
      tasks: state.tasks.map(t =>
        t.id === taskId
          ? { ...t, status, completedAt: status !== 'running' ? Date.now() : null }
          : t
      ),
    }))
  },

  selectTask: (taskId: string) => {
    const task = get().tasks.find(t => t.id === taskId)
    set({ selectedTaskId: taskId, selectedStepIndex: task ? task.steps.length - 1 : 0 })
  },

  selectStep: (index: number) => set({ selectedStepIndex: index }),

  setInputText: (text: string) => set({ inputText: text }),
}))