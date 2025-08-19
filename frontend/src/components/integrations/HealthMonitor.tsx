'use client';

import React, { useState, useEffect } from 'react';
import { IntegrationHealth, apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import {
  HeartIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  SignalIcon,
  BoltIcon,
  ChartBarIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

interface HealthMonitorProps {
  integrationId: number;
}

export function HealthMonitor({ integrationId }: HealthMonitorProps) {
  const [health, setHealth] = useState<IntegrationHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningCheck, setIsRunningCheck] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth();
  }, [integrationId]);

  const fetchHealth = async () => {
    try {
      setError(null);
      setIsLoading(true);
      const healthData = await apiClient.getIntegrationHealth(integrationId);
      setHealth(healthData);
    } catch (err) {
      console.error('Error fetching health data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch health data');
    } finally {
      setIsLoading(false);
    }
  };

  const runHealthCheck = async () => {
    try {
      setIsRunningCheck(true);
      setError(null);
      const healthData = await apiClient.runHealthCheck(integrationId);
      setHealth(healthData);
    } catch (err) {
      console.error('Error running health check:', err);
      setError(err instanceof Error ? err.message : 'Health check failed');
    } finally {
      setIsRunningCheck(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'degraded':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />;
      case 'unhealthy':
        return <XCircleIcon className="w-5 h-5 text-red-600" />;
      default:
        return <ClockIcon className="w-5 h-5 text-neutral-500" />;
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
        return 'bg-neutral-100 text-neutral-800 border-neutral-200';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatResponseTime = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-neutral-200 rounded w-3/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-neutral-200 rounded"></div>
            <div className="h-4 bg-neutral-200 rounded w-2/3"></div>
            <div className="h-4 bg-neutral-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !health) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4 flex items-center">
          <HeartIcon className="w-5 h-5 mr-2" />
          Health Monitor
        </h3>
        <div className="text-center py-4">
          <XCircleIcon className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-sm text-red-600">{error}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchHealth}
            className="mt-3"
          >
            <ArrowPathIcon className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-neutral-900 flex items-center">
          <HeartIcon className="w-5 h-5 mr-2" />
          Health Monitor
        </h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={runHealthCheck}
          loading={isRunningCheck}
          disabled={isRunningCheck}
        >
          <ArrowPathIcon className={`w-4 h-4 ${isRunningCheck ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {health ? (
        <div className="space-y-4">
          {/* Overall Status */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-neutral-700">Status</span>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(health.status)}`}>
              {getStatusIcon(health.status)}
              <span className="ml-1 capitalize">{health.status}</span>
            </span>
          </div>

          {/* Response Time */}
          {health.response_time && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-neutral-700">Response Time</span>
              <span className="text-sm text-neutral-900 flex items-center">
                <BoltIcon className="w-4 h-4 mr-1 text-neutral-500" />
                {formatResponseTime(health.response_time)}
              </span>
            </div>
          )}

          {/* Error Count */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-neutral-700">Error Count</span>
            <span className={`text-sm ${health.error_count > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {health.error_count}
            </span>
          </div>

          {/* Uptime */}
          {health.uptime_percentage !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-neutral-700">Uptime</span>
              <span className="text-sm text-neutral-900 flex items-center">
                <SignalIcon className="w-4 h-4 mr-1 text-neutral-500" />
                {health.uptime_percentage.toFixed(1)}%
              </span>
            </div>
          )}

          {/* Last Check */}
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-neutral-700">Last Check</span>
            <span className="text-sm text-neutral-900 flex items-center">
              <ClockIcon className="w-4 h-4 mr-1 text-neutral-500" />
              {formatDate(health.last_check)}
            </span>
          </div>

          {/* Last Error */}
          {health.last_error && (
            <div>
              <span className="text-sm font-medium text-neutral-700 block mb-2">Last Error</span>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-xs text-red-800">{health.last_error}</p>
              </div>
            </div>
          )}

          {/* Health Checks */}
          {health.checks && (
            <div>
              <span className="text-sm font-medium text-neutral-700 block mb-3">System Checks</span>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-600">Connectivity</span>
                  {health.checks.connectivity ? (
                    <CheckCircleIcon className="w-4 h-4 text-green-600" />
                  ) : (
                    <XCircleIcon className="w-4 h-4 text-red-600" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-600">Authentication</span>
                  {health.checks.authentication ? (
                    <CheckCircleIcon className="w-4 h-4 text-green-600" />
                  ) : (
                    <XCircleIcon className="w-4 h-4 text-red-600" />
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-600">Rate Limits</span>
                  {health.checks.rate_limits ? (
                    <CheckCircleIcon className="w-4 h-4 text-green-600" />
                  ) : (
                    <XCircleIcon className="w-4 h-4 text-red-600" />
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Metrics */}
          {health.metrics && (
            <div>
              <span className="text-sm font-medium text-neutral-700 block mb-3">24h Metrics</span>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-neutral-50 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-neutral-600">Requests</span>
                    <ChartBarIcon className="w-3 h-3 text-neutral-500" />
                  </div>
                  <span className="text-sm font-semibold text-neutral-900">
                    {health.metrics.requests_last_24h.toLocaleString()}
                  </span>
                </div>
                <div className="bg-neutral-50 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-neutral-600">Success Rate</span>
                    <ChartBarIcon className="w-3 h-3 text-neutral-500" />
                  </div>
                  <span className="text-sm font-semibold text-neutral-900">
                    {(health.metrics.success_rate * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="bg-neutral-50 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-neutral-600">Avg Response</span>
                    <BoltIcon className="w-3 h-3 text-neutral-500" />
                  </div>
                  <span className="text-sm font-semibold text-neutral-900">
                    {formatResponseTime(health.metrics.avg_response_time)}
                  </span>
                </div>
                <div className="bg-neutral-50 rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-neutral-600">Errors</span>
                    <ExclamationTriangleIcon className="w-3 h-3 text-neutral-500" />
                  </div>
                  <span className="text-sm font-semibold text-neutral-900">
                    {health.metrics.errors_last_24h}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-4">
          <ClockIcon className="w-8 h-8 text-neutral-400 mx-auto mb-2" />
          <p className="text-sm text-neutral-600">No health data available</p>
          <Button
            variant="outline"
            size="sm"
            onClick={runHealthCheck}
            loading={isRunningCheck}
            className="mt-3"
          >
            <HeartIcon className="w-4 h-4 mr-2" />
            Run Health Check
          </Button>
        </div>
      )}

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-xs text-red-800">{error}</p>
        </div>
      )}
    </div>
  );
}