'use client';

import React, { createContext, useContext, ReactNode } from 'react'
import { useAccessibility, useKeyboardNavigation, useFocusManagement, useAnnouncer } from '@/hooks/useAccessibility'

interface AccessibilityContextType {
  preferences: {
    reduceMotion: boolean
    highContrast: boolean
    largeText: boolean
    screenReader: boolean
  }
  focusVisible: boolean
  announce: (message: string, priority?: 'polite' | 'assertive') => void
  announcements: string[]
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined)

interface AccessibilityProviderProps {
  children: ReactNode
}

export function AccessibilityProvider({ children }: AccessibilityProviderProps) {
  const preferences = useAccessibility()
  const { focusVisible } = useFocusManagement()
  const { announcements, announce } = useAnnouncer()
  
  useKeyboardNavigation()

  const value = {
    preferences,
    focusVisible,
    announce,
    announcements,
  }

  return (
    <AccessibilityContext.Provider value={value}>
      {children}
      
      {/* Screen reader announcements */}
      <div 
        role="status" 
        aria-live="polite" 
        aria-atomic="true"
        className="sr-only"
      >
        {announcements.map((announcement, index) => (
          <div key={index}>{announcement}</div>
        ))}
      </div>
      
      {/* Skip links */}
      <div className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50">
        <a 
          href="#main-content"
          className="bg-primary-600 text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          Skip to main content
        </a>
        <a 
          href="#navigation"
          className="bg-primary-600 text-white px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-primary-500 ml-2"
        >
          Skip to navigation
        </a>
      </div>
    </AccessibilityContext.Provider>
  )
}

export function useAccessibilityContext() {
  const context = useContext(AccessibilityContext)
  if (context === undefined) {
    throw new Error('useAccessibilityContext must be used within an AccessibilityProvider')
  }
  return context
}