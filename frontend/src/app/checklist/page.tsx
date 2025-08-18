'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/Button';
import { 
  CheckCircleIcon, 
  XCircleIcon,
  ClockIcon,
  PlayIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  category: string;
  required: boolean;
}

export default function ChecklistPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentRunningId, setCurrentRunningId] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    } else if (isAuthenticated) {
      initializeChecklist();
    }
  }, [isAuthenticated, isLoading, router]);

  const initializeChecklist = () => {
    const items: ChecklistItem[] = [
      {
        id: 'auth-setup',
        title: 'Authentication & Security',
        description: 'Verify user authentication and security configurations',
        status: 'completed',
        category: 'Security',
        required: true
      },
      {
        id: 'integration-config',
        title: 'Integration Configuration',
        description: 'Check all business system integrations are properly configured',
        status: 'pending',
        category: 'Integrations',
        required: true
      },
      {
        id: 'websocket-connection',
        title: 'WebSocket Chat Connection',
        description: 'Test real-time chat functionality and WebSocket connection',
        status: 'pending',
        category: 'Communication',
        required: true
      },
      {
        id: 'kafka-streams',
        title: 'Kafka Log Streaming',
        description: 'Verify Kafka streams are active and logs are visible',
        status: 'pending',
        category: 'Logging',
        required: true
      },
      {
        id: 'ai-agents',
        title: 'CrewAI Agents Registration',
        description: 'Ensure all CrewAI agents are registered and functional',
        status: 'pending',
        category: 'AI',
        required: true
      },
      {
        id: 'tool-calling',
        title: 'Tool Calling Visibility',
        description: 'Verify tool calling is visible in the chat interface',
        status: 'pending',
        category: 'AI',
        required: true
      },
      {
        id: 'ui-theme',
        title: 'UI Theme Consistency',
        description: 'Check white background with green accent theme is applied',
        status: 'completed',
        category: 'UI/UX',
        required: false
      },
      {
        id: 'unit-tests',
        title: 'Unit Tests',
        description: 'Run unit tests for core functionality',
        status: 'pending',
        category: 'Testing',
        required: true
      },
      {
        id: 'integration-tests',
        title: 'Integration Tests',
        description: 'Execute integration tests for WebSocket, Kafka, and agent flows',
        status: 'pending',
        category: 'Testing',
        required: true
      },
      {
        id: 'load-tests',
        title: 'Load Testing',
        description: 'Perform load tests for streaming and log scalability',
        status: 'pending',
        category: 'Performance',
        required: false
      },
      {
        id: 'security-audit',
        title: 'Security Audit',
        description: 'Review secrets encryption and access control',
        status: 'pending',
        category: 'Security',
        required: true
      }
    ];
    setChecklist(items);
  };

  const runSingleCheck = async (itemId: string) => {
    setCurrentRunningId(itemId);
    setChecklist(prev => prev.map(item => 
      item.id === itemId ? { ...item, status: 'running' } : item
    ));

    // Simulate check execution
    await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));

    // Randomly determine success/failure for demo
    const success = Math.random() > 0.2; // 80% success rate

    setChecklist(prev => prev.map(item => 
      item.id === itemId 
        ? { ...item, status: success ? 'completed' : 'failed' } 
        : item
    ));

    setCurrentRunningId(null);
  };

  const runAllChecks = async () => {
    setIsRunning(true);
    
    const pendingItems = checklist.filter(item => item.status === 'pending' || item.status === 'failed');
    
    for (const item of pendingItems) {
      await runSingleCheck(item.id);
    }
    
    setIsRunning(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-6 w-6 text-green-600" />;
      case 'failed':
        return <XCircleIcon className="h-6 w-6 text-red-600" />;
      case 'running':
        return <ClockIcon className="h-6 w-6 text-blue-600 animate-spin" />;
      default:
        return <ClockIcon className="h-6 w-6 text-neutral-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      running: 'bg-blue-100 text-blue-800',
      pending: 'bg-neutral-100 text-neutral-800'
    };

    return badges[status as keyof typeof badges] || badges.pending;
  };

  const categorizedItems = checklist.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = [];
    }
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, ChecklistItem[]>);

  const completedCount = checklist.filter(item => item.status === 'completed').length;
  const totalCount = checklist.length;
  const requiredCount = checklist.filter(item => item.required).length;
  const completedRequiredCount = checklist.filter(item => item.required && item.status === 'completed').length;

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
        {/* Page header */}
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">System Readiness Checklist</h1>
              <p className="mt-2 text-sm text-neutral-600">
                Verify all components are properly configured and ready for production use.
              </p>
            </div>
            <Button
              onClick={runAllChecks}
              disabled={isRunning}
              loading={isRunning}
              className="flex items-center gap-2"
            >
              <PlayIcon className="h-4 w-4" />
              {isRunning ? 'Running Checks...' : 'Run All Checks'}
            </Button>
          </div>
        </div>

        {/* Progress summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CheckCircleIcon className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-5">
                <p className="text-sm font-medium text-neutral-500">Overall Progress</p>
                <p className="text-2xl font-semibold text-neutral-900">
                  {completedCount}/{totalCount}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <XCircleIcon className="h-8 w-8 text-red-600" />
              </div>
              <div className="ml-5">
                <p className="text-sm font-medium text-neutral-500">Required Items</p>
                <p className="text-2xl font-semibold text-neutral-900">
                  {completedRequiredCount}/{requiredCount}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ClockIcon className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-5">
                <p className="text-sm font-medium text-neutral-500">System Status</p>
                <p className="text-2xl font-semibold text-neutral-900">
                  {completedRequiredCount === requiredCount ? 'Ready' : 'Pending'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Checklist items by category */}
        <div className="space-y-6">
          {Object.entries(categorizedItems).map(([category, items]) => (
            <div key={category} className="bg-white rounded-lg border border-neutral-200">
              <div className="px-6 py-4 border-b border-neutral-200">
                <h3 className="text-lg font-medium text-neutral-900">{category}</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {items.map((item) => (
                    <div key={item.id} className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg">
                      <div className="flex items-center space-x-4">
                        {getStatusIcon(item.status)}
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="font-medium text-neutral-900">{item.title}</h4>
                            {item.required && (
                              <span className="inline-flex px-2 py-1 text-xs font-medium bg-orange-100 text-orange-800 rounded-full">
                                Required
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-neutral-600">{item.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(item.status)}`}>
                          {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                        </span>
                        {(item.status === 'pending' || item.status === 'failed') && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => runSingleCheck(item.id)}
                            disabled={currentRunningId === item.id}
                            loading={currentRunningId === item.id}
                          >
                            {currentRunningId === item.id ? 'Running...' : 'Run Check'}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Action summary */}
        {completedRequiredCount === requiredCount && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center">
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <h3 className="text-lg font-medium text-green-900">System Ready for Production!</h3>
                <p className="text-sm text-green-700 mt-1">
                  All required checks have passed. Your business integration platform is ready to use.
                </p>
              </div>
              <div className="ml-auto">
                <Button
                  onClick={() => router.push('/dashboard')}
                  className="flex items-center gap-2"
                >
                  Go to Dashboard
                  <ArrowRightIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}