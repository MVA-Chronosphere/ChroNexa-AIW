import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

console.log('[main.tsx] Script loaded at', new Date().toISOString())
console.log('[main.tsx] Finding root element...')

const rootElement = document.getElementById('root')
console.log('[main.tsx] Root element:', rootElement ? 'FOUND' : 'NOT FOUND')

if (!rootElement) {
  console.error('[main.tsx] FATAL: Root element is null')
  throw new Error('Root element not found')
}

try {
  console.log('[main.tsx] Creating React root...')
  const root = ReactDOM.createRoot(rootElement)
  
  console.log('[main.tsx] Rendering App...')
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  )
  console.log('[main.tsx] Render called successfully')
} catch (error) {
  console.error('[main.tsx] ERROR:', error)
  if (rootElement) {
    rootElement.innerHTML = '<div style="color:red;padding:20px;"><h1>Error</h1><p>' + String(error) + '</p></div>'
  }
}
