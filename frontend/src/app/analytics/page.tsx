'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import SystemHealthDashboard from '@/components/monitoring/SystemHealthDashboard';
import IntegrationMonitoringPanel from '@/components/monitoring/IntegrationMonitoringPanel';
import RealTimeActivityFeed from '@/components/monitoring/RealTimeActivityFeed';
import AlertsNotifications from '@/components/monitoring/AlertsNotifications';
import KafkaMonitoringWidget from '@/components/monitoring/KafkaMonitoringWidget';
import IntegrationAnalytics from '@/components/analytics/IntegrationAnalytics';
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  Cog6ToothIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

export default function AnalyticsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'overview' | 'integrations' | 'analytics' | 'realtime' | 'alerts' | 'kafka'>('overview');

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

  const tabs = [
    { id: 'overview', name: 'System Health', icon: ChartBarIcon },
    { id: 'integrations', name: 'Integrations', icon: Cog6ToothIcon },
    { id: 'analytics', name: 'Integration Analytics', icon: ArrowTrendingUpIcon },
    { id: 'realtime', name: 'Live Activity', icon: EyeIcon },
    { id: 'alerts', name: 'Alerts', icon: ExclamationTriangleIcon },
    { id: 'kafka', name: 'Kafka', icon: ClockIcon }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <h1 className="text-2xl font-bold text-neutral-900">Analytics & Monitoring Dashboard</h1>
          <p className="mt-2 text-sm text-neutral-600">
            Monitor your integrations performance, system health, and real-time activity across all business systems.
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg border border-neutral-200">
          <div className="border-b border-neutral-200">
            <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
                >
                  <tab.icon className="h-5 w-5" />
                  <span>{tab.name}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <SystemHealthDashboard />
                
                {/* Note: Quick stats will be populated from real system data via SystemHealthDashboard */}
              </div>
            )}

            {activeTab === 'integrations' && (
              <IntegrationMonitoringPanel />
            )}

            {activeTab === 'analytics' && (
              <IntegrationAnalytics />
            )}

            {activeTab === 'realtime' && (
              <RealTimeActivityFeed />
            )}

            {activeTab === 'alerts' && (
              <AlertsNotifications />
            )}

            {activeTab === 'kafka' && (
              <KafkaMonitoringWidget />
            )}
          </div>
        </div>

        {/* Additional Information Panel */}
        <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg border border-primary-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <ChartBarIcon className="h-6 w-6 text-primary-600" />
            <h3 className="text-lg font-medium text-primary-900">Monitoring Information</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-sm">
            <div>
              <h4 className="font-medium text-primary-900 mb-2">System Health</h4>
              <ul className="space-y-1 text-primary-700">
                <li>• Real-time system resource monitoring</li>
                <li>• Component health status tracking</li>
                <li>• Automated alert generation</li>
                <li>• Performance metrics collection</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-primary-900 mb-2">Integration Monitoring</h4>
              <ul className="space-y-1 text-primary-700">
                <li>• API call success/failure tracking</li>
                <li>• Response time monitoring</li>
                <li>• Rate limit detection</li>
                <li>• Authentication status checks</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-primary-900 mb-2">Real-time Events</h4>
              <ul className="space-y-1 text-primary-700">
                <li>• Live WebSocket event streaming</li>
                <li>• Kafka message broker integration</li>
                <li>• Event filtering and search</li>
                <li>• Historical event tracking</li>
              </ul>
            </div>
          </div>
          
          <div className="mt-6 pt-4 border-t border-primary-200">
            <div className="flex items-center justify-between">
              <p className="text-sm text-primary-700">
                All monitoring data is updated in real-time and stored for historical analysis.
              </p>
              <div className="flex items-center space-x-4 text-xs text-primary-600">
                <a href="http://localhost:8001/docs" target="_blank" rel="noopener noreferrer" className="hover:underline">
                  API Documentation
                </a>
                <span>•</span>
                <a href="http://localhost:8080" target="_blank" rel="noopener noreferrer" className="hover:underline">
                  Kafka UI
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}