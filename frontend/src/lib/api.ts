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

// Integration Data Response Types
export interface IntegrationDataResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  total?: number;
  page?: number;
  per_page?: number;
}

// GitHub Types
export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  private: boolean;
  html_url: string;
  clone_url: string;
  language?: string;
  stargazers_count: number;
  watchers_count: number;
  forks_count: number;
  open_issues_count: number;
  visibility: 'public' | 'private';
  created_at: string;
  updated_at: string;
  pushed_at: string;
}

export interface GitHubIssue {
  id: number;
  number: number;
  title: string;
  body?: string;
  state: 'open' | 'closed';
  user: {
    id: number;
    login: string;
    avatar_url: string;
  };
  assignee?: {
    id: number;
    login: string;
    avatar_url: string;
  };
  labels: Array<{
    id: number;
    name: string;
    color: string;
  }>;
  pull_request?: {
    url: string;
    html_url: string;
  };
  created_at: string;
  updated_at: string;
  closed_at?: string;
}

// Slack Types
export interface SlackChannel {
  id: string;
  name: string;
  is_channel: boolean;
  is_group: boolean;
  is_im: boolean;
  is_private: boolean;
  is_archived: boolean;
  num_members: number;
  purpose?: {
    value: string;
    creator: string;
    last_set: number;
  };
  topic?: {
    value: string;
    creator: string;
    last_set: number;
  };
  created: number;
}

export interface SlackUser {
  id: string;
  name: string;
  real_name?: string;
  profile: {
    display_name?: string;
    real_name?: string;
    email?: string;
    image_24?: string;
    image_32?: string;
    image_48?: string;
  };
  is_bot: boolean;
  is_admin: boolean;
  is_owner: boolean;
  is_primary_owner: boolean;
  is_restricted: boolean;
  is_ultra_restricted: boolean;
  deleted: boolean;
}

// Jira Types
export interface JiraProject {
  id: string;
  key: string;
  name: string;
  description?: string;
  projectTypeKey: string;
  avatarUrls?: {
    '16x16'?: string;
    '24x24'?: string;
    '32x32'?: string;
    '48x48'?: string;
  };
  lead?: {
    displayName: string;
    emailAddress: string;
  };
}

export interface JiraIssue {
  id: string;
  key: string;
  fields: {
    summary: string;
    description?: string;
    status: {
      name: string;
      statusCategory: {
        key: string;
        name: string;
      };
    };
    issuetype: {
      name: string;
      subtask: boolean;
    };
    priority?: {
      name: string;
    };
    assignee?: {
      displayName: string;
      emailAddress: string;
    };
    reporter?: {
      displayName: string;
      emailAddress: string;
    };
    project: {
      key: string;
      name: string;
    };
    created: string;
    updated: string;
    resolutiondate?: string;
  };
}

// Salesforce Types
export interface SalesforceAccount {
  Id: string;
  Name: string;
  Type?: string;
  Industry?: string;
  Website?: string;
  Phone?: string;
  BillingCity?: string;
  BillingState?: string;
  BillingCountry?: string;
  NumberOfEmployees?: number;
  AnnualRevenue?: number;
  CreatedDate: string;
  LastModifiedDate: string;
}

export interface SalesforceOpportunity {
  Id: string;
  Name: string;
  StageName: string;
  CloseDate: string;
  Amount?: number;
  Probability?: number;
  Type?: string;
  LeadSource?: string;
  Description?: string;
  AccountId?: string;
  Account?: {
    Id: string;
    Name: string;
  };
  CreatedDate: string;
  LastModifiedDate: string;
}

export interface SalesforceLead {
  Id: string;
  FirstName?: string;
  LastName: string;
  Company: string;
  Title?: string;
  Email?: string;
  Phone?: string;
  Status: string;
  LeadSource?: string;
  Industry?: string;
  Rating?: string;
  City?: string;
  State?: string;
  Country?: string;
  CreatedDate: string;
  LastModifiedDate: string;
  ConvertedDate?: string;
}

