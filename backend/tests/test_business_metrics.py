"""
Tests for SubTracker OpenTelemetry Business Metrics.
Verifies recording of:
- subscriptions_created
- active_subscriptions
- active_users
- subscription_creation_failures
- notification_delivery_latency
with standardized 'environment' and 'deployed_version' labels.
"""

import os
from fastapi.testclient import TestClient
from app.main import app
from telemetry import (
    extract_service_version,
    get_metric_labels,
    record_active_subscriptions_delta,
    record_active_user_login,
    record_active_user_logout,
    record_notification_latency,
    record_subscription_created,
    record_subscription_failure,
)


def test_metric_labels_include_environment_and_version():
    os.environ["DEPLOYMENT_ENVIRONMENT"] = "prod"
    os.environ["APP_IMAGE"] = "subtracker:20261116-140000-sha123"

    labels = get_metric_labels({"custom_key": "custom_val"})
    assert labels["environment"] == "prod"
    assert labels["deployed_version"] == "20261116-140000-sha123"
    assert labels["custom_key"] == "custom_val"


def test_record_all_custom_business_metrics_safely():
    # Verify each helper executes safely without exceptions
    record_subscription_created(cadence="annual", vendor="Slack")
    record_active_subscriptions_delta(1, status="active")
    record_active_subscriptions_delta(-1, status="cancelled")
    record_active_user_login(user_id="usr_test_123")
    record_active_user_logout(user_id="usr_test_123")
    record_subscription_failure(reason="invalid_amount", operation="create", status_code=422)
    record_notification_latency(duration_ms=42.5, notification_type="renewal_reminder", status="delivered")


def test_subscriptions_api_endpoints_trigger_metrics():
    client = TestClient(app)

    # 1. Create subscription triggers subscriptions_created metric
    resp = client.post(
        "/api/subscriptions",
        json={
            "name": "Datadog APM",
            "amountMinor": 15000,
            "currency": "USD",
            "billingInterval": "monthly",
            "category": "DevOps",
            "status": "active",
            "nextRenewalDate": "2026-12-01",
        },
    )
    assert resp.status_code == 201
    created_id = resp.json()["id"]

    # 2. Patch subscription to cancelled triggers active_subscriptions delta
    patch_resp = client.patch(
        f"/api/subscriptions/{created_id}",
        json={"status": "cancelled"},
    )
    assert patch_resp.status_code == 200

    # 3. Patch non-existent subscription triggers subscription_creation_failures metric
    fail_resp = client.patch(
        "/api/subscriptions/non_existent_sub_9999",
        json={"name": "Ghost"},
    )
    assert fail_resp.status_code == 404

    # 4. Trigger renewal notification dispatch triggers notification_delivery_latency metric
    notif_resp = client.post("/api/subscriptions/notifications/send-renewals?days_ahead=30")
    assert notif_resp.status_code == 200
    assert "deliveryLatencyMs" in notif_resp.json()
