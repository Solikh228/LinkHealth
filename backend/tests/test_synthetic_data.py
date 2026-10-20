from datetime import datetime
from services.synthetic_data import generate_synthetic_data, seed_synthetic_data
from repositories.memory import InMemoryTransactionRepository


def test_synthetic_data_generation_volume_and_merchants():
    data = generate_synthetic_data()
    txs = data["transactions"]
    evidence = data["evidence"]

    # At least 25 realistic raw transactions
    assert len(txs) >= 25, f"Expected >= 25 transactions, got {len(txs)}"
    assert len(evidence) >= 15, f"Expected >= 15 evidence records, got {len(evidence)}"

    # Span across key merchants
    merchants = {t.merchantNormalized for t in txs if t.merchantNormalized}
    assert "Figma" in merchants
    assert "Adobe" in merchants
    assert "Amazon Web Services" in merchants
    assert "GitHub" in merchants
    assert "Google Workspace" in merchants
    assert "Notion" in merchants


def test_synthetic_variations():
    data = generate_synthetic_data()
    txs = data["transactions"]

    # Trial conversion
    trial_txs = [t for t in txs if "TRIAL CONV" in t.descriptionRaw]
    assert len(trial_txs) >= 1

    # Price increase in Notion
    notion_txs = [t for t in txs if t.merchantNormalized == "Notion" and "TRIAL" not in t.descriptionRaw]
    notion_amounts = [abs(t.amount.amountMinor) for t in notion_txs]
    assert 1000 in notion_amounts
    assert 1200 in notion_amounts

    # Currency formatting & validity
    for t in txs:
        assert t.amount.currency == "USD"
        assert isinstance(t.amount.amountMinor, int)
        # Dates are valid ISO format YYYY-MM-DD
        datetime.strptime(t.date, "%Y-%m-%d")


def test_seed_synthetic_data_into_repository():
    repo = InMemoryTransactionRepository()
    class DummyBundle:
        tx_repo = repo

    count = seed_synthetic_data(DummyBundle())
    assert count >= 25
    assert len(repo.list(limit=100)) >= 25
