from fastapi.testclient import TestClient


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_unknown_route_uses_error_shape(client: TestClient) -> None:
    r = client.get("/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
