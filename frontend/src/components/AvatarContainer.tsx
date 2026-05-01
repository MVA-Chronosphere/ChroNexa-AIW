import React, { useState, useRef } from 'react'

const AvatarContainer = () => {
  const [isLoaded, setIsLoaded] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '500px', position: 'relative' }}>
      <iframe
        ref={iframeRef}
        src="/avatar-view.html"
        onLoad={() => { setIsLoaded(true); console.log('[AvatarContainer] iframe loaded'); }}
        onError={() => console.error('[AvatarContainer] iframe error')}
        style={{
          width: '100%',
          height: '100%',
          minHeight: '500px',
          border: 'none',
          borderRadius: '12px',
          display: 'block',
        }}
        title="Avatar"
      />
      {!isLoaded && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: '#999' }}>
          Loading Avatar...
        </div>
      )}


    </div>
  )
}

export default AvatarContainer
