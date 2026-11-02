# ==============================================================================
# Stage 1: Build the frontend into static assets
# ==============================================================================
FROM node:20-bookworm-slim AS frontend-builder

WORKDIR /app/frontend

# Install dependencies cleanly for Linux
COPY frontend/package.json ./
RUN npm install --include=optional

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
    STATIC_DIR=/app/backend/static \
    PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONPATH="/app/backend"

# Install curl and libpq runtime library
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast backend dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app/backend

# 1. Install backend dependencies cleanly without frozen lockfile constraint
COPY backend/pyproject.toml backend/uv.lock* backend/README.md* /app/backend/
RUN uv sync --no-install-project --no-cache

# 2. Copy backend source code and sync project
COPY backend/ /app/backend/
RUN uv sync --no-cache

# 3. Copy compiled static frontend assets from stage 1
COPY --from=frontend-builder /app/frontend/.output/public /app/backend/static

# Expose single port for both API and static frontend UI
EXPOSE 8000

# Start FastAPI serving on single port 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
