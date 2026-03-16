"""Pydantic schemas for Multimodal Document Intelligence API."""

from typing import List, Optional
from pydantic import BaseModel, Field


class OcrTokenSchema(BaseModel):
    text: str
    bbox: List[int] = Field(..., min_length=4, max_length=4, description="[x0, y0, x1, y1]")
    confidence: float = Field(default=0.98, ge=0.0, le=1.0)


class DocumentParseRequest(BaseModel):
    document_id: Optional[str] = "DOC-2026-ENG-001"
    tokens: List[OcrTokenSchema]


class SynthesizeDemoRequest(BaseModel):
    seed: int = Field(default=42, ge=0)


class ParsedLineItemSchema(BaseModel):
    item_index: int
    part_number: str
    description: str
    qty: int
    unit_price: float
    total_price: float
    arithmetic_valid: bool


class DocumentParseResponse(BaseModel):
    document_id: Optional[str] = None
    po_number: Optional[str]
    document_date: Optional[str]
    line_items: List[ParsedLineItemSchema]
    subtotal: float
    tax_amount: float
    grand_total: float
    checksum_passed: bool
    reconciliation_notes: str
    ocr_quality_score: float


class HealthResponse(BaseModel):
    status: str
    engine_ready: bool
    coord_max: int
    y_line_tolerance_px: int
