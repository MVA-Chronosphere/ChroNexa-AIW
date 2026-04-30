# ChroNexa - AI Avatar for Temi Robot

An interactive AI Avatar application for the Temi robot with advanced conversational capabilities, realistic 3D animation, and multi-LLM support.

## Features

### 🤖 AI Capabilities
- **Dual LLM Support**: GPT-4 and Ollama 7B
- **Knowledge Base Integration**: Strapi CMS, Q&A Dataset, and GPT fallback
- **Context-Aware Responses**: Multi-source knowledge retrieval
- **Smart Fallback**: Automatic escalation to GPT when KB search fails

### 👨‍⚕️ Avatar System
- **3D Indian Doctor Avatar**: Professional appearance using Three.js
- **Real-time Lip Sync**: Rhubarb integration for mouth shape animation
- **Emotional Expressions**: Neutral, happy, sad, surprised, angry, concerned, thinking
- **Natural Animation**: Smooth transitions and realistic movements

### 🗣️ Speech & Audio
- **Text-to-Speech**: Edge TTS with Indian accent (female/male voices)
- **Multiple Accents**: Support for various Indian language variants
- **Synchronized Audio**: Perfect lip-sync with generated speech
- **Audio Processing**: 22.05kHz sample rate for optimal quality

### 📱 Integration Ready
- **REST API**: Full OpenAPI/Swagger documentation
- **Kotlin App Integration**: CORS-enabled for tablet deployment
- **Standalone Application**: Can run independently or as part of Temi ecosystem
- **WebSocket Support**: Streaming responses for real-time interaction

## Project Structure

```
ChroNexa-AIW/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI application entry
│   │   └── routes/         # API endpoints
│   │       ├── chat.py     # Chat/LLM endpoints
│   │       ├── avatar.py   # Avatar control endpoints
│   │       ├── knowledge_base.py  # KB search endpoints
│   │       └── health.py   # Health checks
│   ├── services/           # Business logic
│   │   ├── llm_service.py
│   │   ├── tts_service.py
│   │   ├── lip_sync_service.py
│   │   └── knowledge_base_service.py
│   ├── config/
│   │   └── settings.py     # Configuration management
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React + TypeScript + Three.js
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── AvatarContainer.tsx
│   │   │   └── ChatInterface.tsx
│   │   ├── services/      # API client services
│   │   ├── hooks/         # React hooks
│   │   ├── store/         # Zustand state management
│   │   ├── types/         # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
└── docs/                  # Documentation
```

## Requirements

### Backend
- Python 3.9+
- FastAPI 0.104.1
- Ollama (optional, for local 7B model)
- Rhubarb (for lip-sync generation)
- OpenAI API key (for GPT-4 access)

### Frontend
- Node.js 18+
- npm or yarn
- Modern browser with WebGL support

## Setup & Installation

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run backend server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

Backend will be available at `http://localhost:8000`
API docs: `http://localhost:8000/api/docs`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

Frontend will be available at `http://localhost:3000`

## Configuration

### Environment Variables (.env)

```env
# LLM Configuration
LLM_PROVIDER=gpt  # or 'ollama'
GPT_API_KEY=your_openai_api_key
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=neural-chat-7b

# Knowledge Base
STRAPI_URL=http://localhost:1337
STRAPI_API_TOKEN=your_token
QA_DATABASE_URL=sqlite:///./qa_database.db

# Text-to-Speech
TTS_PROVIDER=edge-tts  # or 'pyttsx3'
TTS_VOICE=hi-IN
TTS_ACCENT=indian

# Lip Sync
RHUBARB_PATH=/usr/local/bin/rhubarb
AUDIO_SAMPLE_RATE=22050

# Server
DEBUG=False
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
API_PORT=8000
API_HOST=0.0.0.0
```

## API Endpoints

### Chat
- `POST /api/chat/generate` - Generate AI response
- `POST /api/chat/stream` - Stream response (chunked)
- `GET /api/chat/models` - List available models

### Avatar
- `POST /api/avatar/animate` - Trigger avatar animation
- `POST /api/avatar/lip-sync` - Generate lip-sync data
- `GET /api/avatar/expressions` - Get available expressions
- `POST /api/avatar/emotion` - Set avatar emotion

### Knowledge Base
- `POST /api/kb/search` - Search knowledge base
- `GET /api/kb/sources` - Get KB source status
- `GET /api/kb/categories` - Get available categories
- `POST /api/kb/index` - Reindex knowledge base

### Health
- `GET /health` - Health check
- `GET /ready` - Readiness check

## Development

### Code Quality

```bash
# Lint backend
cd backend
flake8 app services config

# Type checking
mypy app services config

# Format code
black app services config

# Frontend linting
cd ../frontend
npm run lint

# Type checking
npm run type-check
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Docker Support

### Build Docker Image

```bash
docker build -t chronexa-avatar:latest .
```

### Run with Docker Compose

```bash
docker-compose up -d
```

## Kotlin Integration

The application provides a REST API for integration with Kotlin applications:

```kotlin
// Example Kotlin integration
val apiClient = HttpClient()

// Generate response
val response = apiClient.post("/api/chat/generate") {
    contentType(ContentType.Application.Json)
    setBody(mapOf(
        "messages" to listOf(
            mapOf("role" to "user", "content" to "Hello!")
        )
    ))
}

// Animate avatar
apiClient.post("/api/avatar/animate") {
    setBody(mapOf(
        "animation_type" to "speaking",
        "text" to response.response,
        "emotion" to "happy"
    ))
}
```

## Performance Optimization

- **Streaming responses** for real-time interaction
- **Caching** for frequently accessed KB entries
- **GPU acceleration** for Three.js rendering
- **Lazy loading** of avatar models

## Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Troubleshooting

### Backend Issues

**Port already in use**
```bash
# Find and kill process using port 8000
lsof -i :8000
kill -9 <PID>
```

**GPT API errors**
- Verify API key in `.env`
- Check OpenAI account status

**Ollama connection issues**
- Ensure Ollama is running
- Verify OLLAMA_URL setting

### Frontend Issues

**CORS errors**
- Check backend CORS_ORIGINS setting
- Verify frontend URL is in whitelist

**Avatar rendering issues**
- Check browser console for WebGL errors
- Verify Three.js version compatibility

**Lip-sync not working**
- Ensure Rhubarb is installed
- Check audio file format (WAV recommended)

## Contributing

1. Create feature branch
2. Make changes
3. Run tests and linting
4. Submit pull request

## License

MIT License - See LICENSE file

## Support

For issues and questions:
- Open GitHub Issues
- Check documentation in `/docs`
- Review API documentation at `/api/docs`

---

**Made with ❤️ for Temi Robot**
