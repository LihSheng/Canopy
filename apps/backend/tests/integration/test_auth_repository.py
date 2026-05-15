from auth.hashing import hash_password
from auth.repository import AuthRepository


class TestAuthRepository:
    def test_create_and_find_by_email(self, db_session):
        repo = AuthRepository(db_session)
        user = repo.create(
            email="test@example.com",
            password_hash=hash_password("secret123"),
            display_name="Test User",
        )
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True

        found = repo.find_by_email("test@example.com")
        assert found is not None
        assert found.id == user.id

    def test_find_by_email_returns_none(self, db_session):
        repo = AuthRepository(db_session)
        assert repo.find_by_email("nonexistent@example.com") is None

    def test_find_by_id(self, db_session, seed_user):
        repo = AuthRepository(db_session)
        found = repo.find_by_id("test-user-1")
        assert found is not None
        assert found.email == "admin@herd.example"

    def test_find_by_id_returns_none(self, db_session):
        repo = AuthRepository(db_session)
        assert repo.find_by_id("nonexistent-id") is None

    def test_update_login_timestamp(self, db_session, seed_user):
        repo = AuthRepository(db_session)
        user = repo.find_by_id("test-user-1")
        assert user is not None
        assert user.last_login_at is None

        repo.update_login_timestamp(user)
        assert user.last_login_at is not None

    def test_email_is_unique(self, db_session):
        repo = AuthRepository(db_session)
        repo.create(
            email="unique@example.com",
            password_hash="hash1",
            display_name="User 1",
        )
        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            repo.create(
                email="unique@example.com",
                password_hash="hash2",
                display_name="User 2",
            )
