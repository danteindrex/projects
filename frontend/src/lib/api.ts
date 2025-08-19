/**
 * API Client for Backend Communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  is_verified: boolean;
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiError {
  detail: string;
}

// Integration Types
export interface Integration {
  id: number;
  name: string;
  description?: string;
  integration_type: string;
  status: 'active' | 'inactive' | 'error' | 'pending' | 'configured';
  base_url?: string;
  credentials: Record<string, string>;
  config: Record<string, any>;
  rate_limit?: number;
  timeout?: number;
  created_at: string;
  updated_at: string;
  last_sync?: string;
  health_status?: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  error_count?: number;
  last_error?: string;
}

export interface IntegrationTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  integration_type: string;
  icon?: string;
  config: {
    endpoints?: Record<string, string>;
    required_credentials: string[];
    optional_credentials?: string[];
    default_settings?: Record<string, any>;
    capabilities?: string[];
  };
  fields: string[];
  documentation_url?: string;
  setup_instructions?: string[];
}

export interface IntegrationUpdate {
  name?: string;
  description?: string;
  base_url?: string;
  credentials?: Record<string, string>;
  config?: Record<string, any>;
  rate_limit?: number;
  timeout?: number;
  status?: 'active' | 'inactive' | 'error' | 'pending' | 'configured';
}

export interface IntegrationHealth {
  integration_id: number;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  last_check: string;
  response_time?: number;
  error_count: number;
  last_error?: string;
  uptime_percentage?: number;
  checks: {
    connectivity: boolean;
    authentication: boolean;
    rate_limits: boolean;
    endpoints: Record<string, boolean>;
  };
  metrics?: {
    avg_response_time: number;
    success_rate: number;
    requests_last_24h: number;
    errors_last_24h: number;
  };
}

// OAuth Types
export interface OAuthConfig {
  supports_oauth: boolean;
  scopes?: string[];
  default_scopes?: string[];
  user_scopes?: string[];
  redirect_uri_required?: boolean;
  note?: string;
}

export interface OAuthSupport {
  integration_type: string;
  supports_oauth: boolean;
  oauth_config?: OAuthConfig;
}

export interface OAuthAuthorizationRequest {
  integration_type: string;
  client_id: string;
  scopes?: string[];
  custom_config?: Record<string, any>;
}

export interface OAuthAuthorizationResponse {
  authorization_url: string;
  state: string;
  integration_type: string;
}

export interface OAuthCallbackRequest {
  integration_type: string;
  authorization_code: string;
  state: string;
  client_id: string;
  client_secret: string;
  name: string;
  description?: string;
  config?: Record<string, any>;
}

// Monitoring Types
export interface ComponentHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time_ms?: number;
  error_message?: string;
  last_check?: string;
  details?: Record<string, any>;
}

export interface HealthStatus {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  components: {
    database: ComponentHealth;
    redis: ComponentHealth;
    kafka: ComponentHealth;
    system_resources: ComponentHealth;
    integrations: ComponentHealth;
  };
}

export interface SystemMetrics {
  timestamp: string;
  system: {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    disk_usage_percent: number;
    uptime_seconds: number;
  };
  application: {
    active_integrations: number;
    total_api_calls_24h: number;
    error_rate_percent: number;
    avg_response_time_ms: number;
  };
}

export interface IntegrationsSummary {
  total: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
  inactive: number;
  by_type: Record<string, number>;
  recent_errors: Array<{
    integration_name: string;
    error_message: string;
    timestamp: string;
  }>;
}

export interface IntegrationEvent {
  call_id: string;
  integration_name: string;
  integration_type: string;
  endpoint: string;
  method: string;
  status_code?: number;
  response_time_ms: number;
  success: boolean;
  error?: string;
  error_type?: string;
  timestamp: number;
}

export interface IntegrationMetrics {
  integration_id: number;
  integration_name: string;
  integration_type: string;
  timeframe: string;
  api_calls: {
    total: number;
    successful: number;
    failed: number;
    rate_limited: number;
  };
  performance: {
    avg_response_time_ms: number;
    min_response_time_ms: number;
    max_response_time_ms: number;
    p95_response_time_ms: number;
  };
  errors: string[];
  health_status: string;
}

export interface IntegrationTestResult {
  success: boolean;
  message: string;
  response_time_ms: number;
  status_code?: number;
  error_details?: string;
  timestamp: string;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.loadToken();
  }

  private loadToken() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('authToken');
    }
  }

  private saveToken(token: string) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('authToken', token);
    }
    this.token = token;
  }

  private removeToken() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
    }
    this.token = null;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      ...options.headers,
    };

    // Only set JSON content-type if not using FormData
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorMessage: string;
        
        try {
          const errorData: ApiError = await response.json();
          errorMessage = errorData.detail || `HTTP ${response.status}: ${response.statusText}`;
        } catch {
          // If response is not JSON, use status text
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }

        // Handle specific status codes with better messages
        switch (response.status) {
          case 400:
            // Check for specific integration errors
            if (errorMessage.includes('integration_type')) {
              errorMessage = 'Invalid integration type. Please select a supported integration.';
            } else if (errorMessage.includes('credentials')) {
              errorMessage = 'Invalid credentials provided. Please check your authentication details.';
            } else {
              errorMessage = errorMessage || 'Invalid request. Please check your input.';
            }
            break;
          case 401:
            errorMessage = 'Authentication required. Please log in again.';
            this.removeToken(); // Clear invalid token
            break;
          case 403:
            errorMessage = 'Access denied. You don\'t have permission for this action.';
            break;
          case 404:
            errorMessage = 'Resource not found. Please check your request.';
            break;
          case 408:
            errorMessage = 'Request timeout. The integration may be slow to respond.';
            break;
          case 422:
            // Handle validation errors specifically
            if (errorMessage.includes('integration_type')) {
              errorMessage = 'Integration type validation failed. Please select a valid type.';
            } else if (errorMessage.includes('credentials')) {
              errorMessage = 'Credential validation failed. Please check all required fields.';
            } else {
              errorMessage = errorMessage || 'Invalid data provided. Please check your input.';
            }
            break;
          case 429:
            errorMessage = 'Rate limit exceeded. Please wait before trying again.';
            break;
          case 500:
            errorMessage = 'Server error occurred. Please try again later.';
            break;
          case 502:
            errorMessage = 'Integration service unavailable. The external service may be down.';
            break;
          case 503:
            errorMessage = 'Service temporarily unavailable. Please try again later.';
            break;
          case 504:
            errorMessage = 'Health check timeout. The integration may be experiencing connectivity issues.';
            break;
        }
        
        throw new Error(errorMessage);
      }

      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return response.text() as unknown as T;
    } catch (error) {
      // Handle network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network connection failed. Please check your internet connection.');
      }
      
      if (error instanceof Error) {
        throw error;
      }
      
      throw new Error('An unexpected error occurred. Please try again.');
    }
  }

  // Auth methods
  async register(userData: RegisterRequest): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await this.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: formData,
    });

    this.saveToken(response.access_token);
    return response;
  }

  logout() {
    this.removeToken();
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Chat methods
  async getChatSessions(): Promise<any[]> {
    return this.request<any[]>('/chat/sessions');
  }

  async createChatSession(title?: string): Promise<any> {
    return this.request<any>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  }

  async getCurrentChatSession(): Promise<any> {
    return this.request<any>('/chat/sessions/current');
  }

  async getChatMessages(sessionId: number): Promise<any[]> {
    return this.request<any[]>(`/chat/sessions/${sessionId}/messages`);
  }

  // Admin methods
  async getAdminChecklist(): Promise<any> {
    return this.request<any>('/admin/checklist');
  }

  // Integration methods
  async getIntegrations(): Promise<Integration[]> {
    return this.request<Integration[]>('/integrations/');
  }

  async getIntegration(id: number): Promise<Integration> {
    return this.request<Integration>(`/integrations/${id}`);
  }

  async createIntegration(integration: {
    name: string;
    description?: string;
    integration_type: string;
    base_url?: string;
    credentials: Record<string, string>;
    config?: Record<string, any>;
    rate_limit?: number;
    timeout?: number;
  }): Promise<Integration> {
    return this.request<Integration>('/integrations/', {
      method: 'POST',
      body: JSON.stringify(integration),
    });
  }

  async updateIntegration(id: number, data: IntegrationUpdate): Promise<Integration> {
    return this.request<Integration>(`/integrations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteIntegration(id: number): Promise<void> {
    return this.request<void>(`/integrations/${id}`, {
      method: 'DELETE',
    });
  }

  async testIntegration(integrationId: number): Promise<any> {
    return this.request<any>(`/integrations/${integrationId}/test`, {
      method: 'POST',
    });
  }

  // Integration Templates
  async getIntegrationTemplates(): Promise<IntegrationTemplate[]> {
    return this.request<IntegrationTemplate[]>('/integrations/templates');
  }

  async getIntegrationTemplate(type: string): Promise<IntegrationTemplate> {
    return this.request<IntegrationTemplate>(`/integrations/templates/${type}`);
  }

  // Health Monitoring
  async getIntegrationHealth(id: number): Promise<IntegrationHealth> {
    return this.request<IntegrationHealth>(`/integrations/${id}/health`);
  }

  async runHealthCheck(id: number): Promise<IntegrationHealth> {
    return this.request<IntegrationHealth>(`/integrations/${id}/health/check`, {
      method: 'POST',
    });
  }

  // OAuth methods
  async getOAuthSupport(integrationType: string): Promise<OAuthSupport> {
    return this.request<OAuthSupport>(`/integrations/oauth/support/${integrationType}`);
  }

  async getOAuthScopes(integrationType: string): Promise<{
    integration_type: string;
    available_scopes: string[];
    default_scopes: string[];
    user_scopes?: string[];
  }> {
    return this.request(`/integrations/oauth/scopes/${integrationType}`);
  }

  async initiateOAuth(request: OAuthAuthorizationRequest): Promise<OAuthAuthorizationResponse> {
    return this.request<OAuthAuthorizationResponse>('/integrations/oauth/authorize', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async completeOAuth(request: OAuthCallbackRequest): Promise<Integration> {
    return this.request<Integration>('/integrations/oauth/callback', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async refreshOAuthToken(integrationId: number, refreshToken: string): Promise<{
    message: string;
    expires_in?: number;
    refreshed_at: string;
  }> {
    return this.request(`/integrations/oauth/refresh/${integrationId}`, {
      method: 'POST',
      body: JSON.stringify({ 
        integration_id: integrationId,
        refresh_token: refreshToken 
      }),
    });
  }

  async revokeOAuthToken(integrationId: number): Promise<{ message: string }> {
    return this.request(`/integrations/oauth/revoke/${integrationId}`, {
      method: 'DELETE',
    });
  }

  // Monitoring endpoints
  async getSystemHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/monitoring/health/detailed');
  }

  async getSystemMetrics(): Promise<any> {
    return this.request<any>('/monitoring/metrics');
  }

  async getIntegrationsSummary(): Promise<IntegrationsSummary> {
    return this.request<IntegrationsSummary>('/monitoring/integrations/summary');
  }

  async testIntegrationMonitoring(integrationId: number): Promise<IntegrationTestResult> {
    return this.request<IntegrationTestResult>(`/monitoring/integrations/${integrationId}/test`, {
      method: 'POST',
    });
  }

  async getIntegrationMetrics(integrationId: number, timeframe: string = '24h'): Promise<IntegrationMetrics> {
    return this.request<IntegrationMetrics>(`/monitoring/integrations/${integrationId}/metrics?timeframe=${timeframe}`);
  }

  async getIntegrationsActivity(limit: number = 50): Promise<IntegrationEvent[]> {
    return this.request<IntegrationEvent[]>(`/monitoring/integrations/activity?limit=${limit}`);
  }

  // Health check
  async healthCheck(): Promise<any> {
    return this.request<any>('/health');
  }

  // WebSocket URL
  getWebSocketUrl(): string {
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/chat/ws';
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  getToken(): string | null {
    return this.token;
  }
}

export const apiClient = new ApiClient();
export default apiClient;