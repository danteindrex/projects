'use client';

import React, { useState, useEffect } from 'react';
import { 
  BellIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';

interface Alert {
  id: string;
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  message: string;
  timestamp: string;
  dismissed?: boolean;
  component?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

interface AlertsNotificationsProps {
  className?: string;
}

export default function AlertsNotifications({ className = '' }: AlertsNotificationsProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    enableToasts: true,
    enableSounds: false,
    criticalOnly: false,
    autoHide: true
  });

  useEffect(() => {
    fetchAlerts();
    
    // Set up periodic alert checking
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAlerts = async () => {
    try {
      // TODO: Implement real API call when alerts endpoint is available
      // const response = await apiClient.getAlerts();
      // setAlerts(response.alerts || []);
      
      // For now, show empty state - no mock data
      setAlerts([]);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      setAlerts([]);
    }
  };

  const dismissAlert = (alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, dismissed: true } : alert
    ));
  };

  const dismissAllAlerts = () => {
    setAlerts(prev => prev.map(alert => ({ ...alert, dismissed: true })));
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'info':
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'info':
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      low: 'bg-gray-100 text-gray-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[severity as keyof typeof colors]}`}>
        {severity}
      </span>
    );
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const alertTime = new Date(timestamp);
    const diffMs = now.getTime() - alertTime.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return alertTime.toLocaleDateString();
  };

  const activeAlerts = alerts.filter(alert => !alert.dismissed);
  const criticalAlerts = activeAlerts.filter(alert => alert.severity === 'critical');

  return (
    <div className={`bg-white rounded-lg border border-neutral-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <BellIcon className="h-6 w-6 text-neutral-700" />
          <h3 className="text-lg font-medium text-neutral-900">Alerts & Notifications</h3>
          {activeAlerts.length > 0 && (
            <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
              {activeAlerts.length}
            </span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-neutral-500 hover:text-neutral-700 transition-colors"
            title="Alert Settings"
          >
            <Cog6ToothIcon className="h-5 w-5" />
          </button>
          
          {activeAlerts.length > 0 && (
            <button
              onClick={dismissAllAlerts}
              className="px-3 py-1 text-sm text-neutral-600 hover:text-neutral-800 transition-colors"
            >
              Dismiss All
            </button>
          )}
        </div>
      </div>

      {/* Alert Settings Panel */}
      {showSettings && (
        <div className="mb-6 p-4 bg-neutral-50 rounded-lg border border-neutral-200">
          <h4 className="text-sm font-medium text-neutral-900 mb-3">Notification Settings</h4>
          <div className="space-y-3">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.enableToasts}
                onChange={(e) => setSettings(prev => ({ ...prev, enableToasts: e.target.checked }))}
                className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-neutral-700">Enable toast notifications</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.enableSounds}
                onChange={(e) => setSettings(prev => ({ ...prev, enableSounds: e.target.checked }))}
                className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-neutral-700">Enable sound alerts</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.criticalOnly}
                onChange={(e) => setSettings(prev => ({ ...prev, criticalOnly: e.target.checked }))}
                className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-neutral-700">Show critical alerts only</span>
            </label>
            
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.autoHide}
                onChange={(e) => setSettings(prev => ({ ...prev, autoHide: e.target.checked }))}
                className="rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-neutral-700">Auto-hide resolved alerts</span>
            </label>
          </div>
        </div>
      )}

      {/* Critical Alerts Summary */}
      {criticalAlerts.length > 0 && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <XCircleIcon className="h-5 w-5 text-red-500" />
            <span className="text-sm font-medium text-red-800">
              {criticalAlerts.length} Critical Alert{criticalAlerts.length > 1 ? 's' : ''} Require Attention
            </span>
          </div>
          <p className="text-sm text-red-700 mt-1">
            Immediate action may be required to restore service functionality.
          </p>
        </div>
      )}

      {/* Alerts List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {activeAlerts.length === 0 ? (
          <div className="text-center py-8 text-neutral-500">
            <CheckCircleIcon className="h-12 w-12 mx-auto mb-4 text-green-300" />
            <p>No active alerts</p>
            <p className="text-sm">All systems are operating normally</p>
          </div>
        ) : (
          activeAlerts
            .filter(alert => !settings.criticalOnly || alert.severity === 'critical')
            .map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${getAlertColor(alert.type)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getAlertIcon(alert.type)}
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h5 className="text-sm font-medium">{alert.title}</h5>
                        {getSeverityBadge(alert.severity)}
                      </div>
                      <p className="text-sm opacity-90">{alert.message}</p>
                      <div className="flex items-center space-x-4 mt-2 text-xs opacity-75">
                        <span>{formatTimeAgo(alert.timestamp)}</span>
                        {alert.component && (
                          <span className="capitalize">Component: {alert.component}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => dismissAlert(alert.id)}
                    className="p-1 hover:bg-black hover:bg-opacity-10 rounded transition-colors"
                    title="Dismiss alert"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))
        )}
      </div>

      {/* Alert Statistics */}
      <div className="mt-6 pt-4 border-t border-neutral-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-red-600">{alerts.filter(a => a.type === 'error' && !a.dismissed).length}</p>
            <p className="text-xs text-neutral-600">Errors</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-yellow-600">{alerts.filter(a => a.type === 'warning' && !a.dismissed).length}</p>
            <p className="text-xs text-neutral-600">Warnings</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-blue-600">{alerts.filter(a => a.type === 'info' && !a.dismissed).length}</p>
            <p className="text-xs text-neutral-600">Info</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">{alerts.filter(a => a.type === 'success' && !a.dismissed).length}</p>
            <p className="text-xs text-neutral-600">Success</p>
          </div>
        </div>
      </div>

      <div className="mt-4 text-xs text-neutral-500 text-right">
        Last updated: {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
}