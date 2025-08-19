'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { IntegrationDetail } from '@/components/integrations/IntegrationDetail';
import { apiClient, Integration } from '@/lib/api';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';

export default function IntegrationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [integration, setIntegration] = useState<Integration | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const integrationId = parseInt(params.id as string);

  useEffect(() => {
    if (!integrationId || isNaN(integrationId)) {
      setError('Invalid integration ID');
      setLoading(false);
      return;
    }

    fetchIntegration();
  }, [integrationId]);

  const fetchIntegration = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getIntegration(integrationId);
      setIntegration(data);
    } catch (err) {
      console.error('Error fetching integration:', err);
      setError(err instanceof Error ? err.message : 'Failed to load integration');
    } finally {
      setLoading(false);
    }
  };

  const handleIntegrationUpdated = (updatedIntegration: Integration) => {
    setIntegration(updatedIntegration);
  };

  const handleIntegrationDeleted = () => {
    router.push('/integrations');
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-neutral-50">
          <div className="px-6 py-8">
            {/* Loading skeleton */}
            <div className="animate-pulse">
              <div className="flex items-center mb-8">
                <div className="w-8 h-8 bg-neutral-200 rounded mr-4"></div>
                <div className="h-8 bg-neutral-200 rounded w-64"></div>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-8">
                <div className="space-y-6">
                  <div className="h-6 bg-neutral-200 rounded w-1/4"></div>
                  <div className="h-4 bg-neutral-200 rounded w-1/2"></div>
                  <div className="h-32 bg-neutral-200 rounded"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !integration) {
    return (
      <DashboardLayout>
        <div className="min-h-screen bg-neutral-50">
          <div className="px-6 py-8">
            <div className="flex items-center mb-8">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/integrations')}
                className="mr-4"
              >
                <ArrowLeftIcon className="w-4 h-4 mr-2" />
                Back to Integrations
              </Button>
              <h1 className="text-2xl font-bold text-neutral-900">Integration Not Found</h1>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-8 text-center">
              <div className="text-6xl mb-4">❌</div>
              <h2 className="text-xl font-semibold text-neutral-900 mb-2">
                Integration Not Found
              </h2>
              <p className="text-neutral-600 mb-6">
                {error || 'The integration you\'re looking for doesn\'t exist or has been removed.'}
              </p>
              <Button
                onClick={() => router.push('/integrations')}
                variant="default"
              >
                Back to Integrations
              </Button>
            </div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="min-h-screen bg-neutral-50">
        <div className="px-6 py-8">
          <div className="flex items-center mb-8">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/integrations')}
              className="mr-4"
            >
              <ArrowLeftIcon className="w-4 h-4 mr-2" />
              Back to Integrations
            </Button>
            <h1 className="text-2xl font-bold text-neutral-900">
              {integration.name}
            </h1>
          </div>

          <IntegrationDetail
            integration={integration}
            onIntegrationUpdated={handleIntegrationUpdated}
            onIntegrationDeleted={handleIntegrationDeleted}
            onRefresh={fetchIntegration}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}