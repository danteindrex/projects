'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { PlusIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { apiClient } from '@/lib/api';
import { 
  PuzzlePieceIcon, 
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CpuChipIcon,
  ShieldCheckIcon,
  BoltIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

export default function DashboardPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [dashboardData, setDashboardData] = useState({
    integrations: [],
    recentActivity: [],
    stats: {
      activeIntegrations: 0,
      chatSessions: 0,
      systemHealth: 0,
      pendingTasks: 0
    },
    loading: true,
    error: null
  });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboardData();
    }
  }, [isAuthenticated]);

  const loadDashboardData = async () => {
    try {
      setDashboardData(prev => ({ ...prev, loading: true, error: null }));
      
      const [integrations, chatSessions] = await Promise.all([
        apiClient.getIntegrations().catch(() => []),
        apiClient.getChatSessions().catch(() => [])
      ]);

      // Calculate real stats
      const activeIntegrations = integrations.filter(i => i.status === 'active').length;
      const totalIntegrations = integrations.length;
      const systemHealth = totalIntegrations > 0 ? 
        Math.round((activeIntegrations / totalIntegrations) * 100) : 100;

      // Get recent activity from integrations with enhanced monitoring info
      const recentActivity = integrations
        .filter(i => i.last_sync || i.created_at)
        .sort((a, b) => new Date(b.last_sync || b.created_at) - new Date(a.last_sync || a.created_at))
        .slice(0, 6)
        .map((integration, index) => {
          const getActivityMessage = (integration) => {
            if (integration.status === 'active') {
              const metrics = integration.config?.monitoring_preferences || [];
              const primaryMetric = metrics[0]?.replace('_', ' ') || 'system data';
              return `${integration.name} monitoring ${primaryMetric} - All systems healthy`;
            } else if (integration.status === 'error') {
              return `${integration.name} connection failed - Requires attention`;
            } else {
              return `${integration.name} is being configured`;
            }
          };
          
          return {
            id: integration.id,
            type: 'integration',
            message: getActivityMessage(integration),
            time: getRelativeTime(integration.last_sync || integration.created_at),
            status: integration.status === 'active' ? 'success' : integration.status === 'error' ? 'error' : 'warning',
            integration_type: integration.integration_type,
            metrics_count: integration.config?.monitoring_preferences?.length || 0
          };
        });

      setDashboardData({
        integrations,
        recentActivity,
        stats: {
          activeIntegrations: totalIntegrations,
          chatSessions: chatSessions.length,
          systemHealth,
          pendingTasks: integrations.filter(i => i.status === 'error').length
        },
        loading: false,
        error: null
      });
    } catch (error) {
      setDashboardData(prev => ({
        ...prev,
        loading: false,
        error: error.message || 'Failed to load dashboard data'
      }));
    }
  };

  const getRelativeTime = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} hours ago`;
    return `${Math.floor(diffInMinutes / 1440)} days ago`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
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

  // Real data from API
  const stats = [
    { 
      name: 'Active Integrations', 
      value: dashboardData.stats.activeIntegrations.toString(), 
      change: dashboardData.integrations.length > 0 ? '+' + dashboardData.integrations.filter(i => i.status === 'active').length : '0',
      changeType: 'positive', 
      icon: PuzzlePieceIcon 
    },
    { 
      name: 'Chat Sessions', 
      value: dashboardData.stats.chatSessions.toString(), 
      change: dashboardData.stats.chatSessions > 0 ? '+' + dashboardData.stats.chatSessions : '0',
      changeType: 'positive', 
      icon: ChatBubbleLeftRightIcon 
    },
    { 
      name: 'System Health', 
      value: dashboardData.stats.systemHealth + '%', 
      change: dashboardData.stats.systemHealth >= 90 ? '+' + (dashboardData.stats.systemHealth - 90) + '%' : '-' + (90 - dashboardData.stats.systemHealth) + '%',
      changeType: dashboardData.stats.systemHealth >= 90 ? 'positive' : 'negative', 
      icon: CheckCircleIcon 
    },
    { 
      name: 'Pending Tasks', 
      value: dashboardData.stats.pendingTasks.toString(), 
      change: dashboardData.stats.pendingTasks > 0 ? '+' + dashboardData.stats.pendingTasks : '0',
      changeType: dashboardData.stats.pendingTasks > 0 ? 'negative' : 'positive', 
      icon: ClockIcon 
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Dashboard</h1>
          <p className="mt-2 text-sm text-neutral-600">
            Welcome back! Here&apos;s what&apos;s happening with your business systems.
          </p>
        </div>

        {/* Enhanced Stats grid with system monitoring */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.name}
              className="relative overflow-hidden rounded-xl bg-white px-6 py-6 shadow-lg border border-neutral-100 hover:shadow-xl transition-all duration-300 hover:border-green-200"
            >
              <dt>
                <div className={`absolute rounded-lg p-3 ${
                  stat.name === 'System Health' 
                    ? dashboardData.stats.systemHealth >= 90 
                      ? 'bg-green-500' 
                      : dashboardData.stats.systemHealth >= 70 
                        ? 'bg-yellow-500' 
                        : 'bg-red-500'
                    : stat.name === 'Pending Tasks'
                      ? dashboardData.stats.pendingTasks > 0
                        ? 'bg-orange-500'
                        : 'bg-green-500'
                      : 'bg-green-600'
                }`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
                <p className="ml-16 truncate text-sm font-medium text-neutral-600">
                  {stat.name}
                </p>
              </dt>
              <dd className="ml-16 flex items-baseline">
                <p className="text-2xl font-semibold text-neutral-900">{stat.value}</p>
                <p
                  className={`ml-2 flex items-baseline text-sm font-semibold ${
                    stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {stat.change}
                </p>
              </dd>
              {/* Add health indicator for System Health */}
              {stat.name === 'System Health' && (
                <div className="mt-2 ml-16">
                  <div className="w-full bg-neutral-200 rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full transition-all duration-300 ${
                        dashboardData.stats.systemHealth >= 90 
                          ? 'bg-green-500' 
                          : dashboardData.stats.systemHealth >= 70 
                            ? 'bg-yellow-500' 
                            : 'bg-red-500'
                      }`}
                      style={{ width: `${dashboardData.stats.systemHealth}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="bg-white shadow-lg rounded-xl border border-neutral-100">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-neutral-900 mb-4">
              Quick Actions
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Link 
                href="/integrations"
                className="flex items-center p-6 border border-neutral-200 rounded-xl hover:bg-green-50 hover:border-green-300 transition-all duration-300 group hover:shadow-md"
              >
                <div className="p-2 bg-green-100 rounded-lg mr-4 group-hover:bg-green-200 transition-colors">
                  <PuzzlePieceIcon className="h-8 w-8 text-green-600 group-hover:text-green-700" />
                </div>
                <div className="text-left">
                  <p className="font-semibold text-neutral-900 group-hover:text-green-900">Add Integration</p>
                  <p className="text-sm text-neutral-600">Connect a new business system</p>
                </div>
              </Link>
              
              <Link 
                href="/chat"
                className="flex items-center p-6 border border-neutral-200 rounded-xl hover:bg-green-50 hover:border-green-300 transition-all duration-300 group hover:shadow-md"
              >
                <div className="p-2 bg-green-100 rounded-lg mr-4 group-hover:bg-green-200 transition-colors">
                  <ChatBubbleLeftRightIcon className="h-8 w-8 text-green-600 group-hover:text-green-700" />
                </div>
                <div className="text-left">
                  <p className="font-semibold text-neutral-900 group-hover:text-green-900">Start Chat</p>
                  <p className="text-sm text-neutral-600">Ask about your systems</p>
                </div>
              </Link>
              
              <Link 
                href="/checklist"
                className="flex items-center p-6 border border-neutral-200 rounded-xl hover:bg-green-50 hover:border-green-300 transition-all duration-300 group hover:shadow-md"
              >
                <div className="p-2 bg-green-100 rounded-lg mr-4 group-hover:bg-green-200 transition-colors">
                  <CheckCircleIcon className="h-8 w-8 text-green-600 group-hover:text-green-700" />
                </div>
                <div className="text-left">
                  <p className="font-semibold text-neutral-900 group-hover:text-green-900">Run Checklist</p>
                  <p className="text-sm text-neutral-600">Verify system readiness</p>
                </div>
              </Link>
            </div>
          </div>
        </div>

        {/* Recent activity */}
        <div className="bg-white shadow-lg rounded-xl border border-neutral-100">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-neutral-900 mb-4">
              Recent Activity
            </h3>
            {dashboardData.loading ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-2 text-sm text-neutral-600">Loading monitoring data...</p>
              </div>
            ) : dashboardData.error ? (
              <div className="text-center py-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <ExclamationTriangleIcon className="h-8 w-8 text-red-500 mx-auto mb-2" />
                  <p className="text-red-700 font-medium">Monitoring Error</p>
                  <p className="text-red-600 text-sm mt-1">{dashboardData.error}</p>
                  <button 
                    onClick={loadDashboardData}
                    className="mt-3 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 text-sm font-medium transition-colors"
                  >
                    Retry Connection
                  </button>
                </div>
              </div>
            ) : dashboardData.recentActivity.length === 0 ? (
              <div className="text-center py-8">
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-8">
                  <CpuChipIcon className="h-16 w-16 text-green-500 mx-auto mb-4" />
                  <h4 className="text-lg font-semibold text-neutral-800 mb-2">System Monitoring Ready</h4>
                  <p className="text-neutral-600 mb-4">
                    Connect your business systems to start monitoring performance, health, and key metrics with AI-powered insights.
                  </p>
                  <div className="grid grid-cols-2 gap-3 text-sm text-neutral-500 mb-6">
                    <div className="flex items-center justify-center space-x-2">
                      <ChartBarIcon className="h-4 w-4" />
                      <span>Real-time Metrics</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2">
                      <ShieldCheckIcon className="h-4 w-4" />
                      <span>Health Monitoring</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2">
                      <BoltIcon className="h-4 w-4" />
                      <span>Automated Alerts</span>
                    </div>
                    <div className="flex items-center justify-center space-x-2">
                      <ChatBubbleLeftRightIcon className="h-4 w-4" />
                      <span>AI Insights</span>
                    </div>
                  </div>
                  <button 
                    onClick={() => window.location.href = '/integrations'}
                    className="inline-flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold shadow-md hover:shadow-lg"
                  >
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Add Your First System
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* System Status Overview */}
                <div className="bg-gradient-to-r from-green-50 to-green-100 rounded-xl p-6 border-2 border-green-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <ShieldCheckIcon className="h-6 w-6 text-green-600" />
                      <div>
                        <h4 className="font-semibold text-green-800">System Overview</h4>
                        <p className="text-sm text-green-700">
                          {dashboardData.integrations.filter(i => i.status === 'active').length} of {dashboardData.integrations.length} systems are healthy
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-green-800">{dashboardData.stats.systemHealth}%</p>
                      <p className="text-xs text-green-600">System Health</p>
                    </div>
                  </div>
                </div>

                {/* Activity Timeline */}
                <div className="flow-root">
                  <ul className="-mb-8">
                    {dashboardData.recentActivity.map((activity, activityIdx) => (
                    <li key={activity.id}>
                      <div className="relative pb-8">
                        {activityIdx !== dashboardData.recentActivity.length - 1 ? (
                          <span
                            className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-neutral-200"
                            aria-hidden="true"
                          />
                        ) : null}
                        <div className="relative flex space-x-3">
                          <div>
                            <span
                              className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${
                                activity.status === 'success'
                                  ? 'bg-green-500'
                                  : activity.status === 'error'
                                  ? 'bg-red-500'
                                  : activity.status === 'warning'
                                  ? 'bg-yellow-500'
                                  : 'bg-blue-500'
                              }`}
                            >
                              {activity.status === 'success' && <CheckCircleIcon className="h-5 w-5 text-white" />}
                              {activity.status === 'error' && <ExclamationTriangleIcon className="h-5 w-5 text-white" />}
                              {activity.status === 'warning' && <ClockIcon className="h-5 w-5 text-white" />}
                              {activity.status === 'info' && <ChatBubbleLeftRightIcon className="h-5 w-5 text-white" />}
                            </span>
                          </div>
                          <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                            <div className="flex-1">
                              <p className="text-sm text-neutral-900 font-medium">{activity.message}</p>
                              <div className="mt-1 flex items-center space-x-3">
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-neutral-100 text-neutral-600">
                                  {activity.integration_type?.replace('_', ' ') || 'Unknown'}
                                </span>
                                {activity.metrics_count > 0 && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-700">
                                    <ChartBarIcon className="h-3 w-3 mr-1" />
                                    {activity.metrics_count} metrics
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="whitespace-nowrap text-right text-sm text-neutral-500">
                              {activity.time}
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
