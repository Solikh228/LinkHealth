# ==============================================================================
# Stage 1: Build the frontend into static assets
# ==============================================================================
FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies with caching
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci || npm install

# Copy frontend source code
COPY frontend/ ./

# Build frontend and generate static index.html into .output/public
ENV VITE_API_MODE=http
ENV VITE_API_BASE_URL=""
RUN npm run build

# ==============================================================================
# Stage 2: Final minimal production image running FastAPI backend
# ==============================================================================
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    STATIC_DIR=/app/backend/static

# Install uv for fast backend dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 1. Install backend dependencies
COPY backend/pyproject.toml backend/uv.lock /app/backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-cache

# 2. Copy backend source code
COPY backend/ /app/backend/

# 3. Copy compiled static frontend assets from stage 1
COPY --from=frontend-builder /app/frontend/.output/public /app/backend/static

# Expose single port for both API and static frontend UI
EXPOSE 8000

# Start FastAPI serving on single port 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
