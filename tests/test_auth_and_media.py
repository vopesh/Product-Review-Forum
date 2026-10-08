import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import jwt
import pytest
from fastapi.security import OAuth2PasswordRequestForm

from app.api.routes.authRoutes import login_user
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.imagekit import upload_media
from app.core.security import hash_password


@pytest.mark.parametrize(
    "password,active,status",
    [
        ("correct-test-password", True, None),
        ("incorrect-test-password", True, 401),
        ("correct-test-password", False, 403),
    ],
)
def test_login_password_and_account_status(password, active, status):
    user = SimpleNamespace(
        id="test-user",
        is_active=active,
        hashed_password=hash_password("correct-test-password"),
    )
    session = SimpleNamespace(
        execute=AsyncMock(return_value=Mock(scalar_one_or_none=Mock(return_value=user)))
    )
    form = OAuth2PasswordRequestForm(username="test@example.com", password=password)
    if status:
        with pytest.raises(AppException) as exc:
            asyncio.run(login_user(form, session))
        assert exc.value.status_code == status
    else:
        token = asyncio.run(login_user(form, session))
        payload = jwt.decode(
            token.access_token,
            settings.AUTH_SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        assert payload["sub"] == user.id


def test_imagekit_adapter_maps_upload_response_without_network(monkeypatch):
    upload = Mock(
        return_value=SimpleNamespace(
            url="https://example.com/fixture.png",
            file_id="fixture-id",
            name="fixture.png",
        )
    )
    monkeypatch.setattr(
        "app.core.imagekit.imagekit",
        SimpleNamespace(files=SimpleNamespace(upload=upload)),
    )
    result = upload_media(content=b"fixture", filename="fixture.png")
    assert result.file_id == "fixture-id"
    assert result.url == "https://example.com/fixture.png"
    upload.assert_called_once_with(
        file=b"fixture",
        file_name="fixture.png",
        folder="/post_uploads/",
        use_unique_file_name=True,
    )
