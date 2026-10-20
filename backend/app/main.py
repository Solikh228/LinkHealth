from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    auth_router,
    dashboard_router,
    findings_router,
    integrations_router,
    subscriptions_router,
    transactions_router,
)

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
