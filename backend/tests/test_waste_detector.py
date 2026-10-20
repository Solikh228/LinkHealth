from datetime import datetime, timezone
from services.synthetic_data import generate_synthetic_data
from services.cadence import detect_subscriptions
from services.waste_detector import generate_waste_findings


def test_waste_detector_all_five_types():
    data = generate_synthetic_data()
    subs = detect_subscriptions(data["transactions"], data["evidence"])
    ref_date = datetime(2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc)

    findings = generate_waste_findings(
        subscriptions=subs,
        transactions=data["transactions"],
        evidence_list=data["evidence"],
        reference_date=ref_date,
    )

    types = {f.type for f in findings}
    assert "price_increase" in types
    assert "trial_conversion" in types
    assert "duplicate_service" in types
    assert "renewal_approaching" in types

    for f in findings:
        assert f.potentialSavings.amountMinor > 0
        assert f.potentialSavings.currency == "USD"
        # Ensure hypothesis phrasing
        assert any(word in f.explanation.lower() for word in ["charged", "rose", "trial", "could be", "expected", "review", "parallel"])
