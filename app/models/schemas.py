"""Pydantic models for request/response schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Document classification types."""
    INVOICE = "invoice"
    NON_INVOICE = "non_invoice"
    UNKNOWN = "unknown"


class Attachment(BaseModel):
    """Email attachment model."""
    name: str
    size: int
    content_type: str
    attachment_id: Optional[str] = None
    local_path: Optional[str] = None


class EmailMessage(BaseModel):
    """Email message model."""
    id: str
    subject: str
    sender: str
    received_at: datetime
    has_attachments: bool
    attachments: List[Attachment] = []


class ClassificationResult(BaseModel):
    """Document classification result."""
    document_type: DocumentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    metadata: Dict[str, Any] = {}


class ProcessingResult(BaseModel):
    """Result of processing an attachment."""
    attachment_name: str
    classification: ClassificationResult
    destination_path: str
    processed_at: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None


class EmailCheckRequest(BaseModel):
    """Request to check emails."""
    max_emails: Optional[int] = Field(default=10, description="Maximum emails to process")
    unread_only: bool = Field(default=True, description="Process only unread emails")


class EmailCheckResponse(BaseModel):
    """Response from email check."""
    emails_processed: int
    attachments_processed: int
    results: List[ProcessingResult]
    timestamp: datetime = Field(default_factory=datetime.now)


class ClassifyRequest(BaseModel):
    """Request to classify a document."""
    file_path: str = Field(..., description="Path to the document to classify")
    file_name: Optional[str] = None


class ClassifyResponse(BaseModel):
    """Response from document classification."""
    file_name: str
    classification: ClassificationResult
    timestamp: datetime = Field(default_factory=datetime.now)
