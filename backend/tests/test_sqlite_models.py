import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database import Base
from models import (
    Action,
    BillingEvidence,
    Connection,
    Finding,
    Subscription,
    Transaction,
    User,
)


@pytest.fixture
def db_session():
    # Isolated in-memory SQLite database with foreign_keys ON
    test_engine = create_engine("sqlite:///:memory:")

    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_sqlite_pragmas(db_session):
    # Verify foreign_keys enabled
    fk_result = db_session.execute(text("PRAGMA foreign_keys")).scalar()
    assert fk_result == 1


def test_models_insertion_and_relationship(db_session):
    user = User(
        id="usr_1",
        email="founder@startup.io",
        password_hash="argon2_hash_value",
        created_at="2026-10-20T00:00:00Z",
    )
    db_session.add(user)
    db_session.commit()

    conn = Connection(
        id="conn_1",
        user_id=user.id,
        name="Silicon Valley Bank",
        type="bank",
        provider="plaid",
        status="connected",
        last_synced_at="2026-10-20T00:00:00Z",
    )
    db_session.add(conn)

    sub = Subscription(
        id="sub_1",
        user_id=user.id,
        name="Datadog",
        category="Monitoring",
        status="active",
        billing_interval="monthly",
        amount_minor=15000,
        currency="USD",
        monthly_equivalent_minor=15000,
        next_renewal_date="2026-11-20",
        confidence=0.99,
        explanation="Infra monitoring agent",
        last_charge_date="2026-10-20",
    )
    db_session.add(sub)
    db_session.commit()

    tx = Transaction(
        id="tx_1",
        connection_id=conn.id,
        subscription_id=sub.id,
        account_name="SVB Operating",
        date="2026-10-20",
        description_raw="DATADOG *PROD MONITOR",
        amount_minor=-15000,
        currency="USD",
        status="posted",
        is_recurring_candidate=True,
        provider_connection_id="p_conn_1",
        provider_transaction_id="p_tx_1",
    )
    db_session.add(tx)

    evidence = BillingEvidence(
        id="ev_1",
        subscription_id=sub.id,
        connection_id=conn.id,
        sender_domain="datadoghq.com",
        subject="Your Datadog monthly receipt",
        received_at="2026-10-20T01:00:00Z",
        confidence=0.98,
    )
    db_session.add(evidence)

    finding = Finding(
        id="fnd_1",
        subscription_id=sub.id,
        subscription_name=sub.name,
        type="price_increase",
        severity="medium",
        status="open",
        title="Datadog spend jumped 20%",
        explanation="Billed $150 vs prior $125",
        potential_savings_minor=2500,
        currency="USD",
        created_at="2026-10-20T02:00:00Z",
    )
    db_session.add(finding)
    db_session.commit()

    action = Action(
        id="act_1",
        finding_id=finding.id,
        decision="confirmed_waste",
        note="Host overprovisioning confirmed",
        created_at="2026-10-20T03:00:00Z",
    )
    db_session.add(action)
    db_session.commit()

    # Query relationships
    loaded_user = db_session.scalar(select(User).where(User.id == "usr_1"))
    assert loaded_user is not None
    assert len(loaded_user.connections) == 1
    assert len(loaded_user.subscriptions) == 1
    assert len(loaded_user.subscriptions[0].findings) == 1
    assert len(loaded_user.subscriptions[0].findings[0].actions) == 1
    assert loaded_user.subscriptions[0].findings[0].actions[0].decision == "confirmed_waste"


def test_unique_constraint_on_transactions(db_session):
    conn = Connection(
        id="conn_dup_test",
        name="Test Bank",
        type="bank",
        provider="plaid",
        status="connected",
    )
    db_session.add(conn)
    db_session.commit()

    tx1 = Transaction(
        id="tx_orig",
        connection_id=conn.id,
        account_name="Checking",
        date="2026-10-20",
        description_raw="SAAS *FEE",
        amount_minor=-2000,
        status="posted",
        is_recurring_candidate=True,
        provider_connection_id="prov_c1",
        provider_transaction_id="prov_t1",
    )
    db_session.add(tx1)
    db_session.commit()

    # Duplicate transaction with identical provider connection + tx id must fail
    tx2 = Transaction(
        id="tx_dup",
        connection_id=conn.id,
        account_name="Checking",
        date="2026-10-20",
        description_raw="SAAS *FEE",
        amount_minor=-2000,
        status="posted",
        is_recurring_candidate=True,
        provider_connection_id="prov_c1",
        provider_transaction_id="prov_t1",
    )
    db_session.add(tx2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_user_and_connections(db_session):
    user = User(
        id="usr_cascade",
        email="delete_me@startup.io",
        password_hash="hash",
        created_at="2026-10-20T00:00:00Z",
    )
    db_session.add(user)
    db_session.commit()

    conn = Connection(
        id="conn_cascade",
        user_id=user.id,
        name="Bank",
        type="bank",
        provider="plaid",
        status="connected",
    )
    sub = Subscription(
        id="sub_cascade",
        user_id=user.id,
        name="Service",
        category="DevOps",
        billing_interval="monthly",
        amount_minor=5000,
        monthly_equivalent_minor=5000,
        next_renewal_date="2026-11-20",
        confidence=1.0,
        explanation="Cascade test",
        last_charge_date="2026-10-20",
    )
    db_session.add_all([conn, sub])
    db_session.commit()

    finding = Finding(
        id="fnd_cascade",
        subscription_id=sub.id,
        subscription_name=sub.name,
        type="forgotten_charge",
        severity="high",
        title="Unused service",
        explanation="No active logons",
        potential_savings_minor=5000,
        created_at="2026-10-20T01:00:00Z",
    )
    db_session.add(finding)
    db_session.commit()

    # Deleting user must cascade and delete connections, subscriptions, and findings
    db_session.delete(user)
    db_session.commit()

    assert db_session.scalar(select(Connection).where(Connection.id == "conn_cascade")) is None
    assert db_session.scalar(select(Subscription).where(Subscription.id == "sub_cascade")) is None
    assert db_session.scalar(select(Finding).where(Finding.id == "fnd_cascade")) is None
