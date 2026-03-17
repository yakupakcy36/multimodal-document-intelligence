"""Unit tests for structured document parser & checksum reconciliation."""

from src.generator import generate_synthetic_spec_document
from src.parser import EngineeringDocumentParser


def test_parser_extraction_and_checksum():
    tokens, truth = generate_synthetic_spec_document(seed=123)
    parser = EngineeringDocumentParser()
    res = parser.parse_document(tokens)

    assert res.po_number == truth["po_number"]
    assert res.document_date == truth["date"]
    assert res.checksum_passed is True
    assert len(res.line_items) == len(truth["items"])

    for item in res.line_items:
        assert item.arithmetic_valid is True
        assert item.qty > 0
        assert item.unit_price > 0
        assert item.total_price > 0
