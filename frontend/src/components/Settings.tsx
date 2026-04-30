import React, { useState, useEffect } from 'react'
import './Settings.css'

interface OllamaConfig {
  url: string
  model: string
}

interface SystemConfig {
  llm_provider: string
  tts_provider: string
  debug_mode: boolean
  ollama: OllamaConfig
  rhubarb: {
    path: string
    audio_sample_rate: number
  }
}

function Settings() {
  const [isOpen, setIsOpen] = useState(false)
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434')
  const [ollamaModel, setOllamaModel] = useState('neural-chat')
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')
  const [systemConfig, setSystemConfig] = useState<SystemConfig | null>(null)

  useEffect(() => {
    // Load current configuration
    loadConfiguration()
  }, [])

  const loadConfiguration = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/settings/ollama')
      const data = await response.json()
      setOllamaUrl(data.url)
      setOllamaModel(data.model)

      // Test connection
      testOllamaConnection()
    } catch (error) {
      console.error('Error loading configuration:', error)
    }
  }

  const testOllamaConnection = async () => {
    try {
      setIsLoading(true)
      setStatus('testing')
      setMessage('Testing Ollama connection...')

      const response = await fetch('http://localhost:8000/api/settings/ollama/test')
      const data = await response.json()

      if (data.status === 'success') {
        setStatus('success')
        setMessage(`✓ Connected to Ollama (${data.models?.length || 0} models available)`)
        setAvailableModels(data.models || [])
      } else {
        setStatus('error')
        setMessage(`✗ ${data.message}`)
      }
    } catch (error) {
      setStatus('error')
      setMessage(`Error: ${String(error)}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSaveConfiguration = async () => {
    try {
      setIsLoading(true)
      setStatus('testing')
      setMessage('Saving and testing configuration...')

      const response = await fetch('http://localhost:8000/api/settings/ollama', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: ollamaUrl,
          model: ollamaModel,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setMessage(`✓ Configuration saved! ${data.message}`)
        setAvailableModels(data.models || [])
      } else {
        setStatus('error')
        setMessage(`✗ ${data.detail || data.message}`)
      }
    } catch (error) {
      setStatus('error')
      setMessage(`Error: ${String(error)}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="settings-container">
      <button
        className="settings-button"
        onClick={() => setIsOpen(!isOpen)}
        title="Open Settings"
      >
        ⚙️ Settings
      </button>

      {isOpen && (
        <div className="settings-modal">
          <div className="settings-modal-content">
            <div className="settings-header">
              <h2>Configuration</h2>
              <button
                className="settings-close"
                onClick={() => setIsOpen(false)}
              >
                ✕
              </button>
            </div>

            <div className="settings-section">
              <h3>Ollama Configuration</h3>
              
              <div className="settings-field">
                <label htmlFor="ollama-url">Ollama Server URL:</label>
                <input
                  id="ollama-url"
                  type="text"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                  className="settings-input"
                  disabled={isLoading}
                />
              </div>

              <div className="settings-field">
                <label htmlFor="ollama-model">Model:</label>
                {availableModels.length > 0 ? (
                  <select
                    id="ollama-model"
                    value={ollamaModel}
                    onChange={(e) => setOllamaModel(e.target.value)}
                    className="settings-select"
                    disabled={isLoading}
                  >
                    {availableModels.map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    id="ollama-model"
                    type="text"
                    value={ollamaModel}
                    onChange={(e) => setOllamaModel(e.target.value)}
                    placeholder="neural-chat"
                    className="settings-input"
                    disabled={isLoading}
                  />
                )}
              </div>

              <div className="settings-actions">
                <button
                  onClick={testOllamaConnection}
                  className="button-secondary"
                  disabled={isLoading}
                >
                  {isLoading && status === 'testing' ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  onClick={handleSaveConfiguration}
                  className="button-primary"
                  disabled={isLoading}
                >
                  {isLoading ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>

              <div className={`settings-status ${status}`}>
                {message && (
                  <p>
                    {status === 'success' && '✓ '}
                    {status === 'error' && '✗ '}
                    {message}
                  </p>
                )}
              </div>

              {availableModels.length > 0 && (
                <div className="settings-info">
                  <p>
                    <strong>Available Models:</strong>
                  </p>
                  <ul>
                    {availableModels.map((model) => (
                      <li key={model}>{model}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="settings-section">
              <h3>Lip Sync & Audio</h3>
              <p className="settings-info-text">
                <strong>What's needed for proper lip sync:</strong>
              </p>
              <ul className="settings-requirements">
                <li>
                  <strong>Rhubarb CLI:</strong> Audio analysis tool to generate mouth shapes
                  <code>/usr/local/bin/rhubarb</code>
                </li>
                <li>
                  <strong>Model with Blend Shapes:</strong> 3D model must have morph targets for mouth
                  positions (A, E, I, O, U, etc.)
                </li>
                <li>
                  <strong>Audio Synchronization:</strong> Timing data matched with animation frames
                </li>
                <li>
                  <strong>Installation:</strong> Rhubarb needs to be installed separately on your system
                </li>
              </ul>
              <p className="settings-note">
                Current avatars may not have blend shapes. Contact support to update models with lip-sync support.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Settings
