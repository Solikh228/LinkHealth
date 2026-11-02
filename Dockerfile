# Multi-service container image for SubTracker Fullstack App
FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_ENV=development

# Install system dependencies, curl, and Node.js (v20)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    bash \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get purge -y --auto-remove gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast backend package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 1. Cache & install backend dependencies
COPY backend/pyproject.toml backend/uv.lock /app/backend/
WORKDIR /app/backend
RUN uv sync --frozen --no-cache

# 2. Cache & install frontend dependencies
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* /app/frontend/
RUN npm install

# 3. Copy application source code
WORKDIR /app
COPY backend /app/backend
COPY frontend /app/frontend
COPY openapi.yaml Makefile /app/

# 4. Copy and configure entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose ports:
# 8080: Frontend Web Application
# 8091: Backend REST API
EXPOSE 8080 8091

ENTRYPOINT ["/app/entrypoint.sh"]
