import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import ReviewInput, SubscriptionPatch
from app.store.database_store import DatabaseStore
from app.store.db_models import UserDB, SubscriptionDB


def test_custom_database_store_initialization():
    """Verify that DatabaseStore initializes, creates tables, and auto-seeds on a fresh DB."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        custom_store = DatabaseStore(engine=engine, session_factory=session_factory)

        # Should be auto-seeded
        subs = custom_store.list_subscriptions()
        assert len(subs) > 0

        user = custom_store.get_user_by_id("usr_1")
        assert user is not None
        assert user.email == "alex@studio.dev"

        # Check DB directly via raw SQLAlchemy
        with custom_store.get_session() as s:
            user_count = s.query(UserDB).count()
            sub_count = s.query(SubscriptionDB).count()
            assert user_count >= 1
            assert sub_count >= 1

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass


def test_database_persistence_across_store_instances():
    """Verify data persisted by one store instance is read by a second store instance pointing to same DB."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine1 = create_engine(db_url, connect_args={"check_same_thread": False})
        store1 = DatabaseStore(engine=engine1)

        # Mutate subscription in store1
        patch = SubscriptionPatch(displayName="Updated Figma Pro", note="Team approved")
        updated = store1.update_subscription("sub_figma", patch)
        assert updated.displayName == "Updated Figma Pro"
        assert updated.note == "Team approved"

        engine1.dispose()

        # Connect with a fresh engine/store instance on the same DB file
        engine2 = create_engine(db_url, connect_args={"check_same_thread": False})
        store2 = DatabaseStore(engine=engine2)

        detail = store2.get_subscription_detail("sub_figma")
        assert detail is not None
        assert detail.displayName == "Updated Figma Pro"
        assert detail.note == "Team approved"

        engine2.dispose()
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass


def test_finding_review_persistence():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        store = DatabaseStore(engine=engine)

        # Review a finding
        rev_input = ReviewInput(
            decision="confirm",
            note="Canceling duplicate license",
        )
        detail = store.review_finding("fnd_dup", rev_input)
        assert detail is not None
        assert detail.status == "confirmed"
        assert len(detail.reviews) == 1
        assert detail.reviews[0].decision == "confirm"
        assert detail.reviews[0].note == "Canceling duplicate license"

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
