import React, { useState, useRef, useEffect } from 'react'
import { useChatStore } from '@store'
import { chatService } from '@services/api'
import type { ChatMessage } from '@types'
import './ChatInterface.css'

function ChatInterface() {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const audioRef = useRef<HTMLAudioElement>(null)
  const avatarIframeRef = useRef<HTMLIFrameElement | null>(null)
  const { messages, addMessage } = useChatStore()

  // Grab the avatar iframe so we can postMessage lip sync cues to it
  useEffect(() => {
    const iframe = document.querySelector('iframe[title="Avatar"]') as HTMLIFrameElement | null
    if (iframe) avatarIframeRef.current = iframe
  }, [])

  const sendToAvatar = (msg: Record<string, unknown>) => {
    avatarIframeRef.current?.contentWindow?.postMessage(msg, '*')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userText = input.trim()
    const userMessage: ChatMessage = {
      role: 'user',
      content: userText,
      timestamp: Date.now()
    }
    addMessage(userMessage)
    setInput('')

    setIsLoading(true)
    try {
      // Full pipeline: LLM → TTS → Lip Sync
      const result = await chatService.speak({
        text: userText,
        temperature: 0.7,
        max_tokens: 512,
      })

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: result.response_text,
        timestamp: Date.now()
      }
      addMessage(assistantMessage)

      // Play audio + animate lip sync
      await playWithLipSync(result.audio_data, result.mouth_cues)
    } catch (error) {
      console.error('[ChatInterface] Speak pipeline error:', error)
      // Fallback: try text-only generation
      try {
        const fallback = await chatService.generateResponse({
          messages: [{ role: 'user', content: userText }],
          temperature: 0.7,
          max_tokens: 512,
          use_knowledge_base: true
        })
        addMessage({ role: 'assistant', content: fallback.response, timestamp: Date.now() })
      } catch (fallbackErr) {
        console.error('[ChatInterface] Fallback also failed:', fallbackErr)
        addMessage({ role: 'assistant', content: 'Sorry, I could not process your request.', timestamp: Date.now() })
      }
    } finally {
      setIsLoading(false)
    }
  }

  const playWithLipSync = async (
    audioDataUri: string,
    mouthCues: Array<{ start: number; end: number; value: string }>
  ) => {
    if (!audioRef.current) return
    setIsPlaying(true)

    // Send audio + cues to avatar iframe.
    // HeadAudio plays audio via AudioContext — do NOT also play via <audio>
    // element or it will echo. Only use <audio> as fallback if HeadAudio fails.
    sendToAvatar({
      type: 'playAudioWithLipSync',
      audioUrl: audioDataUri,
      _mouthCues: mouthCues
    })

    console.log('[ChatInterface] Lip sync: HeadAudio primary,', mouthCues?.length || 0, 'cues as fallback')

    // Listen for audioEnded from iframe to clear isPlaying
    const onAudioEnded = (e: MessageEvent) => {
      if (e.data?.type === 'audioEnded') {
        setIsPlaying(false)
        window.removeEventListener('message', onAudioEnded)
      }
    }
    window.addEventListener('message', onAudioEnded)

    // Fallback timeout in case the message never arrives
    const lastCue = mouthCues?.[mouthCues.length - 1]
    const fallbackMs = lastCue ? lastCue.end * 1000 + 3000 : 15000
    setTimeout(() => {
      window.removeEventListener('message', onAudioEnded)
      setIsPlaying(false)
    }, fallbackMs)
  }

  return (
    <div className="chat-interface">
      <audio ref={audioRef} onEnded={() => setIsPlaying(false)} />
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        {isLoading && (
          <div className="message message-loading">
            <div className="loading-indicator">...</div>
          </div>
        )}
        {isPlaying && (
          <div className="message message-playing">
            <div className="playing-indicator">🔊 Avatar speaking...</div>
          </div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything..."
          className="chat-input"
          disabled={isLoading || isPlaying}
        />
        <button type="submit" className="chat-submit" disabled={isLoading || isPlaying}>
          {isPlaying ? 'Speaking...' : 'Send'}
        </button>
      </form>
    </div>
  )
}

export default ChatInterface
