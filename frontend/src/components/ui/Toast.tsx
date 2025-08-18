'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon, 
  InformationCircleIcon,
  XMarkIcon 
} from '@heroicons/react/24/outline';

interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearAllToasts: () => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? (toast.persistent ? undefined : 5000),
    };

    setToasts(prev => [...prev, newToast]);

    // Auto-remove toast after duration (if not persistent)
    if (newToast.duration) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, clearAllToasts }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (context === undefined) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
  if (toasts.length === 0) return null;

  return (
    <div 
      className="fixed top-4 right-4 z-50 space-y-2" 
      aria-live="polite" 
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const getToastStyles = (type: Toast['type']) => {
    const styles = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800',
    };
    return styles[type];
  };

  const getIcon = (type: Toast['type']) => {
    const iconProps = { className: 'h-5 w-5 flex-shrink-0' };
    
    switch (type) {
      case 'success':
        return <CheckCircleIcon {...iconProps} className="h-5 w-5 text-green-400" />;
      case 'error':
        return <XCircleIcon {...iconProps} className="h-5 w-5 text-red-400" />;
      case 'warning':
        return <ExclamationTriangleIcon {...iconProps} className="h-5 w-5 text-yellow-400" />;
      case 'info':
        return <InformationCircleIcon {...iconProps} className="h-5 w-5 text-blue-400" />;
    }
  };

  return (
    <div
      className={`
        max-w-sm w-full border rounded-lg shadow-lg p-4 
        transform transition-all duration-300 ease-in-out
        animate-slide-up
        ${getToastStyles(toast.type)}
      `}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getIcon(toast.type)}
        </div>
        <div className="ml-3 w-0 flex-1">
          <p className="text-sm font-medium">
            {toast.title}
          </p>
          {toast.message && (
            <p className="mt-1 text-sm opacity-90">
              {toast.message}
            </p>
          )}
        </div>
        <div className="ml-4 flex-shrink-0 flex">
          <button
            className="inline-flex rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            onClick={() => onRemove(toast.id)}
            aria-label="Close notification"
          >
            <XMarkIcon className="h-5 w-5 opacity-60 hover:opacity-100 transition-opacity" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper hook for common toast patterns
export function useToastHelpers() {
  const { addToast } = useToast();

  return {
    success: (title: string, message?: string) => 
      addToast({ type: 'success', title, message }),
    
    error: (title: string, message?: string) => 
      addToast({ type: 'error', title, message, persistent: true }),
    
    warning: (title: string, message?: string) => 
      addToast({ type: 'warning', title, message }),
    
    info: (title: string, message?: string) => 
      addToast({ type: 'info', title, message }),
  };
}