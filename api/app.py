"""FastAPI application for Multimodal Document Intelligence & Tabular Extraction."""

from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, HTTPException, status

from src.config import DEFAULT_DOC_CONFIG
from src.generator import generate_synthetic_spec_document, OcrToken
from src.parser import EngineeringDocumentParser
from api.schemas import (
    OcrTokenSchema,
    DocumentParseRequest,
    SynthesizeDemoRequest,
    ParsedLineItemSchema,
    DocumentParseResponse,
    HealthResponse,
)

parser: Optional[EngineeringDocumentParser] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global parser
    parser = EngineeringDocumentParser()
    yield


app = FastAPI(
    title="Multimodal Document Intelligence API",
    description=(
        "Production industrial 2D spatial layout and tabular information extraction engine. "
        "Performs coordinate line clustering, column bounding box alignment, and deterministic "
        "arithmetic checksum reconciliation on technical Purchase Orders and Bill of Materials (BOM)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["Diagnostics"])
def health():
    return HealthResponse(
        status="healthy",
        engine_ready=(parser is not None),
        coord_max=DEFAULT_DOC_CONFIG.coord_max,
        y_line_tolerance_px=DEFAULT_DOC_CONFIG.y_line_tolerance_px,
    )


@app.post("/parse/document", response_model=DocumentParseResponse, tags=["Document Intelligence"])
def parse_document(req: DocumentParseRequest):
    """Processes arbitrary OCR token streams and reconstructs structured procurement schema."""
    if parser is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Parser engine not ready")

    ocr_tokens = [
        OcrToken(
            text=t.text,
            x0=t.bbox[0],
            y0=t.bbox[1],
            x1=t.bbox[2],
            y1=t.bbox[3],
            confidence=t.confidence,
        )
        for t in req.tokens
    ]

    res = parser.parse_document(ocr_tokens)

    items = [
        ParsedLineItemSchema(
            item_index=it.item_index,
            part_number=it.part_number,
            description=it.description,
            qty=it.qty,
            unit_price=it.unit_price,
            total_price=it.total_price,
            arithmetic_valid=it.arithmetic_valid,
        )
        for it in res.line_items
    ]

    return DocumentParseResponse(
        document_id=req.document_id,
        po_number=res.po_number,
        document_date=res.document_date,
        line_items=items,
        subtotal=res.subtotal,
        tax_amount=res.tax_amount,
        grand_total=res.grand_total,
        checksum_passed=res.checksum_passed,
        reconciliation_notes=res.reconciliation_notes,
        ocr_quality_score=res.ocr_quality_score,
    )


@app.post("/parse/synthetic-demo", response_model=DocumentParseResponse, tags=["Demonstration"])
def parse_synthetic_demo(req: SynthesizeDemoRequest):
    """Generates a realistic synthetic engineering spec PO and returns extracted structured tables."""
    if parser is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Parser engine not ready")

    tokens, _ = generate_synthetic_spec_document(seed=req.seed)
    res = parser.parse_document(tokens)

    items = [
        ParsedLineItemSchema(
            item_index=it.item_index,
            part_number=it.part_number,
            description=it.description,
            qty=it.qty,
            unit_price=it.unit_price,
            total_price=it.total_price,
            arithmetic_valid=it.arithmetic_valid,
        )
        for it in res.line_items
    ]

    return DocumentParseResponse(
        document_id=f"DEMO-PO-SEED-{req.seed}",
        po_number=res.po_number,
        document_date=res.document_date,
        line_items=items,
        subtotal=res.subtotal,
        tax_amount=res.tax_amount,
        grand_total=res.grand_total,
        checksum_passed=res.checksum_passed,
        reconciliation_notes=res.reconciliation_notes,
        ocr_quality_score=res.ocr_quality_score,
    )
