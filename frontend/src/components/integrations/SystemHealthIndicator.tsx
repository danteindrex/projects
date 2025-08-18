'use client';

import React, { useEffect, useState } from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ClockIcon,
  SignalIcon,
  CpuChipIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface HealthMetric {
  name: string;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  value: string | number;
  description?: string;
  timestamp?: string;
}

interface SystemHealthProps {
  integrationId: string;
  integrationType: string;
  status: 'active' | 'error' | 'testing' | 'inactive';
  metrics?: HealthMetric[];
  lastCheck?: string;
  responseTime?: number;
}

export default function SystemHealthIndicator({
  integrationId,
  integrationType,
  status,
  metrics = [],
  lastCheck,
  responseTime
}: SystemHealthProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [realTimeData, setRealTimeData] = useState<HealthMetric[]>(metrics);

  useEffect(() => {
    // Simulate real-time updates (in production, this would be WebSocket or polling)
    const interval = setInterval(() => {
      if (status === 'active') {
        setRealTimeData(prev => 
          prev.map(metric => ({
            ...metric,
            timestamp: new Date().toISOString(),
            // Simulate small variations in values
            value: typeof metric.value === 'number' 
              ? Math.max(0, metric.value + (Math.random() - 0.5) * 5)
              : metric.value
          }))
        );
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [status]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'error': return 'text-red-600 bg-red-100';
      case 'testing': return 'text-yellow-600 bg-yellow-100';
      case 'inactive': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircleIcon className="h-4 w-4" />;
      case 'error': return <XCircleIcon className="h-4 w-4" />;
      case 'testing': return <ClockIcon className="h-4 w-4" />;
      case 'inactive': return <ExclamationTriangleIcon className="h-4 w-4" />;
      default: return <ExclamationTriangleIcon className="h-4 w-4" />;
    }
  };

  const getMetricStatusColor = (metricStatus: string) => {
    switch (metricStatus) {
      case 'healthy': return 'text-green-700 bg-green-50 border-green-200';
      case 'warning': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'critical': return 'text-red-700 bg-red-50 border-red-200';
      default: return 'text-gray-700 bg-gray-50 border-gray-200';
    }
  };

  const getMetricIcon = (metricStatus: string) => {
    switch (metricStatus) {
      case 'healthy': return <CheckCircleIcon className="h-3 w-3" />;
      case 'warning': return <ExclamationTriangleIcon className="h-3 w-3" />;
      case 'critical': return <XCircleIcon className="h-3 w-3" />;
      default: return <ClockIcon className="h-3 w-3" />;
    }
  };

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-4 hover:border-neutral-300 transition-colors">
      {/* Main Status Header */}
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          <div className={`p-1.5 rounded-full ${getStatusColor(status).split(' ')[1]}`}>
            {getStatusIcon(status)}
          </div>
          <div>
            <h4 className="font-medium text-neutral-900 capitalize">
              {integrationType.replace('_', ' ')} System
            </h4>
            <div className="flex items-center space-x-2 text-sm text-neutral-500">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${getStatusColor(status)}`}>
                {status === 'active' ? 'Online' : status === 'error' ? 'Offline' : status}
              </span>
              {responseTime && (
                <span className="flex items-center space-x-1">
                  <SignalIcon className="h-3 w-3" />
                  <span>{responseTime}ms</span>
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {status === 'active' && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-600 font-medium">Live</span>
            </div>
          )}
          <button className="text-neutral-400 hover:text-neutral-600">
            <ChartBarIcon className={`h-4 w-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* Expanded Health Metrics */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-neutral-100">
          {realTimeData.length > 0 ? (
            <div className="space-y-3">
              <h5 className="text-sm font-medium text-neutral-700 flex items-center space-x-2">
                <CpuChipIcon className="h-4 w-4" />
                <span>System Metrics</span>
              </h5>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {realTimeData.map((metric, idx) => (
                  <div 
                    key={idx}
                    className={`p-3 rounded-lg border ${getMetricStatusColor(metric.status)}`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        {getMetricIcon(metric.status)}
                        <span className="text-sm font-medium">{metric.name}</span>
                      </div>
                      <span className="text-sm font-semibold">
                        {typeof metric.value === 'number' ? metric.value.toFixed(1) : metric.value}
                      </span>
                    </div>
                    
                    {metric.description && (
                      <p className="text-xs opacity-75 mb-2">{metric.description}</p>
                    )}
                    
                    {metric.timestamp && (
                      <p className="text-xs opacity-60">
                        Updated {new Date(metric.timestamp).toLocaleTimeString()}
                      </p>
                    )}
                  </div>
                ))}
              </div>
              
              {lastCheck && (
                <div className="mt-3 text-xs text-neutral-500 flex items-center space-x-1">
                  <ClockIcon className="h-3 w-3" />
                  <span>Last health check: {new Date(lastCheck).toLocaleString()}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-6">
              <div className="bg-green-50 rounded-full p-4 w-16 h-16 mx-auto mb-4">
                <CpuChipIcon className="h-8 w-8 text-green-400 mx-auto" />
              </div>
              <p className="text-sm text-neutral-600 font-medium">No health metrics available</p>
              <p className="text-xs text-neutral-500">Metrics will appear once monitoring is configured</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}