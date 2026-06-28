import os
import socket
from pathlib import Path

import uvicorn


HOST = "127.0.0.1"
LOCAL_API_URL_FILE = Path(".local_api_url")


def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((HOST, port))
        except OSError:
            return False
        return True


def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    raise RuntimeError(
        f"No free port found from {start_port} to {start_port + max_attempts - 1}"
    )


def write_local_api_url(port: int) -> None:
    LOCAL_API_URL_FILE.write_text(f"http://localhost:{port}\n", encoding="utf-8")


if __name__ == "__main__":
    requested_port = os.getenv("PORT")
    port = int(requested_port) if requested_port else find_available_port(8000)
    write_local_api_url(port)
    print(f"FastAPI backend running at http://localhost:{port}")
    uvicorn.run("app.app:app", host=HOST, port=port, reload=True)
