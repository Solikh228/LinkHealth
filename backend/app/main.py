import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import (
    auth_router,
    dashboard_router,
    findings_router,
    integrations_router,
    subscriptions_router,
    transactions_router,
)
from routers.overview import router as overview_router
from routers.subscriptions import router as contract_subscriptions_router
from routers.findings import router as contract_findings_router
from routers.connections import router as contract_connections_router
from routers.statements import router as statements_router
from routers.bank_integrations import router as bank_integrations_router
from routers.email_integrations import router as email_integrations_router

app = FastAPI(
    title="SubTracker API",
    description="Backend REST API for Hidden B2B Subscriptions & Waste Finder Tracker",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static directory for serving pre-built frontend SPA
STATIC_DIR = os.getenv("STATIC_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"))

if os.path.isdir(STATIC_DIR):
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.middleware("http")
async def spa_fallback_middleware(request: Request, call_next):
    accept = request.headers.get("accept", "")
    path = request.url.path

    # If it's a browser requesting an HTML page for non-API routes, return index.html
    if (
        request.method == "GET"
        and "text/html" in accept
        and not path.startswith(("/api", "/docs", "/openapi.json", "/health"))
        and os.path.isdir(STATIC_DIR)
    ):
        direct_file = os.path.join(STATIC_DIR, path.lstrip("/"))
        if path != "/" and os.path.isfile(direct_file):
            return FileResponse(direct_file)
        index_html = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_html):
            return FileResponse(index_html)

    response = await call_next(request)

    # If 404 on GET and not an API/docs route, check direct static file or fallback to index.html
    if (
        response.status_code == 404
        and request.method == "GET"
        and not path.startswith(("/api", "/docs", "/openapi.json", "/health"))
        and os.path.isdir(STATIC_DIR)
    ):
        direct_file = os.path.join(STATIC_DIR, path.lstrip("/"))
        if os.path.isfile(direct_file):
            return FileResponse(direct_file)
        index_html = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_html):
            return FileResponse(index_html)

    return response

# Contract routers
app.include_router(overview_router)
app.include_router(contract_subscriptions_router)
app.include_router(contract_findings_router)
app.include_router(contract_connections_router)
app.include_router(statements_router)
app.include_router(bank_integrations_router)
app.include_router(email_integrations_router)

# Include routers at root level
app.include_router(auth_router)
app.include_router(integrations_router)
app.include_router(dashboard_router)
app.include_router(transactions_router)
app.include_router(subscriptions_router)
app.include_router(findings_router)

# Also include with /api prefix for client flexibility
app.include_router(auth_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(transactions_router, prefix="/api")
app.include_router(subscriptions_router, prefix="/api")
app.include_router(findings_router, prefix="/api")


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": "SubTracker API", "version": "1.0.0"}


@app.get("/", tags=["Health"])
def root():
    return {
        "name": "SubTracker API",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }
