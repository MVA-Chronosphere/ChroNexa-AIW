# Installation Guide

## Prerequisites

Before setting up ChroNexa, ensure you have:

- Python 3.9 or higher
- Node.js 18.0 or higher
- npm or yarn package manager
- Git

### Optional but Recommended

- Docker and Docker Compose (for containerized setup)
- Ollama (for local 7B model support)
- Rhubarb CLI (for lip-sync generation)

## Step-by-Step Setup

### 1. Clone and Navigate to Project

```bash
git clone <repository-url>
cd ChroNexa-AIW
```

### 2. Backend Setup

#### Option A: Native Python Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Edit .env with your settings (use your favorite editor)
# Set GPT_API_KEY, OLLAMA_URL, STRAPI settings, etc.
nano .env  # or use your preferred editor

# Run backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option B: Docker Setup (Backend)

```bash
# From project root
docker build -t chronexa-backend:latest ./backend

# Run container
docker run -p 8000:8000 \
  -e GPT_API_KEY=your_api_key \
  -e LLM_PROVIDER=gpt \
  chronexa-backend:latest
```

### 3. Frontend Setup

#### Option A: Native Node.js Setup

```bash
# From project root
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

#### Option B: Docker Setup (Frontend)

```bash
# From project root
docker build -t chronexa-frontend:latest ./frontend

# Run container
docker run -p 3000:3000 \
  -e VITE_API_URL=http://localhost:8000 \
  chronexa-frontend:latest
```

### 4. Docker Compose Setup (All Services)

```bash
# From project root
docker-compose up -d

# Check services
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Configuration

### Backend Configuration (.env)

Key environment variables:

```env
# LLM Provider (required)
LLM_PROVIDER=gpt              # Use 'gpt' or 'ollama'
GPT_API_KEY=sk-...           # Your OpenAI API key
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=neural-chat

# Knowledge Base
STRAPI_URL=http://localhost:1337
STRAPI_API_TOKEN=your_token
QA_DATABASE_URL=sqlite:///./qa_database.db

# Text-to-Speech
TTS_PROVIDER=edge-tts        # or 'pyttsx3'
TTS_VOICE=hi-IN              # Indian Hindi
TTS_ACCENT=indian

# Lip Sync
RHUBARB_PATH=/usr/local/bin/rhubarb
AUDIO_SAMPLE_RATE=22050

# Server
DEBUG=False
CORS_ORIGINS=["http://localhost:3000"]
API_PORT=8000
API_HOST=0.0.0.0

# Database
DATABASE_URL=sqlite:///./chronexa.db

# Logging
LOG_LEVEL=INFO
```

### Frontend Configuration

The frontend automatically connects to the backend via the proxy configured in `vite.config.ts`.

For production, update:
```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://your-backend-url:8000',
    changeOrigin: true
  }
}
```

## Installing Optional Dependencies

### Rhubarb for Lip Sync

**macOS:**
```bash
brew install rhubarb
```

**Ubuntu/Debian:**
```bash
sudo apt-get install rhubarb
```

**Windows:**
- Download from: https://github.com/DanielSWolf/rhubarb-lip-sync
- Add to system PATH

### Ollama for Local LLM

```bash
# Download and install from https://ollama.ai

# Pull 7B model
ollama pull neural-chat

# Run Ollama
ollama serve
```

## Verification

### Backend Health Check

```bash
# Health check
curl http://localhost:8000/health

# Response should be:
# {"status":"healthy","service":"ChroNexa AI Avatar API"}

# API docs
# Open browser to http://localhost:8000/api/docs
```

### Frontend Verification

```bash
# Check if frontend is running
curl http://localhost:3000

# Should return HTML content
```

## Troubleshooting

### Python Issues

**ModuleNotFoundError**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

**Port already in use**
```bash
# Find process using port 8000
lsof -i :8000
# Kill process
kill -9 <PID>
```

### Node.js Issues

**npm install fails**
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and package-lock
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Docker Issues

**Permission denied**
```bash
# On Linux/macOS
sudo usermod -aG docker $USER
# Logout and login again
```

**Port conflicts**
```bash
# Use different ports
docker run -p 8001:8000 chronexa-backend:latest
docker run -p 3001:3000 chronexa-frontend:latest
```

## Next Steps

1. Configure your LLM provider (GPT or Ollama)
2. Set up Strapi CMS if using Strapi knowledge base
3. Prepare your Q&A dataset
4. Test the API endpoints
5. Customize the avatar appearance
6. Deploy to Temi robot

## Support

For detailed API documentation, visit: `http://localhost:8000/api/docs`

For more information, see:
- [README.md](../README.md) - Project overview
- [API Documentation](api.md) - API endpoint details
- [Architecture](architecture.md) - System architecture
