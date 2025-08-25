'use client';

import React, { useState, useEffect } from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  PlayIcon,
  ChartBarIcon,
  ClockIcon,
  ExclamationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { Integration, IntegrationMetrics, IntegrationTestResult, IntegrationsSummary } from '@/lib/api';
import apiClient from '@/lib/api';

interface IntegrationMonitoringPanelProps {
  className?: string;
}

export default function IntegrationMonitoringPanel({ className = '' }: IntegrationMonitoringPanelProps) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [summary, setSummary] = useState<IntegrationsSummary | null>(null);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [metrics, setMetrics] = useState<IntegrationMetrics | null>(null);
  const [testResults, setTestResults] = useState<Record<number, IntegrationTestResult>>({});
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<Record<number, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setError(null);
      const [integrationsData, summaryData] = await Promise.all([
        apiClient.getIntegrations(),
        apiClient.getIntegrationsSummary().catch(() => ({
          total: 0,
          healthy: 0,
          degraded: 0,
          unhealthy: 0,
          inactive: 0,
          by_type: {},
          recent_errors: []
        }))
      ]);
      setIntegrations(integrationsData);
      
      // Transform summary data to match expected structure
      if (summaryData && (summaryData as any).total_integrations !== undefined) {
        const transformedSummary = {
          total: (summaryData as any).total_integrations || (summaryData as any).total || 0,
          healthy: summaryData.healthy || 0,
          degraded: summaryData.degraded || 0,
          unhealthy: summaryData.unhealthy || 0,
          inactive: summaryData.inactive || 0,
          by_type: summaryData.by_type || {},
          recent_errors: summaryData.recent_errors || []
        };
        setSummary(transformedSummary);
      } else {
        // Fallback: calculate summary from integrations data
        const calculatedSummary = {
          total: integrationsData.length,
          healthy: integrationsData.filter(i => i.health_status === 'healthy').length,
          degraded: integrationsData.filter(i => i.health_status === 'degraded').length,
          unhealthy: integrationsData.filter(i => i.health_status === 'unhealthy').length,
          inactive: integrationsData.filter(i => i.status === 'inactive').length,
          by_type: {},
          recent_errors: []
        };
        setSummary(calculatedSummary);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch integration data');
    } finally {
      setLoading(false);
    }
  };

  const testIntegration = async (integration: Integration) => {
    setTesting(prev => ({ ...prev, [integration.id]: true }));
    try {
      const result = await apiClient.testIntegrationMonitoring(integration.id);
      setTestResults(prev => ({ ...prev, [integration.id]: result }));
      
      // Refresh integration data after test
      await fetchData();
    } catch (err) {
      setTestResults(prev => ({ 
        ...prev, 
        [integration.id]: {
          success: false,
          message: err instanceof Error ? err.message : 'Test failed',
          response_time_ms: 0,
          timestamp: new Date().toISOString()
        }
      }));
    } finally {
      setTesting(prev => ({ ...prev, [integration.id]: false }));
    }
  };

  const fetchIntegrationMetrics = async (integration: Integration) => {
    try {
      const metricsData = await apiClient.getIntegrationMetrics(integration.id, '24h');
      setMetrics(metricsData);
      setSelectedIntegration(integration);
    } catch (err) {
      console.error('Failed to fetch integration metrics:', err);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'unhealthy':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'degraded':
        return 'bg-yellow-100 text-yellow-800';
      case 'unhealthy':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-neutral-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
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
          <h3 className="text-lg font-medium">Integration Monitoring Unavailable</h3>
        </div>
        <p className="mt-2 text-sm text-red-500">{error}</p>
        <button
          onClick={fetchData}
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
        <h3 className="text-lg font-medium text-neutral-900">Integration Monitoring</h3>
        <button
          onClick={fetchData}
          className="p-2 text-neutral-500 hover:text-neutral-700 transition-colors"
          title="Refresh"
        >
          <ArrowPathIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center space-x-2">
              <ChartBarIcon className="h-6 w-6 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-blue-900">Total</p>
                <p className="text-2xl font-bold text-blue-700">{summary.total}</p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <div>
                <p className="text-sm font-medium text-green-900">Healthy</p>
                <p className="text-2xl font-bold text-green-700">{summary.healthy}</p>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />
              <div>
                <p className="text-sm font-medium text-yellow-900">Degraded</p>
                <p className="text-2xl font-bold text-yellow-700">{summary.degraded}</p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <div className="flex items-center space-x-2">
              <XCircleIcon className="h-6 w-6 text-red-600" />
              <div>
                <p className="text-sm font-medium text-red-900">Unhealthy</p>
                <p className="text-2xl font-bold text-red-700">{summary.unhealthy}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Integration List */}
      <div className="space-y-4">
        <h4 className="text-md font-medium text-neutral-900">Integration Health Status</h4>
        {integrations.length === 0 ? (
          <div className="text-center py-8 text-neutral-500">
            <ChartBarIcon className="h-12 w-12 mx-auto mb-4 text-neutral-300" />
            <p>No integrations configured</p>
            <p className="text-sm">Add integrations to start monitoring</p>
          </div>
        ) : (
          <div className="space-y-3">
            {integrations.map((integration) => (
              <div key={integration.id} className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(integration.health_status || 'unknown')}
                    <div>
                      <h5 className="text-sm font-medium text-neutral-900">{integration.name}</h5>
                      <p className="text-xs text-neutral-600 capitalize">{integration.integration_type}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(integration.health_status || 'unknown')}`}>
                      {integration.health_status || 'Unknown'}
                    </span>
                    
                    <button
                      onClick={() => fetchIntegrationMetrics(integration)}
                      className="p-1 text-neutral-500 hover:text-neutral-700 transition-colors"
                      title="View Metrics"
                    >
                      <ChartBarIcon className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => testIntegration(integration)}
                      disabled={testing[integration.id]}
                      className="p-1 text-neutral-500 hover:text-neutral-700 transition-colors disabled:opacity-50"
                      title="Test Integration"
                    >
                      {testing[integration.id] ? (
                        <ArrowPathIcon className="h-4 w-4 animate-spin" />
                      ) : (
                        <PlayIcon className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Integration Details */}
                <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                  <div>
                    <p className="text-neutral-500">Error Count</p>
                    <p className="font-medium">{integration.error_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-neutral-500">Last Check</p>
                    <p className="font-medium">
                      {(integration as any).last_health_check 
                        ? new Date((integration as any).last_health_check).toLocaleTimeString()
                        : 'Never'
                      }
                    </p>
                  </div>
                  <div>
                    <p className="text-neutral-500">Status</p>
                    <p className="font-medium capitalize">{integration.status}</p>
                  </div>
                </div>

                {/* Test Results */}
                {testResults[integration.id] && (
                  <div className="mt-3 p-3 bg-white rounded border">
                    <div className="flex items-center space-x-2">
                      {testResults[integration.id].success ? (
                        <CheckCircleIcon className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircleIcon className="h-4 w-4 text-red-500" />
                      )}
                      <span className="text-xs font-medium">
                        Test {testResults[integration.id].success ? 'Passed' : 'Failed'}
                      </span>
                      <span className="text-xs text-neutral-500">
                        ({testResults[integration.id].response_time_ms}ms)
                      </span>
                    </div>
                    <p className="text-xs text-neutral-600 mt-1">
                      {testResults[integration.id].message}
                    </p>
                  </div>
                )}

                {/* Last Error */}
                {integration.last_error && (
                  <div className="mt-3 p-3 bg-red-50 rounded border border-red-200">
                    <div className="flex items-center space-x-2">
                      <ExclamationCircleIcon className="h-4 w-4 text-red-500" />
                      <span className="text-xs font-medium text-red-800">Last Error</span>
                    </div>
                    <p className="text-xs text-red-700 mt-1">{integration.last_error}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Integration Metrics Modal/Panel */}
      {selectedIntegration && metrics && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-md font-medium text-blue-900">
              Metrics: {selectedIntegration.name}
            </h4>
            <button
              onClick={() => {
                setSelectedIntegration(null);
                setMetrics(null);
              }}
              className="text-blue-600 hover:text-blue-800"
            >
              ×
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-900">{metrics.api_calls.total}</p>
              <p className="text-sm text-blue-700">Total API Calls</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-700">{metrics.api_calls.successful}</p>
              <p className="text-sm text-blue-700">Successful</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-700">{metrics.api_calls.failed}</p>
              <p className="text-sm text-blue-700">Failed</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-900">{metrics.performance.avg_response_time_ms}ms</p>
              <p className="text-sm text-blue-700">Avg Response</p>
            </div>
          </div>
        </div>
      )}

      <div className="mt-4 text-xs text-neutral-500 text-right">
        Last updated: {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
}