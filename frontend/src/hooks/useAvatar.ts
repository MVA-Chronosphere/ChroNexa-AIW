import { useEffect, useRef } from 'react'
import { IndianDoctorAvatar } from '@services/avatar'

export const useAvatar = (containerRef: React.RefObject<HTMLDivElement>) => {
  const avatarRef = useRef<IndianDoctorAvatar | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Small delay to ensure container is properly laid out in the DOM
    const timeoutId = setTimeout(() => {
      try {
        if (containerRef.current && !avatarRef.current) {
          avatarRef.current = new IndianDoctorAvatar(containerRef.current)
          console.log('✅ Avatar initialized successfully')
        }
      } catch (error) {
        console.error('❌ Failed to initialize avatar:', error)
      }
    }, 100)

    return () => {
      clearTimeout(timeoutId)
      if (avatarRef.current) {
        avatarRef.current.dispose()
        avatarRef.current = null
      }
    }
  }, [containerRef])

  return avatarRef
}
