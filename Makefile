.PHONY: run dev backend frontend test test-backend test-frontend test-e2e e2e install build openapi docker-build docker-run help

help:
	@echo "Available commands:"
	@echo "  make run          - Run the backend server on port 8091"
	@echo "  make dev          - Run both backend and frontend concurrently"
	@echo "  make backend      - Run FastAPI backend server (port 8091)"
	@echo "  make frontend     - Run frontend dev server (port 5173)"
	@echo "  make test         - Run all test suites (backend & frontend)"
	@echo "  make test-backend - Run backend pytest suite"
	@echo "  make test-frontend- Run frontend vitest suite"
	@echo "  make e2e          - Run Playwright end-to-end test suite"
	@echo "  make install      - Install all dependencies (uv sync & npm install)"
	@echo "  make build        - Build frontend application"
	@echo "  make openapi      - Re-export openapi.yaml specification"
	@echo "  make docker-build - Build fullstack Docker image"
	@echo "  make docker-run   - Run fullstack Docker container"

run:
	cd backend && uv run uvicorn backend.main:app --reload --port 8091

backend:
	cd backend && uv run uvicorn backend.main:app --reload --port 8091

frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest

test-frontend:
	cd frontend && npm test

e2e:
	npx playwright test

test-e2e: e2e

install:
	cd backend && uv sync
	cd frontend && npm install

build:
	cd frontend && npm run build

openapi:
	cd backend && uv run python scripts/export_openapi.py

docker-build:
	docker build -t fullstack-app:latest .

docker-run:
	docker run -p 8000:8000 fullstack-app:latest
