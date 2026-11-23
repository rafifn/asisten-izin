import pytest
from fastapi.testclient import TestClient


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_unknown_route_uses_error_shape(client: TestClient) -> None:
    r = client.get("/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_cors_origins_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import Settings, parse_origins

    assert parse_origins(None) == ("http://localhost:3000",)
    assert parse_origins(" ") == ("http://localhost:3000",)
    assert parse_origins("https://a.example, https://b.example") == (
        "https://a.example",
        "https://b.example",
    )
    monkeypatch.setenv("CORS_ORIGINS", "https://staging.example")
    assert Settings.from_env().cors_origins == ("https://staging.example",)


def test_cors_header_uses_configured_origin() -> None:
    from app.config import Settings
    from app.main import create_app

    app = create_app(Settings(cors_origins=("https://staging.example",)))
    c = TestClient(app)
    r = c.get("/healthz", headers={"Origin": "https://staging.example"})
    assert r.headers.get("access-control-allow-origin") == "https://staging.example"
    r = c.get("/healthz", headers={"Origin": "http://localhost:3000"})
    assert "access-control-allow-origin" not in r.headers
