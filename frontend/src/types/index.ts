export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: number
}

export interface ChatRequest {
  messages: ChatMessage[]
  model?: string
  temperature?: number
  max_tokens?: number
  use_knowledge_base?: boolean
}

export interface ChatResponse {
  response: string
  model: string
  tokens_used: number
  source: 'gpt' | 'ollama' | 'knowledge_base'
}

export interface AvatarState {
  emotion: 'neutral' | 'happy' | 'sad' | 'surprised' | 'angry' | 'concerned' | 'thinking'
  isAnimating: boolean
  currentAnimation: string | null
}

export interface MouthCue {
  start: number
  end: number
  value: string
}

export interface SpeakRequest {
  text: string
  model?: string
  temperature?: number
  max_tokens?: number
}

export interface SpeakResponse {
  status: string
  response_text: string
  audio_data: string
  audio_duration: number
  mouth_cues: MouthCue[]
  model: string
  tokens: number
}

export interface LipSyncData {
  audio_path: string
  mouth_shapes: string[]
  timings: number[]
  duration: number
}

export interface KBSearchResult {
  question: string
  answer: string
  source: 'strapi' | 'qa_dataset' | 'gpt'
  confidence: number
}
