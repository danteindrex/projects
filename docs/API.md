# Business Systems Integration Platform - API Documentation

## Overview

The Business Systems Integration Platform provides a comprehensive REST API for managing integrations, chat sessions, and AI agents. The API is built with FastAPI and follows OpenAPI standards.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Getting a Token

1. Register a new user or login with existing credentials
2. Use the returned access token for subsequent API calls

## API Endpoints

### Authentication

#### POST /api/v1/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username", 
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "username",
  "full_name": "John Doe",
  "role": "user",
  "is_verified": false
}
```

#### POST /api/v1/auth/login
Login with email/username and password.

**Request Body (Form Data):**
```
username: user@example.com
password: password123
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### GET /api/v1/auth/me
Get current user information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com", 
  "username": "username",
  "full_name": "John Doe",
  "role": "user",
  "is_verified": false
}
```

#### POST /api/v1/auth/refresh
Refresh the access token.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "access_token": "new_jwt_token_here",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Chat Management

#### POST /api/v1/chat/sessions
Create a new chat session.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "message": "Hello, I need help with my Jira issues"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "message_id": "uuid", 
  "content": "Hello, I need help with my Jira issues",
  "message_type": "user",
  "metadata": {
    "session_title": "Hello, I need help with my Jira issues"
  }
}
```

#### GET /api/v1/chat/sessions
Get user's chat sessions.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "session_id": "uuid",
    "message_id": 0,
    "content": "Session Title",
    "message_type": "session",
    "metadata": {
      "status": "active",
      "total_messages": 5
    }
  }
]
```

### WebSocket Chat

#### WS /api/v1/chat/ws/{session_id}
Real-time chat WebSocket connection.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws/session_123');
```

**Message Types:**

1. **Connection Established**
```json
{
  "type": "connection_established",
  "session_id": "session_123",
  "timestamp": "2023-01-01T00:00:00Z"
}
```

2. **Send Message**
```json
{
  "message": "What are my open Jira tickets?",
  "metadata": {}
}
```

3. **Agent Thinking**
```json
{
  "type": "agent_event",
  "content": "thinking",
  "metadata": {
    "event_type": "thinking",
    "details": "Processing your request..."
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

4. **Tool Execution**
```json
{
  "type": "tool_result",
  "content": "API call completed successfully",
  "metadata": {
    "tool_name": "integration_api",
    "status": "completed",
    "result": "Data retrieved from external system"
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

5. **Response Streaming**
```json
{
  "type": "token",
  "content": "word ",
  "metadata": {
    "token_index": 1,
    "total_tokens": 50
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

6. **Final Response**
```json
{
  "type": "final",
  "content": "Response completed",
  "metadata": {
    "session_id": "session_123",
    "tokens_used": 150
  },
  "timestamp": "2023-01-01T00:00:00Z"
}
```

### Integrations

#### GET /api/v1/integrations
Get user's integrations.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Jira Integration",
    "integration_type": "jira",
    "status": "active",
    "config": {
      "endpoint": "https://company.atlassian.net"
    },
    "created_at": "2023-01-01T00:00:00Z",
    "last_sync": "2023-01-01T12:00:00Z"
  }
]
```

#### POST /api/v1/integrations
Create a new integration.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "Jira Integration",
  "integration_type": "jira",
  "config": {
    "endpoint": "https://company.atlassian.net",
    "project_key": "PROJ"
  },
  "credentials": {
    "api_token": "your_api_token",
    "email": "user@company.com"
  }
}
```

#### PUT /api/v1/integrations/{integration_id}
Update an existing integration.

#### DELETE /api/v1/integrations/{integration_id}
Delete an integration.

#### POST /api/v1/integrations/{integration_id}/test
Test integration connection.

### Health & Monitoring

#### GET /health
System health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123
}
```

#### GET /
Root endpoint with system information.

**Response:**
```json
{
  "message": "Business Systems Integration Platform",
  "version": "1.0.0", 
  "status": "running"
}
```

## Error Handling

The API uses standard HTTP status codes and returns errors in the following format:

```json
{
  "detail": "Error description"
}
```

### Common Status Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **General endpoints**: 60 requests per minute
- **Authentication endpoints**: 5 requests per minute
- **Chat endpoints**: 30 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window

## Pagination

List endpoints support pagination using query parameters:

- `page`: Page number (default: 1)
- `size`: Page size (default: 20, max: 100)

**Example:**
```
GET /api/v1/chat/sessions?page=2&size=10
```

**Response includes pagination metadata:**
```json
{
  "items": [...],
  "total": 150,
  "page": 2,
  "size": 10,
  "pages": 15
}
```

## Interactive Documentation

Visit the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## SDKs and Libraries

### Python SDK Example

```python
import requests

class BusinessPlatformClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({'Authorization': f'Bearer {token}'})
    
    def login(self, username, password):
        response = self.session.post(
            f'{self.base_url}/api/v1/auth/login',
            data={'username': username, 'password': password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data['access_token']
        self.session.headers.update({'Authorization': f'Bearer {self.token}'})
        return data
    
    def create_chat_session(self, message):
        response = self.session.post(
            f'{self.base_url}/api/v1/chat/sessions',
            json={'message': message}
        )
        response.raise_for_status()
        return response.json()
    
    def get_integrations(self):
        response = self.session.get(f'{self.base_url}/api/v1/integrations')
        response.raise_for_status()
        return response.json()

# Usage
client = BusinessPlatformClient('http://localhost:8000')
client.login('user@example.com', 'password')
session = client.create_chat_session('Hello AI!')
integrations = client.get_integrations()
```

### JavaScript SDK Example

```javascript
class BusinessPlatformClient {
    constructor(baseUrl, token = null) {
        this.baseUrl = baseUrl;
        this.token = token;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
        
        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const data = await this.request('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });
        
        this.token = data.access_token;
        return data;
    }

    async createChatSession(message) {
        return this.request('/api/v1/chat/sessions', {
            method: 'POST',
            body: JSON.stringify({ message })
        });
    }

    connectWebSocket(sessionId) {
        const ws = new WebSocket(`ws://${this.baseUrl.replace('http://', '')}/api/v1/chat/ws/${sessionId}`);
        return ws;
    }
}

// Usage
const client = new BusinessPlatformClient('http://localhost:8000');
await client.login('user@example.com', 'password');
const session = await client.createChatSession('Hello AI!');
const ws = client.connectWebSocket(session.session_id);
```

## WebSocket Best Practices

1. **Connection Management**: Always handle connection events properly
2. **Message Handling**: Parse JSON messages safely with try-catch
3. **Reconnection**: Implement automatic reconnection logic
4. **Error Handling**: Handle WebSocket errors gracefully
5. **Rate Limiting**: Respect message rate limits to avoid disconnection

## Testing

Use the provided test scripts to verify API functionality:

```bash
# Run backend API tests
cd backend && python -m pytest tests/

# Run load tests
k6 run tests/load/api-load-test.js

# Test WebSocket connection
node tests/websocket-test.js
```