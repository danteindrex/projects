'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

export default function AnalyticsPage() {
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

  // Mock analytics data
  const analyticsData = [
    {
      title: 'Integration Performance',
      value: '98.5%',
      change: '+2.1%',
      trend: 'up',
      icon: ChartBarIcon,
      color: 'green'
    },
    {
      title: 'API Calls Today',
      value: '1,247',
      change: '+15%',
      trend: 'up',
      icon: ArrowTrendingUpIcon,
      color: 'blue'
    },
    {
      title: 'Average Response Time',
      value: '245ms',
      change: '-12ms',
      trend: 'down',
      icon: ClockIcon,
      color: 'yellow'
    },
    {
      title: 'Active Connections',
      value: '12',
      change: '+2',
      trend: 'up',
      icon: CheckCircleIcon,
      color: 'green'
    }
  ];

  const recentAlerts = [
    {
      id: 1,
      type: 'warning',
      message: 'Zendesk API response time increased',
      time: '5 minutes ago',
      status: 'active'
    },
    {
      id: 2,
      type: 'success',
      message: 'Jira integration health check passed',
      time: '15 minutes ago',
      status: 'resolved'
    },
    {
      id: 3,
      type: 'info',
      message: 'New integration added: GitHub',
      time: '1 hour ago',
      status: 'info'
    }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <h1 className="text-2xl font-bold text-neutral-900">Analytics Dashboard</h1>
          <p className="mt-2 text-sm text-neutral-600">
            Monitor your integrations performance and system health in real-time.
          </p>
        </div>

        {/* Metrics grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {analyticsData.map((metric) => (
            <div
              key={metric.title}
              className="bg-white overflow-hidden rounded-lg border border-neutral-200 p-6"
            >
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <metric.icon 
                    className={`h-8 w-8 ${
                      metric.color === 'green' ? 'text-green-600' :
                      metric.color === 'blue' ? 'text-blue-600' :
                      metric.color === 'yellow' ? 'text-yellow-600' : 'text-neutral-600'
                    }`} 
                  />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-neutral-500 truncate">
                      {metric.title}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-neutral-900">
                        {metric.value}
                      </div>
                      <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                        metric.trend === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {metric.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Chart */}
          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <h3 className="text-lg font-medium text-neutral-900 mb-4">
              Integration Performance (24h)
            </h3>
            <div className="h-64 flex items-center justify-center bg-neutral-50 rounded-lg">
              <div className="text-center text-neutral-500">
                <ChartBarIcon className="h-12 w-12 mx-auto mb-2" />
                <p>Chart visualization would appear here</p>
                <p className="text-sm">Connect to real analytics service</p>
              </div>
            </div>
          </div>

          {/* API Usage Chart */}
          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <h3 className="text-lg font-medium text-neutral-900 mb-4">
              API Usage Trends
            </h3>
            <div className="h-64 flex items-center justify-center bg-neutral-50 rounded-lg">
              <div className="text-center text-neutral-500">
                <ArrowTrendingUpIcon className="h-12 w-12 mx-auto mb-2" />
                <p>Usage trends would appear here</p>
                <p className="text-sm">Real-time data visualization</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent alerts */}
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <h3 className="text-lg font-medium text-neutral-900 mb-4">
            Recent Alerts & Events
          </h3>
          <div className="space-y-4">
            {recentAlerts.map((alert) => (
              <div key={alert.id} className="flex items-center space-x-3 p-3 bg-neutral-50 rounded-lg">
                <div>
                  {alert.type === 'warning' && (
                    <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />
                  )}
                  {alert.type === 'success' && (
                    <CheckCircleIcon className="h-6 w-6 text-green-500" />
                  )}
                  {alert.type === 'info' && (
                    <ChartBarIcon className="h-6 w-6 text-blue-500" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-neutral-900">{alert.message}</p>
                  <p className="text-xs text-neutral-500">{alert.time}</p>
                </div>
                <div>
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                    alert.status === 'active' ? 'bg-yellow-100 text-yellow-800' :
                    alert.status === 'resolved' ? 'bg-green-100 text-green-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {alert.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}