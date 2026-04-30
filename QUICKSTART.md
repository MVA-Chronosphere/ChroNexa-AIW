# Quick Start Guide

Get ChroNexa AI Avatar running in minutes!

## Prerequisites

- Python 3.9+
- Node.js 18+
- Git

## Option 1: Native Setup (Recommended for Development)

### 1. Clone and Setup Backend

```bash
# Navigate to project
cd ChroNexa-AIW

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GPT_API_KEY or configure Ollama
```

### 2. Start Backend Server

```bash
# From backend directory
python -m uvicorn app.main:app --reload
```

✅ Backend running at: `http://localhost:8000`  
📖 API Docs: `http://localhost:8000/api/docs`

### 3. Setup Frontend (New Terminal Window)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

✅ Frontend running at: `http://localhost:3000`

### 4. Test the Application

1. Open browser: `http://localhost:3000`
2. Type a message in the chat input
3. See the AI Avatar respond!

---

## Option 2: Docker Setup (Recommended for Deployment)

### One-Command Setup

```bash
# From project root
docker-compose up -d
```

✅ Services running:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/api/docs`

### Check Status

```bash
docker-compose ps
docker-compose logs -f
```

### Stop Services

```bash
docker-compose down
```

---

## Configuration

### Set Your LLM Provider

**Option A: Use GPT-4**

```bash
# In backend/.env
LLM_PROVIDER=gpt
GPT_API_KEY=sk-your-openai-api-key
```

**Option B: Use Ollama (Local)**

```bash
# In backend/.env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=neural-chat

# Then install and run Ollama:
# brew install ollama  (or download from ollama.ai)
# ollama serve
```

---

## Useful Commands

```bash
# Run linting
make lint-backend
make lint-frontend

# Run tests
make test-backend

# Format code
make format-backend

# View all commands
make help
```

---

## Troubleshooting

### Port Already in Use

```bash
# Kill process using port 8000
lsof -i :8000
kill -9 <PID>
```

### CORS Errors

Ensure backend `.env` has frontend URL:
```env
CORS_ORIGINS=["http://localhost:3000"]
```

### Avatar Not Rendering

- Check browser console for WebGL errors
- Update your graphics drivers

---

## Next Steps

1. **Customize Avatar**
   - Edit `frontend/src/services/avatar.ts`
   - Add doctor's name, appearance details

2. **Add Knowledge Base**
   - Set up Strapi at `http://localhost:1337`
   - Configure in `backend/.env`

3. **Deploy to Temi**
   - Use Docker image
   - Update Kotlin app to call `/api/chat/generate`

4. **Production Setup**
   - See [INSTALLATION.md](docs/INSTALLATION.md)
   - See [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## API Quick Reference

### Generate Response
```bash
curl -X POST http://localhost:8000/api/chat/generate \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Animate Avatar
```bash
curl -X POST http://localhost:8000/api/avatar/animate \
  -H "Content-Type: application/json" \
  -d '{
    "animation_type": "speaking",
    "text": "Hello! How can I help?",
    "emotion": "happy"
  }'
```

---

## Support

- **API Documentation**: `http://localhost:8000/api/docs`
- **Full Docs**: [README.md](README.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Installation**: [docs/INSTALLATION.md](docs/INSTALLATION.md)

---

**Ready to go!** 🚀
