'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  CheckCircleIcon, 
  XCircleIcon,
  ClockIcon,
  FunnelIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { IntegrationEvent } from '@/lib/api';
import apiClient from '@/lib/api';

interface RealTimeActivityFeedProps {
  className?: string;
}

interface ActivityEvent extends IntegrationEvent {
  id: string;
  expanded?: boolean;
}

export default function RealTimeActivityFeed({ className = '' }: RealTimeActivityFeedProps) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [filteredEvents, setFilteredEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    integration: '',
    eventType: '',
    status: ''
  });
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    fetchInitialEvents();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    applyFilters();
  }, [events, filters]);

  const fetchInitialEvents = async () => {
    try {
      setError(null);
      const eventsData = await apiClient.getIntegrationsActivity(50);
      const eventsWithIds = eventsData.map(event => ({
        ...event,
        id: `${event.call_id || Date.now()}-${Math.random()}`,
        expanded: false
      }));
      setEvents(eventsWithIds);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch activity events');
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    try {
      const wsUrl = 'wss://businesshub-backend-latest.onrender.com/api/v1/monitoring/integrations/realtime';
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'api_call_success' || data.type === 'api_call_failure') {
            const newEvent: ActivityEvent = {
              id: `${Date.now()}-${Math.random()}`,
              call_id: data.call_id || `call_${Date.now()}`,
              integration_name: data.integration_name || 'Unknown',
              integration_type: data.integration_type || 'unknown',
              endpoint: data.endpoint || '',
              method: data.method || 'GET',
              status_code: data.status_code,
              response_time_ms: data.response_time_ms || 0,
              success: data.type === 'api_call_success',
              error: data.error,
              error_type: data.error_type,
              timestamp: data.timestamp || Date.now(),
              expanded: false
            };
            
            setEvents(prev => [newEvent, ...prev.slice(0, 99)]); // Keep last 100 events
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setIsConnected(false);
      };
      
      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to connect WebSocket:', err);
      setError('Failed to connect to real-time feed');
    }
  };

  const applyFilters = () => {
    let filtered = events;
    
    if (filters.integration) {
      filtered = filtered.filter(event => 
        event.integration_name.toLowerCase().includes(filters.integration.toLowerCase())
      );
    }
    
    if (filters.eventType) {
      filtered = filtered.filter(event => 
        event.integration_type.toLowerCase().includes(filters.eventType.toLowerCase())
      );
    }
    
    if (filters.status) {
      if (filters.status === 'success') {
        filtered = filtered.filter(event => event.success);
      } else if (filters.status === 'failure') {
        filtered = filtered.filter(event => !event.success);
      }
    }
    
    setFilteredEvents(filtered);
  };

  const toggleEventExpansion = (eventId: string) => {
    setEvents(prev => prev.map(event => 
      event.id === eventId 
        ? { ...event, expanded: !event.expanded }
        : event
    ));
  };

  const getEventIcon = (event: ActivityEvent) => {
    if (event.success) {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    } else if (event.error_type === 'rate_limit') {
      return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
    } else {
      return <XCircleIcon className="h-5 w-5 text-red-500" />;
    }
  };

  const getEventColor = (event: ActivityEvent) => {
    if (event.success) {
      return 'border-l-green-500 bg-green-50';
    } else if (event.error_type === 'rate_limit') {
      return 'border-l-yellow-500 bg-yellow-50';
    } else {
      return 'border-l-red-500 bg-red-50';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const getUniqueIntegrations = () => {
    const integrations = [...new Set(events.map(e => e.integration_name))];
    return integrations.sort();
  };

  const getUniqueTypes = () => {
    const types = [...new Set(events.map(e => e.integration_type))];
    return types.sort();
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-neutral-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg border border-neutral-200 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <h3 className="text-lg font-medium text-neutral-900">Real-Time Activity Feed</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-xs text-neutral-500">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchInitialEvents}
            className="p-2 text-neutral-500 hover:text-neutral-700 transition-colors"
            title="Refresh"
          >
            <ArrowPathIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 p-4 bg-neutral-50 rounded-lg border border-neutral-200">
        <div className="flex items-center space-x-2 mb-3">
          <FunnelIcon className="h-5 w-5 text-neutral-500" />
          <span className="text-sm font-medium text-neutral-700">Filters</span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-neutral-700 mb-1">Integration</label>
            <select
              value={filters.integration}
              onChange={(e) => setFilters(prev => ({ ...prev, integration: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Integrations</option>
              {getUniqueIntegrations().map(integration => (
                <option key={integration} value={integration}>{integration}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-neutral-700 mb-1">Type</label>
            <select
              value={filters.eventType}
              onChange={(e) => setFilters(prev => ({ ...prev, eventType: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Types</option>
              {getUniqueTypes().map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-neutral-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="">All Status</option>
              <option value="success">Success</option>
              <option value="failure">Failure</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center space-x-2">
              <XCircleIcon className="h-5 w-5 text-red-500" />
              <span className="text-sm font-medium text-red-800">Error</span>
            </div>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        )}
        
        {filteredEvents.length === 0 ? (
          <div className="text-center py-8 text-neutral-500">
            <ClockIcon className="h-12 w-12 mx-auto mb-4 text-neutral-300" />
            <p>No activity events</p>
            <p className="text-sm">Events will appear here as they occur</p>
          </div>
        ) : (
          filteredEvents.map((event) => (
            <div
              key={event.id}
              className={`border-l-4 p-4 rounded-r-lg cursor-pointer transition-all ${getEventColor(event)}`}
              onClick={() => toggleEventExpansion(event.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {getEventIcon(event)}
                  <div>
                    <h5 className="text-sm font-medium text-neutral-900">
                      {event.integration_name} - {event.method} {event.endpoint}
                    </h5>
                    <p className="text-xs text-neutral-600">
                      {event.integration_type} • {formatTimestamp(event.timestamp)}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {event.status_code && (
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      event.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {event.status_code}
                    </span>
                  )}
                  <span className="text-xs text-neutral-500">
                    {event.response_time_ms}ms
                  </span>
                </div>
              </div>
              
              {event.expanded && (
                <div className="mt-3 pt-3 border-t border-neutral-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <p className="font-medium text-neutral-700">Call ID</p>
                      <p className="text-neutral-600">{event.call_id}</p>
                    </div>
                    <div>
                      <p className="font-medium text-neutral-700">Response Time</p>
                      <p className="text-neutral-600">{event.response_time_ms}ms</p>
                    </div>
                    {event.error && (
                      <div className="md:col-span-2">
                        <p className="font-medium text-neutral-700">Error</p>
                        <p className="text-red-600">{event.error}</p>
                      </div>
                    )}
                    {event.error_type && (
                      <div>
                        <p className="font-medium text-neutral-700">Error Type</p>
                        <p className="text-neutral-600">{event.error_type}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Connection Info */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center space-x-2">
          <InformationCircleIcon className="h-4 w-4 text-blue-500" />
          <span className="text-xs font-medium text-blue-800">Real-time Connection</span>
        </div>
        <p className="text-xs text-blue-700 mt-1">
          {isConnected 
            ? 'Connected to live event stream. New events will appear automatically.'
            : 'Attempting to reconnect to live event stream...'
          }
        </p>
        <p className="text-xs text-blue-600 mt-1">
          Kafka UI: <a href="http://localhost:8080" target="_blank" rel="noopener noreferrer" className="underline">http://localhost:8080</a>
        </p>
      </div>

      <div className="mt-4 text-xs text-neutral-500 text-right">
        Showing {filteredEvents.length} of {events.length} events
      </div>
    </div>
  );
}