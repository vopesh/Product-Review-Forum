from fastapi import FastAPI

from app.app import app


def test_fastapi_app_imports() -> None:
    assert isinstance(app, FastAPI)
