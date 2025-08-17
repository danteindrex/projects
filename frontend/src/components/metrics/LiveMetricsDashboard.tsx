'use client';

import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon,
  CpuChipIcon,
  ServerIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

interface MetricData {
  timestamp: string;
  value: number;
  label: string;
}

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  active_connections: number;
  requests_per_second: number;
  error_rate: number;
  response_time: number;
}

interface AgentMetrics {
  total_agents: number;
  active_agents: number;
  busy_agents: number;
  error_agents: number;
  avg_response_time: number;
}

const mockSystemMetrics: SystemMetrics = {
  cpu_usage: 45.2,
  memory_usage: 67.8,
  active_connections: 1247,
  requests_per_second: 89.3,
  error_rate: 0.8,
  response_time: 245.6
};

const mockAgentMetrics: AgentMetrics = {
  total_agents: 15,
  active_agents: 12,
  busy_agents: 8,
  error_agents: 1,
  avg_response_time: 156.7
};

export default function LiveMetricsDashboard() {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>(mockSystemMetrics);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetrics>(mockAgentMetrics);
  const [isLive, setIsLive] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    if (isLive) {
      const interval = setInterval(() => {
        updateMetrics();
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isLive]);

  const updateMetrics = () => {
    // Simulate real-time metric updates
    setSystemMetrics(prev => ({
      cpu_usage: Math.max(0, Math.min(100, prev.cpu_usage + (Math.random() - 0.5) * 10)),
      memory_usage: Math.max(0, Math.min(100, prev.memory_usage + (Math.random() - 0.5) * 5)),
      active_connections: Math.max(0, prev.active_connections + Math.floor((Math.random() - 0.5) * 50)),
      requests_per_second: Math.max(0, prev.requests_per_second + (Math.random() - 0.5) * 20)),
      error_rate: Math.max(0, Math.min(100, prev.error_rate + (Math.random() - 0.5) * 2)),
      response_time: Math.max(0, prev.response_time + (Math.random() - 0.5) * 50)
    }));

    setAgentMetrics(prev => ({
      total_agents: prev.total_agents,
      active_agents: Math.max(0, Math.min(prev.total_agents, prev.active_agents + Math.floor((Math.random() - 0.5) * 2))),
      busy_agents: Math.max(0, Math.min(prev.active_agents, prev.busy_agents + Math.floor((Math.random() - 0.5) * 2))),
      error_agents: Math.max(0, Math.min(prev.total_agents, prev.error_agents + Math.floor((Math.random() - 0.5) * 2))),
      avg_response_time: Math.max(0, prev.avg_response_time + (Math.random() - 0.5) * 30)
    }));

    setLastUpdate(new Date());
  };

  const getMetricColor = (value: number, threshold: number, isLowerBetter: boolean = false) => {
    if (isLowerBetter) {
      return value <= threshold ? 'text-green-600' : value <= threshold * 1.5 ? 'text-yellow-600' : 'text-red-600';
    }
    return value <= threshold ? 'text-green-600' : value <= threshold * 1.5 ? 'text-yellow-600' : 'text-red-600';
  };

  const getMetricIcon = (metric: string) => {
    switch (metric) {
      case 'cpu':
        return <CpuChipIcon className="h-6 w-6" />;
      case 'memory':
        return <ServerIcon className="h-6 w-6" />;
      case 'connections':
        return <ChartBarIcon className="h-6 w-6" />;
      case 'requests':
        return <ChartBarIcon className="h-6 w-6" />;
      case 'errors':
        return <ExclamationTriangleIcon className="h-6 w-6" />;
      case 'response':
        return <ChartBarIcon className="h-6 w-6" />;
      default:
        return <ChartBarIcon className="h-6 w-6" />;
    }
  };

  const formatMetricValue = (value: number, unit: string = '') => {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M${unit}`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K${unit}`;
    } else {
      return `${value.toFixed(1)}${unit}`;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Live Metrics Dashboard</h1>
          <p className="text-neutral-600 mt-1">Real-time system performance monitoring</p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${isLive ? 'bg-green-500' : 'bg-neutral-400'}`}></div>
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

      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* CPU Usage */}
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getMetricIcon('cpu')}
              <h3 className="font-medium text-neutral-900">CPU Usage</h3>
            </div>
            <span className={`text-2xl font-bold ${getMetricColor(systemMetrics.cpu_usage, 70)}`}>
              {systemMetrics.cpu_usage.toFixed(1)}%
            </span>
          </div>
          
          <div className="w-full bg-neutral-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-500 ${
                systemMetrics.cpu_usage <= 70 ? 'bg-green-500' : 
                systemMetrics.cpu_usage <= 85 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${systemMetrics.cpu_usage}%` }}
            ></div>
          </div>
          
          <p className="text-sm text-neutral-600 mt-2">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Memory Usage */}
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getMetricIcon('memory')}
              <h3 className="font-medium text-neutral-900">Memory Usage</h3>
            </div>
            <span className={`text-2xl font-bold ${getMetricColor(systemMetrics.memory_usage, 80)}`}>
              {systemMetrics.memory_usage.toFixed(1)}%
            </span>
          </div>
          
          <div className="w-full bg-neutral-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-500 ${
                systemMetrics.memory_usage <= 80 ? 'bg-green-500' : 
                systemMetrics.memory_usage <= 90 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${systemMetrics.memory_usage}%` }}
            ></div>
          </div>
          
          <p className="text-sm text-neutral-600 mt-2">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>

        {/* Active Connections */}
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getMetricIcon('connections')}
              <h3 className="font-medium text-neutral-900">Active Connections</h3>
            </div>
            <span className="text-2xl font-bold text-blue-600">
              {formatMetricValue(systemMetrics.active_connections)}
            </span>
          </div>
          
          <div className="text-3xl font-bold text-neutral-900 mb-2">
            {systemMetrics.active_connections.toLocaleString()}
          </div>
          
          <p className="text-sm text-neutral-600">
            WebSocket & HTTP connections
          </p>
        </div>

        {/* Requests per Second */}
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getMetricIcon('requests')}
              <h3 className="font-medium text-neutral-900">Requests/sec</h3>
            </div>
            <span className="text-2xl font-bold text-blue-600">
              {systemMetrics.requests_per_second.toFixed(1)}
            </span>
          </div>
          
          <div className="text-3xl font-bold text-neutral-900 mb-2">
            {systemMetrics.requests_per_second.toFixed(1)}
          </div>
          
          <p className="text-sm text-neutral-600">
            API requests per second
          </p>
        </div>

        {/* Error Rate */}
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getMetricIcon('errors')}
              <h3 className="font-medium text-neutral-900">Error Rate</h3>
            </div>
            <span className={`text-2xl font-bold ${getMetricColor(systemMetrics.error_rate, 2, true)}`}>
              {systemMetrics.error_rate.toFixed(1)}%
            </span>
          </div>
          
          <div className="text-3xl font-bold text-neutral-900 mb-2">
            {systemMetrics.error_rate.toFixed(1)}%
          </div>
          
          <p className="text-sm text-neutral-600">
            Failed requests percentage
          </p>
        </div>

        {/* Response Time */}
        <div className="bg-white p-6 rounded-lg border border-neutral-200 shadow-soft">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              {getMetricIcon('response')}
              <h3 className="font-medium text-neutral-900">Avg Response Time</h3>
            </div>
            <span className={`text-2xl font-bold ${getMetricColor(systemMetrics.response_time, 500, true)}`}>
              {formatMetricValue(systemMetrics.response_time, 'ms')}
            </span>
          </div>
          
          <div className="text-3xl font-bold text-neutral-900 mb-2">
            {systemMetrics.response_time.toFixed(0)}ms
          </div>
          
          <p className="text-sm text-neutral-600">
            Average API response time
          </p>
        </div>
      </div>

      {/* Agent Metrics */}
      <div className="bg-white rounded-lg border border-neutral-200 shadow-soft">
        <div className="px-6 py-4 border-b border-neutral-200">
          <h2 className="text-lg font-medium text-neutral-900">Agent Performance</h2>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            {/* Total Agents */}
            <div className="text-center">
              <div className="text-3xl font-bold text-neutral-900 mb-2">
                {agentMetrics.total_agents}
              </div>
              <div className="text-sm text-neutral-600">Total Agents</div>
            </div>
            
            {/* Active Agents */}
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {agentMetrics.active_agents}
              </div>
              <div className="text-sm text-neutral-600">Active</div>
            </div>
            
            {/* Busy Agents */}
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {agentMetrics.busy_agents}
              </div>
              <div className="text-sm text-neutral-600">Busy</div>
            </div>
            
            {/* Error Agents */}
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600 mb-2">
                {agentMetrics.error_agents}
              </div>
              <div className="text-sm text-neutral-600">Errors</div>
            </div>
            
            {/* Avg Response Time */}
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600 mb-2">
                {agentMetrics.avg_response_time.toFixed(0)}ms
              </div>
              <div className="text-sm text-neutral-600">Avg Response</div>
            </div>
          </div>
        </div>
      </div>

      {/* Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-5 w-5 text-green-600" />
            <span className="font-medium text-green-800">System Healthy</span>
          </div>
          <p className="text-sm text-green-700 mt-1">
            All critical metrics are within normal ranges
          </p>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <CpuChipIcon className="h-5 w-5 text-blue-600" />
            <span className="font-medium text-blue-800">Agents Operational</span>
          </div>
          <p className="text-sm text-blue-700 mt-1">
            {agentMetrics.active_agents} of {agentMetrics.total_agents} agents are active
          </p>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
            <span className="font-medium text-yellow-800">Monitor Closely</span>
          </div>
          <p className="text-sm text-yellow-700 mt-1">
            Some metrics approaching thresholds
          </p>
        </div>
      </div>

      {/* Last Update */}
      <div className="text-center text-sm text-neutral-500">
        Last updated: {lastUpdate.toLocaleString()}
      </div>
    </div>
  );
}
