"""Realistic synthetic engineering document and OCR token generator."""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import numpy as np


@dataclass
class OcrToken:
    text: str
    x0: int
    y0: int
    x1: int
    y1: int
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "bbox": [self.x0, self.y0, self.x1, self.y1],
            "confidence": round(self.confidence, 3),
        }


SAMPLE_PARTS = [
    ("6ES7512-1DK01-0AB0", "CPU 1512C-1 PN Compact Controller", 4, 1250.00),
    ("6GK5208-0BA00-2AC2", "SCALANCE X208 Managed Industrial Switch", 6, 420.50),
    ("6SL3210-1PE21-8AL0", "SINAMICS G120 Variable Frequency Drive 7.5kW", 2, 1840.00),
    ("3RT2026-1BB40", "SIRIUS Power Contactor 25A 24VDC", 12, 65.20),
    ("6EP1334-3BA10", "SITOP Modular 24V/10A Power Supply", 5, 215.00),
    ("3SU1100-0AB20-1CA0", "Pushbutton Actuator Red 22mm Momentary", 20, 18.50),
    ("7ML5033-1AA00-1A", "SITRANS Ultrasonic Liquid Level Transmitter", 3, 980.00),
]


def generate_synthetic_spec_document(seed: int = 42) -> Tuple[List[OcrToken], Dict[str, Any]]:
    """
    Synthesizes a realistic industrial Purchase Order / Bill of Materials spec sheet
    with 2D spatial coordinate tokens, table grid, and ground truth metadata.
    """
    np.random.seed(seed)
    tokens: List[OcrToken] = []

    # 1. Document Header Block (y: 60 - 180)
    tokens.append(OcrToken("SIEMENS", 80, 70, 210, 95, 0.99))
    tokens.append(OcrToken("INDUSTRIAL", 225, 70, 390, 95, 0.98))
    tokens.append(OcrToken("AUTOMATION", 405, 70, 580, 95, 0.99))

    tokens.append(OcrToken("PURCHASE", 80, 115, 185, 132, 0.97))
    tokens.append(OcrToken("ORDER", 195, 115, 260, 132, 0.98))
    po_num = f"PO-2026-ENG-{np.random.randint(1000, 9999)}"
    tokens.append(OcrToken("NO:", 275, 115, 305, 132, 0.95))
    tokens.append(OcrToken(po_num, 320, 115, 510, 132, 0.99))

    tokens.append(OcrToken("DATE:", 720, 115, 775, 132, 0.98))
    tokens.append(OcrToken("2026-03-14", 785, 115, 895, 132, 0.99))

    # 2. Table Column Headers (y: 220 - 245)
    headers = [
        ("ITEM", 80, 120),
        ("PART_NUMBER", 150, 310),
        ("DESCRIPTION", 330, 620),
        ("QTY", 640, 685),
        ("UNIT_PRICE", 710, 800),
        ("TOTAL", 830, 910),
    ]
    for name, x0, x1 in headers:
        tokens.append(OcrToken(name, x0, 225, x1, 245, 0.98))

    # 3. Table Rows (y: 270 - 620)
    n_rows = np.random.randint(4, 7)
    selected_indices = np.random.choice(len(SAMPLE_PARTS), size=n_rows, replace=False)

    y_cursor = 275
    line_items_truth = []
    subtotal = 0.0

    for idx, sample_idx in enumerate(selected_indices, start=1):
        part_no, desc, default_qty, default_price = SAMPLE_PARTS[sample_idx]
        qty = int(np.random.randint(1, 10))
        price = float(default_price)
        row_total = round(qty * price, 2)
        subtotal += row_total

        y0 = y_cursor
        y1 = y_cursor + 20

        tokens.append(OcrToken(str(idx), 85, y0, 110, y1, 0.99))
        tokens.append(OcrToken(part_no, 150, y0, 315, y1, 0.97))

        # Split description into individual words for realistic OCR tokenization
        desc_words = desc.split()
        x_desc = 330
        for w in desc_words:
            w_len = len(w) * 6 + 3
            tokens.append(OcrToken(w, x_desc, y0, x_desc + w_len, y1, 0.95))
            x_desc += w_len + 5

        tokens.append(OcrToken(str(qty), 655, y0, 680, y1, 0.99))
        tokens.append(OcrToken(f"{price:.2f}", 720, y0, 785, y1, 0.98))
        tokens.append(OcrToken(f"{row_total:.2f}", 835, y0, 905, y1, 0.98))

        line_items_truth.append(
            {
                "item_index": idx,
                "part_number": part_no,
                "description": desc,
                "qty": qty,
                "unit_price": price,
                "total_price": row_total,
            }
        )
        y_cursor += 36

    # 4. Table Financial Footer Block (y: 720 - 820)
    subtotal = round(subtotal, 2)
    tax_rate = 0.20
    tax_amount = round(subtotal * tax_rate, 2)
    grand_total = round(subtotal + tax_amount, 2)

    # Subtotal
    tokens.append(OcrToken("SUBTOTAL:", 680, 720, 785, 738, 0.98))
    tokens.append(OcrToken(f"{subtotal:.2f}", 820, 720, 910, 738, 0.99))

    # VAT (20%)
    tokens.append(OcrToken("VAT", 705, 755, 740, 773, 0.97))
    tokens.append(OcrToken("(20%):", 745, 755, 785, 773, 0.96))
    tokens.append(OcrToken(f"{tax_amount:.2f}", 820, 755, 910, 773, 0.99))

    # Grand Total
    tokens.append(OcrToken("GRAND", 680, 795, 735, 815, 0.99))
    tokens.append(OcrToken("TOTAL:", 740, 795, 795, 815, 0.99))
    tokens.append(OcrToken(f"{grand_total:.2f}", 815, 795, 915, 815, 0.99))

    ground_truth = {
        "po_number": po_num,
        "date": "2026-03-14",
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "grand_total": grand_total,
        "items": line_items_truth,
    }

    # Simulate realistic OCR token shuffle (OCR engines return tokens unordered)
    np.random.shuffle(tokens)

    return tokens, ground_truth
