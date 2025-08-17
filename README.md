# Business Systems Integration & AI-Powered Management Platform

A multi-tenant platform for integrating business systems with AI-powered management, real-time monitoring, and professional dashboard interfaces.

## 🚀 Features

- **Multi-tenant Architecture**: Secure isolation between different organizations
- **Business System Integration**: Connect any API-based system with configurable templates
- **Real-time Log Streaming**: Live monitoring via Kafka integration
- **AI-Powered Chat Interface**: WebSocket-based chat with CrewAI agents
- **Professional Dashboard**: Clean white background with green accent theme
- **Comprehensive Testing**: Unit, integration, and load testing suite
- **Admin Checklist**: Pre-deployment verification system

## 🏗️ Architecture

### Frontend (Next.js + React)
- Integration setup wizard
- Real-time logs dashboard
- Live chat interface with streaming
- Admin checklist and testing UI
- Professional white + green theme

### Backend (FastAPI)
- WebSocket streaming with structured messages
- Kafka integration for real-time logging
- CrewAI agent management
- Multi-tenant security with RLS

### Data Layer
- Supabase for authentication and data storage
- Encrypted API key storage
- Real-time subscriptions

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, React 18, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+
- **AI**: CrewAI, OpenAI/Anthropic
- **Real-time**: WebSockets, Kafka
- **Database**: Supabase (PostgreSQL)
- **Testing**: pytest, Playwright
- **Deployment**: Docker, Docker Compose

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Supabase account

### 1. Clone and Setup
```bash
git clone <repository-url>
cd business-systems-platform
```

### 2. Start Infrastructure Services
```bash
docker-compose up -d
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Frontend Setup
```bash
cd frontend
npm install
```

### 5. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 6. Start Services
```bash
# Start backend
cd backend
uvicorn main:app --reload

# Start frontend
cd frontend
npm run dev
```

## 📋 Admin Checklist

Before going live, ensure all items are completed:

- [ ] Supabase Auth + RLS configured
- [ ] Integration setup validated
- [ ] WebSocket chat working end-to-end
- [ ] Kafka streams active and visible in UI
- [ ] CrewAI agents registered per integration
- [ ] Tool calling visible in the chat UI
- [ ] UI theme consistent (white + green accents)
- [ ] Checklist passes all items
- [ ] Unit tests written and passing
- [ ] Integration tests for WebSocket, Kafka, agent flows passing
- [ ] Load tests for streaming/log scalability
- [ ] Security audit for secrets and access control

## 🧪 Testing

### Run Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
npm run test:integration

# Load testing
npm run test:load
```

## 🔒 Security Features

- Multi-tenant isolation with Row Level Security (RLS)
- Encrypted API key storage
- Secure WebSocket communication
- Rate limiting and access controls
- Comprehensive audit logging

## 📊 Real-time Features

- **Live Chat**: WebSocket-based streaming with visible tool calling
- **Log Streaming**: Real-time system monitoring via Kafka
- **Agent Activity**: Visible thinking and tool execution phases
- **System Health**: Live integration status and metrics

## 🤖 AI Agent System

- **Integration Agents**: Auto-provisioned per connected system
- **Router Agent**: Central intelligence for query routing
- **Tool Calling**: Visible execution of external API calls
- **Response Streaming**: Token-by-token output delivery

## 🎨 UI/UX Design

- **Primary**: Clean white background for clarity
- **Accents**: Professional green tones (teal, sea-green)
- **Typography**: High contrast for readability
- **Layout**: Modern, responsive dashboard design
- **Accessibility**: WCAG 2.1 AA compliant

## 📈 Monitoring & Analytics

- Real-time system health metrics
- Integration performance tracking
- User activity analytics
- Error rate monitoring
- Response time tracking

## 🔧 Configuration

### Integration Templates
Pre-built templates for common systems:
- Jira
- Zendesk
- Salesforce
- GitHub
- Custom API endpoints

### WebSocket Message Schema
```json
{
  "type": "token|agent_event|tool_result|notice|final",
  "content": "message content",
  "metadata": {},
  "timestamp": "ISO 8601"
}
```

## 🚀 Deployment

### Production
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Environment variables
export ENVIRONMENT=production
export SUPABASE_URL=your_supabase_url
export SUPABASE_ANON_KEY=your_anon_key
export OPENAI_API_KEY=your_openai_key
```

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the admin checklist

---

**Built with ❤️ for modern business operations**
