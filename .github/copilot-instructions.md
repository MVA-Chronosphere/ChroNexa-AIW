<!-- AI Avatar for Temi Robot - Project Instructions -->

## Project Overview
AI Avatar application for temi robot with:
- Python FastAPI backend supporting GPT-4 and Ollama 7B
- React/TypeScript frontend with Three.js for 3D Indian Doctor avatar
- Rhubarb lip sync integration for avatar animations
- Text-to-speech with Indian accent (female voice)
- Knowledge base integration (Strapi, Q&A dataset, GPT)
- REST API for Kotlin app integration
- Support for multiple LLM providers

## Development Guidelines

### Backend Requirements
- FastAPI Python server
- Support for OpenAI GPT-4 and Ollama 7B models
- Knowledge base service (Strapi integration, Q&A, GPT fallback)
- Text-to-speech service with Indian accent
- Lip sync data generation via Rhubarb
- CORS enabled for Kotlin app integration
- Environment-based configuration (GPT_API_KEY, OLLAMA_URL, etc.)

### Frontend Requirements
- React with TypeScript
- Three.js for 3D avatar rendering
- Indian Doctor avatar with professional appearance
- Real-time lip sync animation
- WebSocket support for streaming responses
- Responsive design for tablet integration

### API Specifications
- All endpoints return JSON
- Authentication via API keys or bearer tokens
- Standardized error responses
- Swagger/OpenAPI documentation at /api/docs

### Testing & Deployment
- Unit tests for backend services
- Integration tests for API endpoints
- Docker support for containerization
- CI/CD ready configuration

---

- [x] Verify copilot-instructions.md exists
- [ ] Scaffold project structure
- [ ] Customize project files
- [ ] Create core backend services
- [ ] Create core frontend components
- [ ] Setup database models
- [ ] Compile and test
- [ ] Documentation complete
