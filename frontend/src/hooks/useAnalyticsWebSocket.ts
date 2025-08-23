/**
 * Custom hook for real-time analytics WebSocket connection
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import { apiClient } from '@/lib/api';

interface AnalyticsData {
  total_integrations: number;
  active_integrations: number;
  total_calls_24h: number;
  successful_calls_24h: number;
  success_rate_24h: number;
  avg_response_time_ms: number;
  integrations: Array<{
    id: number;
    name: string;
    type: string;
    status: string;
    health_status: string;
    calls_24h: number;
    success_rate: number;
  }>;
}

interface UseAnalyticsWebSocketReturn {
  analyticsData: AnalyticsData | null;
  isConnected: boolean;
  error: string | null;
  requestUpdate: () => void;
  subscribeToIntegration: (integrationId: number) => void;
}

export function useAnalyticsWebSocket(): UseAnalyticsWebSocketReturn {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!apiClient.isAuthenticated()) {
      setError('Authentication required for real-time analytics');
      return;
    }

    try {
      const token = apiClient.getToken();
      const wsUrl = `ws://localhost:8000/api/v1/analytics/ws?token=${token}`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('Analytics WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('Analytics WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('Analytics WebSocket error:', error);
        setError('WebSocket connection error');
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to establish WebSocket connection');
    }
  }, []);

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'initial_analytics':
      case 'analytics_update':
        setAnalyticsData(message.data);
        break;
      
      case 'live_update':
        // Merge live update with existing data
        if (analyticsData) {
          setAnalyticsData(prev => ({
            ...prev!,
            ...message.data
          }));
        }
        break;
      
      case 'integration_analytics':
        // Update specific integration data
        if (analyticsData) {
          setAnalyticsData(prev => ({
            ...prev!,
            integrations: prev!.integrations.map(integration =>
              integration.id === message.integration_id
                ? { ...integration, ...message.data }
                : integration
            )
          }));
        }
        break;
      
      case 'error':
        setError(message.message);
        break;
      
      default:
        console.log('Unknown WebSocket message type:', message.type);
    }
  };

  const requestUpdate = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'request_update'
      }));
    }
  }, []);

  const subscribeToIntegration = useCallback((integrationId: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe_integration',
        integration_id: integrationId
      }));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    analyticsData,
    isConnected,
    error,
    requestUpdate,
    subscribeToIntegration
  };
}