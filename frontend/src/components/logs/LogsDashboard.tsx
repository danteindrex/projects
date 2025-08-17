'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/Button';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  PlayIcon,
  PauseIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  source: string;
  metadata: any;
  tenant_id?: string;
}

interface LogFilter {
  level: string[];
  source: string[];
  search: string;
  timeRange: string;
}

const mockLogs: LogEntry[] = [
  {
    id: '1',
    timestamp: new Date(Date.now() - 1000).toISOString(),
    level: 'info',
    message: 'User authentication successful',
    source: 'auth_service',
    metadata: { user_id: '123', ip: '192.168.1.1' }
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 2000).toISOString(),
    level: 'info',
    message: 'Integration API call completed',
    source: 'jira_integration',
    metadata: { endpoint: '/rest/api/2/issue', response_time: 245 }
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 3000).toISOString(),
    level: 'warning',
    message: 'Rate limit approaching threshold',
    source: 'rate_limiter',
    metadata: { current_rate: 95, limit: 100 }
  },
  {
    id: '4',
    timestamp: new Date(Date.now() - 4000).toISOString(),
    level: 'error',
    message: 'Database connection timeout',
    source: 'database',
    metadata: { retry_count: 3, timeout_ms: 5000 }
  },
  {
    id: '5',
    timestamp: new Date(Date.now() - 5000).toISOString(),
    level: 'info',
    message: 'WebSocket connection established',
    source: 'websocket_service',
    metadata: { session_id: 'ws_456', user_id: '123' }
  },
  {
    id: '6',
    timestamp: new Date(Date.now() - 6000).toISOString(),
    level: 'debug',
    message: 'Agent task execution started',
    source: 'crewai_agent',
    metadata: { agent_id: 'agent_789', task_type: 'data_retrieval' }
  }
];

