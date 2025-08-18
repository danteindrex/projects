'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { CogIcon, UserGroupIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';

export default function AdminPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
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
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <h1 className="text-2xl font-bold text-neutral-900">Admin Panel</h1>
          <p className="mt-2 text-sm text-neutral-600">
            System administration and configuration settings.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <CogIcon className="h-8 w-8 text-primary-600" />
              <h3 className="text-lg font-semibold text-neutral-900">System Configuration</h3>
            </div>
            <p className="text-neutral-600 text-sm">
              Configure system-wide settings, API limits, and integration defaults.
            </p>
          </div>

          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <UserGroupIcon className="h-8 w-8 text-teal-600" />
              <h3 className="text-lg font-semibold text-neutral-900">User Management</h3>
            </div>
            <p className="text-neutral-600 text-sm">
              Manage user accounts, roles, and permissions across the platform.
            </p>
          </div>

          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <ShieldCheckIcon className="h-8 w-8 text-green-600" />
              <h3 className="text-lg font-semibold text-neutral-900">Security Settings</h3>
            </div>
            <p className="text-neutral-600 text-sm">
              Configure authentication, encryption, and security policies.
            </p>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-2">Coming Soon</h3>
          <p className="text-blue-800 text-sm">
            Admin panel functionality is currently under development. Full administrative features will be available in the next release.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}