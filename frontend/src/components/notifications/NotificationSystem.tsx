'use client';

import React, { useState, useEffect } from 'react';
import { 
  BellIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
  metadata?: any;
}

interface NotificationSettings {
  enabled: boolean;
  sound: boolean;
  desktop: boolean;
  types: {
    info: boolean;
    success: boolean;
    warning: boolean;
    error: boolean;
  };
}

export default function NotificationSystem() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [settings, setSettings] = useState<NotificationSettings>({
    enabled: true,
    sound: true,
    desktop: true,
    types: {
      info: true,
      success: true,
      warning: true,
      error: true
    }
  });

  useEffect(() => {
    // Initialize with some mock notifications
    const mockNotifications: Notification[] = [
      {
        id: '1',
        type: 'success',
        title: 'Integration Connected',
        message: 'Jira integration has been successfully connected and tested.',
        timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 minutes ago
        read: false
      },
      {
        id: '2',
        type: 'warning',
        title: 'High Memory Usage',
        message: 'System memory usage is approaching 80%. Consider optimization.',
        timestamp: new Date(Date.now() - 1000 * 60 * 15), // 15 minutes ago
        read: false
      },
      {
        id: '3',
        type: 'info',
        title: 'Agent Started',
        message: 'CrewAI agent "jira_specialist" has been initialized and is ready.',
        timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 minutes ago
        read: true
      }
    ];

    setNotifications(mockNotifications);
    updateUnreadCount(mockNotifications);

    // Simulate real-time notifications
    const interval = setInterval(() => {
      addRandomNotification();
    }, 10000); // Add notification every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const updateUnreadCount = (notifs: Notification[]) => {
    setUnreadCount(notifs.filter(n => !n.read).length);
  };

  const addRandomNotification = () => {
    const types: Notification['type'][] = ['info', 'success', 'warning', 'error'];
    const randomType = types[Math.floor(Math.random() * types.length)];
    
    const notificationTemplates = {
      info: [
        { title: 'System Update', message: 'Background maintenance completed successfully.' },
        { title: 'New Feature', message: 'Real-time metrics dashboard is now available.' },
        { title: 'Agent Status', message: 'All AI agents are responding normally.' }
      ],
      success: [
        { title: 'Task Completed', message: 'Data synchronization job finished successfully.' },
        { title: 'Integration Test', message: 'API connection test passed with flying colors.' },
        { title: 'Backup Complete', message: 'System backup completed successfully.' }
      ],
      warning: [
        { title: 'Performance Alert', message: 'Response time is slightly above normal.' },
        { title: 'Resource Usage', message: 'CPU usage is approaching threshold.' },
        { title: 'Connection Warning', message: 'Some integrations showing slow response.' }
      ],
      error: [
        { title: 'Connection Failed', message: 'Failed to connect to external API.' },
        { title: 'Agent Error', message: 'AI agent encountered an error and was restarted.' },
        { title: 'System Warning', message: 'Database connection timeout detected.' }
      ]
    };

    const templates = notificationTemplates[randomType];
    const template = templates[Math.floor(Math.random() * templates.length)];

    const newNotification: Notification = {
      id: Date.now().toString(),
      type: randomType,
      title: template.title,
      message: template.message,
      timestamp: new Date(),
      read: false
    };

    setNotifications(prev => [newNotification, ...prev]);
    updateUnreadCount([newNotification, ...notifications]);

    // Play notification sound if enabled
    if (settings.sound) {
      playNotificationSound();
    }

    // Show desktop notification if enabled
    if (settings.desktop && 'Notification' in window) {
      showDesktopNotification(newNotification);
    }
  };

  const playNotificationSound = () => {
    try {
      const audio = new Audio('/notification-sound.mp3'); // Would need actual sound file
      audio.volume = 0.3;
      audio.play().catch(() => {
        // Fallback: create a simple beep
        const context = new (window.AudioContext || (window as any).webkitAudioContext)();
        const oscillator = context.createOscillator();
        const gainNode = context.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(context.destination);
        
        oscillator.frequency.value = 800;
        gainNode.gain.value = 0.1;
        
        oscillator.start();
        setTimeout(() => oscillator.stop(), 200);
      });
    } catch (error) {
      console.log('Could not play notification sound');
    }
  };

  const showDesktopNotification = (notification: Notification) => {
    if (Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        tag: notification.id
      });
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          showDesktopNotification(notification);
        }
      });
    }
  };

  const markAsRead = (notificationId: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
    updateUnreadCount(notifications.map(n => n.id === notificationId ? { ...n, read: true } : n));
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const removeNotification = (notificationId: string) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId));
    updateUnreadCount(notifications.filter(n => n.id !== notificationId));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'info':
        return <InformationCircleIcon className="h-5 w-5 text-blue-600" />;
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-600" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />;
      case 'error':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-600" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-600" />;
    }
  };

  const getNotificationColor = (type: Notification['type']) => {
    switch (type) {
      case 'info':
        return 'border-blue-200 bg-blue-50';
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-neutral-200 bg-neutral-50';
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative p-2 text-neutral-600 hover:text-neutral-900 transition-colors"
      >
        <BellIcon className="h-6 w-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notifications Panel */}
      {showNotifications && (
        <div className="absolute right-0 top-12 w-96 bg-white border border-neutral-200 rounded-lg shadow-soft z-50">
          <div className="p-4 border-b border-neutral-200">
            <div className="flex items-center justify-between">
              <h3 className="font-medium text-neutral-900">Notifications</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  Mark all read
                </button>
                <button
                  onClick={clearAllNotifications}
                  className="text-sm text-neutral-500 hover:text-neutral-700"
                >
                  Clear all
                </button>
              </div>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-6 text-center text-neutral-500">
                <BellIcon className="h-12 w-12 mx-auto mb-2 text-neutral-300" />
                <p>No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-neutral-200">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-4 hover:bg-neutral-50 transition-colors ${
                      !notification.read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 mt-1">
                        {getNotificationIcon(notification.type)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-medium text-neutral-900">
                            {notification.title}
                          </h4>
                          <button
                            onClick={() => removeNotification(notification.id)}
                            className="text-neutral-400 hover:text-neutral-600"
                          >
                            <XMarkIcon className="h-4 w-4" />
                          </button>
                        </div>
                        
                        <p className="text-sm text-neutral-600 mt-1">
                          {notification.message}
                        </p>
                        
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-neutral-500">
                            {formatTimestamp(notification.timestamp)}
                          </span>
                          
                          {!notification.read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="text-xs text-primary-600 hover:text-primary-700"
                            >
                              Mark as read
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Settings */}
          <div className="p-4 border-t border-neutral-200 bg-neutral-50">
            <div className="flex items-center justify-between">
              <span className="text-sm text-neutral-600">Settings</span>
              <button
                onClick={() => setSettings(prev => ({ ...prev, enabled: !prev.enabled }))}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  settings.enabled 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-neutral-100 text-neutral-600'
                }`}
              >
                {settings.enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {showNotifications && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowNotifications(false)}
        />
      )}
    </div>
  );
}
