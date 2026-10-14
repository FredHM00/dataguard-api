"""Observabilidade: request-id, access log sem segredos e metricas (Etapa 12)."""

import json
import logging
import re

PREFIX = "/api/v1"


def _auth(client, email):
    client.post(f"{PREFIX}/auth/register", json={"email": email, "password": "segredo-123"})
    token = client.post(
        f"{PREFIX}/auth/login", data={"username": email, "password": "segredo-123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_request_id_is_generated_and_unique(client):
    first = client.get("/health")
    second = client.get("/health")
    assert re.fullmatch(r"[0-9a-f]{32}", first.headers["X-Request-ID"])
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


def test_request_id_from_client_is_echoed(client):
    response = client.get("/health", headers={"X-Request-ID": "trilha-123"})
    assert response.headers["X-Request-ID"] == "trilha-123"


def test_access_log_hides_query_and_secrets(client, caplog):
    logger = logging.getLogger("dataguard.access")
    old_propagate, logger.propagate = logger.propagate, True
    try:
        with caplog.at_level(logging.INFO, logger="dataguard.access"):
            client.get("/health?token=segredo-na-url")
            client.post(
                f"{PREFIX}/auth/login",
                data={"username": "ninguem@example.com", "password": "segredo-123"},
            )
    finally:
        logger.propagate = old_propagate
    lines = [record for record in caplog.records if record.name == "dataguard.access"]
    assert lines, "esperava linhas de access log"
    blob_parts = []
    for record in lines:
        data = {k: v for k, v in record.__dict__.items() if not k.startswith("_")}
        blob_parts.append(json.dumps(data, default=str))
    blob = " ".join(blob_parts)
    assert "segredo-na-url" not in blob
    assert "segredo-123" not in blob
    assert "?token=" not in blob
    health = next(record for record in lines if record.path == "/health")
    assert health.method == "GET"
    assert health.status == 200
    assert health.duration_ms >= 0


def test_metrics_counts_requests(client):
    before = client.get("/metrics").text
    client.get("/health")
    after = client.get("/metrics").text
    assert "dataguard_http_requests_total" in after
    assert "dataguard_http_errors_total" in after

    def total(text):
        match = re.search(r'\{route="/health",method="GET",status="200"\} (\d+)', text)
        return int(match.group(1)) if match else 0

    assert total(after) >= total(before) + 1
