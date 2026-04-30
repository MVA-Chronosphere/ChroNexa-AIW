# API Documentation

## Base URL

```
http://localhost:8000/api
```

## Authentication

Currently, the API uses CORS-based access control. For production, implement:
- Bearer token authentication
- API key authentication
- OAuth 2.0

## Endpoints

### Health & Status

#### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "ChroNexa AI Avatar API"
}
```

#### GET /ready
Readiness check for service initialization.

**Response:**
```json
{
  "status": "ready",
  "service": "ChroNexa AI Avatar API"
}
```

---

### Chat Endpoints

#### POST /chat/generate
Generate a response from the AI using configured LLM.

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 512,
  "use_knowledge_base": true
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you for asking!",
  "model": "gpt-4",
  "tokens_used": 45,
  "source": "gpt"
}
```

**Parameters:**
- `messages` (required): Array of message objects with role and content
- `model` (optional): Model to use (default from config)
- `temperature` (optional): Sampling temperature 0-2 (default: 0.7)
- `max_tokens` (optional): Maximum tokens to generate (default: 512)
- `use_knowledge_base` (optional): Use KB search before LLM (default: true)

**Status Codes:**
- `200`: Success
- `400`: Invalid request
- `500`: Server error

#### POST /chat/stream
Stream response using chunked transfer encoding.

**Same parameters as `/chat/generate`**

**Response:** Streamed text chunks

#### GET /chat/models
Get list of available LLM models.

**Response:**
```json
{
  "models": [
    {
      "name": "gpt-4",
      "provider": "openai",
      "active": true
    },
    {
      "name": "ollama-7b",
      "provider": "ollama",
      "active": false
    }
  ]
}
```

---

### Avatar Endpoints

#### POST /avatar/animate
Trigger avatar animation with parameters.

**Request Body:**
```json
{
  "animation_type": "speaking",
  "text": "Hello, I am your AI doctor assistant.",
  "emotion": "happy",
  "duration": 5.0
}
```

**Response:**
```json
{
  "status": "queued",
  "animation_id": "anim_001",
  "duration": 5.0
}
```

**Parameters:**
- `animation_type` (required): "speaking", "idle", "gesture"
- `text` (required): Text to display/speak
- `emotion` (optional): "neutral", "happy", "sad", "surprised", "angry", "concerned", "thinking"
- `duration` (optional): Animation duration in seconds

#### POST /avatar/lip-sync
Generate lip sync data from audio.

**Request Body:**
```json
{
  "audio_path": "/path/to/audio.wav",
  "text": "Hello, world!"
}
```

**Response:**
```json
{
  "status": "pending",
  "audio_path": "/path/to/audio.wav",
  "mouth_shapes": ["A", "E", "I", "O", "U"],
  "timings": [0.0, 0.5, 1.0, 1.5, 2.0],
  "duration": 2.5
}
```

#### GET /avatar/expressions
Get available facial expressions.

**Response:**
```json
{
  "expressions": [
    "neutral",
    "happy",
    "sad",
    "surprised",
    "angry",
    "concerned",
    "thinking"
  ]
}
```

#### POST /avatar/emotion
Set avatar emotional state.

**Request Body:**
```json
{
  "emotion": "happy"
}
```

**Response:**
```json
{
  "status": "updated",
  "emotion": "happy"
}
```

---

### Knowledge Base Endpoints

#### POST /kb/search
Search knowledge base across all sources.

**Request Body:**
```json
{
  "query": "What are the symptoms of diabetes?",
  "category": "medical",
  "limit": 5
}
```

**Response:**
```json
{
  "results": [
    {
      "question": "What are diabetes symptoms?",
      "answer": "Common symptoms include increased thirst, frequent urination...",
      "source": "strapi",
      "confidence": 0.95
    }
  ],
  "total": 1
}
```

**Parameters:**
- `query` (required): Search query
- `category` (optional): Filter by category
- `limit` (optional): Maximum results (default: 5)

**Response Fields:**
- `question`: Original question from KB
- `answer`: Answer text
- `source`: "strapi", "qa_dataset", or "gpt"
- `confidence`: Confidence score 0-1

#### GET /kb/sources
Get knowledge base source status.

**Response:**
```json
{
  "sources": [
    {
      "name": "strapi",
      "active": false,
      "items": 0
    },
    {
      "name": "qa_dataset",
      "active": false,
      "items": 0
    },
    {
      "name": "gpt",
      "active": true,
      "method": "fallback"
    }
  ]
}
```

#### GET /kb/categories
Get available KB categories.

**Response:**
```json
{
  "categories": [
    "general",
    "medical",
    "faq",
    "temi_features"
  ]
}
```

#### POST /kb/index
Reindex knowledge base from all sources.

**Response:**
```json
{
  "status": "reindexing",
  "message": "Knowledge base reindexing started"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing/invalid auth |
| 404 | Not Found - Resource doesn't exist |
| 500 | Server Error - Internal error |
| 503 | Service Unavailable - Server temporarily down |

---

## Rate Limiting

Currently not implemented. Will be added for production deployments.

---

## Webhooks

Planned for future releases:
- Response generated
- Avatar animation completed
- Error occurred

---

## Changelog

### v0.1.0 (Initial Release)
- Chat generation endpoints
- Avatar animation endpoints
- Knowledge base search
- Lip sync generation
- Health checks

---

## Examples

### Example 1: Generate Response and Animate Avatar

```bash
# Step 1: Generate response
curl -X POST http://localhost:8000/api/chat/generate \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "use_knowledge_base": true
  }'

# Response:
# {"response":"Hello! How can I help you today?","model":"gpt-4","tokens_used":12,"source":"gpt"}

# Step 2: Animate avatar with response
curl -X POST http://localhost:8000/api/avatar/animate \
  -H "Content-Type: application/json" \
  -d '{
    "animation_type": "speaking",
    "text": "Hello! How can I help you today?",
    "emotion": "happy"
  }'
```

### Example 2: Search Knowledge Base

```bash
curl -X POST http://localhost:8000/api/kb/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to use the Temi robot?",
    "category": "temi_features",
    "limit": 3
  }'
```

---

## Testing with Postman

1. Import the API collection from `/docs/postman-collection.json`
2. Set base URL: `http://localhost:8000`
3. Test individual endpoints

---

## WebSocket Support (Planned)

Streaming responses will support WebSocket for real-time interaction:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/chat/stream');
ws.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  console.log(chunk.text);  // Partial response
};
```

---

For more information, visit the interactive API docs at:
```
http://localhost:8000/api/docs
```
