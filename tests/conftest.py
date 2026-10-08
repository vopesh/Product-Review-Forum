import os

# Public fixtures only; no live services or production credentials are used.
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/test_db")
os.environ.setdefault("IMAGEKIT_PUBLIC_KEY", "dummy_public_key")
os.environ.setdefault("IMAGEKIT_PRIVATE_KEY", "dummy_private_key")
os.environ.setdefault("IMAGEKIT_URL_ENDPOINT", "https://ik.imagekit.io/dummy")
os.environ.setdefault("AUTH_SECRET_KEY", "test-only-signing-key-for-ci-do-not-use")
