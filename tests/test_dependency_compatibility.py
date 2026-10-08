import io
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import anyio
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from git import Repo
from PIL import Image

import jwt


def test_requests_urllib3_local_http_roundtrip():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"dependency-check")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with requests.Session() as session:
            session.trust_env = False
            response = session.get(f"http://127.0.0.1:{server.server_port}", timeout=5)
            assert response.status_code == 200
            assert response.content == b"dependency-check"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_pillow_image_roundtrip():
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format="PNG")
    buffer.seek(0)
    with Image.open(buffer) as image:
        image.load()
        assert image.size == (8, 8)
        assert image.getpixel((0, 0)) == (255, 0, 0)


def test_gitpython_local_repository(tmp_path):
    with Repo.init(tmp_path) as repo:
        (tmp_path / "sample.txt").write_text("sample\n")
        repo.index.add(["sample.txt"])
        repo.index.commit("Compatibility fixture")
        assert repo.head.commit.message == "Compatibility fixture"
        assert not repo.is_dirty()


def test_anyio_task_group():
    values = []

    async def worker():
        await anyio.sleep(0)
        values.append("done")

    async def run():
        async with anyio.create_task_group() as group:
            group.start_soon(worker)

    anyio.run(run)
    assert values == ["done"]


def test_cryptography_pyjwt_rsa_roundtrip():
    # Generated ephemeral key, never stored or logged. Library-level test only:
    # the application deliberately uses HS256, not RSA.
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    token = jwt.encode({"sub": "test-user"}, key, algorithm="RS256")
    assert jwt.decode(token, public, algorithms=["RS256"])["sub"] == "test-user"
