from unittest.mock import MagicMock

import pytest

from auth.domain import LoginInput
from auth.hashing import hash_password
from auth.service import AuthService
from common.errors import AuthError


class TestAuthServiceLogin:
    def test_login_success(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.password_hash = hash_password("pass123")
        mock_user.is_active = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(mock_db)
        result = service.login(LoginInput(email="test@example.com", password="pass123"))

        assert result.user.email == "test@example.com"
        assert result.user.display_name == "Test User"
        assert result.token is not None

    def test_login_wrong_password(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.password_hash = hash_password("correct")
        mock_user.is_active = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(mock_db)
        with pytest.raises(AuthError, match="Invalid email or password"):
            service.login(LoginInput(email="test@example.com", password="wrong"))

    def test_login_user_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AuthService(mock_db)
        with pytest.raises(AuthError, match="Invalid email or password"):
            service.login(LoginInput(email="nobody@example.com", password="pass"))

    def test_login_inactive_user(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.password_hash = hash_password("pass123")
        mock_user.is_active = False

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(mock_db)
        with pytest.raises(AuthError, match="Account is inactive"):
            service.login(LoginInput(email="test@example.com", password="pass123"))


class TestAuthServiceValidateSession:
    def test_validate_valid_token(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.password_hash = hash_password("pass123")
        mock_user.is_active = True

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        service = AuthService(mock_db)
        login_result = service.login(LoginInput(email="test@example.com", password="pass123"))

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        session = service.validate_session(login_result.token)

        assert session.authenticated is True
        assert session.user.email == "test@example.com"

    def test_validate_invalid_token(self):
        mock_db = MagicMock()
        service = AuthService(mock_db)
        session = service.validate_session("garbage-token")

        assert session.authenticated is False
        assert session.user is None

    def test_validate_token_inactive_user(self):
        mock_db = MagicMock()
        active_user = MagicMock()
        active_user.id = "u1"
        active_user.email = "test@example.com"
        active_user.display_name = "Test User"
        active_user.password_hash = hash_password("pass123")
        active_user.is_active = True

        inactive_user = MagicMock()
        inactive_user.id = "u1"
        inactive_user.is_active = False

        mock_db.query.return_value.filter.return_value.first.return_value = active_user
        service = AuthService(mock_db)
        login_result = service.login(LoginInput(email="test@example.com", password="pass123"))

        mock_db.query.return_value.filter.return_value.first.return_value = inactive_user
        session = service.validate_session(login_result.token)

        assert session.authenticated is False


class TestCreateTokenImpersonation:
    """Cover _create_token impersonation branch (lines 37-39)."""

    def test_create_token_with_impersonation(self):
        from auth.service import _create_token

        token, expires = _create_token(
            user_id="admin-1",
            tenant_id="tenant-1",
            impersonated=True,
            admin_id="admin-1",
            impersonation_session_id="sess-1",
        )
        assert token is not None
        assert expires is not None


class TestLogout:
    """Cover logout no-op (line 159)."""

    def test_logout_does_nothing(self):
        from unittest.mock import MagicMock

        from auth.service import AuthService

        service = AuthService(MagicMock())
        # Should not raise
        service.logout("some-token")


class TestValidateSessionTenantError:
    """Cover auth/service.py lines 138-139: AuthError clears tenant_id."""

    def test_validate_token_with_invalid_tenant_returns_none_tenant_id(self):
        from unittest.mock import MagicMock, patch

        from auth.domain import LoginInput
        from auth.hashing import hash_password
        from auth.service import AuthService
        from common.errors import AuthError

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.email = "test@example.com"
        mock_user.display_name = "Test User"
        mock_user.password_hash = hash_password("pass123")
        mock_user.is_active = True

        # Set up memberships.mock_tenant_membership and mock_tenant for get_user_tenants
        mock_membership = MagicMock()
        mock_membership.tenant_id = "tenant-1"
        mock_membership.role = "admin"

        mock_tenant = MagicMock()
        mock_tenant.id = "tenant-1"
        mock_tenant.name = "Test Tenant"

        # login: first query is find_by_email via filter().first()
        # then get_user_tenants uses filter().all() for memberships
        # and filter().order_by().all() for tenants
        filter_mock = mock_db.query.return_value.filter.return_value
        filter_mock.first.return_value = mock_user
        filter_mock.all.return_value = [mock_membership]
        filter_mock.order_by.return_value.all.return_value = [mock_tenant]

        service = AuthService(mock_db)
        login_result = service.login(LoginInput(email="test@example.com", password="pass123"))

        # Reset for validate_session: user found but tenant validation fails
        filter_mock.first.return_value = mock_user
        filter_mock.all.return_value = [mock_membership]
        filter_mock.order_by.return_value.all.return_value = [mock_tenant]

        with patch("auth.service.MembershipValidator") as mock_validator_cls:
            mock_validator = MagicMock()
            mock_validator_cls.return_value = mock_validator
            mock_validator.validate_membership.side_effect = AuthError("No membership")

            session = service.validate_session(login_result.token)

            assert session.authenticated is True
            assert session.tenant_id is None
            assert session.tenant_role is None
