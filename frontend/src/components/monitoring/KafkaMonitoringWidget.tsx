'use client';

import React, { useState, useEffect } from 'react';
import { 
  QueueListIcon,
  ArrowTopRightOnSquareIcon,
  InformationCircleIcon,
  ChartBarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface KafkaTopic {
  name: string;
  partitions: number;
  messages: number;
  consumers: number;
  status: 'active' | 'inactive' | 'error';
}

interface KafkaMonitoringWidgetProps {
  className?: string;
}

export default function KafkaMonitoringWidget({ className = '' }: KafkaMonitoringWidgetProps) {
  const [topics, setTopics] = useState<KafkaTopic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [kafkaStatus, setKafkaStatus] = useState<'connected' | 'disconnected' | 'unknown'>('unknown');

  useEffect(() => {
    fetchKafkaData();
    const interval = setInterval(fetchKafkaData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchKafkaData = async () => {
    try {
      setError(null);
      
      // TODO: Implement real Kafka API call when endpoint is available
      // const response = await apiClient.getKafkaTopics();
      // setTopics(response.topics || []);
      
      // For now, show empty state - no mock data
      setTopics([]);
      setKafkaStatus('unknown');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch Kafka data');
      setKafkaStatus('disconnected');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'inactive':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const totalMessages = topics.reduce((sum, topic) => sum + topic.messages, 0);
  const totalConsumers = topics.reduce((sum, topic) => sum + topic.consumers, 0);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg border border-neutral-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
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
          <QueueListIcon className="h-6 w-6 text-neutral-700" />
          <h3 className="text-lg font-medium text-neutral-900">Kafka Monitoring</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              kafkaStatus === 'connected' ? 'bg-green-500' : 
              kafkaStatus === 'disconnected' ? 'bg-red-500' : 'bg-yellow-500'
            }`}></div>
            <span className="text-xs text-neutral-500 capitalize">{kafkaStatus}</span>
          </div>
        </div>
        
        <a
          href="http://localhost:8080"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center space-x-2 px-3 py-2 text-sm text-primary-600 hover:text-primary-700 border border-primary-200 hover:border-primary-300 rounded-md transition-colors"
        >
          <span>Open Kafka UI</span>
          <ArrowTopRightOnSquareIcon className="h-4 w-4" />
        </a>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
            <span className="text-sm font-medium text-red-800">Kafka Connection Error</span>
          </div>
          <p className="text-sm text-red-700 mt-1">{error}</p>
          <p className="text-xs text-red-600 mt-2">
            Make sure Kafka is running: <code className="bg-red-100 px-1 rounded">docker-compose up -d</code>
          </p>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center space-x-2">
            <QueueListIcon className="h-6 w-6 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-blue-900">Topics</p>
              <p className="text-2xl font-bold text-blue-700">{topics.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="h-6 w-6 text-green-600" />
            <div>
              <p className="text-sm font-medium text-green-900">Messages</p>
              <p className="text-2xl font-bold text-green-700">{totalMessages.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <div className="flex items-center space-x-2">
            <InformationCircleIcon className="h-6 w-6 text-purple-600" />
            <div>
              <p className="text-sm font-medium text-purple-900">Consumers</p>
              <p className="text-2xl font-bold text-purple-700">{totalConsumers}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Topics List */}
      <div className="space-y-3">
        <h4 className="text-md font-medium text-neutral-900">Active Topics</h4>
        {topics.length === 0 ? (
          <div className="text-center py-8 text-neutral-500">
            <QueueListIcon className="h-12 w-12 mx-auto mb-4 text-neutral-300" />
            <p>No Kafka topics found</p>
            <p className="text-sm">Topics will appear when events are published</p>
          </div>
        ) : (
          <div className="space-y-2">
            {topics.map((topic) => (
              <div key={topic.name} className="bg-neutral-50 rounded-lg p-4 border border-neutral-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <QueueListIcon className="h-5 w-5 text-neutral-500" />
                    <div>
                      <h5 className="text-sm font-medium text-neutral-900">{topic.name}</h5>
                      <p className="text-xs text-neutral-600">
                        {topic.partitions} partition{topic.partitions > 1 ? 's' : ''} • 
                        {topic.consumers} consumer{topic.consumers > 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <p className="text-sm font-medium text-neutral-900">
                        {topic.messages.toLocaleString()}
                      </p>
                      <p className="text-xs text-neutral-600">messages</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(topic.status)}`}>
                      {topic.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Integration Events Info */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center space-x-2 mb-2">
          <InformationCircleIcon className="h-5 w-5 text-blue-500" />
          <span className="text-sm font-medium text-blue-800">Integration Event Streaming</span>
        </div>
        <p className="text-sm text-blue-700">
          All integration API calls, health checks, and system events are streamed to Kafka topics in real-time.
        </p>
        <div className="mt-3 space-y-1 text-xs text-blue-600">
          <p><strong>integrations:</strong> API calls, authentication, health checks</p>
          <p><strong>chat:</strong> WebSocket messages, agent responses</p>
          <p><strong>agents:</strong> AI agent tasks, tool executions</p>
          <p><strong>system:</strong> Infrastructure events, alerts</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 pt-4 border-t border-neutral-200">
        <div className="flex items-center justify-between">
          <div className="text-xs text-neutral-500">
            Monitor live events in Kafka UI for detailed debugging
          </div>
          <div className="flex items-center space-x-2">
            <a
              href="http://localhost:8080/ui/clusters/local/topics"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary-600 hover:text-primary-700 underline"
            >
              View Topics
            </a>
            <span className="text-xs text-neutral-400">•</span>
            <a
              href="http://localhost:8080/ui/clusters/local/consumers"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-primary-600 hover:text-primary-700 underline"
            >
              View Consumers
            </a>
          </div>
        </div>
      </div>

      <div className="mt-4 text-xs text-neutral-500 text-right">
        Last updated: {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
}