// Zendesk Types
export interface ZendeskTicket {
  id: number;
  subject: string;
  description?: string;
  status: 'new' | 'open' | 'pending' | 'hold' | 'solved' | 'closed';
  priority?: 'low' | 'normal' | 'high' | 'urgent';
  type?: 'problem' | 'incident' | 'question' | 'task';
  requester?: {
    id: number;
    name: string;
    email: string;
  };
  assignee?: {
    id: number;
    name: string;
    email: string;
  };
  organization_id?: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ZendeskUser {
  id: number;
  name: string;
  email: string;
  role: 'end-user' | 'agent' | 'admin';
  active: boolean;
  verified: boolean;
  suspended: boolean;
  organization_id?: number;
  phone?: string;
  time_zone?: string;
  created_at: string;
  updated_at: string;
}

export interface ZendeskOrganization {
  id: number;
  name: string;
  domain_names: string[];
  details?: string;
  notes?: string;
  shared_tickets: boolean;
  shared_comments: boolean;
  external_id?: string;
  created_at: string;
  updated_at: string;
}

// Trello Types
export interface TrelloBoard {
  id: string;
  name: string;
  desc?: string;
  closed: boolean;
  url: string;
  shortUrl: string;
  prefs: {
    permissionLevel: string;
    voting: string;
    comments: string;
    background: string;
  };
  dateLastActivity: string;
  dateLastView?: string;
}

export interface TrelloList {
  id: string;
  name: string;
  closed: boolean;
  pos: number;
  idBoard: string;
}

export interface TrelloCard {
  id: string;
  name: string;
  desc?: string;
  closed: boolean;
  idList: string;
  idBoard: string;
  pos: number;
  url: string;
  shortUrl: string;
  due?: string;
  dueComplete: boolean;
  dateLastActivity: string;
  labels: Array<{
    id: string;
    idBoard: string;
    name: string;
    color: string;
  }>;
  members: Array<{
    id: string;
    fullName: string;
    username: string;
  }>;
}

// Asana Types
export interface AsanaProject {
  gid: string;
  name: string;
  notes?: string;
  archived: boolean;
  current_status?: {
    text: string;
    color: string;
    created_at: string;
  };
  team?: {
    gid: string;
    name: string;
  };
  owner?: {
    gid: string;
    name: string;
    email: string;
  };
  created_at: string;
  modified_at: string;
}

export interface AsanaTask {
  gid: string;
  name: string;
  notes?: string;
  completed: boolean;
  due_on?: string;
  due_at?: string;
  projects?: Array<{
    gid: string;
    name: string;
  }>;
  assignee?: {
    gid: string;
    name: string;
    email: string;
  };
  created_at: string;
  modified_at: string;
  completed_at?: string;
}

export interface AsanaTeam {
  gid: string;
  name: string;
  description?: string;
  organization?: {
    gid: string;
    name: string;
  };
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
        console.log('🚨 Backend error response:', {
          status: response.status,
          originalMessage: errorMessage,
          url: url,
          method: config.method || 'GET'
        });
        
