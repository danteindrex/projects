'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import DashboardLayout from '@/components/layout/DashboardLayout';
import IntegrationWizard from '@/components/integrations/IntegrationWizard';
import IntegrationMonitoringPanel from '@/components/monitoring/IntegrationMonitoringPanel';
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

interface Integration {
  id: number;
  name: string;
  description?: string;
  integration_type: string;
  status: string;
  config?: any;
  auth_type?: string;
  credentials?: any;
  last_sync?: string;
  token_expires_at?: string;
}

export default function IntegrationsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [showWizard, setShowWizard] = useState(false);
  const [editingIntegration, setEditingIntegration] = useState<Integration | null>(null);
  const [loadingIntegrations, setLoadingIntegrations] = useState(true);
  const [expandedIntegrations, setExpandedIntegrations] = useState<Set<number>>(new Set());
  const [deletingIntegrations, setDeletingIntegrations] = useState<Set<number>>(new Set());

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
      const data = await apiClient.getIntegrations();
      console.log('Integrations loaded:', data);
      setIntegrations(data || []);
    } catch (error) {
      console.error('Failed to load integrations:', error);
      setIntegrations([]);
    } finally {
      setLoadingIntegrations(false);
    }
  };

  const handleRefreshToken = async (integration: Integration) => {
    try {
      if (!integration.credentials?.refresh_token) {
        alert('No refresh token available. Please reconnect the integration.');
        return;
      }
      await apiClient.refreshOAuthToken(integration.id, integration.credentials.refresh_token);
      alert('Token refreshed successfully!');
      loadIntegrations();
    } catch (error) {
      console.error('Failed to refresh token:', error);
      alert('Failed to refresh token. Please try reconnecting the integration.');
    }
  };

  const handleRevokeIntegration = async (integration: Integration) => {
    // Add to deleting set for visual feedback
    setDeletingIntegrations(prev => new Set(prev).add(integration.id));
    
    try {
      if (integration.auth_type === 'oauth2') {
        try {
          await apiClient.revokeOAuthToken(integration.id);
        } catch (oauthError) {
          console.warn('OAuth revoke failed (continuing with delete):', oauthError);
        }
      }
      await apiClient.deleteIntegration(integration.id);
      alert('Integration deleted successfully!');
      await loadIntegrations(); // Ensure reload completes
    } catch (error: any) {
      console.error('Failed to delete integration:', error);
      const errorMessage = error?.message || 'Failed to delete integration.';
      
      // Show more specific error messages
      if (errorMessage.includes('Authentication required')) {
        alert('Your session has expired. Please log in again.');
      } else if (errorMessage.includes('not found')) {
        alert('This integration no longer exists. Refreshing...');
        await loadIntegrations();
      } else {
        alert(`Failed to delete integration: ${errorMessage}`);
      }
    } finally {
      // Remove from deleting set
      setDeletingIntegrations(prev => {
        const newSet = new Set(prev);
        newSet.delete(integration.id);
        return newSet;
      });
    }
  };

  const handleTestIntegration = async (integrationId: number) => {
    try {
      await apiClient.testIntegration(integrationId);
      alert('Integration test successful!');
    } catch (error) {
      console.error('Integration test failed:', error);
      alert('Integration test failed. You may need to refresh or reconnect.');
    }
  };

  const handleCreateIntegration = (integrationData: any) => {
    setShowWizard(false);
    loadIntegrations();
  };

  const handleUpdateIntegration = async (integrationData: any) => {
    if (!editingIntegration) return;

    try {
      await apiClient.updateIntegration(editingIntegration.id, integrationData);
      alert('Integration updated successfully!');
      setEditingIntegration(null);
      loadIntegrations();
    } catch (error) {
      console.error('Failed to update integration:', error);
      alert('Failed to update integration.');
    }
  };

  const handleConfigureIntegration = (integration: Integration) => {
    setEditingIntegration(integration);
    setShowWizard(true);
  };

  const toggleExpandIntegration = (id: number) => {
    setExpandedIntegrations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
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
            onClick={() => { setEditingIntegration(null); setShowWizard(true); }}
            className="flex items-center gap-2 bg-green-200 hover:bg-green-300 text-black"
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

            {/* Integration Monitoring Section */}
            <div className="bg-white rounded-lg border border-neutral-200 p-6">
              <div className="flex items-center space-x-3 mb-6">
                <ChartBarIcon className="h-6 w-6 text-primary-600" />
                <h2 className="text-lg font-medium text-neutral-900">Integration Monitoring</h2>
              </div>
              <IntegrationMonitoringPanel className="border-0 p-0 bg-transparent" />
            </div>

            {/* Integration Cards Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {integrations.map((integration) => {
                const getIntegrationIcon = (type: string) => {
                  const icons: Record<string, string> = {
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
                            {integration.config.monitoring_preferences.slice(0, 3).map((metric: string, idx: number) => (
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
                      
                      {/* Display full configuration */}
                      {integration.config && Object.keys(integration.config).filter(k => k !== 'monitoring_preferences').length > 0 && (
                        <div className="mb-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <p className="text-xs font-medium text-neutral-600 mb-2">Configuration:</p>
                          <div className="space-y-1">
                            {Object.entries(integration.config)
                              .filter(([key]) => key !== 'monitoring_preferences')
                              .map(([key, value]) => (
                                <div key={key} className="flex items-start gap-2 text-xs">
                                  <span className="font-medium text-neutral-700 min-w-[80px]">{key.replace(/_/g, ' ')}:</span>
                                  <span className="text-neutral-600 break-all">
                                    {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                                  </span>
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Expanded details view */}
                      {expandedIntegrations.has(integration.id) && (
                        <div className="mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                          <p className="text-xs font-medium text-blue-800 mb-2">Integration Details:</p>
                          <div className="space-y-2 text-xs">
                            <div>
                              <span className="font-medium text-blue-700">ID:</span> {integration.id}
                            </div>
                            <div>
                              <span className="font-medium text-blue-700">Type:</span> {integration.integration_type}
                            </div>
                            <div>
                              <span className="font-medium text-blue-700">Status:</span> {integration.status}
                            </div>
                            {integration.credentials && (
                              <div>
                                <span className="font-medium text-blue-700">Credentials:</span>
                                <div className="mt-1 p-2 bg-white rounded border border-blue-100">
                                  {Object.entries(integration.credentials).map(([key, value]) => (
                                    <div key={key} className="text-gray-600">
                                      {key}: {key.includes('token') || key.includes('secret') || key.includes('password') 
                                        ? '••••••••' 
                                        : String(value)}
                                    </div>
                                  ))}
                                </div>
                              </div>
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
                      
                      {/* OAuth Status Indicator */}
                      {integration.auth_type === 'oauth2' && (
                        <div className="mb-3 flex items-center space-x-2">
                          <div className="flex items-center space-x-1 text-blue-600">
                            <ShieldCheckIcon className="h-3 w-3" />
                            <span className="text-xs font-medium">OAuth 2.0</span>
                          </div>
                          {integration.token_expires_at && (
                            <span className="text-xs text-neutral-500">
                              Token expires: {new Date(integration.token_expires_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Action buttons */}
                      <div className="flex space-x-2">
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="flex items-center justify-center space-x-1 px-2"
                          onClick={() => toggleExpandIntegration(integration.id)}
                        >
                          <EyeIcon className="h-4 w-4" />
                          <span>{expandedIntegrations.has(integration.id) ? 'Hide' : 'Details'}</span>
                        </Button>
                        
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="flex-1 flex items-center justify-center space-x-1"
                          onClick={() => handleTestIntegration(integration.id)}
                        >
                          <CheckCircleIcon className="h-4 w-4" />
                          <span>Test</span>
                        </Button>
                        
                        {integration.auth_type === 'oauth2' && integration.credentials?.refresh_token ? (
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="flex-1 flex items-center justify-center space-x-1"
                            onClick={() => handleRefreshToken(integration)}
                          >
                            <Cog6ToothIcon className="h-4 w-4" />
                            <span>Refresh</span>
                          </Button>
                        ) : (
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="flex-1 flex items-center justify-center space-x-1"
                            onClick={() => handleConfigureIntegration(integration)}
                          >
                            <Cog6ToothIcon className="h-4 w-4" />
                            <span>Configure</span>
                          </Button>
                        )}
                        
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="text-red-600 hover:text-red-700 hover:border-red-300 disabled:opacity-50"
                          disabled={deletingIntegrations.has(integration.id)}
                          onClick={() => {
                            if (confirm('Are you sure you want to delete this integration?')) {
                              handleRevokeIntegration(integration);
                            }
                          }}
                        >
                          {deletingIntegrations.has(integration.id) ? (
                            <div className="h-4 w-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <TrashIcon className="h-4 w-4" />
                          )}
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
              onClick={() => { setEditingIntegration(null); setShowWizard(true); }}
              className="flex items-center gap-2 mx-auto px-6 py-3 text-base bg-green-200 hover:bg-green-300 text-black"
              size="lg"
            >
              <PlusIcon className="h-5 w-5" />
              Connect Your First System
            </Button>
          </div>
        )}

        {(showWizard || editingIntegration) && (
          <div className="fixed inset-0 backdrop-blur-md flex items-center justify-center z-50">
            <div className="bg-white rounded-2xl p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto shadow-2xl">
              <IntegrationWizard
                onComplete={editingIntegration ? handleUpdateIntegration : handleCreateIntegration}
                onCancel={() => { setShowWizard(false); setEditingIntegration(null); }}
                integrationToEdit={editingIntegration}
              />
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
