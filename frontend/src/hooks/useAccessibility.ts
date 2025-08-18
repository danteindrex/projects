import { useEffect, useState } from 'react'

interface AccessibilityPreferences {
  reduceMotion: boolean
  highContrast: boolean
  largeText: boolean
  screenReader: boolean
}

export function useAccessibility() {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>({
    reduceMotion: false,
    highContrast: false,
    largeText: false,
    screenReader: false,
  })

  useEffect(() => {
    // Check for prefers-reduced-motion
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPreferences(prev => ({ ...prev, reduceMotion: reducedMotion.matches }))

    // Check for prefers-contrast
    const highContrast = window.matchMedia('(prefers-contrast: high)')
    setPreferences(prev => ({ ...prev, highContrast: highContrast.matches }))

    // Check for large text preference
    const largeText = window.matchMedia('(min-resolution: 2dppx)')
    setPreferences(prev => ({ ...prev, largeText: largeText.matches }))

    // Check for screen reader
    const screenReader = window.navigator?.userAgent?.includes('NVDA') || 
                        window.navigator?.userAgent?.includes('JAWS') ||
                        window.speechSynthesis !== undefined

    setPreferences(prev => ({ ...prev, screenReader: !!screenReader }))

    // Listen for changes
    const handleReducedMotionChange = () => {
      setPreferences(prev => ({ ...prev, reduceMotion: reducedMotion.matches }))
    }

    const handleContrastChange = () => {
      setPreferences(prev => ({ ...prev, highContrast: highContrast.matches }))
    }

    reducedMotion.addListener(handleReducedMotionChange)
    highContrast.addListener(handleContrastChange)

    return () => {
      reducedMotion.removeListener(handleReducedMotionChange)
      highContrast.removeListener(handleContrastChange)
    }
  }, [])

  return preferences
}

export function useKeyboardNavigation() {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip to main content (Alt+M)
      if (event.altKey && event.key === 'm') {
        event.preventDefault()
        const main = document.querySelector('main')
        if (main) {
          main.focus()
          main.scrollIntoView()
        }
      }

      // Skip to navigation (Alt+N) 
      if (event.altKey && event.key === 'n') {
        event.preventDefault()
        const nav = document.querySelector('nav')
        if (nav) {
          nav.focus()
          nav.scrollIntoView()
        }
      }

      // Escape key to close modals/dropdowns
      if (event.key === 'Escape') {
        const activeElement = document.activeElement as HTMLElement
        if (activeElement?.getAttribute('role') === 'dialog') {
          activeElement.blur()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])
}

export function useFocusManagement() {
  const [focusVisible, setFocusVisible] = useState(false)

  useEffect(() => {
    const handleFocus = () => setFocusVisible(true)
    const handleBlur = () => setFocusVisible(false)
    const handleMouseDown = () => setFocusVisible(false)

    document.addEventListener('focusin', handleFocus)
    document.addEventListener('focusout', handleBlur)
    document.addEventListener('mousedown', handleMouseDown)

    return () => {
      document.removeEventListener('focusin', handleFocus)
      document.removeEventListener('focusout', handleBlur)
      document.removeEventListener('mousedown', handleMouseDown)
    }
  }, [])

  return { focusVisible }
}

export function useAnnouncer() {
  const [announcements, setAnnouncements] = useState<string[]>([])

  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    setAnnouncements(prev => [...prev, message])
    
    // Remove announcement after it's been read
    setTimeout(() => {
      setAnnouncements(prev => prev.filter(msg => msg !== message))
    }, 1000)
  }

  return { announcements, announce }
}