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

// Real activity events will be loaded from API or WebSocket

export default function ActivityTicker() {
  const [activities, setActivities] = useState<ActivityEvent[]>([]);
  const [isLive, setIsLive] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load real activities from API
    loadActivities();
    
    if (isLive) {
      // Set up real-time activity listener if WebSocket is available
      // TODO: Connect to real activity stream when backend endpoint is ready
      // const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/activity';
      // const ws = new WebSocket(wsUrl);
      // ws.onmessage = (event) => {
      //   const activity = JSON.parse(event.data);
      //   addActivity(activity);
      // };
      // return () => ws.close();
    }
  }, [isLive]);

  const loadActivities = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call when activity endpoint is ready
      // const activities = await apiClient.getActivityFeed();
      // setActivities(activities);
      
      // For now, start with empty activities
      setActivities([]);
    } catch (error) {
      console.error('Failed to load activities:', error);
      setActivities([]);
    } finally {
      setLoading(false);
    }
  };

  const addActivity = (activity: ActivityEvent) => {
    setActivities(prev => [activity, ...prev.slice(0, 49)]); // Keep last 50 activities
  };

  const updateActivityStatus = (id: string, status: ActivityEvent['status']) => {
    setActivities(prev => 
      prev.map(a => 
        a.id === id ? { ...a, status } : a
      )
    );
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
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-2 text-neutral-600">Loading activities...</span>
            </div>
          ) : activities.length === 0 ? (
            <div className="text-center py-12">
              <ServerIcon className="h-16 w-16 text-neutral-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-neutral-900 mb-2">No Activity Yet</h3>
              <p className="text-neutral-600 mb-4">
                Activity will appear here when you start using integrations and agents.
              </p>
              <p className="text-sm text-neutral-500">
                Connect your first integration to see real-time activity updates.
              </p>
            </div>
          ) : (
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
                            {key}: {String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              ))}
            </div>
          )}
          
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
