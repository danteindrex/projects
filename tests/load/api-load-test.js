import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 10 },   // Stay at 10 users
    { duration: '30s', target: 50 },  // Ramp up to 50 users
    { duration: '2m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests under 1s
    http_req_failed: ['rate<0.1'],     // Error rate under 10%
    errors: ['rate<0.1'],              // Custom error rate under 10%
  },
};

const BASE_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000';

// Test data
const testUsers = [
  { email: 'loadtest1@example.com', username: 'loadtest1', password: 'testpass123' },
  { email: 'loadtest2@example.com', username: 'loadtest2', password: 'testpass123' },
  { email: 'loadtest3@example.com', username: 'loadtest3', password: 'testpass123' },
];

export function setup() {
  // Register test users
  const headers = { 'Content-Type': 'application/json' };
  
  testUsers.forEach(user => {
    const payload = JSON.stringify({
      email: user.email,
      username: user.username,
      password: user.password,
      full_name: `Load Test User ${user.username}`
    });
    
    const res = http.post(`${BASE_URL}/api/v1/auth/register`, payload, { headers });
    console.log(`Setup user ${user.username}: ${res.status}`);
  });
  
  return { testUsers };
}

export default function(data) {
  // Select random test user
  const user = data.testUsers[Math.floor(Math.random() * data.testUsers.length)];
  
  // Test scenarios (randomly selected)
  const scenarios = [
    () => testAuthFlow(user),
    () => testChatAPI(user),
    () => testWebSocketChat(user),
    () => testHealthEndpoints(),
  ];
  
  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  scenario();
  
  sleep(Math.random() * 3 + 1); // Random sleep 1-4 seconds
}

function testAuthFlow(user) {
  const headers = { 'Content-Type': 'application/x-www-form-urlencoded' };
  
  // Login
  const loginPayload = `username=${user.email}&password=${user.password}`;
  const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, loginPayload, { headers });
  
  const loginSuccess = check(loginRes, {
    'login status is 200': (r) => r.status === 200,
    'login returns token': (r) => r.json('access_token') !== undefined,
  });
  
  if (!loginSuccess) {
    errorRate.add(1);
    return;
  }
  
  const token = loginRes.json('access_token');
  const authHeaders = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
  
  // Get user info
  const userRes = http.get(`${BASE_URL}/api/v1/auth/me`, { headers: authHeaders });
  
  const userSuccess = check(userRes, {
    'user info status is 200': (r) => r.status === 200,
    'user info returns email': (r) => r.json('email') === user.email,
  });
  
  if (!userSuccess) {
    errorRate.add(1);
  }
  
  // Refresh token
  const refreshRes = http.post(`${BASE_URL}/api/v1/auth/refresh`, null, { headers: authHeaders });
  
  const refreshSuccess = check(refreshRes, {
    'refresh token status is 200': (r) => r.status === 200,
    'refresh returns new token': (r) => r.json('access_token') !== undefined,
  });
  
  if (!refreshSuccess) {
    errorRate.add(1);
  }
}

function testChatAPI(user) {
  // Login first
  const loginPayload = `username=${user.email}&password=${user.password}`;
  const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, loginPayload, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  
  if (loginRes.status !== 200) {
    errorRate.add(1);
    return;
  }
  
  const token = loginRes.json('access_token');
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
  
  // Create chat session
  const chatPayload = JSON.stringify({
    message: `Load test message from ${user.username} at ${new Date().toISOString()}`
  });
  
  const chatRes = http.post(`${BASE_URL}/api/v1/chat/sessions`, chatPayload, { headers });
  
  const chatSuccess = check(chatRes, {
    'chat session created': (r) => r.status === 200,
    'chat returns session_id': (r) => r.json('session_id') !== undefined,
  });
  
  if (!chatSuccess) {
    errorRate.add(1);
    return;
  }
  
  // Get chat sessions
  const sessionsRes = http.get(`${BASE_URL}/api/v1/chat/sessions`, { headers });
  
  const sessionsSuccess = check(sessionsRes, {
    'get sessions status is 200': (r) => r.status === 200,
    'sessions is array': (r) => Array.isArray(r.json()),
  });
  
  if (!sessionsSuccess) {
    errorRate.add(1);
  }
}

function testWebSocketChat(user) {
  // Login first to get token (simplified for WebSocket test)
  const sessionId = `load_test_${Math.random().toString(36).substr(2, 9)}`;
  const url = `${WS_URL}/api/v1/chat/ws/${sessionId}`;
  
  const res = ws.connect(url, {}, function (socket) {
    let messagesReceived = 0;
    let connectionEstablished = false;
    
    socket.on('open', () => {
      console.log(`WebSocket connected for session: ${sessionId}`);
    });
    
    socket.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        messagesReceived++;
        
        if (message.type === 'connection_established') {
          connectionEstablished = true;
          // Send test message
          socket.send(JSON.stringify({
            message: `WebSocket load test from ${user.username}`
          }));
        }
        
        // Close after receiving final message or timeout
        if (message.type === 'final' || messagesReceived > 20) {
          socket.close();
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
        errorRate.add(1);
      }
    });
    
    socket.on('error', (e) => {
      console.error('WebSocket error:', e);
      errorRate.add(1);
    });
    
    socket.on('close', () => {
      const success = connectionEstablished && messagesReceived > 0;
      if (!success) {
        errorRate.add(1);
      }
    });
    
    // Timeout after 10 seconds
    setTimeout(() => {
      if (socket.readyState === 1) {
        socket.close();
      }
    }, 10000);
  });
  
  check(res, {
    'WebSocket connection successful': (r) => r && r.status === 101,
  });
}

function testHealthEndpoints() {
  // Test root endpoint
  const rootRes = http.get(`${BASE_URL}/`);
  
  const rootSuccess = check(rootRes, {
    'root endpoint status is 200': (r) => r.status === 200,
    'root endpoint returns status': (r) => r.json('status') === 'running',
  });
  
  if (!rootSuccess) {
    errorRate.add(1);
  }
  
  // Test health endpoint
  const healthRes = http.get(`${BASE_URL}/health`);
  
  const healthSuccess = check(healthRes, {
    'health endpoint status is 200': (r) => r.status === 200,
    'health endpoint returns healthy': (r) => r.json('status') === 'healthy',
  });
  
  if (!healthSuccess) {
    errorRate.add(1);
  }
}

export function teardown(data) {
  // Cleanup: This would ideally clean up test users
  // For now, just log completion
  console.log('Load test completed');
}