import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from repositories.sqlalchemy import (
    SqlAlchemyConnectionRepository,
    SqlAlchemyFindingRepository,
    SqlAlchemySubscriptionRepository,
    SqlAlchemyTransactionRepository,
)
from schemas import (
    ConnectionResponse,
    FindingActionRequest,
    FindingResponse,
    Money,
    SubscriptionResponse,
    TransactionResponse,
)


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    clean_path = db_path.replace("\\", "/")
    url = f"sqlite:///{clean_path}"
    engine = create_engine(url)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    yield TestingSession, engine

    engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


def test_sqlalchemy_repositories_persistence(temp_db):
    TestingSession, engine = temp_db

    # Session 1: Create connection, subscription, transaction, finding
    with TestingSession() as session1:
        conn_repo = SqlAlchemyConnectionRepository(session1)
        sub_repo = SqlAlchemySubscriptionRepository(session1)
        tx_repo = SqlAlchemyTransactionRepository(session1)
        finding_repo = SqlAlchemyFindingRepository(session1)

        conn = ConnectionResponse(
            id="c_sql_1",
            name="Brex Cash",
            type="bank",
            provider="plaid",
            status="connected",
            lastSyncedAt="2026-10-20T00:00:00Z",
        )
        conn_repo.add(conn)

        sub = SubscriptionResponse(
            id="s_sql_1",
            name="Notion Team",
            vendorDomain="notion.so",
            category="Productivity",
            status="active",
            billingInterval="monthly",
            amount=Money(amountMinor=1000, currency="USD"),
            monthlyEquivalent=Money(amountMinor=1000, currency="USD"),
            nextRenewalDate="2026-11-15",
            confidence=0.95,
            explanation="Team workspace",
            lastChargeDate="2026-10-15",
        )
        sub_repo.add(sub)

        tx = TransactionResponse(
            id="tx_sql_1",
            connectionId="c_sql_1",
            subscriptionId="s_sql_1",
            accountName="Brex Operating",
            date="2026-10-15",
            descriptionRaw="NOTION LABS INC",
            amount=Money(amountMinor=-1000, currency="USD"),
            status="posted",
            isRecurringCandidate=True,
        )
        tx_repo.add(tx)

        finding = FindingResponse(
            id="fnd_sql_1",
            subscriptionId="s_sql_1",
            subscriptionName="Notion Team",
            type="renewal_approaching",
            severity="low",
            status="open",
            title="Renewal upcoming",
            explanation="Renews in 25 days",
            potentialSavings=Money(amountMinor=1000, currency="USD"),
            createdAt="2026-10-20T00:00:00Z",
        )
        finding_repo.add(finding)

    # Session 2: Read and verify data persisted across independent sessions
    with TestingSession() as session2:
        conn_repo = SqlAlchemyConnectionRepository(session2)
        sub_repo = SqlAlchemySubscriptionRepository(session2)
        tx_repo = SqlAlchemyTransactionRepository(session2)
        finding_repo = SqlAlchemyFindingRepository(session2)

        conns = conn_repo.list()
        assert len(conns) == 1
        assert conns[0].name == "Brex Cash"

        loaded_sub = sub_repo.get_by_id("s_sql_1")
        assert loaded_sub is not None
        assert loaded_sub.name == "Notion Team"

        txs = tx_repo.list(subscription_id="s_sql_1")
        assert len(txs) == 1
        assert txs[0].descriptionRaw == "NOTION LABS INC"

        loaded_fnd = finding_repo.get_by_id("fnd_sql_1")
        assert loaded_fnd is not None
        assert loaded_fnd.status == "open"

        # Apply action
        action_res = finding_repo.apply_action(
            "fnd_sql_1",
            FindingActionRequest(decision="confirmed_waste", note="Cancelled seat"),
        )
        assert action_res is not None
        assert action_res.status == "confirmed_waste"
        assert action_res.confirmedSavings is not None
        assert action_res.confirmedSavings.amountMinor == 1000

    # Session 3: Verify updated action persisted
    with TestingSession() as session3:
        finding_repo = SqlAlchemyFindingRepository(session3)
        persisted_fnd = finding_repo.get_by_id("fnd_sql_1")
        assert persisted_fnd.status == "confirmed_waste"
        assert persisted_fnd.confirmedSavings.amountMinor == 1000
