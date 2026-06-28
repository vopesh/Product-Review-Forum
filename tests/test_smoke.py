import os

from fastapi import FastAPI

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test_db")
os.environ.setdefault("IMAGEKIT_PUBLIC_KEY", "dummy_public_key")
os.environ.setdefault("IMAGEKIT_PRIVATE_KEY", "dummy_private_key")
os.environ.setdefault("IMAGEKIT_URL_ENDPOINT", "https://ik.imagekit.io/dummy")

from app.app import app


def test_fastapi_app_imports() -> None:
    assert isinstance(app, FastAPI)