        switch (response.status) {
          case 400:
            // Check for specific integration errors
            if (errorMessage.includes('integration_type')) {
              errorMessage = 'Invalid integration type. Please select a supported integration.';
            } else if (errorMessage.includes('credentials')) {
              console.log('🔍 ACTUAL backend error (before masking):', errorMessage);
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

  // Integration-specific data endpoints
  async getGitHubRepositories(integrationId: number, page: number = 1, perPage: number = 30): Promise<IntegrationDataResponse<GitHubRepository[]>> {
    return this.request<IntegrationDataResponse<GitHubRepository[]>>(`/integrations/${integrationId}/github/repositories?page=${page}&per_page=${perPage}`);
  }

  async getGitHubIssues(integrationId: number, page: number = 1, perPage: number = 30, state: string = 'all'): Promise<IntegrationDataResponse<GitHubIssue[]>> {
    return this.request<IntegrationDataResponse<GitHubIssue[]>>(`/integrations/${integrationId}/github/issues?page=${page}&per_page=${perPage}&state=${state}`);
  }

  async getSlackChannels(integrationId: number, excludeArchived: boolean = true): Promise<IntegrationDataResponse<SlackChannel[]>> {
    return this.request<IntegrationDataResponse<SlackChannel[]>>(`/integrations/${integrationId}/slack/channels?exclude_archived=${excludeArchived}`);
  }

  async getSlackUsers(integrationId: number): Promise<IntegrationDataResponse<SlackUser[]>> {
    return this.request<IntegrationDataResponse<SlackUser[]>>(`/integrations/${integrationId}/slack/users`);
  }

  async getJiraProjects(integrationId: number): Promise<IntegrationDataResponse<JiraProject[]>> {
    return this.request<IntegrationDataResponse<JiraProject[]>>(`/integrations/${integrationId}/jira/projects`);
  }

  async getJiraIssues(integrationId: number, projectKey?: string, maxResults: number = 50): Promise<IntegrationDataResponse<any>> {
    const params = new URLSearchParams();
    params.append('max_results', maxResults.toString());
    if (projectKey) {
      params.append('project_key', projectKey);
    }
    return this.request<IntegrationDataResponse<any>>(`/integrations/${integrationId}/jira/issues?${params.toString()}`);
  }

  async getSalesforceAccounts(integrationId: number, limit: number = 20): Promise<IntegrationDataResponse<SalesforceAccount[]>> {
    return this.request<IntegrationDataResponse<SalesforceAccount[]>>(`/integrations/${integrationId}/salesforce/accounts?limit=${limit}`);
  }

  async getSalesforceOpportunities(integrationId: number, limit: number = 20): Promise<IntegrationDataResponse<SalesforceOpportunity[]>> {
    return this.request<IntegrationDataResponse<SalesforceOpportunity[]>>(`/integrations/${integrationId}/salesforce/opportunities?limit=${limit}`);
  }

  async getSalesforceLeads(integrationId: number, limit: number = 20): Promise<IntegrationDataResponse<SalesforceLead[]>> {
    return this.request<IntegrationDataResponse<SalesforceLead[]>>(`/integrations/${integrationId}/salesforce/leads?limit=${limit}`);
  }

  async getZendeskTickets(integrationId: number, page: number = 1, perPage: number = 100): Promise<IntegrationDataResponse<ZendeskTicket[]>> {
    return this.request<IntegrationDataResponse<ZendeskTicket[]>>(`/integrations/${integrationId}/zendesk/tickets?page=${page}&per_page=${perPage}`);
  }

  async getZendeskUsers(integrationId: number, page: number = 1, perPage: number = 100): Promise<IntegrationDataResponse<ZendeskUser[]>> {
    return this.request<IntegrationDataResponse<ZendeskUser[]>>(`/integrations/${integrationId}/zendesk/users?page=${page}&per_page=${perPage}`);
  }

  async getZendeskOrganizations(integrationId: number, page: number = 1, perPage: number = 100): Promise<IntegrationDataResponse<ZendeskOrganization[]>> {
    return this.request<IntegrationDataResponse<ZendeskOrganization[]>>(`/integrations/${integrationId}/zendesk/organizations?page=${page}&per_page=${perPage}`);
  }

  async getTrelloBoards(integrationId: number): Promise<IntegrationDataResponse<TrelloBoard[]>> {
    return this.request<IntegrationDataResponse<TrelloBoard[]>>(`/integrations/${integrationId}/trello/boards`);
  }

  async getTrelloCards(integrationId: number, boardId?: string): Promise<IntegrationDataResponse<TrelloCard[]>> {
    const params = boardId ? `?board_id=${boardId}` : '';
    return this.request<IntegrationDataResponse<TrelloCard[]>>(`/integrations/${integrationId}/trello/cards${params}`);
  }

  async getTrelloLists(integrationId: number, boardId?: string): Promise<IntegrationDataResponse<TrelloList[]>> {
    const params = boardId ? `?board_id=${boardId}` : '';
    return this.request<IntegrationDataResponse<TrelloList[]>>(`/integrations/${integrationId}/trello/lists${params}`);
  }

  async getAsanaProjects(integrationId: number): Promise<IntegrationDataResponse<AsanaProject[]>> {
    return this.request<IntegrationDataResponse<AsanaProject[]>>(`/integrations/${integrationId}/asana/projects`);
  }

  async getAsanaTasks(integrationId: number, projectGid?: string, completedSince?: string): Promise<IntegrationDataResponse<AsanaTask[]>> {
    const params = new URLSearchParams();
    if (projectGid) {
      params.append('project_gid', projectGid);
    }
    if (completedSince) {
      params.append('completed_since', completedSince);
    }
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return this.request<IntegrationDataResponse<AsanaTask[]>>(`/integrations/${integrationId}/asana/tasks${queryString}`);
  }

  async getAsanaTeams(integrationId: number): Promise<IntegrationDataResponse<AsanaTeam[]>> {
    return this.request<IntegrationDataResponse<AsanaTeam[]>>(`/integrations/${integrationId}/asana/teams`);
  }

  // Analytics endpoints
  async getAnalyticsOverview(): Promise<any> {
    return this.request<any>('/analytics/integrations/overview');
  }

  async getAnalyticsDashboardSummary(): Promise<any> {
    return this.request<any>('/analytics/dashboard/summary');
  }

  async getIntegrationPerformanceTrends(
    integrationId: number, 
    timeframe: '24h' | '7d' | '30d' = '7d'
  ): Promise<any> {
    return this.request<any>(`/analytics/integrations/${integrationId}/performance-trends?timeframe=${timeframe}`);
  }

  async getIntegrationErrorAnalysis(
    integrationId: number, 
    days: number = 7
  ): Promise<any> {
    return this.request<any>(`/analytics/integrations/${integrationId}/error-analysis?days=${days}`);
  }

  async getIntegrationUsagePatterns(
    integrationId: number, 
    days: number = 30
  ): Promise<any> {
    return this.request<any>(`/analytics/integrations/${integrationId}/usage-patterns?days=${days}`);
  }

  async getCostAnalysis(
    timeframe: '7d' | '30d' | '90d' = '30d'
  ): Promise<any> {
    return this.request<any>(`/analytics/cost-analysis?timeframe=${timeframe}`);
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