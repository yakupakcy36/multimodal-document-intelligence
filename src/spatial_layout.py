"""2D spatial layout analysis, line clustering, and reading order reconstruction."""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import numpy as np
from src.config import DocumentConfig, DEFAULT_DOC_CONFIG
from src.generator import OcrToken


@dataclass
class TextLine:
    line_id: int
    text: str
    tokens: List[OcrToken]
    bbox: Tuple[int, int, int, int]  # (x0, y0, x1, y1)
    mean_confidence: float


class SpatialLayoutEngine:
    """Reconstructs 2D reading order and tabular coordinate lines from unordered OCR tokens."""

    def __init__(self, config: DocumentConfig = DEFAULT_DOC_CONFIG):
        self.config = config

    def cluster_into_lines(self, tokens: List[OcrToken]) -> List[TextLine]:
        """
        Sorts tokens vertically, clusters into visual lines based on vertical overlap tolerance,
        and sorts tokens horizontally within each line to reconstruct natural reading order.
        """
        if not tokens:
            return []

        # Sort primarily by vertical top coordinate
        sorted_by_y = sorted(tokens, key=lambda t: (t.y0, t.x0))

        clusters: List[List[OcrToken]] = []
        for token in sorted_by_y:
            placed = False
            token_mid_y = (token.y0 + token.y1) / 2.0

            for cluster in clusters:
                # Compare against cluster vertical centroid
                cluster_mid_y = np.mean([(t.y0 + t.y1) / 2.0 for t in cluster])
                if abs(token_mid_y - cluster_mid_y) <= self.config.y_line_tolerance_px:
                    cluster.append(token)
                    placed = True
                    break

            if not placed:
                clusters.append([token])

        # Sort clusters from top to bottom
        clusters.sort(key=lambda cl: np.mean([t.y0 for t in cl]))

        lines: List[TextLine] = []
        for idx, cluster in enumerate(clusters, start=1):
            # Sort tokens in the line left to right
            cluster_sorted_x = sorted(cluster, key=lambda t: t.x0)
            line_text = " ".join([t.text for t in cluster_sorted_x])

            x0 = min(t.x0 for t in cluster_sorted_x)
            y0 = min(t.y0 for t in cluster_sorted_x)
            x1 = max(t.x1 for t in cluster_sorted_x)
            y1 = max(t.y1 for t in cluster_sorted_x)
            conf = float(np.mean([t.confidence for t in cluster_sorted_x]))

            lines.append(
                TextLine(
                    line_id=idx,
                    text=line_text,
                    tokens=cluster_sorted_x,
                    bbox=(x0, y0, x1, y1),
                    mean_confidence=round(conf, 3),
                )
            )

        return lines
