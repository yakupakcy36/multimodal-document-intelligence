"""Integration tests for Multimodal Document Intelligence API."""

import pytest
from fastapi.testclient import TestClient
from api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["engine_ready"] is True


def test_parse_synthetic_demo_endpoint(client):
    payload = {"seed": 42}
    response = client.post("/parse/synthetic-demo", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "PO-2026-ENG" in data["po_number"]
    assert data["checksum_passed"] is True
    assert len(data["line_items"]) >= 4
    assert data["grand_total"] > data["subtotal"]


def test_parse_custom_document_endpoint(client):
    payload = {
        "document_id": "CUSTOM-PO-001",
        "tokens": [
            {"text": "PURCHASE", "bbox": [80, 115, 185, 132], "confidence": 0.99},
            {"text": "ORDER", "bbox": [195, 115, 260, 132], "confidence": 0.99},
            {"text": "PO-2026-ENG-9999", "bbox": [320, 115, 510, 132], "confidence": 0.99},
            {"text": "2026-03-15", "bbox": [785, 115, 895, 132], "confidence": 0.99},
        ]
    }
    response = client.post("/parse/document", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["po_number"] == "PO-2026-ENG-9999"
    assert data["document_date"] == "2026-03-15"
