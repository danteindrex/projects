'use client';

import React, { useState, useEffect } from 'react';
import { 
  CogIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ClockIcon,
  UserIcon,
  ServerIcon
} from '@heroicons/react/24/outline';

interface ActivityEvent {
  id: string;
  type: 'agent_action' | 'system_event' | 'user_action' | 'integration_event';
  title: string;
  description: string;
  timestamp: Date;
  status: 'pending' | 'running' | 'completed' | 'failed';
  metadata?: any;
  user?: string;
  agent?: string;
}

const mockActivityEvents: ActivityEvent[] = [
  {
    id: '1',
    type: 'agent_action',
    title: 'Jira Issue Analysis',
    description: 'Agent "jira_specialist" is analyzing recent issues',
    timestamp: new Date(Date.now() - 1000 * 30), // 30 seconds ago
    status: 'running',
    agent: 'jira_specialist',
    metadata: { issue_count: 15, priority: 'high' }
  },
  {
    id: '2',
    type: 'integration_event',
    title: 'Salesforce Sync',
    description: 'Data synchronization completed successfully',
    timestamp: new Date(Date.now() - 1000 * 60 * 2), // 2 minutes ago
    status: 'completed',
    metadata: { records_synced: 1247, duration: '45s' }
  },
  {
    id: '3',
    type: 'user_action',
    title: 'Integration Test',
    description: 'User tested Zendesk connection',
    timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 minutes ago
    status: 'completed',
    user: 'admin@company.com',
    metadata: { response_time: '245ms', status: 'success' }
  },
  {
    id: '4',
    type: 'system_event',
    title: 'Health Check',
    description: 'System health check completed',
    timestamp: new Date(Date.now() - 1000 * 60 * 10), // 10 minutes ago
    status: 'completed',
    metadata: { checks_passed: 23, checks_failed: 0 }
  }
];

