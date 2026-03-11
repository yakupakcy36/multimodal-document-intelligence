"""Configuration parameters for Multimodal Document Intelligence & 2D Spatial Layout."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentConfig:
    # Coordinate system bounds (standard normalized OCR 0 - 1000 scale)
    coord_max: int = 1000
    y_line_tolerance_px: int = 14  # Vertical threshold for grouping tokens into the same line
    x_word_gap_tolerance_px: int = 24  # Horizontal gap threshold for merging adjacent words

    # Tabular layout recognition
    table_header_iou_threshold: float = 0.35
    min_table_columns: int = 3

    # Storage paths
    artifacts_dir: Path = Path("artifacts")
    benchmark_filename: str = "document_benchmark_summary.json"


DEFAULT_DOC_CONFIG = DocumentConfig()
