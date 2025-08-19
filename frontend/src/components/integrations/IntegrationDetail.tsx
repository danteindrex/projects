'use client';

import React, { useState, useEffect } from 'react';
import { Integration, IntegrationHealth } from '@/lib/api';
import { INTEGRATION_ICONS, INTEGRATION_NAMES } from '@/lib/integrationTypes';
import { HealthMonitor } from './HealthMonitor';
import { IntegrationEditForm } from './IntegrationEditForm';
import { IntegrationActions } from './IntegrationActions';
import { Button } from '@/components/ui/Button';
import {
  PencilIcon,
  Cog6ToothIcon,
  ClockIcon,
  GlobeAltIcon,
  KeyIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

interface IntegrationDetailProps {
  integration: Integration;
  onIntegrationUpdated: (integration: Integration) => void;
  onIntegrationDeleted: () => void;
  onRefresh: () => void;
}

export function IntegrationDetail({ 
  integration, 
  onIntegrationUpdated, 
  onIntegrationDeleted,
  onRefresh 
}: IntegrationDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [health, setHealth] = useState<IntegrationHealth | null>(null);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircleIcon className="w-5 h-5 text-green-600" />;
      case 'error':
        return <XCircleIcon className="w-5 h-5 text-red-600" />;
      case 'inactive':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />;
      default:
        return <ClockIcon className="w-5 h-5 text-neutral-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'inactive':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-neutral-100 text-neutral-800 border-neutral-200';
    }
  };

  const integrationIcon = INTEGRATION_ICONS[integration.integration_type as keyof typeof INTEGRATION_ICONS] || '⚙️';
  const integrationName = INTEGRATION_NAMES[integration.integration_type as keyof typeof INTEGRATION_NAMES] || integration.integration_type;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (isEditing) {
    return (
      <IntegrationEditForm
        integration={integration}
        onSave={(updatedIntegration) => {
          onIntegrationUpdated(updatedIntegration);
          setIsEditing(false);
        }}
        onCancel={() => setIsEditing(false)}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <div className="text-4xl">{integrationIcon}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-3 mb-2">
                <h2 className="text-2xl font-bold text-neutral-900">{integration.name}</h2>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(integration.status)}`}>
                  {getStatusIcon(integration.status)}
                  <span className="ml-1 capitalize">{integration.status}</span>
                </span>
              </div>
              <p className="text-sm text-neutral-600 mb-1">
                <span className="font-medium">Type:</span> {integrationName}
              </p>
              {integration.description && (
                <p className="text-neutral-700">{integration.description}</p>
              )}
            </div>
          </div>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEditing(true)}
            >
              <PencilIcon className="w-4 h-4 mr-2" />
              Edit
            </Button>
          </div>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4 flex items-center">
              <Cog6ToothIcon className="w-5 h-5 mr-2" />
              Configuration
            </h3>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-1">
                    Base URL
                  </label>
                  <div className="flex items-center text-sm text-neutral-900">
                    <GlobeAltIcon className="w-4 h-4 mr-2 text-neutral-500" />
                    {integration.base_url || 'Not configured'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-1">
                    Rate Limit
                  </label>
                  <div className="flex items-center text-sm text-neutral-900">
                    <ChartBarIcon className="w-4 h-4 mr-2 text-neutral-500" />
                    {integration.rate_limit ? `${integration.rate_limit} req/min` : 'No limit'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-1">
                    Timeout
                  </label>
                  <div className="flex items-center text-sm text-neutral-900">
                    <ClockIcon className="w-4 h-4 mr-2 text-neutral-500" />
                    {integration.timeout ? `${integration.timeout}s` : 'Default'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-1">
                    Credentials
                  </label>
                  <div className="flex items-center text-sm text-neutral-900">
                    <KeyIcon className="w-4 h-4 mr-2 text-neutral-500" />
                    {Object.keys(integration.credentials).length} configured
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Configuration */}
          {integration.config && Object.keys(integration.config).length > 0 && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-neutral-900 mb-4">
                Advanced Configuration
              </h3>
              <div className="bg-neutral-50 rounded-lg p-4">
                <pre className="text-sm text-neutral-700 overflow-x-auto">
                  {JSON.stringify(integration.config, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Health Monitor */}
          <HealthMonitor integrationId={integration.id} />

          {/* Integration Actions */}
          <IntegrationActions
            integration={integration}
            onIntegrationDeleted={onIntegrationDeleted}
            onRefresh={onRefresh}
          />

          {/* Timestamps */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">
              Timeline
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Created
                </label>
                <p className="text-sm text-neutral-900">
                  {formatDate(integration.created_at)}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">
                  Last Updated
                </label>
                <p className="text-sm text-neutral-900">
                  {formatDate(integration.updated_at)}
                </p>
              </div>
              {integration.last_sync && (
                <div>
                  <label className="block text-sm font-medium text-neutral-700 mb-1">
                    Last Sync
                  </label>
                  <p className="text-sm text-neutral-900">
                    {formatDate(integration.last_sync)}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}