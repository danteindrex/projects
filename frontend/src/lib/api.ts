/**
 * API Client for Backend Communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001/api/v1';

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
          case 422:
            errorMessage = errorMessage || 'Invalid data provided. Please check your input.';
            break;
          case 429:
            errorMessage = 'Too many requests. Please wait before trying again.';
            break;
          case 500:
            errorMessage = 'Server error occurred. Please try again later.';
            break;
          case 503:
            errorMessage = 'Service temporarily unavailable. Please try again later.';
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

  // Admin methods
  async getAdminChecklist(): Promise<any> {
    return this.request<any>('/admin/checklist');
  }

  // Integration methods
  async getIntegrations(): Promise<any[]> {
    return this.request<any[]>('/integrations/');
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
  }): Promise<any> {
    return this.request<any>('/integrations/', {
      method: 'POST',
      body: JSON.stringify(integration),
    });
  }

  async testIntegration(integrationId: string): Promise<any> {
    return this.request<any>(`/integrations/${integrationId}/test`, {
      method: 'POST',
    });
  }

  // Health check
  async healthCheck(): Promise<any> {
    return this.request<any>('/health');
  }

  // WebSocket URL
  getWebSocketUrl(): string {
    return process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001/api/v1/chat/ws';
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