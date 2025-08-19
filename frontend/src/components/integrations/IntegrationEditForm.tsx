'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Integration, IntegrationUpdate, apiClient } from '@/lib/api';
import { INTEGRATION_TYPES, INTEGRATION_ICONS, INTEGRATION_NAMES } from '@/lib/integrationTypes';
import { Button } from '@/components/ui/Button';
import {
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const editSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  description: z.string().optional(),
  base_url: z.string().url('Please enter a valid URL').optional().or(z.literal('')),
  rate_limit: z.number().min(1).optional().or(z.literal(0)),
  timeout: z.number().min(1).max(300).optional().or(z.literal(0)),
  status: z.enum(['active', 'inactive', 'error', 'pending', 'configured']),
  api_key: z.string().optional(),
  username: z.string().optional(),
  password: z.string().optional(),
  api_token: z.string().optional(),
  access_key: z.string().optional(),
  secret_key: z.string().optional(),
  client_id: z.string().optional(),
  client_secret: z.string().optional(),
  tenant_id: z.string().optional(),
  subscription_id: z.string().optional(),
  region: z.string().optional(),
  refresh_token: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

interface IntegrationEditFormProps {
  integration: Integration;
  onSave: (integration: Integration) => void;
  onCancel: () => void;
}

export function IntegrationEditForm({ integration, onSave, onCancel }: IntegrationEditFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCredentials, setShowCredentials] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    watch,
    setValue,
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: integration.name,
      description: integration.description || '',
      base_url: integration.base_url || '',
      rate_limit: integration.rate_limit || 0,
      timeout: integration.timeout || 0,
      status: integration.status,
      // Credentials - don't show existing values for security
      api_key: '',
      username: '',
      password: '',
      api_token: '',
      access_key: '',
      secret_key: '',
      client_id: '',
      client_secret: '',
      tenant_id: '',
      subscription_id: '',
      region: '',
      refresh_token: '',
    }
  });

  const integrationIcon = INTEGRATION_ICONS[integration.integration_type as keyof typeof INTEGRATION_ICONS] || '⚙️';
  const integrationName = INTEGRATION_NAMES[integration.integration_type as keyof typeof INTEGRATION_NAMES] || integration.integration_type;

  const onSubmit = async (data: EditFormData) => {
    setIsLoading(true);
    setError(null);

    try {
      // Prepare credentials object - only include non-empty values
      const credentials: Record<string, string> = { ...integration.credentials };
      const credentialFields = [
        'api_key', 'username', 'password', 'api_token', 'access_key', 
        'secret_key', 'client_id', 'client_secret', 'tenant_id', 
        'subscription_id', 'region', 'refresh_token'
      ];

      credentialFields.forEach(field => {
        const value = data[field as keyof EditFormData] as string;
        if (value && value.trim()) {
          credentials[field] = value.trim();
        }
      });

      const updateData: IntegrationUpdate = {
        name: data.name,
        description: data.description || undefined,
        base_url: data.base_url || undefined,
        rate_limit: data.rate_limit || undefined,
        timeout: data.timeout || undefined,
        status: data.status,
        credentials,
      };

      const updatedIntegration = await apiClient.updateIntegration(integration.id, updateData);
      onSave(updatedIntegration);
    } catch (err) {
      console.error('Error updating integration:', err);
      setError(err instanceof Error ? err.message : 'Failed to update integration');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'inactive':
        return 'text-yellow-600';
      default:
        return 'text-neutral-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{integrationIcon}</div>
          <div>
            <h2 className="text-xl font-bold text-neutral-900">Edit Integration</h2>
            <p className="text-sm text-neutral-600">{integrationName}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
        >
          <XMarkIcon className="w-4 h-4" />
        </Button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-600 flex-shrink-0" />
            <span className="text-red-800 text-sm">{error}</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Basic Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-neutral-700 mb-2">
              Integration Name *
            </label>
            <input
              {...register('name')}
              type="text"
              id="name"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="status" className="block text-sm font-medium text-neutral-700 mb-2">
              Status *
            </label>
            <select
              {...register('status')}
              id="status"
              className={`w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent ${getStatusColor(watch('status'))}`}
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="configured">Configured</option>
              <option value="pending">Pending</option>
              <option value="error">Error</option>
            </select>
            {errors.status && (
              <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>
            )}
          </div>
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium text-neutral-700 mb-2">
            Description
          </label>
          <textarea
            {...register('description')}
            id="description"
            rows={3}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Optional description of this integration"
          />
        </div>

        {/* Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label htmlFor="base_url" className="block text-sm font-medium text-neutral-700 mb-2">
              Base URL
            </label>
            <input
              {...register('base_url')}
              type="url"
              id="base_url"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="https://api.example.com"
            />
            {errors.base_url && (
              <p className="mt-1 text-sm text-red-600">{errors.base_url.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="rate_limit" className="block text-sm font-medium text-neutral-700 mb-2">
              Rate Limit (req/min)
            </label>
            <input
              {...register('rate_limit', { valueAsNumber: true })}
              type="number"
              id="rate_limit"
              min="0"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="0 = no limit"
            />
          </div>

          <div>
            <label htmlFor="timeout" className="block text-sm font-medium text-neutral-700 mb-2">
              Timeout (seconds)
            </label>
            <input
              {...register('timeout', { valueAsNumber: true })}
              type="number"
              id="timeout"
              min="1"
              max="300"
              className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="30"
            />
            {errors.timeout && (
              <p className="mt-1 text-sm text-red-600">{errors.timeout.message}</p>
            )}
          </div>
        </div>

        {/* Credentials Section */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-neutral-900">Credentials</h3>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowCredentials(!showCredentials)}
            >
              {showCredentials ? 'Hide' : 'Update'} Credentials
            </Button>
          </div>

          {showCredentials && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-neutral-50 rounded-lg">
              <div className="col-span-full">
                <p className="text-sm text-neutral-600 mb-4">
                  Only enter credentials that you want to update. Leave fields empty to keep existing values.
                </p>
              </div>

              <div>
                <label htmlFor="api_key" className="block text-sm font-medium text-neutral-700 mb-2">
                  API Key
                </label>
                <input
                  {...register('api_key')}
                  type="password"
                  id="api_key"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="api_token" className="block text-sm font-medium text-neutral-700 mb-2">
                  API Token
                </label>
                <input
                  {...register('api_token')}
                  type="password"
                  id="api_token"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="username" className="block text-sm font-medium text-neutral-700 mb-2">
                  Username
                </label>
                <input
                  {...register('username')}
                  type="text"
                  id="username"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-neutral-700 mb-2">
                  Password
                </label>
                <input
                  {...register('password')}
                  type="password"
                  id="password"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="client_id" className="block text-sm font-medium text-neutral-700 mb-2">
                  Client ID
                </label>
                <input
                  {...register('client_id')}
                  type="text"
                  id="client_id"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="client_secret" className="block text-sm font-medium text-neutral-700 mb-2">
                  Client Secret
                </label>
                <input
                  {...register('client_secret')}
                  type="password"
                  id="client_secret"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="access_key" className="block text-sm font-medium text-neutral-700 mb-2">
                  Access Key
                </label>
                <input
                  {...register('access_key')}
                  type="password"
                  id="access_key"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="secret_key" className="block text-sm font-medium text-neutral-700 mb-2">
                  Secret Key
                </label>
                <input
                  {...register('secret_key')}
                  type="password"
                  id="secret_key"
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-4 pt-6 border-t border-neutral-200">
          <Button
            type="button"
            variant="ghost"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            loading={isLoading}
            disabled={!isDirty}
          >
            <CheckCircleIcon className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </form>
    </div>
  );
}