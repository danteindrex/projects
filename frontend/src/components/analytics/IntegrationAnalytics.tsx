'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { 
  ChartBarIcon,
  ExclamationCircleIcon,
  PuzzlePieceIcon
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

  useEffect(() => {
    loadIntegrations();
  }, []);

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await apiClient.getIntegrations();
      if (!data || !Array.isArray(data)) {
        throw new Error('Invalid integrations data received from server');
      }
      
      // Only show active integrations that have analytics support
      const activeIntegrations = data.filter((integration: Integration) => 
        integration.status === 'active' && isAnalyticsSupported(integration.integration_type)
      );
      
      setIntegrations(activeIntegrations);
      
      // Set first integration as active tab
      if (activeIntegrations.length > 0 && !activeTab) {
        setActiveTab(activeIntegrations[0].id.toString());
      }
      
      // If no active integrations, show helpful message
      if (activeIntegrations.length === 0 && data.length > 0) {
        const inactiveCount = data.filter((integration: Integration) => 
          isAnalyticsSupported(integration.integration_type)
        ).length;
        
        if (inactiveCount > 0) {
          setError(`You have ${inactiveCount} supported integration(s) that are not active. Please activate them in the Integrations section to view analytics.`);
        }
      }
    } catch (err: any) {
      const errorMessage = err?.message || 'Failed to load integrations';
      setError(errorMessage);
      console.error('Failed to load integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  const isAnalyticsSupported = (integrationType: string): boolean => {
    const supportedTypes = ['github', 'slack', 'jira', 'salesforce', 'zendesk', 'trello', 'asana'];
    return supportedTypes.includes(integrationType.toLowerCase());
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
    return icons[type.toLowerCase()] || '🔌';
  };

  const renderAnalyticsComponent = (integration: Integration) => {
    const integrationType = integration.integration_type.toLowerCase();
    
    switch (integrationType) {
      case 'github':
        return <GitHubAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'slack':
        return <SlackAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'jira':
        return <JiraAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'salesforce':
        return <SalesforceAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'zendesk':
        return <ZendeskAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'trello':
        return <TrelloAnalytics integrationId={integration.id} integrationName={integration.name} />;
      case 'asana':
        return <AsanaAnalytics integrationId={integration.id} integrationName={integration.name} />;
      default:
        return (
          <div className="text-center py-8">
            <ChartBarIcon className="mx-auto h-8 w-8 text-neutral-400 mb-2" />
            <p className="text-sm text-neutral-600">Analytics for {integrationType} coming soon</p>
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
          Go to <a href="/integrations" className="text-primary-600 hover:underline">Integrations</a> to set up your first connection
        </p>
      </div>
    );
  }

  const activeIntegration = integrations.find(i => i.id.toString() === activeTab);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-semibold text-neutral-900 mb-2">Integration Analytics</h2>
        <p className="text-sm text-neutral-600">
          View detailed analytics and metrics for your configured integrations
        </p>
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