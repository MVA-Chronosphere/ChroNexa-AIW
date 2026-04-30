import axios from 'axios'
import type { ChatRequest, ChatResponse, SpeakRequest, SpeakResponse } from '@types'

const API_BASE_URL = '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const chatService = {
  generateResponse: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/chat/generate', request)
    return response.data
  },

  /** Full pipeline: LLM → TTS → Lip Sync. Returns audio + mouth cues. */
  speak: async (request: SpeakRequest): Promise<SpeakResponse> => {
    const response = await apiClient.post<SpeakResponse>('/chat/speak', request)
    return response.data
  },

  streamResponse: async (request: ChatRequest) => {
    return apiClient.post('/chat/stream', request, {
      responseType: 'stream'
    })
  },

  getAvailableModels: async () => {
    const response = await apiClient.get('/chat/models')
    return response.data
  }
}

export const avatarService = {
  animateAvatar: async (animationType: string, text: string, emotion: string = 'neutral') => {
    const response = await apiClient.post('/avatar/animate', {
      animation_type: animationType,
      text,
      emotion
    })
    return response.data
  },

  generateLipSync: async (audioPath: string, text: string) => {
    const response = await apiClient.post('/avatar/lip-sync', {
      audio_path: audioPath,
      text
    })
    return response.data
  },

  getExpressions: async () => {
    const response = await apiClient.get('/avatar/expressions')
    return response.data
  },

  setEmotion: async (emotion: string) => {
    const response = await apiClient.post('/avatar/emotion', { emotion })
    return response.data
  }
}

export const knowledgeBaseService = {
  search: async (query: string, limit: number = 5) => {
    const response = await apiClient.post('/kb/search', {
      query,
      limit
    })
    return response.data
  },

  getCategories: async () => {
    const response = await apiClient.get('/kb/categories')
    return response.data
  },

  getSources: async () => {
    const response = await apiClient.get('/kb/sources')
    return response.data
  }
}

export const healthService = {
  check: async () => {
    const response = await apiClient.get('/health')
    return response.data
  },

  ready: async () => {
    const response = await apiClient.get('/ready')
    return response.data
  }
}
