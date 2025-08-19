'use client';

import React, { useState, useEffect } from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  CpuChipIcon,
  CircleStackIcon,
  ServerIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { HealthStatus, SystemMetrics, ComponentHealth } from '@/lib/api';
import apiClient from '@/lib/api';

interface SystemHealthDashboardProps {
  className?: string;
}

export default function SystemHealthDashboard({ className = '' }: SystemHealthDashboardProps) {
  const [healthData, setHealthData] = useState<HealthStatus | null>(null);
  const [metricsData, setMetricsData] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealthData();
    const interval = setInterval(fetchHealthData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchHealthData = async () => {
    try {
      setError(null);
      const [health, metrics] = await Promise.all([
        apiClient.getSystemHealth(),
        apiClient.getSystemMetrics()
      ]);
      setHealthData(health);
      
      // Transform the metrics data to match expected structure
      if (metrics) {
        const transformedMetrics = {
          system: {
            cpu_usage_percent: metrics.cpu_percent || 0,
            memory_usage_percent: metrics.memory_percent || 0,
            disk_usage_percent: metrics.disk_percent || 0,
            uptime_seconds: metrics.uptime_seconds || 0
          },
          application: {
            active_integrations: 0, // Will be populated from integrations summary
            total_api_calls_24h: metrics.request_count || 0,
            error_rate_percent: metrics.error_count && metrics.request_count 
              ? (metrics.error_count / metrics.request_count) * 100 
              : 0,
            avg_response_time_ms: (metrics.avg_response_time || 0) * 1000 // Convert to ms
          }
        };
        setMetricsData(transformedMetrics);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="h-6 w-6 text-green-500" />;
      case 'degraded':
        return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />;
      case 'unhealthy':
        return <XCircleIcon className="h-6 w-6 text-red-500" />;
      default:
        return <ClockIcon className="h-6 w-6 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'unhealthy':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-neutral-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg border border-red-200 p-6 ${className}`}>
        <div className="flex items-center space-x-2 text-red-600">
          <XCircleIcon className="h-6 w-6" />
          <h3 className="text-lg font-medium">System Health Unavailable</h3>
        </div>
        <p className="mt-2 text-sm text-red-500">{error}</p>
        <button
          onClick={fetchHealthData}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-neutral-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-neutral-900">System Health Dashboard</h3>
        <div className="flex items-center space-x-2">
          {getStatusIcon(healthData?.overall_status || 'unknown')}
          <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(healthData?.overall_status || 'unknown')}`}>
            {healthData?.overall_status || 'Unknown'}
          </span>
        </div>
      </div>

      {/* System Metrics */}
      {metricsData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center space-x-3">
              <CpuChipIcon className="h-8 w-8 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-blue-900">CPU Usage</p>
                <p className="text-2xl font-bold text-blue-700">{metricsData.system.cpu_usage_percent.toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
            <div className="flex items-center space-x-3">
              <CircleStackIcon className="h-8 w-8 text-green-600" />
              <div>
                <p className="text-sm font-medium text-green-900">Memory Usage</p>
                <p className="text-2xl font-bold text-green-700">{metricsData.system.memory_usage_percent.toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
            <div className="flex items-center space-x-3">
              <ServerIcon className="h-8 w-8 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-purple-900">Disk Usage</p>
                <p className="text-2xl font-bold text-purple-700">{metricsData.system.disk_usage_percent.toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200">
            <div className="flex items-center space-x-3">
              <ClockIcon className="h-8 w-8 text-orange-600" />
              <div>
                <p className="text-sm font-medium text-orange-900">Uptime</p>
                <p className="text-lg font-bold text-orange-700">{formatUptime(metricsData.system.uptime_seconds)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Component Health Status */}
      {healthData && (
        <div className="space-y-4">
          <h4 className="text-md font-medium text-neutral-900">Component Status</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(healthData.components).map(([componentName, component]) => (
              <div key={componentName} className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
                <div className="flex items-center justify-between mb-2">
                  <h5 className="text-sm font-medium text-neutral-900 capitalize">
                    {componentName.replace('_', ' ')}
                  </h5>
                  {getStatusIcon(component.status)}
                </div>
                <div className="space-y-1">
                  <p className={`text-xs px-2 py-1 rounded-full ${getStatusColor(component.status)}`}>
                    {component.status}
                  </p>
                  {component.response_time_ms && (
                    <p className="text-xs text-neutral-600">
                      Response: {component.response_time_ms.toFixed(0)}ms
                    </p>
                  )}
                  {component.error_message && (
                    <p className="text-xs text-red-600 truncate" title={component.error_message}>
                      {component.error_message}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Application Metrics */}
      {metricsData && (
        <div className="mt-6 pt-6 border-t border-neutral-200">
          <h4 className="text-md font-medium text-neutral-900 mb-4">Application Metrics</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900">{metricsData.application.active_integrations}</p>
              <p className="text-sm text-neutral-600">Active Integrations</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900">{metricsData.application.total_api_calls_24h.toLocaleString()}</p>
              <p className="text-sm text-neutral-600">API Calls (24h)</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900">{metricsData.application.error_rate_percent.toFixed(2)}%</p>
              <p className="text-sm text-neutral-600">Error Rate</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-neutral-900">{metricsData.application.avg_response_time_ms.toFixed(0)}ms</p>
              <p className="text-sm text-neutral-600">Avg Response Time</p>
            </div>
          </div>
        </div>
      )}

      <div className="mt-4 text-xs text-neutral-500 text-right">
        Last updated: {healthData ? new Date(healthData.timestamp).toLocaleTimeString() : 'Never'}
      </div>
    </div>
  );
}