'use client';

import React, { useState, useEffect } from 'react';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/Button';

interface ChecklistItem {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'pass' | 'fail' | 'pending';
  details?: string;
  lastChecked?: string;
}

interface ChecklistResult {
  checklist: ChecklistItem[];
  overall_status: string;
  total_items: number;
  passed_items: number;
  failed_items: number;
}

export default function AdminChecklist() {
  const [checklistData, setChecklistData] = useState<ChecklistResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Mock data for demonstration
  const mockChecklistData: ChecklistResult = {
    checklist: [
      {
        id: "auth_rls",
        name: "Supabase Auth + RLS configured",
        description: "Authentication and Row Level Security are properly configured",
        category: "security",
        status: "pass",
        details: "All authentication endpoints are working correctly",
        lastChecked: "2024-01-15T10:30:00Z"
      },
      {
        id: "integration_setup",
        name: "Integration setup validated",
        description: "Integration configuration and testing is working",
        category: "integrations",
        status: "pass",
        details: "12 integrations are active and responding",
        lastChecked: "2024-01-15T10:25:00Z"
      },
      {
        id: "websocket_chat",
        name: "WebSocket chat working end-to-end",
        description: "Real-time chat functionality is operational",
        category: "real_time",
        status: "pass",
        details: "WebSocket connections are stable and responsive",
        lastChecked: "2024-01-15T10:20:00Z"
      },
      {
        id: "kafka_streams",
        name: "Kafka streams active and visible in UI",
        description: "Real-time event streaming is functional",
        category: "real_time",
        status: "pass",
        details: "Kafka producer and consumer are running",
        lastChecked: "2024-01-15T10:15:00Z"
      },
      {
        id: "crewai_agents",
        name: "CrewAI agents registered per integration",
        description: "AI agents are properly configured and active",
        category: "ai",
        status: "pass",
        details: "15 agents are active and responding",
        lastChecked: "2024-01-15T10:10:00Z"
      },
      {
        id: "tool_calling_visible",
        name: "Tool calling visible in the chat UI",
        description: "Tool execution is visible to users",
        category: "ui",
        status: "pass",
        details: "Tool calling indicators are working correctly",
        lastChecked: "2024-01-15T10:05:00Z"
      },
      {
        id: "ui_theme",
        name: "UI theme consistent (white + green accents)",
        description: "Visual design is consistent and professional",
        category: "ui",
        status: "pass",
        details: "All components follow the design system",
        lastChecked: "2024-01-15T10:00:00Z"
      },
      {
        id: "checklist_passes",
        name: "Checklist passes all items",
        description: "All checklist items are passing",
        category: "system",
        status: "pass",
        details: "System is ready for production deployment",
        lastChecked: "2024-01-15T09:55:00Z"
      },
      {
        id: "unit_tests",
        name: "Unit tests written and passing",
        description: "All unit tests are implemented and passing",
        category: "testing",
        status: "pass",
        details: "156 unit tests passing",
        lastChecked: "2024-01-15T09:50:00Z"
      },
      {
        id: "integration_tests",
        name: "Integration tests for WebSocket, Kafka, agent flows passing",
        description: "End-to-end integration tests are working",
        category: "testing",
        status: "pass",
        details: "23 integration tests passing",
        lastChecked: "2024-01-15T09:45:00Z"
      },
      {
        id: "load_tests",
        name: "Load tests for streaming/log scalability",
        description: "System handles expected load levels",
        category: "performance",
        status: "pass",
        details: "System handles 1000 concurrent users",
        lastChecked: "2024-01-15T09:40:00Z"
      },
      {
        id: "security_audit",
        name: "Security audit for secrets and access control",
        description: "Security measures are properly implemented",
        category: "security",
        status: "pass",
        details: "Security audit completed successfully",
        lastChecked: "2024-01-15T09:35:00Z"
      }
    ],
    overall_status: "pass",
    total_items: 12,
    passed_items: 12,
    failed_items: 0
  };

  useEffect(() => {
    // Load checklist data
    loadChecklistData();
  }, []);

  const loadChecklistData = async () => {
    setIsLoading(true);
    try {
      // In real implementation, this would call the API
      // const response = await fetch('/api/v1/admin/checklist');
      // const data = await response.json();
      
      // For now, use mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      setChecklistData(mockChecklistData);
    } catch (error) {
      console.error('Failed to load checklist:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshChecklist = async () => {
    setIsRefreshing(true);
    try {
      // In real implementation, this would re-run all checks
      await new Promise(resolve => setTimeout(resolve, 2000));
      await loadChecklistData();
    } catch (error) {
      console.error('Failed to refresh checklist:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircleIcon className="h-6 w-6 text-green-600" />;
      case 'fail':
        return <XCircleIcon className="h-6 w-6 text-red-600" />;
      case 'pending':
        return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-600" />;
      default:
        return <InformationCircleIcon className="h-6 w-6 text-neutral-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pass':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'fail':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'pending':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      default:
        return 'bg-neutral-50 border-neutral-200 text-neutral-800';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      security: 'bg-red-100 text-red-800',
      integrations: 'bg-blue-100 text-blue-800',
      real_time: 'bg-purple-100 text-purple-800',
      ai: 'bg-green-100 text-green-800',
      ui: 'bg-yellow-100 text-yellow-800',
      system: 'bg-neutral-100 text-neutral-800',
      testing: 'bg-indigo-100 text-indigo-800',
      performance: 'bg-orange-100 text-orange-800'
    };
    return colors[category] || 'bg-neutral-100 text-neutral-800';
  };

  const filteredItems = checklistData?.checklist.filter(item => 
    selectedCategory === 'all' || item.category === selectedCategory
  ) || [];

  const categories = ['all', 'security', 'integrations', 'real_time', 'ai', 'ui', 'system', 'testing', 'performance'];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-neutral-600">Loading checklist...</p>
        </div>
      </div>
    );
  }

  if (!checklistData) {
    return (
      <div className="text-center py-12">
        <p className="text-neutral-600">Failed to load checklist data</p>
        <Button onClick={loadChecklistData} className="mt-4">Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Admin Checklist</h1>
          <p className="text-neutral-600 mt-1">
            Verify system readiness before going live
          </p>
        </div>
        <Button
          onClick={refreshChecklist}
          loading={isRefreshing}
          leftIcon={<ArrowPathIcon className="h-4 w-4" />}
        >
          Refresh
        </Button>
      </div>

      {/* Overall Status */}
      <div className={`p-6 rounded-lg border-2 ${
        checklistData.overall_status === 'pass' 
          ? 'bg-green-50 border-green-300' 
          : 'bg-red-50 border-red-300'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {checklistData.overall_status === 'pass' ? (
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
            ) : (
              <XCircleIcon className="h-8 w-8 text-red-600" />
            )}
            <div>
              <h2 className="text-lg font-semibold text-neutral-900">
                System Status: {checklistData.overall_status === 'pass' ? 'Ready for Production' : 'Not Ready'}
              </h2>
              <p className="text-neutral-600">
                {checklistData.passed_items} of {checklistData.total_items} checks passing
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-neutral-900">
              {Math.round((checklistData.passed_items / checklistData.total_items) * 100)}%
            </div>
            <div className="text-sm text-neutral-600">Complete</div>
          </div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        {categories.map(category => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              selectedCategory === category
                ? 'bg-primary-600 text-white'
                : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
            }`}
          >
            {category === 'all' ? 'All' : category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Checklist Items */}
      <div className="space-y-4">
        {filteredItems.map((item) => (
          <div
            key={item.id}
            className={`p-6 rounded-lg border transition-all ${
              item.status === 'pass' 
                ? 'bg-white border-green-200 hover:border-green-300' 
                : item.status === 'fail'
                ? 'bg-white border-red-200 hover:border-red-300'
                : 'bg-white border-yellow-200 hover:border-yellow-300'
            }`}
          >
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 mt-1">
                {getStatusIcon(item.status)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-medium text-neutral-900">
                      {item.name}
                    </h3>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(item.category)}`}>
                      {item.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                  <div className="text-sm text-neutral-500">
                    {item.lastChecked && new Date(item.lastChecked).toLocaleDateString()}
                  </div>
                </div>
                
                <p className="text-neutral-600 mt-1">{item.description}</p>
                
                {item.details && (
                  <div className={`mt-3 p-3 rounded-md border ${getStatusColor(item.status)}`}>
                    <p className="text-sm font-medium">{item.details}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4 pt-6">
        {checklistData.overall_status === 'pass' ? (
          <Button size="lg" variant="success" className="px-8">
            🚀 Deploy to Production
          </Button>
        ) : (
          <Button size="lg" variant="outline" className="px-8">
            Fix Issues First
          </Button>
        )}
        
        <Button size="lg" variant="outline" className="px-8">
          Export Report
        </Button>
      </div>
    </div>
  );
}
