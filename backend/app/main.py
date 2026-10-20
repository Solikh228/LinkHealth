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
