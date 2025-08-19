'use client';

import React, { useState } from 'react';
import { Integration, apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import {
  PlayIcon,
  StopIcon,
  TrashIcon,
  WrenchIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

interface IntegrationActionsProps {
  integration: Integration;
  onIntegrationDeleted: () => void;
  onRefresh: () => void;
}

export function IntegrationActions({ 
  integration, 
  onIntegrationDeleted, 
  onRefresh 
}: IntegrationActionsProps) {
  const [isTestLoading, setIsTestLoading] = useState(false);
  const [isDeleteLoading, setIsDeleteLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    details?: any;
  } | null>(null);

  const handleTestConnection = async () => {
    setIsTestLoading(true);
    setTestResult(null);

    try {
      const result = await apiClient.testIntegration(integration.id);
      setTestResult({
        success: true,
        message: 'Connection test successful!',
        details: result
      });
      // Refresh the integration to get updated status
      setTimeout(() => {
        onRefresh();
      }, 1000);
    } catch (err) {
      console.error('Connection test failed:', err);
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : 'Connection test failed',
      });
    } finally {
      setIsTestLoading(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleteLoading(true);

    try {
      await apiClient.deleteIntegration(integration.id);
      onIntegrationDeleted();
    } catch (err) {
      console.error('Error deleting integration:', err);
      // Show error to user - you might want to add a toast notification here
      alert(err instanceof Error ? err.message : 'Failed to delete integration');
    } finally {
      setIsDeleteLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  const getStatusAction = () => {
    switch (integration.status) {
      case 'active':
        return {
          label: 'Disable',
          icon: StopIcon,
          variant: 'outline' as const,
          action: () => {
            // This would require an API endpoint to change status
            console.log('Disable integration');
          }
        };
      case 'inactive':
        return {
          label: 'Enable',
          icon: PlayIcon,
          variant: 'default' as const,
          action: () => {
            // This would require an API endpoint to change status
            console.log('Enable integration');
          }
        };
      default:
        return null;
    }
  };

  const statusAction = getStatusAction();

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold text-neutral-900 mb-4 flex items-center">
        <WrenchIcon className="w-5 h-5 mr-2" />
        Actions
      </h3>

      <div className="space-y-3">
        {/* Test Connection */}
        <Button
          variant="default"
          size="sm"
          onClick={handleTestConnection}
          loading={isTestLoading}
          disabled={isTestLoading}
          className="w-full"
        >
          <PlayIcon className="w-4 h-4 mr-2" />
          Test Connection
        </Button>

        {/* Status Toggle */}
        {statusAction && (
          <Button
            variant={statusAction.variant}
            size="sm"
            onClick={statusAction.action}
            className="w-full"
          >
            <statusAction.icon className="w-4 h-4 mr-2" />
            {statusAction.label}
          </Button>
        )}

        {/* Delete Integration */}
        {!showDeleteConfirm ? (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDeleteConfirm(true)}
            className="w-full text-red-600 border-red-300 hover:bg-red-50 hover:border-red-400"
          >
            <TrashIcon className="w-4 h-4 mr-2" />
            Delete Integration
          </Button>
        ) : (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center mb-3">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-600 mr-2" />
              <span className="text-sm font-medium text-red-800">Confirm Deletion</span>
            </div>
            <p className="text-sm text-red-700 mb-3">
              This action cannot be undone. All configuration and historical data will be lost.
            </p>
            <div className="flex space-x-2">
              <Button
                variant="default"
                size="sm"
                onClick={handleDelete}
                loading={isDeleteLoading}
                disabled={isDeleteLoading}
                className="flex-1 bg-red-600 hover:bg-red-700"
              >
                <TrashIcon className="w-4 h-4 mr-2" />
                Delete
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleteLoading}
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Test Result */}
      {testResult && (
        <div className={`mt-4 p-3 rounded-lg border ${
          testResult.success 
            ? 'bg-green-50 border-green-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <div className="flex items-center mb-2">
            {testResult.success ? (
              <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2" />
            ) : (
              <XCircleIcon className="w-5 h-5 text-red-600 mr-2" />
            )}
            <span className={`text-sm font-medium ${
              testResult.success ? 'text-green-800' : 'text-red-800'
            }`}>
              {testResult.success ? 'Test Successful' : 'Test Failed'}
            </span>
          </div>
          <p className={`text-sm ${
            testResult.success ? 'text-green-700' : 'text-red-700'
          }`}>
            {testResult.message}
          </p>
          {testResult.details && (
            <details className="mt-2">
              <summary className={`text-xs cursor-pointer ${
                testResult.success ? 'text-green-600' : 'text-red-600'
              }`}>
                Show Details
              </summary>
              <pre className={`mt-2 text-xs p-2 rounded overflow-x-auto ${
                testResult.success 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {JSON.stringify(testResult.details, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}

      {/* Integration Status Info */}
      <div className="mt-6 pt-4 border-t border-neutral-200">
        <h4 className="text-sm font-medium text-neutral-700 mb-2">Status Information</h4>
        <div className="space-y-2 text-sm text-neutral-600">
          <div className="flex items-center justify-between">
            <span>Current Status:</span>
            <span className="capitalize font-medium">{integration.status}</span>
          </div>
          {integration.error_count !== undefined && (
            <div className="flex items-center justify-between">
              <span>Error Count:</span>
              <span className={integration.error_count > 0 ? 'text-red-600 font-medium' : 'text-green-600'}>
                {integration.error_count}
              </span>
            </div>
          )}
          {integration.last_error && (
            <div>
              <span className="block mb-1">Last Error:</span>
              <div className="bg-red-50 border border-red-200 rounded p-2">
                <p className="text-xs text-red-800">{integration.last_error}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}