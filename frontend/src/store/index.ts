import { create } from 'zustand'
import type { AvatarState, ChatMessage } from '@types'

interface ChatStore {
  messages: ChatMessage[]
  isLoading: boolean
  addMessage: (message: ChatMessage) => void
  clearMessages: () => void
  setLoading: (loading: boolean) => void
}

interface AvatarStore {
  state: AvatarState
  setEmotion: (emotion: AvatarState['emotion']) => void
  setAnimating: (animating: boolean) => void
  setCurrentAnimation: (animation: string | null) => void
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  isLoading: false,
  addMessage: (message: ChatMessage) =>
    set((state) => ({
      messages: [...state.messages, message]
    })),
  clearMessages: () => set({ messages: [] }),
  setLoading: (loading: boolean) => set({ isLoading: loading })
}))

export const useAvatarStore = create<AvatarStore>((set) => ({
  state: {
    emotion: 'neutral',
    isAnimating: false,
    currentAnimation: null
  },
  setEmotion: (emotion) =>
    set((state) => ({
      state: { ...state.state, emotion }
    })),
  setAnimating: (animating) =>
    set((state) => ({
      state: { ...state.state, isAnimating: animating }
    })),
  setCurrentAnimation: (animation) =>
    set((state) => ({
      state: { ...state.state, currentAnimation: animation }
    }))
}))
