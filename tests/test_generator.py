"""Unit tests for synthetic document & OCR token generator."""

from src.generator import generate_synthetic_spec_document, OcrToken


def test_synthetic_document_generator():
    tokens, truth = generate_synthetic_spec_document(seed=42)
    assert len(tokens) > 30
    assert "PO-2026-ENG" in truth["po_number"]
    assert truth["subtotal"] > 0.0
    assert truth["grand_total"] > truth["subtotal"]
    assert len(truth["items"]) >= 4

    for t in tokens:
        assert isinstance(t, OcrToken)
        assert 0 <= t.x0 < t.x1 <= 1000
        assert 0 <= t.y0 < t.y1 <= 1000
        assert 0.0 <= t.confidence <= 1.0
