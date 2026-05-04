from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import supabase_client as supabase_module
from app.services.supabase_client import SupabaseNotConfigured


@pytest.fixture
def mock_supabase(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace `supabase_client.client()` with one that returns a MagicMock."""
    fake = MagicMock()
    fake.auth.sign_up = AsyncMock()
    fake.auth.sign_in_with_password = AsyncMock()
    fake.auth.sign_out = AsyncMock()
    monkeypatch.setattr(
        supabase_module.supabase_client,
        "client",
        AsyncMock(return_value=fake),
    )
    return fake


def test_signup_returns_user_and_token(client, mock_supabase: MagicMock) -> None:
    mock_supabase.auth.sign_up.return_value = SimpleNamespace(
        user=SimpleNamespace(id="u-1", email="a@b.com"),
        session=SimpleNamespace(access_token="tok-1"),
    )
    resp = client.post(
        "/auth/signup", json={"email": "a@b.com", "password": "secret123"}
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "user_id": "u-1",
        "email": "a@b.com",
        "access_token": "tok-1",
    }


def test_login_returns_session_tokens(client, mock_supabase: MagicMock) -> None:
    mock_supabase.auth.sign_in_with_password.return_value = SimpleNamespace(
        user=SimpleNamespace(id="u-1"),
        session=SimpleNamespace(access_token="tok", refresh_token="rfr"),
    )
    resp = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "secret123"}
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "user_id": "u-1",
        "access_token": "tok",
        "refresh_token": "rfr",
    }


def test_login_with_bad_credentials_returns_401(
    client, mock_supabase: MagicMock
) -> None:
    mock_supabase.auth.sign_in_with_password.return_value = SimpleNamespace(
        user=None, session=None
    )
    resp = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_logout_succeeds(client, mock_supabase: MagicMock) -> None:
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_503_when_supabase_not_configured(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        supabase_module.supabase_client,
        "client",
        AsyncMock(side_effect=SupabaseNotConfigured("missing creds")),
    )
    resp = client.post(
        "/auth/login", json={"email": "a@b.com", "password": "x"}
    )
    assert resp.status_code == 503
    assert "missing creds" in resp.json()["detail"]