export default function ActivityTicker() {
  const [activities, setActivities] = useState<ActivityEvent[]>(mockActivityEvents);
  const [isLive, setIsLive] = useState(true);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (isLive) {
      const interval = setInterval(() => {
        addRandomActivity();
      }, 8000); // Add activity every 8 seconds

      return () => clearInterval(interval);
    }
  }, [isLive]);

  const addRandomActivity = () => {
    const activityTypes: ActivityEvent['type'][] = [
      'agent_action',
      'system_event',
      'user_action',
      'integration_event'
    ];

    const activityTemplates = {
      agent_action: [
        {
          title: 'Data Processing',
          description: 'Agent "data_processor" is processing customer data',
          agent: 'data_processor',
          metadata: { records_processed: Math.floor(Math.random() * 1000) + 100 }
        },
        {
          title: 'API Call',
          description: 'Agent "api_specialist" is making external API call',
          agent: 'api_specialist',
          metadata: { endpoint: '/api/v2/users', method: 'GET' }
        },
        {
          title: 'Report Generation',
          description: 'Agent "reporter" is generating monthly report',
          agent: 'reporter',
          metadata: { report_type: 'monthly', sections: 8 }
        }
      ],
      system_event: [
        {
          title: 'Cache Update',
          description: 'System cache has been refreshed',
          metadata: { cache_size: '2.4GB', items_updated: 156 }
        },
        {
          title: 'Backup Started',
          description: 'Automated backup process initiated',
          metadata: { backup_type: 'incremental', estimated_duration: '15m' }
        },
        {
          title: 'Performance Scan',
          description: 'System performance scan completed',
          metadata: { scan_duration: '2m 34s', issues_found: 0 }
        }
      ],
      user_action: [
        {
          title: 'Dashboard Access',
          description: 'User accessed metrics dashboard',
          user: 'user@company.com',
          metadata: { page: '/dashboard', session_duration: '12m' }
        },
        {
          title: 'Integration Setup',
          description: 'User configured new integration',
          user: 'admin@company.com',
          metadata: { integration: 'GitHub', status: 'active' }
        },
        {
          title: 'Report Export',
          description: 'User exported activity report',
          user: 'analyst@company.com',
          metadata: { format: 'CSV', records: 2341 }
        }
      ],
      integration_event: [
        {
          title: 'Webhook Received',
          description: 'Webhook from external system received',
          metadata: { source: 'Jira', event_type: 'issue_updated' }
        },
        {
          title: 'Rate Limit Reset',
          description: 'API rate limit has been reset',
          metadata: { integration: 'Salesforce', reset_time: '00:00 UTC' }
        },
        {
          title: 'Connection Test',
          description: 'Integration connection test completed',
          metadata: { integration: 'Zendesk', response_time: '189ms' }
        }
      ]
    };

    const randomType = activityTypes[Math.floor(Math.random() * activityTypes.length)];
    const templates = activityTemplates[randomType];
    const template = templates[Math.floor(Math.random() * templates.length)];

    const newActivity: ActivityEvent = {
      id: Date.now().toString(),
      type: randomType,
      title: template.title,
      description: template.description,
      timestamp: new Date(),
      status: 'running',
      ...template
    };

    setActivities(prev => [newActivity, ...prev.slice(0, 49)]); // Keep last 50 activities

    // Simulate status change after a delay
    setTimeout(() => {
      setActivities(prev => 
        prev.map(a => 
          a.id === newActivity.id 
            ? { ...a, status: Math.random() > 0.1 ? 'completed' : 'failed' }
            : a
        )
      );
    }, 3000 + Math.random() * 4000); // 3-7 seconds
  };

  const getActivityIcon = (type: ActivityEvent['type']) => {
    switch (type) {
      case 'agent_action':
        return <CogIcon className="h-4 w-4 text-blue-600" />;
      case 'system_event':
        return <ServerIcon className="h-4 w-4 text-purple-600" />;
      case 'user_action':
        return <UserIcon className="h-4 w-4 text-green-600" />;
      case 'integration_event':
        return <CheckCircleIcon className="h-4 w-4 text-orange-600" />;
      default:
        return <InformationCircleIcon className="h-4 w-4 text-neutral-600" />;
    }
  };

  const getStatusIcon = (status: ActivityEvent['status']) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="h-4 w-4 text-yellow-600" />;
      case 'running':
        return <CogIcon className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />;
      default:
        return <InformationCircleIcon className="h-4 w-4 text-neutral-600" />;
    }
  };

  const getStatusColor = (status: ActivityEvent['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'running':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'completed':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'failed':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-neutral-50 border-neutral-200 text-neutral-600';
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (seconds < 60) return `${seconds}s ago`;
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return timestamp.toLocaleDateString();
  };

  const getTypeLabel = (type: ActivityEvent['type']) => {
    switch (type) {
      case 'agent_action':
        return 'Agent';
      case 'system_event':
        return 'System';
      case 'user_action':
        return 'User';
      case 'integration_event':
        return 'Integration';
      default:
        return 'Event';
    }
  };

  const displayedActivities = showAll ? activities : activities.slice(0, 8);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium text-neutral-900">Activity Ticker</h2>
          <p className="text-sm text-neutral-600">Real-time system and agent activity</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500' : 'bg-neutral-400'}`}></div>
          <span className="text-sm text-neutral-600">
            {isLive ? 'Live' : 'Paused'}
          </span>
          <button
            onClick={() => setIsLive(!isLive)}
            className="px-3 py-1 text-sm bg-neutral-100 hover:bg-neutral-200 rounded-md transition-colors"
          >
            {isLive ? 'Pause' : 'Resume'}
          </button>
        </div>
      </div>

      {/* Activity Stream */}
      <div className="bg-white rounded-lg border border-neutral-200 shadow-soft">
        <div className="p-4">
          <div className="space-y-3">
            {displayedActivities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start space-x-3 p-3 hover:bg-neutral-50 rounded-lg transition-colors"
              >
                <div className="flex-shrink-0 mt-1">
                  {getActivityIcon(activity.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-sm font-medium text-neutral-900">
                        {activity.title}
                      </h3>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}>
                        {activity.status}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-2 text-xs text-neutral-500">
                      {getStatusIcon(activity.status)}
                      <span>{formatTimestamp(activity.timestamp)}</span>
                    </div>
                  </div>
                  
                  <p className="text-sm text-neutral-600 mb-2">
                    {activity.description}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 text-xs text-neutral-500">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-neutral-100 text-neutral-700">
                        {getTypeLabel(activity.type)}
                      </span>
                      
                      {activity.agent && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                          {activity.agent}
                        </span>
                      )}
                      
                      {activity.user && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                          {activity.user.split('@')[0]}
                        </span>
                      )}
                    </div>
                    
                    {activity.metadata && (
                      <div className="text-xs text-neutral-500">
                        {Object.entries(activity.metadata).slice(0, 2).map(([key, value]) => (
                          <span key={key} className="mr-2">
                            {key}: {value}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {activities.length > 8 && (
            <div className="text-center pt-4">
              <button
                onClick={() => setShowAll(!showAll)}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                {showAll ? 'Show Less' : `Show All ${activities.length} Activities`}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Activity Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-neutral-200 shadow-soft text-center">
          <div className="text-2xl font-bold text-blue-600">
            {activities.filter(a => a.type === 'agent_action').length}
          </div>
          <div className="text-sm text-neutral-600">Agent Actions</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-neutral-200 shadow-soft text-center">
          <div className="text-2xl font-bold text-purple-600">
            {activities.filter(a => a.type === 'system_event').length}
          </div>
          <div className="text-sm text-neutral-600">System Events</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-neutral-200 shadow-soft text-center">
          <div className="text-2xl font-bold text-green-600">
            {activities.filter(a => a.type === 'user_action').length}
          </div>
          <div className="text-sm text-neutral-600">User Actions</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-neutral-200 shadow-soft text-center">
          <div className="text-2xl font-bold text-orange-600">
            {activities.filter(a => a.type === 'integration_event').length}
          </div>
          <div className="text-sm text-neutral-600">Integration Events</div>
        </div>
      </div>
    </div>
  );
}
