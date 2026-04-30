.PHONY: help install dev test lint format clean docker-build docker-up docker-down

help:
	@echo "ChroNexa AI Avatar - Available Commands"
	@echo "======================================="
	@echo ""
	@echo "Backend Commands:"
	@echo "  make install-backend      - Install backend dependencies"
	@echo "  make run-backend          - Run backend server"
	@echo "  make test-backend         - Run backend tests"
	@echo "  make lint-backend         - Lint backend code"
	@echo "  make format-backend       - Format backend code"
	@echo ""
	@echo "Frontend Commands:"
	@echo "  make install-frontend     - Install frontend dependencies"
	@echo "  make dev-frontend         - Run frontend dev server"
	@echo "  make build-frontend       - Build frontend for production"
	@echo "  make lint-frontend        - Lint frontend code"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make docker-build         - Build Docker images"
	@echo "  make docker-up            - Start services with Docker Compose"
	@echo "  make docker-down          - Stop services"
	@echo "  make docker-logs          - View Docker logs"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean                - Clean build artifacts"
	@echo "  make setup                - Setup both backend and frontend"

install-backend:
	cd backend && python -m venv venv && \
	. venv/bin/activate && \
	pip install -r requirements.txt

run-backend:
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test-backend:
	cd backend && python -m pytest

lint-backend:
	cd backend && python -m flake8 app services config

format-backend:
	cd backend && python -m black app services config

install-frontend:
	cd frontend && npm install

dev-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

lint-frontend:
	cd frontend && npm run lint

type-check-frontend:
	cd frontend && npm run type-check

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-logs-backend:
	docker-compose logs -f backend

docker-logs-frontend:
	docker-compose logs -f frontend

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	find . -type d -name dist -exec rm -rf {} +
	find . -type d -name build -exec rm -rf {} +

setup: install-backend install-frontend
	@echo "Setup complete! Both backend and frontend dependencies installed."

# Development targets
dev: docker-up
	@echo "Services started. Access:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/api/docs"

prod-build: clean docker-build
	@echo "Production build complete"
