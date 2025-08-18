'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import DashboardLayout from '@/components/layout/DashboardLayout';
import IntegrationWizard from '@/components/integrations/IntegrationWizard';
import { Button } from '@/components/ui/Button';
import { 
  PlusIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  PuzzlePieceIcon,
  CpuChipIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ClockIcon,
  Cog6ToothIcon,
  TrashIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

export default function IntegrationsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [integrations, setIntegrations] = useState([]);
  const [showWizard, setShowWizard] = useState(false);
  const [loadingIntegrations, setLoadingIntegrations] = useState(true);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    } else if (isAuthenticated) {
      loadIntegrations();
    }
  }, [isAuthenticated, isLoading, router]);

  const loadIntegrations = async () => {
    try {
      console.log('Loading integrations...');
      console.log('User authenticated:', apiClient.isAuthenticated());
      console.log('Token:', apiClient.getToken());
      
      const data = await apiClient.getIntegrations();
      console.log('Integrations loaded:', data);
      setIntegrations(data || []);
    } catch (error) {
      console.error('Failed to load integrations:', error);
      setIntegrations([]); // Start with empty array instead of mock data
    } finally {
      setLoadingIntegrations(false);
    }
  };

  const handleCreateIntegration = (integrationData: any) => {
    console.log('Creating integration:', integrationData);
    setShowWizard(false);
    loadIntegrations();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-neutral-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <div>Redirecting to login...</div>;
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">Integrations</h1>
            <p className="text-neutral-600">Manage your business system connections</p>
          </div>
          <Button
            onClick={() => setShowWizard(true)}
            className="flex items-center gap-2"
          >
            <PlusIcon className="h-5 w-5" />
            Add Integration
          </Button>
        </div>

        {loadingIntegrations ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-neutral-600">Loading integrations...</p>
          </div>
        ) : integrations.length > 0 ? (
          <div className="space-y-6">
            {/* Integration Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-700">Active Systems</p>
                    <p className="text-2xl font-bold text-green-800">
                      {integrations.filter(i => i.status === 'active').length}
                    </p>
                  </div>
                  <ShieldCheckIcon className="h-8 w-8 text-green-600" />
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-700">Total Integrations</p>
                    <p className="text-2xl font-bold text-blue-800">{integrations.length}</p>
                  </div>
                  <CpuChipIcon className="h-8 w-8 text-blue-600" />
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-purple-700">Monitoring Metrics</p>
                    <p className="text-2xl font-bold text-purple-800">
                      {integrations.reduce((sum, i) => sum + (i.config?.monitoring_preferences?.length || 0), 0)}
                    </p>
                  </div>
                  <ChartBarIcon className="h-8 w-8 text-purple-600" />
                </div>
              </div>
              
              <div className={`bg-gradient-to-br ${integrations.filter(i => i.status === 'error').length > 0 ? 'from-red-50 to-red-100 border-red-200' : 'from-neutral-50 to-neutral-100 border-neutral-200'} rounded-lg p-4 border`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${integrations.filter(i => i.status === 'error').length > 0 ? 'text-red-700' : 'text-neutral-700'}`}>Issues</p>
                    <p className={`text-2xl font-bold ${integrations.filter(i => i.status === 'error').length > 0 ? 'text-red-800' : 'text-neutral-800'}`}>
                      {integrations.filter(i => i.status === 'error').length}
                    </p>
                  </div>
                  <ExclamationTriangleIcon className={`h-8 w-8 ${integrations.filter(i => i.status === 'error').length > 0 ? 'text-red-600' : 'text-neutral-600'}`} />
                </div>
              </div>
            </div>

            {/* Integration Cards Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {integrations.map((integration: any) => {
                const getIntegrationIcon = (type: string) => {
                  const icons = {
                    jira: '🎯', asana: '📋', trello: '📊',
                    zendesk: '🎫', freshdesk: '🆘',
                    salesforce: '☁️', hubspot: '🔶',
                    github: '🐙', gitlab: '🦊',
                    slack: '💬', aws: '☁️', azure: '🔷',
                    google_analytics: '📈', custom: '🔧'
                  };
                  return icons[type] || '🔌';
                };
                
                const getStatusColor = (status: string) => {
                  switch (status) {
                    case 'active': return 'green';
                    case 'error': return 'red';
                    case 'testing': return 'yellow';
                    default: return 'gray';
                  }
                };
                
                const statusColor = getStatusColor(integration.status);
                
                return (
                  <div key={integration.id} className="bg-white rounded-xl border border-neutral-200 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
                    {/* Header with status indicator */}
                    <div className={`h-2 bg-gradient-to-r ${
                      statusColor === 'green' ? 'from-green-400 to-green-600' :
                      statusColor === 'red' ? 'from-red-400 to-red-600' :
                      statusColor === 'yellow' ? 'from-yellow-400 to-yellow-600' :
                      'from-gray-400 to-gray-600'
                    }`} />
                    
                    <div className="p-6">
                      {/* Integration header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <span className="text-2xl">{getIntegrationIcon(integration.integration_type)}</span>
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3 className="text-lg font-semibold text-neutral-900 truncate">{integration.name}</h3>
                            <p className="text-sm text-neutral-500 capitalize">{integration.integration_type?.replace('_', ' ')}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {integration.status === 'active' && (
                            <div className="flex items-center space-x-1 text-green-600">
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                              <span className="text-xs font-medium">Live</span>
                            </div>
                          )}
                          {integration.status === 'error' && (
                            <div className="flex items-center space-x-1 text-red-600">
                              <ExclamationTriangleIcon className="h-4 w-4" />
                              <span className="text-xs font-medium">Error</span>
                            </div>
                          )}
                          {integration.status === 'testing' && (
                            <div className="flex items-center space-x-1 text-yellow-600">
                              <ClockIcon className="h-4 w-4" />
                              <span className="text-xs font-medium">Testing</span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Description */}
                      <p className="text-neutral-600 text-sm mb-4 line-clamp-2">
                        {integration.description || 'No description available'}
                      </p>
                      
                      {/* Monitoring metrics */}
                      {integration.config?.monitoring_preferences && integration.config.monitoring_preferences.length > 0 && (
                        <div className="mb-4">
                          <p className="text-xs font-medium text-neutral-500 mb-2">Monitoring:</p>
                          <div className="flex flex-wrap gap-1">
                            {integration.config.monitoring_preferences.slice(0, 3).map((metric, idx) => (
                              <span key={idx} className={`inline-flex px-2 py-1 text-xs rounded-full ${
                                statusColor === 'green' ? 'bg-green-100 text-green-700' :
                                statusColor === 'red' ? 'bg-red-100 text-red-700' :
                                statusColor === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {metric.replace(/_/g, ' ')}
                              </span>
                            ))}
                            {integration.config.monitoring_preferences.length > 3 && (
                              <span className="inline-flex px-2 py-1 text-xs rounded-full bg-neutral-100 text-neutral-600">
                                +{integration.config.monitoring_preferences.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Status and last sync */}
                      <div className="flex items-center justify-between mb-4">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          statusColor === 'green' ? 'bg-green-100 text-green-800' :
                          statusColor === 'red' ? 'bg-red-100 text-red-800' :
                          statusColor === 'yellow' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {integration.status === 'active' ? 'Active' : integration.status === 'error' ? 'Error' : 'Testing'}
                        </span>
                        <span className="text-xs text-neutral-500">
                          {integration.last_sync ? `Last sync: ${new Date(integration.last_sync).toLocaleDateString()}` : 'Never synced'}
                        </span>
                      </div>
                      
                      {/* Action buttons */}
                      <div className="flex space-x-2">
                        <Button variant="outline" size="sm" className="flex-1 flex items-center justify-center space-x-1">
                          <EyeIcon className="h-4 w-4" />
                          <span>View</span>
                        </Button>
                        <Button variant="outline" size="sm" className="flex-1 flex items-center justify-center space-x-1">
                          <Cog6ToothIcon className="h-4 w-4" />
                          <span>Configure</span>
                        </Button>
                        <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700 hover:border-red-300">
                          <TrashIcon className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="text-center py-12 bg-gradient-to-br from-neutral-50 to-blue-50 rounded-xl border border-neutral-200">
            <div className="relative">
              <PuzzlePieceIcon className="mx-auto h-20 w-20 text-green-500 mb-8" />
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-600 rounded-full flex items-center justify-center shadow-lg">
                <PlusIcon className="h-3 w-3 text-white" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-neutral-900 mb-2">Ready to Monitor Your Systems?</h3>
            <p className="text-neutral-600 mb-6 max-w-md mx-auto">
              Connect your business systems to unlock AI-powered monitoring, real-time insights, and automated health checks.
            </p>
            <div className="grid grid-cols-2 gap-4 text-sm text-neutral-500 mb-8 max-w-lg mx-auto">
              <div className="flex items-center justify-center space-x-2">
                <ChartBarIcon className="h-4 w-4" />
                <span>Real-time Metrics</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <ShieldCheckIcon className="h-4 w-4" />
                <span>Health Monitoring</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <CpuChipIcon className="h-4 w-4" />
                <span>System Insights</span>
              </div>
              <div className="flex items-center justify-center space-x-2">
                <CheckCircleIcon className="h-4 w-4" />
                <span>Automated Alerts</span>
              </div>
            </div>
            <Button
              onClick={() => setShowWizard(true)}
              className="flex items-center gap-2 mx-auto px-6 py-3 text-base"
              size="lg"
            >
              <PlusIcon className="h-5 w-5" />
              Connect Your First System
            </Button>
          </div>
        )}

        {showWizard && (
          <div className="fixed inset-0 bg-neutral-900/60 flex items-center justify-center z-50 backdrop-blur-sm">
            <div className="bg-white rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <IntegrationWizard
                onComplete={handleCreateIntegration}
                onCancel={() => setShowWizard(false)}
              />
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}