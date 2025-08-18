'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { UserGroupIcon, PlusIcon, UserIcon } from '@heroicons/react/24/outline';

export default function TeamPage() {
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

  // Mock team data
  const teamMembers = [
    {
      id: 1,
      name: 'Current User',
      email: 'you@company.com',
      role: 'Admin',
      status: 'Active',
      avatar: null
    }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">Team Management</h1>
              <p className="mt-2 text-sm text-neutral-600">
                Manage your team members and their access to integrations.
              </p>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              <PlusIcon className="h-4 w-4" />
              Invite Member
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-neutral-200">
          <div className="px-6 py-4 border-b border-neutral-200">
            <h3 className="text-lg font-medium text-neutral-900">Team Members</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {teamMembers.map((member) => (
                <div key={member.id} className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
                      <UserIcon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h4 className="font-medium text-neutral-900">{member.name}</h4>
                      <p className="text-sm text-neutral-600">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                      {member.status}
                    </span>
                    <span className="inline-flex px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                      {member.role}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-blue-900 mb-2">Team Collaboration Features</h3>
          <p className="text-blue-800 text-sm mb-4">
            Team management features are coming soon. You&apos;ll be able to invite team members, manage permissions, and collaborate on integrations.
          </p>
          <ul className="text-blue-800 text-sm space-y-1">
            <li>• Invite team members via email</li>
            <li>• Assign role-based permissions</li>
            <li>• Share integrations and chat sessions</li>
            <li>• Audit team activity and access logs</li>
          </ul>
        </div>
      </div>
    </DashboardLayout>
  );
}