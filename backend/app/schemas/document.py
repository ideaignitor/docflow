"""Pydantic schemas for Document management."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document lifecycle status."""

    PENDING = "pending"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class DocumentCategory(str, Enum):
    """Document category types."""

    I9 = "i9"
    W4 = "w4"
    DIRECT_DEPOSIT = "direct_deposit"
    TAX_FORM = "tax_form"
    IDENTIFICATION = "identification"
    CERTIFICATION = "certification"
    LICENSE = "license"
    POLICY_ACKNOWLEDGMENT = "policy_acknowledgment"
    BENEFITS = "benefits"
    PERFORMANCE = "performance"
    OTHER = "other"


class SubmissionChannel(str, Enum):
    """How the document was submitted."""

    UPLOAD = "upload"
    EMAIL = "email"
    SMS = "sms"
    FAX = "fax"
    CLOUD_STORAGE = "cloud_storage"
    HRIS_SYNC = "hris_sync"


class DocumentMetadata(BaseModel):
    """Metadata associated with a document."""

    issue_date: Optional[datetime] = Field(
        default=None,
        description="Date the document was issued",
    )
    expiration_date: Optional[datetime] = Field(
        default=None,
        description="Date the document expires (for licenses, certifications, etc.)",
    )
    issuer: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Entity that issued the document",
    )
    document_number: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Document reference number (license #, certificate #, etc.)",
    )
    state: Optional[str] = Field(
        default=None,
        max_length=2,
        description="State code if applicable (e.g., CA, NY)",
    )
    country: Optional[str] = Field(
        default=None,
        max_length=3,
        description="Country code (ISO 3166-1 alpha-3)",
    )
    custom_fields: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom metadata fields as key-value pairs",
    )


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""

    employee_id: str = Field(
        ...,
        description="ID of the employee this document belongs to",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Document name/title",
    )
    category: DocumentCategory = Field(
        default=DocumentCategory.OTHER,
        description="Document category",
    )
    file_name: str = Field(
        ...,
        description="Original filename",
    )
    file_type: str = Field(
        ...,
        description="MIME type of the file",
    )
    file_size: int = Field(
        ...,
        ge=0,
        description="File size in bytes",
    )
    storage_path: str = Field(
        ...,
        description="Path to file in storage",
    )
    submission_channel: SubmissionChannel = Field(
        default=SubmissionChannel.UPLOAD,
        description="How the document was submitted",
    )
    metadata: Optional[DocumentMetadata] = Field(
        default=None,
        description="Document metadata",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Notes about the document",
    )


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Document name/title",
    )
    category: Optional[DocumentCategory] = Field(
        default=None,
        description="Document category",
    )
    status: Optional[DocumentStatus] = Field(
        default=None,
        description="Document status",
    )
    metadata: Optional[DocumentMetadata] = Field(
        default=None,
        description="Document metadata",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Notes about the document",
    )


class Document(BaseModel):
    """Full document schema for responses."""

    id: str = Field(..., description="Unique document ID")
    org_id: str = Field(..., description="Organization ID")
    employee_id: str = Field(..., description="Employee ID")
    name: str = Field(..., description="Document name")
    category: str = Field(..., description="Document category")
    status: str = Field(..., description="Document status")
    file_name: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    storage_path: str = Field(..., description="Storage path")
    submission_channel: str = Field(..., description="Submission channel")

    # Metadata fields (flattened for convenience)
    issue_date: Optional[datetime] = Field(default=None)
    expiration_date: Optional[datetime] = Field(default=None)
    issuer: Optional[str] = Field(default=None)
    document_number: Optional[str] = Field(default=None)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Full metadata object")

    # Review fields
    reviewed_by: Optional[str] = Field(default=None)
    reviewed_by_name: Optional[str] = Field(default=None)
    reviewed_at: Optional[datetime] = Field(default=None)
    review_notes: Optional[str] = Field(default=None)
    rejection_reason: Optional[str] = Field(default=None)

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None)
    submitted_at: Optional[datetime] = Field(default=None)

    # Versioning
    version: int = Field(default=1, description="Document version number")

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Paginated response for document list."""

    documents: List[Document] = Field(..., description="List of documents")
    total: int = Field(..., ge=0, description="Total count")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, le=100, description="Page size")
    has_next: bool = Field(..., description="Has next page")
    has_previous: bool = Field(..., description="Has previous page")


class ExpiringDocumentResponse(BaseModel):
    """Response for documents expiring soon."""

    document_id: str = Field(..., description="Document ID")
    document_name: str = Field(..., description="Document name")
    employee_id: str = Field(..., description="Employee ID")
    employee_name: Optional[str] = Field(default=None, description="Employee name")
    category: str = Field(..., description="Document category")
    expiration_date: datetime = Field(..., description="Expiration date")
    days_until_expiration: int = Field(..., description="Days until expiration")


class ExpiringDocumentsListResponse(BaseModel):
    """List of documents expiring within a time range."""

    documents: List[ExpiringDocumentResponse] = Field(...)
    total: int = Field(..., ge=0)
    days_ahead: int = Field(..., description="Number of days looked ahead")
