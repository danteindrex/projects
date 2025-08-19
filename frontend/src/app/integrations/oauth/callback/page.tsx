'use client';

import React, { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { CheckCircleIcon, XCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface OAuthCallbackState {
  status: 'processing' | 'success' | 'error';
  message: string;
  integration?: any;
}

export default function OAuthCallback() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [state, setState] = useState<OAuthCallbackState>({
    status: 'processing',
    message: 'Processing OAuth callback...'
  });

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');

        // Check for OAuth errors
        if (error) {
          setState({
            status: 'error',
            message: errorDescription || `OAuth error: ${error}`
          });
          return;
        }

        if (!code || !state) {
          setState({
            status: 'error',
            message: 'Missing authorization code or state parameter'
          });
          return;
        }

        // Retrieve OAuth flow data from sessionStorage
        const oauthData = sessionStorage.getItem(`oauth_${state}`);
        if (!oauthData) {
          setState({
            status: 'error',
            message: 'OAuth session expired or invalid. Please try again.'
          });
          return;
        }

        const {
          integration_type,
          client_id,
          client_secret,
          name,
          description,
          config
        } = JSON.parse(oauthData);

        setState({
          status: 'processing',
          message: 'Exchanging authorization code for access token...'
        });

        // Complete OAuth flow
        const integration = await apiClient.completeOAuth({
          integration_type,
          authorization_code: code,
          state,
          client_id,
          client_secret,
          name,
          description,
          config
        });

        // Clean up session storage
        sessionStorage.removeItem(`oauth_${state}`);

        setState({
          status: 'success',
          message: 'Integration created successfully!',
          integration
        });

        // Redirect to integrations page after a delay
        setTimeout(() => {
          router.push('/integrations');
        }, 3000);

      } catch (error) {
        console.error('OAuth callback error:', error);
        setState({
          status: 'error',
          message: error instanceof Error ? error.message : 'Failed to complete OAuth flow'
        });
      }
    };

    handleCallback();
  }, [searchParams, router]);

  const handleRetry = () => {
    router.push('/integrations');
  };

  return (
    <div className="min-h-screen bg-neutral-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full mb-4">
            {state.status === 'processing' && (
              <ArrowPathIcon className="h-12 w-12 text-primary-600 animate-spin" />
            )}
            {state.status === 'success' && (
              <CheckCircleIcon className="h-12 w-12 text-green-600" />
            )}
            {state.status === 'error' && (
              <XCircleIcon className="h-12 w-12 text-red-600" />
            )}
          </div>
          
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-neutral-900">
            {state.status === 'processing' && 'Processing OAuth'}
            {state.status === 'success' && 'Integration Complete'}
            {state.status === 'error' && 'OAuth Failed'}
          </h2>
          
          <p className="mt-2 text-center text-sm text-neutral-600">
            {state.message}
          </p>

          {state.integration && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="text-sm text-green-800">
                <p className="font-medium">{state.integration.name}</p>
                <p className="text-green-600">
                  Status: {state.integration.status}
                  {state.integration.health_status && ` • Health: ${state.integration.health_status}`}
                </p>
              </div>
            </div>
          )}

          {state.status === 'success' && (
            <p className="mt-4 text-sm text-neutral-500">
              Redirecting to integrations page...
            </p>
          )}

          {state.status === 'error' && (
            <div className="mt-6">
              <button
                onClick={handleRetry}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Return to Integrations
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}