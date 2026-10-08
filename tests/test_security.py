import asyncio
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

from app.app import health_check
from app.core.config import Settings, settings
from app.core.exceptions import AppException
from app.core.security import create_access_token, get_current_user


def session_for(user):
    return SimpleNamespace(
        execute=AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=user)))
    )


def authenticate(token, session):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return asyncio.run(get_current_user(credentials, session))


def test_valid_token_authenticates_active_user():
    user = SimpleNamespace(id="test-user", is_active=True)
    session = session_for(user)
    assert authenticate(create_access_token(user.id), session) is user
    session.execute.assert_awaited_once()


@pytest.mark.parametrize(
    "case",
    [
        "expired",
        "wrong_signature",
        "malformed",
        "missing_exp",
        "missing_sub",
        "wrong_algorithm",
        "invalid_exp",
    ],
)
def test_invalid_tokens_are_rejected_before_database_access(case):
    payload = {
        "sub": "test-user",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    key = settings.AUTH_SECRET_KEY
    algorithm = "HS256"
    if case == "expired":
        payload["exp"] = datetime.now(timezone.utc) - timedelta(minutes=5)
    elif case == "missing_exp":
        del payload["exp"]
    elif case == "missing_sub":
        del payload["sub"]
    elif case == "wrong_signature":
        key = "different-test-only-signing-key-for-ci"
    elif case == "wrong_algorithm":
        algorithm = "HS384"
        key = "different-test-only-signing-key-for-ci-with-48-bytes"
    elif case == "invalid_exp":
        payload["exp"] = []
    token = (
        "invalid.token"
        if case == "malformed"
        else jwt.encode(payload, key, algorithm=algorithm)
    )
    session = session_for(None)
    with pytest.raises(AppException) as exc:
        authenticate(token, session)
    assert exc.value.status_code == 401
    session.execute.assert_not_awaited()


@pytest.mark.parametrize(
    "user", [None, SimpleNamespace(id="test-user", is_active=False)]
)
def test_missing_or_inactive_user_is_rejected(user):
    with pytest.raises(AppException) as exc:
        authenticate(create_access_token("test-user"), session_for(user))
    assert exc.value.status_code == 401


@pytest.mark.parametrize(
    "secret",
    [
        "tiny-key",
        "change-this-development-secret-key",
        "replace-with-a-random-32-byte-or-longer-secret",
    ],
)
def test_weak_or_placeholder_configuration_is_rejected(secret):
    with pytest.raises(ValidationError) as exc:
        Settings(AUTH_SECRET_KEY=secret, _env_file=None)
    assert secret not in str(exc.value)


def test_secret_is_required(monkeypatch):
    monkeypatch.delenv("AUTH_SECRET_KEY")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_algorithm_configuration_cannot_mix_key_families():
    with pytest.raises(ValidationError):
        Settings(AUTH_ALGORITHM="RS256", _env_file=None)


def test_health_response_hides_database_exception(monkeypatch):
    monkeypatch.setattr(
        "app.app.engine",
        SimpleNamespace(
            connect=Mock(side_effect=RuntimeError("private-database-error-marker"))
        ),
    )
    response = asyncio.run(health_check())
    assert response.status_code == 503
    assert json.loads(response.body)["errors"]["database"] == "Database unavailable"
    assert b"private-database-error-marker" not in response.body
