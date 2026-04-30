import React, { useState, useRef } from 'react'

// Oculus visemes (matching HeadAudio output + our GLB morph targets)
const VISEME_LABELS: Record<string, string> = {
  viseme_sil: 'sil (Rest)',
  viseme_PP: 'PP (M/B/P)',
  viseme_aa: 'aa (Ah)',
  viseme_E: 'E (Eh)',
  viseme_I: 'I (Ee)',
  viseme_O: 'O (Oh)',
  viseme_U: 'U (Oo)',
  viseme_FF: 'FF (F/V)',
  viseme_TH: 'TH (Th)',
  viseme_DD: 'DD (T/D)',
  viseme_kk: 'kk (K/G)',
  viseme_SS: 'SS (S/Z)',
  viseme_nn: 'nn (N)',
  viseme_RR: 'RR (R/L)',
  viseme_CH: 'CH (Ch/J)',
}

const AvatarContainer = () => {
  const [isLoaded, setIsLoaded] = useState(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  const sendToAvatar = (msg: Record<string, unknown>) => {
    iframeRef.current?.contentWindow?.postMessage(msg, '*')
  }

  const testViseme = (v: string) => sendToAvatar({ type: 'testViseme', viseme: v, weight: 1.0 })

  const playDemo = () => sendToAvatar({ type: 'testLipSync' })

  const playHello = () => {
    sendToAvatar({
      type: 'lipSync',
      mouthCues: [
        { start: 0.0, end: 0.08, value: 'X' },
        { start: 0.08, end: 0.20, value: 'H' },
        { start: 0.20, end: 0.35, value: 'C' },
        { start: 0.35, end: 0.50, value: 'H' },
        { start: 0.50, end: 0.70, value: 'E' },
        { start: 0.70, end: 0.85, value: 'X' },
      ],
    })
  }

  const playCycle = () => {
    const letters = ['X', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'X']
    sendToAvatar({
      type: 'lipSync',
      mouthCues: letters.map((v, i) => ({ start: i * 0.4, end: (i + 1) * 0.4, value: v })),
    })
  }

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

      {/* Lip Sync Test Controls — remove after integration */}
      {isLoaded && (
        <div style={{
          padding: '10px', background: 'rgba(0,0,0,0.75)', borderRadius: '0 0 12px 12px',
          display: 'flex', flexDirection: 'column', gap: '6px',
          position: 'absolute', bottom: 0, left: 0, right: 0, zIndex: 100,
        }}>
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {Object.entries(VISEME_LABELS).map(([k, label]) => (
              <button key={k} onClick={() => testViseme(k)}
                style={{ padding: '4px 10px', border: 'none', borderRadius: '4px', background: '#4361ee', color: '#fff', cursor: 'pointer', fontSize: '12px' }}>
                {label}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button onClick={playDemo} style={{ padding: '4px 12px', border: 'none', borderRadius: '4px', background: '#2d6a4f', color: '#fff', cursor: 'pointer', fontSize: '12px' }}>
              Demo Sequence
            </button>
            <button onClick={playHello} style={{ padding: '4px 12px', border: 'none', borderRadius: '4px', background: '#2d6a4f', color: '#fff', cursor: 'pointer', fontSize: '12px' }}>
              "Hello"
            </button>
            <button onClick={playCycle} style={{ padding: '4px 12px', border: 'none', borderRadius: '4px', background: '#2d6a4f', color: '#fff', cursor: 'pointer', fontSize: '12px' }}>
              Cycle All
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default AvatarContainer
