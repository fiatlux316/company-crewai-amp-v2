from __future__ import annotations

from pathlib import Path
import httpx


def deploy_package(
    artifact: str | Path,
    *,
    server_url: str,
    token: str | None = None,
    timeout_seconds: float = 60.0,
) -> dict:
    path = Path(artifact).resolve()
    if path.suffix != ".crewpkg":
        raise ValueError("artifact must use .crewpkg extension")
    headers = {
        "Content-Type": "application/octet-stream",
        "X-Crew-Filename": path.name,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = server_url.rstrip("/") + "/api/v1/crews/deploy"
    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.post(url, content=path.read_bytes(), headers=headers)
        response.raise_for_status()
        return response.json()
