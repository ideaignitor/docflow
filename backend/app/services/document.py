"""Document Service for DocFlow HR.

This module provides document management functionality including:
- Document creation with metadata
- Document retrieval and listing
- Metadata updates
- Expiration tracking and alerts
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.db.zerodb_client import ZeroDBClient
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentMetadata,
    DocumentStatus,
    DocumentUpdate,
    ExpiringDocumentResponse,
)
from app.services.audit import emit_audit_event

logger = logging.getLogger(__name__)

DOCUMENTS_TABLE = "documents"


class DocumentService:
    """Service for managing documents and their metadata."""

    def __init__(self, db: ZeroDBClient) -> None:
        """Initialize the document service.

        Args:
            db: ZeroDB client instance.
        """
        self.db = db

    async def create_document(
        self,
        data: DocumentCreate,
        org_id: str,
        actor_id: str,
        actor_email: Optional[str] = None,
    ) -> Document:
        """Create a new document with metadata.

        Args:
            data: Document creation data.
            org_id: Organization ID.
            actor_id: ID of user creating the document.
            actor_email: Email of user creating the document.

        Returns:
            The created Document.
        """
        document_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Build document record
        doc_data: Dict[str, Any] = {
            "id": document_id,
            "org_id": org_id,
            "employee_id": data.employee_id,
            "name": data.name,
            "category": data.category.value,
            "status": DocumentStatus.NEEDS_REVIEW.value,
            "file_name": data.file_name,
            "file_type": data.file_type,
            "file_size": data.file_size,
            "storage_path": data.storage_path,
            "submission_channel": data.submission_channel.value,
            "notes": data.notes,
            "version": 1,
            "created_at": now.isoformat(),
            "submitted_at": now.isoformat(),
        }

        # Add metadata fields if provided
        if data.metadata:
            metadata = data.metadata
            if metadata.issue_date:
                doc_data["issue_date"] = metadata.issue_date.isoformat()
            if metadata.expiration_date:
                doc_data["expiration_date"] = metadata.expiration_date.isoformat()
            if metadata.issuer:
                doc_data["issuer"] = metadata.issuer
            if metadata.document_number:
                doc_data["document_number"] = metadata.document_number
            if metadata.state:
                doc_data["state"] = metadata.state
            if metadata.country:
                doc_data["country"] = metadata.country
            if metadata.custom_fields:
                doc_data["custom_fields"] = metadata.custom_fields

            # Store full metadata object for querying
            doc_data["metadata"] = metadata.model_dump(exclude_none=True)

        logger.info(f"Creating document {document_id} for employee {data.employee_id}")

        # Insert into database
        await self.db.table_insert(DOCUMENTS_TABLE, [doc_data])

        # Emit audit event
        await emit_audit_event(
            db=self.db,
            entity_type="document",
            entity_id=document_id,
            action="document.received",
            actor_id=actor_id,
            org_id=org_id,
            actor_email=actor_email,
            metadata={
                "category": data.category.value,
                "submission_channel": data.submission_channel.value,
                "employee_id": data.employee_id,
            },
        )

        return self._row_to_document(doc_data)

    async def get_document(
        self,
        document_id: str,
        org_id: str,
    ) -> Optional[Document]:
        """Get a document by ID.

        Args:
            document_id: Document ID.
            org_id: Organization ID (for access control).

        Returns:
            Document if found, None otherwise.
        """
        rows = await self.db.table_query(
            DOCUMENTS_TABLE,
            filters={"id": document_id, "org_id": org_id},
            limit=1,
        )

        if not rows:
            return None

        return self._row_to_document(rows[0])

    async def list_documents(
        self,
        org_id: str,
        employee_id: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Document], int]:
        """List documents with filtering.

        Args:
            org_id: Organization ID.
            employee_id: Optional filter by employee.
            category: Optional filter by category.
            status: Optional filter by status.
            page: Page number.
            page_size: Items per page.

        Returns:
            Tuple of (documents list, total count).
        """
        filters: Dict[str, Any] = {"org_id": org_id}

        if employee_id:
            filters["employee_id"] = employee_id
        if category:
            filters["category"] = category
        if status:
            filters["status"] = status

        offset = (page - 1) * page_size

        rows = await self.db.table_query(
            DOCUMENTS_TABLE,
            filters=filters,
            limit=page_size,
            offset=offset,
        )

        # Get total count
        all_rows = await self.db.table_query(
            DOCUMENTS_TABLE,
            filters=filters,
            limit=10000,
            offset=0,
        )
        total = len(all_rows)

        documents = [self._row_to_document(row) for row in rows]

        return documents, total

    async def update_document(
        self,
        document_id: str,
        org_id: str,
        data: DocumentUpdate,
        actor_id: str,
        actor_email: Optional[str] = None,
    ) -> Optional[Document]:
        """Update a document's metadata.

        Args:
            document_id: Document ID.
            org_id: Organization ID.
            data: Update data.
            actor_id: ID of user making the update.
            actor_email: Email of user making the update.

        Returns:
            Updated Document if found, None otherwise.
        """
        # Verify document exists
        existing = await self.get_document(document_id, org_id)
        if not existing:
            return None

        now = datetime.utcnow()
        update_data: Dict[str, Any] = {"updated_at": now.isoformat()}

        if data.name is not None:
            update_data["name"] = data.name
        if data.category is not None:
            update_data["category"] = data.category.value
        if data.status is not None:
            update_data["status"] = data.status.value
        if data.notes is not None:
            update_data["notes"] = data.notes

        # Handle metadata update
        if data.metadata is not None:
            metadata = data.metadata
            if metadata.issue_date is not None:
                update_data["issue_date"] = metadata.issue_date.isoformat()
            if metadata.expiration_date is not None:
                update_data["expiration_date"] = metadata.expiration_date.isoformat()
            if metadata.issuer is not None:
                update_data["issuer"] = metadata.issuer
            if metadata.document_number is not None:
                update_data["document_number"] = metadata.document_number
            if metadata.state is not None:
                update_data["state"] = metadata.state
            if metadata.country is not None:
                update_data["country"] = metadata.country
            if metadata.custom_fields is not None:
                update_data["custom_fields"] = metadata.custom_fields

            # Update full metadata object
            update_data["metadata"] = metadata.model_dump(exclude_none=True)

        logger.info(f"Updating document {document_id}")

        await self.db.table_update(
            DOCUMENTS_TABLE,
            filters={"id": document_id},
            update=update_data,
        )

        # Emit audit event
        await emit_audit_event(
            db=self.db,
            entity_type="document",
            entity_id=document_id,
            action="document.updated",
            actor_id=actor_id,
            org_id=org_id,
            actor_email=actor_email,
            metadata={"updated_fields": list(update_data.keys())},
        )

        return await self.get_document(document_id, org_id)

    async def get_expiring_documents(
        self,
        org_id: str,
        days_ahead: int = 30,
    ) -> List[ExpiringDocumentResponse]:
        """Get documents expiring within a specified number of days.

        Args:
            org_id: Organization ID.
            days_ahead: Number of days to look ahead for expirations.

        Returns:
            List of expiring documents.
        """
        now = datetime.utcnow()
        cutoff_date = now + timedelta(days=days_ahead)

        # Query documents with expiration dates
        # Note: ZeroDB may need specific query syntax for date ranges
        rows = await self.db.table_query(
            DOCUMENTS_TABLE,
            filters={"org_id": org_id},
            limit=1000,
        )

        expiring = []
        for row in rows:
            exp_date_str = row.get("expiration_date")
            if not exp_date_str:
                continue

            try:
                if isinstance(exp_date_str, str):
                    exp_date = datetime.fromisoformat(exp_date_str.replace("Z", "+00:00"))
                else:
                    exp_date = exp_date_str

                # Check if expires within the window and not already expired
                if now <= exp_date.replace(tzinfo=None) <= cutoff_date:
                    days_until = (exp_date.replace(tzinfo=None) - now).days

                    expiring.append(
                        ExpiringDocumentResponse(
                            document_id=row["id"],
                            document_name=row.get("name", ""),
                            employee_id=row.get("employee_id", ""),
                            employee_name=row.get("employee_name"),
                            category=row.get("category", "other"),
                            expiration_date=exp_date,
                            days_until_expiration=days_until,
                        )
                    )
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid expiration date for document {row.get('id')}: {e}")

        # Sort by expiration date (soonest first)
        expiring.sort(key=lambda x: x.days_until_expiration)

        return expiring

    async def get_expired_documents(
        self,
        org_id: str,
    ) -> List[Document]:
        """Get all expired documents.

        Args:
            org_id: Organization ID.

        Returns:
            List of expired documents.
        """
        now = datetime.utcnow()

        rows = await self.db.table_query(
            DOCUMENTS_TABLE,
            filters={"org_id": org_id},
            limit=10000,
        )

        expired = []
        for row in rows:
            exp_date_str = row.get("expiration_date")
            if not exp_date_str:
                continue

            try:
                if isinstance(exp_date_str, str):
                    exp_date = datetime.fromisoformat(exp_date_str.replace("Z", "+00:00"))
                else:
                    exp_date = exp_date_str

                if exp_date.replace(tzinfo=None) < now:
                    expired.append(self._row_to_document(row))
            except (ValueError, TypeError):
                continue

        return expired

    def _row_to_document(self, row: Dict[str, Any]) -> Document:
        """Convert a database row to a Document object.

        Args:
            row: Dictionary from database query.

        Returns:
            Document object.
        """
        # Parse datetime fields
        def parse_datetime(val: Any) -> Optional[datetime]:
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val.replace("Z", "+00:00"))
                except ValueError:
                    return None
            return None

        return Document(
            id=row["id"],
            org_id=row["org_id"],
            employee_id=row.get("employee_id", ""),
            name=row.get("name", ""),
            category=row.get("category", "other"),
            status=row.get("status", "pending"),
            file_name=row.get("file_name", ""),
            file_type=row.get("file_type", ""),
            file_size=row.get("file_size", 0),
            storage_path=row.get("storage_path", ""),
            submission_channel=row.get("submission_channel", "upload"),
            issue_date=parse_datetime(row.get("issue_date")),
            expiration_date=parse_datetime(row.get("expiration_date")),
            issuer=row.get("issuer"),
            document_number=row.get("document_number"),
            metadata=row.get("metadata"),
            reviewed_by=row.get("reviewed_by"),
            reviewed_by_name=row.get("reviewed_by_name"),
            reviewed_at=parse_datetime(row.get("reviewed_at")),
            review_notes=row.get("review_notes"),
            rejection_reason=row.get("rejection_reason"),
            created_at=parse_datetime(row.get("created_at")) or datetime.utcnow(),
            updated_at=parse_datetime(row.get("updated_at")),
            submitted_at=parse_datetime(row.get("submitted_at")),
            version=row.get("version", 1),
        )


# Convenience functions
async def create_document(
    db: ZeroDBClient,
    data: DocumentCreate,
    org_id: str,
    actor_id: str,
    actor_email: Optional[str] = None,
) -> Document:
    """Create a new document."""
    service = DocumentService(db)
    return await service.create_document(data, org_id, actor_id, actor_email)


async def get_document(
    db: ZeroDBClient,
    document_id: str,
    org_id: str,
) -> Optional[Document]:
    """Get a document by ID."""
    service = DocumentService(db)
    return await service.get_document(document_id, org_id)


async def get_expiring_documents(
    db: ZeroDBClient,
    org_id: str,
    days_ahead: int = 30,
) -> List[ExpiringDocumentResponse]:
    """Get documents expiring soon."""
    service = DocumentService(db)
    return await service.get_expiring_documents(org_id, days_ahead)