export default function LogsDashboard() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  const [isLive, setIsLive] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState<LogFilter>({
    level: ['info', 'warning', 'error'],
    source: [],
    search: '',
    timeRange: '1h'
  });
  
  const logsEndRef = useRef<HTMLDivElement>(null);
  const liveUpdateInterval = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Initialize with mock logs
    setLogs(mockLogs);
    
    // Start live updates
    if (isLive) {
      startLiveUpdates();
    }

    return () => {
      if (liveUpdateInterval.current) {
        clearInterval(liveUpdateInterval.current);
      }
    };
  }, [isLive]);

  useEffect(() => {
    applyFilters();
  }, [logs, filter]);

  useEffect(() => {
    scrollToBottom();
  }, [filteredLogs]);

  const startLiveUpdates = () => {
    if (liveUpdateInterval.current) {
      clearInterval(liveUpdateInterval.current);
    }

    liveUpdateInterval.current = setInterval(() => {
      if (isLive) {
        addNewLog();
      }
    }, 2000);
  };

  const addNewLog = () => {
    const newLog: LogEntry = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      level: ['info', 'warning', 'error', 'debug'][Math.floor(Math.random() * 4)] as any,
      message: generateRandomLogMessage(),
      source: ['auth_service', 'jira_integration', 'rate_limiter', 'database', 'websocket_service', 'crewai_agent'][Math.floor(Math.random() * 6)],
      metadata: { random_data: Math.random() }
    };

    setLogs(prev => [newLog, ...prev.slice(0, 99)]); // Keep last 100 logs
  };

  const generateRandomLogMessage = (): string => {
    const messages = [
      'API request processed successfully',
      'User session created',
      'Integration health check completed',
      'Data synchronization started',
      'Cache updated',
      'Background job completed',
      'Webhook received',
      'Rate limit reset',
      'Connection pool refreshed',
      'Metrics collected'
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  };

  const applyFilters = () => {
    let filtered = logs;

    // Filter by level
    if (filter.level.length > 0) {
      filtered = filtered.filter(log => filter.level.includes(log.level));
    }

    // Filter by source
    if (filter.source.length > 0) {
      filtered = filtered.filter(log => filter.source.includes(log.source));
    }

    // Filter by search
    if (filter.search) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(filter.search.toLowerCase()) ||
        log.source.toLowerCase().includes(filter.search.toLowerCase())
      );
    }

    // Filter by time range
    const now = new Date();
    const timeRanges: Record<string, number> = {
      '15m': 15 * 60 * 1000,
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000
    };

    if (filter.timeRange in timeRanges) {
      const cutoff = new Date(now.getTime() - timeRanges[filter.timeRange]);
      filtered = filtered.filter(log => new Date(log.timestamp) > cutoff);
    }

    setFilteredLogs(filtered);
  };

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const toggleLive = () => {
    setIsLive(!isLive);
    if (!isLive) {
      startLiveUpdates();
    } else if (liveUpdateInterval.current) {
      clearInterval(liveUpdateInterval.current);
    }
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const exportLogs = () => {
    const csvContent = [
      'Timestamp,Level,Source,Message,Metadata',
      ...filteredLogs.map(log => 
        `${log.timestamp},${log.level},${log.source},"${log.message}","${JSON.stringify(log.metadata)}"`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />;
      case 'info':
        return <InformationCircleIcon className="h-4 w-4 text-blue-600" />;
      case 'debug':
        return <InformationCircleIcon className="h-4 w-4 text-neutral-600" />;
      default:
        return <InformationCircleIcon className="h-4 w-4 text-neutral-600" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'debug':
        return 'bg-neutral-50 border-neutral-200 text-neutral-600';
      default:
        return 'bg-neutral-50 border-neutral-200 text-neutral-600';
    }
  };

  const getSources = () => {
    const sources = Array.from(new Set(logs.map(log => log.source)));
    return sources;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Real-Time Logs</h1>
          <p className="text-neutral-600 mt-1">Monitor system activity and events in real-time</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <Button
            onClick={toggleLive}
            variant={isLive ? 'default' : 'outline'}
            leftIcon={isLive ? <PauseIcon className="h-4 w-4" /> : <PlayIcon className="h-4 w-4" />}
          >
            {isLive ? 'Live' : 'Paused'}
          </Button>
          
          <Button
            onClick={clearLogs}
            variant="outline"
            size="sm"
          >
            Clear
          </Button>
          
          <Button
            onClick={exportLogs}
            variant="outline"
            size="sm"
          >
            Export
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Search
            </label>
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
              <input
                type="text"
                value={filter.search}
                onChange={(e) => setFilter(prev => ({ ...prev, search: e.target.value }))}
                placeholder="Search logs..."
                className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          {/* Level Filter */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Level
            </label>
            <select
              multiple
              value={filter.level}
              onChange={(e) => {
                const selected = Array.from(e.target.selectedOptions, option => option.value);
                setFilter(prev => ({ ...prev, level: selected }));
              }}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
          </div>

          {/* Source Filter */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Source
            </label>
            <select
              multiple
              value={filter.source}
              onChange={(e) => {
                const selected = Array.from(e.target.selectedOptions, option => option.value);
                setFilter(prev => ({ ...prev, source: selected }));
              }}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {getSources().map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>
          </div>

          {/* Time Range */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              Time Range
            </label>
            <select
              value={filter.timeRange}
              onChange={(e) => setFilter(prev => ({ ...prev, timeRange: e.target.value }))}
              className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="15m">Last 15 minutes</option>
              <option value="1h">Last hour</option>
              <option value="6h">Last 6 hours</option>
              <option value="24h">Last 24 hours</option>
            </select>
          </div>
        </div>
      </div>

      {/* Logs Display */}
      <div className="bg-white rounded-lg border border-neutral-200 shadow-soft">
        <div className="px-6 py-4 border-b border-neutral-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-neutral-900">
              Logs ({filteredLogs.length})
            </h3>
            <div className="flex items-center space-x-2 text-sm text-neutral-600">
              <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-500' : 'bg-neutral-400'}`}></div>
              {isLive ? 'Live' : 'Paused'}
            </div>
          </div>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {filteredLogs.length === 0 ? (
            <div className="p-6 text-center text-neutral-500">
              No logs match the current filters
            </div>
          ) : (
            <div className="divide-y divide-neutral-200">
              {filteredLogs.map((log) => (
                <div key={log.id} className="p-4 hover:bg-neutral-50 transition-colors">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getLevelIcon(log.level)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLevelColor(log.level)}`}>
                            {log.level.toUpperCase()}
                          </span>
                          <span className="text-sm font-medium text-neutral-900">
                            {log.source}
                          </span>
                        </div>
                        <div className="text-sm text-neutral-500">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                      
                      <p className="text-sm text-neutral-700 mt-1">{log.message}</p>
                      
                      {log.metadata && Object.keys(log.metadata).length > 0 && (
                        <div className="mt-2 text-xs text-neutral-600">
                          <details className="cursor-pointer">
                            <summary className="hover:text-neutral-800">Metadata</summary>
                            <pre className="mt-1 p-2 bg-neutral-100 rounded text-xs overflow-x-auto">
                              {JSON.stringify(log.metadata, null, 2)}
                            </pre>
                          </details>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-neutral-200 shadow-soft">
          <div className="text-2xl font-bold text-neutral-900">{logs.length}</div>
          <div className="text-sm text-neutral-600">Total Logs</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-neutral-200 shadow-soft">
          <div className="text-2xl font-bold text-red-600">
            {logs.filter(log => log.level === 'error').length}
          </div>
          <div className="text-sm text-neutral-600">Errors</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-neutral-200 shadow-soft">
          <div className="text-2xl font-bold text-yellow-600">
            {logs.filter(log => log.level === 'warning').length}
          </div>
          <div className="text-sm text-neutral-600">Warnings</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-neutral-200 shadow-soft">
          <div className="text-2xl font-bold text-blue-600">
            {logs.filter(log => log.level === 'info').length}
          </div>
          <div className="text-sm text-neutral-600">Info</div>
        </div>
      </div>
    </div>
  );
}
