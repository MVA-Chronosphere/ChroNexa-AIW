import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.test.tsx'
import './index.css'

console.log('main.test.tsx: Loading React...')

const rootElement = document.getElementById('root')
console.log('main.test.tsx: Root element:', rootElement)

if (!rootElement) {
  console.error('main.test.tsx: Root element not found!')
} else {
  console.log('main.test.tsx: Creating React root...')
  try {
    const root = ReactDOM.createRoot(rootElement)
    console.log('main.test.tsx: Rendering App...')
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    )
    console.log('main.test.tsx: App rendered successfully!')
  } catch (error) {
    console.error('main.test.tsx: Error rendering:', error)
  }
}
