"""Unit tests for spatial layout line clustering."""

from src.generator import generate_synthetic_spec_document
from src.spatial_layout import SpatialLayoutEngine


def test_spatial_layout_line_clustering():
    tokens, _ = generate_synthetic_spec_document(seed=42)
    engine = SpatialLayoutEngine()
    lines = engine.cluster_into_lines(tokens)

    assert len(lines) >= 8
    # Top-to-bottom monotonicity check
    for i in range(len(lines) - 1):
        assert lines[i].bbox[1] <= lines[i + 1].bbox[1]

    # First line should be header vendor name
    assert "SIEMENS" in lines[0].text
