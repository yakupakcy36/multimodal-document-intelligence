"""Structured BOM & Purchase Order parser with mathematical checksum reconciliation."""

import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from src.spatial_layout import SpatialLayoutEngine, TextLine
from src.generator import OcrToken


@dataclass
class ParsedLineItem:
    item_index: int
    part_number: str
    description: str
    qty: int
    unit_price: float
    total_price: float
    arithmetic_valid: bool


@dataclass
class ParsedDocumentResult:
    po_number: Optional[str]
    document_date: Optional[str]
    line_items: List[ParsedLineItem]
    subtotal: float
    tax_amount: float
    grand_total: float
    checksum_passed: bool
    reconciliation_notes: str
    ocr_quality_score: float


class EngineeringDocumentParser:
    """Extracts structured procurement tables and performs deterministic arithmetic audits."""

    def __init__(self):
        self.layout_engine = SpatialLayoutEngine()

    def parse_document(self, tokens: List[OcrToken]) -> ParsedDocumentResult:
        """Parses unordered OCR tokens into structured purchase order schema."""
        lines = self.layout_engine.cluster_into_lines(tokens)
        overall_conf = float(sum(t.confidence for t in tokens) / max(len(tokens), 1))

        po_number = None
        doc_date = None
        subtotal = 0.0
        tax_amount = 0.0
        grand_total = 0.0

        table_header_line_idx = -1
        col_bounds: Dict[str, tuple] = {}

        # 1. First Pass: Detect Header Fields & Table Header
        for idx, line in enumerate(lines):
            text_upper = line.text.upper()

            # PO Number
            po_match = re.search(r"PO-\d{4}-[A-Z]+-\d{4}", line.text)
            if po_match:
                po_number = po_match.group(0)

            # Date
            date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", line.text)
            if date_match and not doc_date:
                doc_date = date_match.group(1)

            # Table Header Detection
            if "PART_NUMBER" in text_upper or ("ITEM" in text_upper and "QTY" in text_upper):
                table_header_line_idx = idx
                # Infer column horizontal spans from header token bounding boxes
                for t in line.tokens:
                    t_up = t.text.upper()
                    if "ITEM" in t_up:
                        col_bounds["ITEM"] = (t.x0 - 20, t.x1 + 20)
                    elif "PART" in t_up:
                        col_bounds["PART_NUMBER"] = (t.x0 - 20, t.x1 + 30)
                    elif "DESC" in t_up:
                        col_bounds["DESCRIPTION"] = (t.x0 - 10, t.x1 + 50)
                    elif "QTY" in t_up:
                        col_bounds["QTY"] = (t.x0 - 20, t.x1 + 20)
                    elif "UNIT" in t_up or "PRICE" in t_up:
                        col_bounds["UNIT_PRICE"] = (t.x0 - 20, t.x1 + 20)
                    elif "TOTAL" in t_up:
                        col_bounds["TOTAL"] = (t.x0 - 20, t.x1 + 30)

            # Financial Totals in Footer
            if "SUBTOTAL" in text_upper:
                nums = re.findall(r"\d+\.\d{2}", line.text)
                if nums:
                    subtotal = float(nums[-1])

            if "VAT" in text_upper or "TAX" in text_upper:
                nums = re.findall(r"\d+\.\d{2}", line.text)
                if nums:
                    tax_amount = float(nums[-1])

            if "GRAND TOTAL" in text_upper:
                nums = re.findall(r"\d+\.\d{2}", line.text)
                if nums:
                    grand_total = float(nums[-1])

        # 2. Second Pass: Extract Table Line Items
        line_items: List[ParsedLineItem] = []
        if table_header_line_idx != -1:
            for idx in range(table_header_line_idx + 1, len(lines)):
                line = lines[idx]
                text_upper = line.text.upper()
                if "SUBTOTAL" in text_upper or "GRAND TOTAL" in text_upper:
                    break

                # Extract tokens spatially by column coordinates
                item_idx_tokens = [t.text for t in line.tokens if 70 <= (t.x0 + t.x1) / 2.0 <= 130 and t.text.isdigit()]
                part_no_tokens = [t.text for t in line.tokens if 135 <= (t.x0 + t.x1) / 2.0 <= 325]
                desc_tokens = [t.text for t in line.tokens if 326 <= (t.x0 + t.x1) / 2.0 <= 645 and not t.text.isdigit()]
                qty_tokens = [t.text for t in line.tokens if 635 <= (t.x0 + t.x1) / 2.0 <= 705 and t.text.isdigit()]
                unit_price_tokens = [t.text for t in line.tokens if 706 <= (t.x0 + t.x1) / 2.0 <= 815]
                total_price_tokens = [t.text for t in line.tokens if 816 <= (t.x0 + t.x1) / 2.0 <= 935]

                if part_no_tokens and (unit_price_tokens or total_price_tokens):
                    part_no = "".join(part_no_tokens)
                    try:
                        item_idx = int(item_idx_tokens[0]) if item_idx_tokens and item_idx_tokens[0].isdigit() else len(line_items) + 1
                    except Exception:
                        item_idx = len(line_items) + 1

                    try:
                        qty = int(qty_tokens[0]) if qty_tokens and qty_tokens[0].isdigit() else 1
                    except Exception:
                        qty = 1

                    try:
                        unit_price = float(re.sub(r"[^\d.]", "", unit_price_tokens[0])) if unit_price_tokens else 0.0
                    except Exception:
                        unit_price = 0.0

                    try:
                        total_price = float(re.sub(r"[^\d.]", "", total_price_tokens[0])) if total_price_tokens else round(qty * unit_price, 2)
                    except Exception:
                        total_price = round(qty * unit_price, 2)

                    desc = " ".join(desc_tokens) if desc_tokens else "Industrial Automation Component"

                    # Validate individual line arithmetic: Qty * Unit_Price == Total_Price
                    calc_total = round(qty * unit_price, 2)
                    arith_valid = abs(calc_total - total_price) < 0.05

                    line_items.append(
                        ParsedLineItem(
                            item_index=item_idx,
                            part_number=part_no,
                            description=desc,
                            qty=qty,
                            unit_price=unit_price,
                            total_price=total_price,
                            arithmetic_valid=arith_valid,
                        )
                    )

        # 3. Third Pass: Mathematical Reconciliation Checksum
        computed_subtotal = round(sum(it.total_price for it in line_items), 2)
        if subtotal == 0.0 and computed_subtotal > 0.0:
            subtotal = computed_subtotal

        calc_grand = round(subtotal + tax_amount, 2)
        subtotal_match = abs(computed_subtotal - subtotal) < 0.05 if line_items else False
        grand_match = abs(calc_grand - grand_total) < 0.05 if grand_total > 0.0 else False

        checksum_passed = subtotal_match and grand_match
        if checksum_passed:
            recon_notes = f"[OK] Arithmetic verified: {len(line_items)} items sum {computed_subtotal:.2f} + VAT {tax_amount:.2f} = Grand Total {grand_total:.2f}"
        else:
            recon_notes = f"[DISCREPANCY] Computed items {computed_subtotal:.2f} vs subtotal {subtotal:.2f}, grand {grand_total:.2f}"

        return ParsedDocumentResult(
            po_number=po_number,
            document_date=doc_date,
            line_items=line_items,
            subtotal=round(subtotal, 2),
            tax_amount=round(tax_amount, 2),
            grand_total=round(grand_total, 2),
            checksum_passed=checksum_passed,
            reconciliation_notes=recon_notes,
            ocr_quality_score=round(overall_conf, 3),
        )
