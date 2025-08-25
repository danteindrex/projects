'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
// import { useAnalyticsWebSocket } from '@/hooks/useAnalyticsWebSocket';
import { 
  ChartBarIcon,
  ExclamationCircleIcon,
  PuzzlePieceIcon,
  WifiIcon,
  SignalIcon
} from '@heroicons/react/24/outline';

// Import all analytics components
import GitHubAnalytics from './GitHubAnalytics';
import SlackAnalytics from './SlackAnalytics';
import JiraAnalytics from './JiraAnalytics';
import SalesforceAnalytics from './SalesforceAnalytics';
import ZendeskAnalytics from './ZendeskAnalytics';
import TrelloAnalytics from './TrelloAnalytics';
import AsanaAnalytics from './AsanaAnalytics';

interface Integration {
  id: number;
  name: string;
  integration_type: string;
  status: string;
}

export default function IntegrationAnalytics() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Real-time analytics WebSocket connection (temporarily disabled for debugging)
  // const { 
  //   analyticsData, 
  //   isConnected, 
  //   error: wsError, 
  //   requestUpdate, 
  //   subscribeToIntegration 
  // } = useAnalyticsWebSocket();
  
  // Temporary mock values for debugging
  const analyticsData = null;
  const isConnected = false;
  const requestUpdate = () => {};

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 Loading integrations...');
      const data = await apiClient.getIntegrations();
      console.log('📊 Raw integrations data:', data);
      
      if (!data || !Array.isArray(data)) {
        throw new Error('Invalid integrations data received from server');
      }
      
      console.log(`📈 Found ${data.length} total integrations`);
      
      // Log all integrations with their details
      data.forEach((integration: Integration, index) => {
        console.log(`${index + 1}. ${integration.name} (${integration.integration_type}) - Status: ${integration.status}`);
      });
      
      // Filter for analytics-supported integrations
      const supportedIntegrations = data.filter((integration: Integration) => 
        isAnalyticsSupported(integration.integration_type)
      );
      
      console.log(`🎯 ${supportedIntegrations.length} integrations support analytics`);
      
      // Filter for active integrations
      const activeIntegrations = supportedIntegrations.filter((integration: Integration) => {
        const normalizedStatus = integration.status.toLowerCase()
          .replace('integrationstatus.', '')  // Remove lowercase enum prefix
          .replace(/^.*\./, '')  // Remove any enum prefix (handles IntegrationType.GITHUB)
          .replace('_', '');  // Remove underscores
        
        console.log(`🔍 Checking status: ${integration.status} (normalized: ${normalizedStatus})`);
        return normalizedStatus === 'active';
      });
      
      console.log(`✅ ${activeIntegrations.length} active integrations with analytics support`);
      
      // Show ALL supported integrations for debugging, not just active ones
      setIntegrations(supportedIntegrations);
      
      // Set first integration as active tab
      if (supportedIntegrations.length > 0 && !activeTab) {
        setActiveTab(supportedIntegrations[0].id.toString());
      }
      
      // Provide detailed feedback
      if (supportedIntegrations.length === 0 && data.length > 0) {
        const unsupportedTypes = data.map(i => i.integration_type).filter(type => !isAnalyticsSupported(type));
        setError(`No supported integrations found. You have integrations of types: ${unsupportedTypes.join(', ')}. Supported types are: github, slack, jira, salesforce, zendesk, trello, asana.`);
      } else if (activeIntegrations.length === 0 && supportedIntegrations.length > 0) {
        const inactiveIntegrations = supportedIntegrations.filter(i => i.status !== 'active');
        setError(`Found ${supportedIntegrations.length} supported integration(s), but none are active. Inactive integrations: ${inactiveIntegrations.map(i => `${i.name} (${i.status})`).join(', ')}. Please activate them in the Integrations section.`);
      }
    } catch (err: any) {
      const errorMessage = err?.message || 'Failed to load integrations';
      setError(errorMessage);
      console.error('❌ Failed to load integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  const isAnalyticsSupported = (integrationType: string): boolean => {
    const supportedTypes = ['github', 'slack', 'jira', 'salesforce', 'zendesk', 'trello', 'asana'];
    
    // Handle both enum values (IntegrationType.GITHUB) and string values ('github')
    const normalizedType = integrationType.toLowerCase()
      .replace('integrationtype.', '')  // Remove lowercase enum prefix
      .replace(/^.*\./, '')  // Remove any enum prefix (handles IntegrationType.GITHUB)
      .replace('_', '');  // Remove underscores
    
    console.log(`🔍 Checking if ${integrationType} (normalized: ${normalizedType}) is supported`);
    const isSupported = supportedTypes.includes(normalizedType);
    console.log(`${isSupported ? '✅' : '❌'} ${integrationType} support: ${isSupported}`);
    
    return isSupported;
  };

  const getIntegrationIcon = (type: string) => {
    const icons = {
      github: '🐙',
      slack: '💬',
      jira: '🎯',
      salesforce: '☁️',
      zendesk: '🎫',
      trello: '📊',
      asana: '📋',
      hubspot: '🔶',
      gitlab: '🦊',
      aws: '☁️',
      azure: '🔷',
      google_analytics: '📈'
    };
    return icons[type.toLowerCase() as keyof typeof icons] || '🔌';
  };

  const renderAnalyticsComponent = (integration: Integration) => {
    // Normalize the integration type to handle enum values
    const integrationType = integration.integration_type.toLowerCase()
      .replace('integrationtype.', '')  // Remove lowercase enum prefix
      .replace(/^.*\./, '')  // Remove any enum prefix (handles IntegrationType.GITHUB)
      .replace('_', '');  // Remove underscores
    
    console.log(`🎯 Rendering analytics for: ${integration.integration_type} (normalized: ${integrationType})`);
    
    switch (integrationType) {
      case 'github':
        console.log('✅ Loading GitHubAnalytics component');
        return <GitHubAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'slack':
        console.log('✅ Loading SlackAnalytics component');
        return <SlackAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'jira':
        console.log('✅ Loading JiraAnalytics component');
        return <JiraAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'salesforce':
        console.log('✅ Loading SalesforceAnalytics component');
        return <SalesforceAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'zendesk':
        console.log('✅ Loading ZendeskAnalytics component');
        return <ZendeskAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'trello':
        console.log('✅ Loading TrelloAnalytics component');
        return <TrelloAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'asana':
        console.log('✅ Loading AsanaAnalytics component');
        return <AsanaAnalytics integrationId={integration.id} integrationName={integration.name} />;
      default:
        console.log(`❌ No analytics component found for: ${integrationType}`);
        return (
          <div className="text-center py-8">
            <ChartBarIcon className="mx-auto h-8 w-8 text-neutral-400 mb-2" />
            <p className="text-sm text-neutral-600">Analytics for {integrationType} coming soon</p>
            <p className="text-xs text-neutral-500 mt-2">Debug: Original type was &quot;{integration.integration_type}&quot;</p>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-4 bg-neutral-200 rounded w-1/4 mb-4"></div>
          <div className="flex space-x-2 mb-6">
            <div className="h-10 bg-neutral-200 rounded w-24"></div>
            <div className="h-10 bg-neutral-200 rounded w-24"></div>
            <div className="h-10 bg-neutral-200 rounded w-24"></div>
          </div>
          <div className="space-y-4">
            <div className="h-32 bg-neutral-200 rounded"></div>
            <div className="h-48 bg-neutral-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <ExclamationCircleIcon className="mx-auto h-8 w-8 text-neutral-400 mb-2" />
        <p className="text-sm text-neutral-600 mb-4">{error}</p>
        <button
          onClick={loadIntegrations}
          className="text-sm text-primary-600 hover:text-primary-700"
        >
          Try again
        </button>
      </div>
    );
  }

  if (integrations.length === 0) {
    return (
      <div className="text-center py-12 bg-gradient-to-br from-neutral-50 to-blue-50 rounded-xl border border-neutral-200">
        <div className="relative">
          <PuzzlePieceIcon className="mx-auto h-16 w-16 text-neutral-400 mb-6" />
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-primary-600 rounded-full flex items-center justify-center">
            <ChartBarIcon className="h-2 w-2 text-white" />
          </div>
        </div>
        <h3 className="text-lg font-medium text-neutral-900 mb-2">No Analytics Available</h3>
        <p className="text-neutral-600 mb-4 max-w-md mx-auto">
          Connect and configure your integrations to unlock powerful analytics and insights for your business systems.
        </p>
        <div className="grid grid-cols-2 gap-2 text-sm text-neutral-500 mb-6 max-w-lg mx-auto">
          <div className="flex items-center justify-center space-x-2">
            <span>🐙</span>
            <span>GitHub</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <span>💬</span>
            <span>Slack</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <span>🎯</span>
            <span>Jira</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <span>☁️</span>
            <span>Salesforce</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <span>🎫</span>
            <span>Zendesk</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <span>📊</span>
            <span>Trello</span>
          </div>
        </div>
        <p className="text-xs text-neutral-500">
          Go to <Link href="/integrations" className="text-primary-600 hover:underline">Integrations</Link> to set up your first connection
        </p>
      </div>
    );
  }

  const activeIntegration = integrations.find(i => i.id.toString() === activeTab);

  return (
    <div className="space-y-6">
      {/* Header with Real-time Status */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-neutral-900 mb-2">Integration Analytics</h2>
          <p className="text-sm text-neutral-600">
            View detailed analytics and metrics for your configured integrations
          </p>
        </div>
        
        {/* Real-time Connection Status */}
        <div className="flex items-center space-x-3">
          {analyticsData && (
            <div className="text-sm text-neutral-600">
              <span className="font-medium">{(analyticsData as any).total_calls_24h}</span> calls today
            </div>
          )}
          
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium ${
            isConnected 
              ? 'bg-green-100 text-green-800' 
              : 'bg-neutral-100 text-neutral-600'
          }`}>
            {isConnected ? (
              <>
                <SignalIcon className="h-3 w-3" />
                <span>Live</span>
              </>
            ) : (
              <>
                <WifiIcon className="h-3 w-3" />
                <span>Offline</span>
              </>
            )}
          </div>
          
          {isConnected && (
            <button
              onClick={requestUpdate}
              className="text-xs text-primary-600 hover:text-primary-700 underline"
            >
              Refresh
            </button>
          )}
        </div>
      </div>

      {/* Integration Tabs */}
      <div className="border-b border-neutral-200">
        <nav className="-mb-px flex space-x-1 overflow-x-auto" aria-label="Integration tabs">
          {integrations.map((integration) => (
            <button
              key={integration.id}
              onClick={() => setActiveTab(integration.id.toString())}
              className={`${
                activeTab === integration.id.toString()
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
              } whitespace-nowrap py-3 px-4 border-b-2 font-medium text-sm flex items-center space-x-2 transition-colors`}
            >
              <span>{getIntegrationIcon(integration.integration_type)}</span>
              <span>{integration.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Analytics Content */}
      <div className="min-h-[400px]">
        {activeIntegration && (
          <div className="space-y-4">
            {/* Integration Header */}
            <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg border border-primary-200 p-4">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getIntegrationIcon(activeIntegration.integration_type)}</span>
                  <div>
                    <h3 className="font-medium text-primary-900">{activeIntegration.name}</h3>
                    <p className="text-sm text-primary-700 capitalize">
                      {activeIntegration.integration_type.replace('_', ' ')} Analytics
                    </p>
                  </div>
                </div>
                <div className="flex-1"></div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-primary-800">Active</span>
                </div>
              </div>
            </div>

            {/* Analytics Component */}
            <div className="bg-white rounded-lg border border-neutral-200 p-6">
              {renderAnalyticsComponent(activeIntegration)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}