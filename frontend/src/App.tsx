import React from 'react'
import AvatarContainer from '@components/AvatarContainer'
import ChatInterface from '@components/ChatInterface'
import Settings from '@components/Settings'
import './App.css'

function App() {
  return (
    <div className="app">
      <Settings />
      <header className="app-header">
        <h1>ChroNexa - AI Avatar for Temi Robot</h1>
        <p>Interactive AI Doctor Assistant</p>
      </header>

      <main className="app-main">
        <div className="avatar-section">
          <AvatarContainer />
        </div>
        <div className="chat-section">
          <ChatInterface />
        </div>
      </main>

      <footer className="app-footer">
        <p>&copy; 2026 ChroNexa. Powered by AI Avatar Technology.</p>
      </footer>
    </div>
  )
}

export default App
