# System Architecture

## Overview

ChroNexa is a modular AI Avatar system designed for the Temi robot with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Temi Robot (Tablet)                       │
│                   (Kotlin Application)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                    REST API (HTTP)
                         │
        ┌────────────────┴────────────────┐
        │                                 │
    ┌───▼──────────────┐         ┌───────▼──────┐
    │  Frontend (Web)  │         │ Backend API  │
    │  React/Three.js  │         │ FastAPI      │
    └────────┬─────────┘         └───────┬──────┘
             │                          │
             └──────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
    ┌───▼────────┐              ┌──────▼──────┐
    │   LLM      │              │ Knowledge   │
    │  Services  │              │  Base       │
    │            │              │             │
    │ - GPT-4    │              │ - Strapi    │
    │ - Ollama   │              │ - Q&A DB    │
    └────────────┘              │ - GPT       │
                                └─────────────┘
```

## Components

### Frontend (React + TypeScript + Three.js)

**Responsibilities:**
- 3D avatar rendering
- User interface for chat
- Real-time lip sync animation
- State management

**Technology Stack:**
- React 18.2
- TypeScript
- Three.js (3D rendering)
- Zustand (state management)
- Axios (HTTP client)
- Vite (build tool)

**Key Components:**
- `AvatarContainer`: 3D avatar visualization
- `ChatInterface`: User input and message display
- `useAvatar`: Custom hook for avatar lifecycle

### Backend (Python + FastAPI)

**Responsibilities:**
- API endpoint management
- LLM service orchestration
- Knowledge base integration
- Text-to-speech synthesis
- Lip sync data generation

**Technology Stack:**
- Python 3.9+
- FastAPI (web framework)
- Pydantic (data validation)
- Uvicorn (ASGI server)
- SQLAlchemy (ORM)

**Services:**

#### LLM Service
- Multi-provider support (GPT, Ollama)
- Message history management
- Token tracking

#### Text-to-Speech Service
- Indian accent support
- Multiple voice options
- Audio file generation

#### Lip Sync Service
- Rhubarb integration
- Mouth shape generation
- Timing synchronization

#### Knowledge Base Service
- Multi-source search
- Fallback chain (Strapi → Q&A DB → GPT)
- Category filtering

## Data Flow

### Chat Interaction Flow

```
1. User Input
   └─> ChatInterface Component
       └─> Sends POST /api/chat/generate
           │
2. Backend Processing
   └─> ChatRoute Handler
       ├─> Search Knowledge Base (if enabled)
       │   ├─> Query Strapi
       │   ├─> Query Q&A Database
       │   └─> Fallback to GPT if no results
       │
       ├─> Call LLM Service
       │   ├─> Use KB results if available
       │   └─> Generate response
       │
       └─> Return Response
           │
3. Frontend Rendering
   └─> Update Chat Messages
       └─> Trigger Avatar Animation
           ├─> Call POST /api/avatar/animate
           ├─> Call POST /api/avatar/lip-sync
           └─> Render lip sync data
```

### Avatar Animation Flow

```
1. Animation Request
   └─> AvatarContainer Component
       └─> Sends POST /api/avatar/animate
           │
2. Backend Processing
   └─> AvatarRoute Handler
       ├─> Generate TTS Audio
       │   └─> TextToSpeechService
       │
       ├─> Generate Lip Sync
       │   ├─> Call Rhubarb
       │   └─> Get mouth shapes + timings
       │
       └─> Return Animation Data
           │
3. Frontend Rendering
   └─> IndianDoctorAvatar Class
       ├─> Play audio
       ├─> Sync mouth movements
       └─> Update facial expressions
```

## Knowledge Base Integration

### Search Priority Chain

```
User Query
   │
   ├─> Strapi CMS Search
   │   └─ High confidence, structured data
   │      └─ Found? → Return
   │      └─ Not found? → Continue
   │
   ├─> Q&A Database Search
   │   └─ Pre-indexed Q&A pairs
   │      └─ Found? → Return
   │      └─ Not found? → Continue
   │
   └─> GPT Fallback
       └─ Generate contextual response
          └─ Return
```

### Configuration

```python
# config/settings.py
class Settings:
    strapi_url: str              # Strapi CMS location
    strapi_api_token: str        # Authentication token
    qa_database_url: str         # Q&A database connection
    llm_provider: str            # gpt or ollama
```

## API Architecture

### Request/Response Model

All API endpoints follow RESTful conventions:

```
Request:
├─ Method: POST/GET
├─ Headers:
│  ├─ Content-Type: application/json
│  └─ Accept: application/json
└─ Body: JSON (POST only)

Response:
├─ Status: 200/400/500
├─ Headers:
│  └─ Content-Type: application/json
└─ Body: JSON
```

### Service Layers

```
FastAPI Routes
    │
    ├─> Pydantic Models (Validation)
    │
    ├─> Business Logic (Services)
    │   ├─> LLMService
    │   ├─> TextToSpeechService
    │   ├─> LipSyncService
    │   └─> KnowledgeBaseService
    │
    └─> Data Access (Future: Database layer)
```

## Security Considerations

### Current Implementation
- CORS enabled for specified origins
- Environment-based configuration
- API key storage in .env

### Production Recommendations
- Implement Bearer token authentication
- Add API rate limiting
- Use HTTPS/TLS
- Validate and sanitize inputs
- Implement logging and monitoring
- Use secrets manager

## Performance Optimization

### Frontend
- Lazy loading of Three.js models
- WebGL offscreen rendering
- Animation frame throttling
- Component memoization

### Backend
- Response caching for KB queries
- Async/await for I/O operations
- Connection pooling
- Request queuing

### Network
- Gzip compression
- Response streaming
- WebSocket support (planned)

## Deployment Architecture

### Development
```
Local Machine
├─ Backend: http://localhost:8000
└─ Frontend: http://localhost:3000
```

### Docker Compose
```
Docker Network
├─ Backend Container: :8000
├─ Frontend Container: :3000
└─ Ollama Container: :11434
```

### Production (Kubernetes - Planned)
```
K8s Cluster
├─ API Service (Backend)
├─ Web Service (Frontend)
├─ Cache Service (Redis)
├─ Database Service (PostgreSQL)
└─ Ingress Controller
```

## Scalability Considerations

1. **Horizontal Scaling**
   - Multiple API instances
   - Load balancer (nginx, HAProxy)
   - Shared cache (Redis)

2. **Vertical Scaling**
   - Increase container resources
   - GPU acceleration for Three.js

3. **Database**
   - Use PostgreSQL instead of SQLite
   - Implement connection pooling
   - Add caching layer

4. **Content Delivery**
   - CDN for static assets
   - S3 for audio files

## Monitoring & Logging

### Planned Implementation
- Request logging
- Error tracking (Sentry)
- Performance metrics (Prometheus)
- Distributed tracing (Jaeger)

### Health Checks
```
/health    - Basic connectivity
/ready     - Service initialization status
```

## Testing Strategy

### Frontend Testing
- Unit tests (Jest + React Testing Library)
- Integration tests
- E2E tests (Cypress/Playwright)

### Backend Testing
- Unit tests (pytest)
- Integration tests
- API endpoint tests
- Load testing

## Extension Points

1. **Custom LLM Providers**
   - Extend `LLMService` base class
   - Implement provider-specific logic

2. **Knowledge Base Sources**
   - Extend `KnowledgeBaseService`
   - Add new source adapters

3. **Avatar Customization**
   - Extend `IndianDoctorAvatar` class
   - Add animations and expressions

4. **Authentication**
   - Implement middleware
   - Add token validation

---

For implementation details, refer to the README and specific service documentation.
