from services.normalizer import is_non_subscription_transaction, normalize_merchant
from services.cadence import detect_subscriptions
from services.synthetic_data import generate_synthetic_data
from schemas import Money, TransactionResponse


def test_merchant_normalizer():
    name, domain, cat = normalize_merchant("AMZN MKTP US*2K389 AWS.AMAZON.COM")
    assert name == "Amazon Web Services"
    assert domain == "aws.amazon.com"
    assert cat == "Infrastructure"

    name, domain, _ = normalize_merchant("GITHUB INC DIR DEP")
    assert name == "GitHub"
    assert domain == "github.com"

    name, domain, _ = normalize_merchant("FIGMA.COM *INV48201")
    assert name == "Figma"
    assert domain == "figma.com"


def test_exclusion_of_non_subscriptions():
    assert is_non_subscription_transaction("PAYROLL DIRECT DEP GUSTO") is True
    assert is_non_subscription_transaction("ONLINE BANKING TRANSFER TO CHK 1234") is True
    assert is_non_subscription_transaction("WIRE TRANS FEE") is True
    assert is_non_subscription_transaction("ZELLE PAYMENT TO JOHN") is True
    assert is_non_subscription_transaction("ATM WITHDRAWAL MAIN ST") is True

    # Subscription charges should NOT be excluded
    assert is_non_subscription_transaction("FIGMA.COM *INV") is False
    assert is_non_subscription_transaction("ADOBE *CREATIVE CLOUD") is False


def test_subscription_cadence_and_detection():
    data = generate_synthetic_data()
    detected = detect_subscriptions(data["transactions"], data["evidence"])

    assert len(detected) >= 5

    names = {s.name for s in detected}
    assert "Figma" in names
    assert "Adobe Creative Cloud" in names
    assert "Amazon Web Services" in names
    assert "Google Workspace" in names

    figma_sub = next(s for s in detected if s.name == "Figma")
    assert figma_sub.billingInterval == "monthly"
    assert figma_sub.amount.amountMinor == 1500
    assert figma_sub.confidence >= 0.85
    assert "monthly cadence" in figma_sub.explanation.lower()
    assert len(figma_sub.evidence) >= 1
