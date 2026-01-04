"""Audit Log API routes for DocFlow HR.

This module provides endpoints for querying and exporting audit events:
- GET /events - Query audit events with filters
- GET /events/entity/{entity_type}/{entity_id} - Get events for specific entity
- GET /export - Export audit events as JSON or CSV
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from app.api.deps import ActiveUserDep, DBDep, require_role
from app.schemas.audit import (
    AuditEvent,
    AuditEventListResponse,
    DocumentAuditTrailResponse,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

router = APIRouter()

# Roles allowed to access audit logs
AUDIT_ACCESS_ROLES = ["super_admin", "org_admin", "hr_manager", "auditor"]


async def get_audit_viewer(
    current_user: Annotated[dict, Depends(require_role(AUDIT_ACCESS_ROLES))],
) -> dict:
    """Dependency to ensure user has audit access permissions."""
    return current_user


AuditViewerDep = Annotated[dict, Depends(get_audit_viewer)]


@router.get(
    "/events",
    response_model=AuditEventListResponse,
    summary="Query Audit Events",
    description="Query audit events with optional filters. Results are paginated and scoped to the user's organization.",
)
async def query_audit_events(
    db: DBDep,
    viewer: AuditViewerDep,
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type (document, employee, legal_hold)"),
    entity_id: Optional[str] = Query(default=None, description="Filter by entity ID"),
    action: Optional[str] = Query(default=None, description="Filter by action type"),
    actor_id: Optional[str] = Query(default=None, description="Filter by actor ID"),
    start_date: Optional[datetime] = Query(default=None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter events before this date"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> AuditEventListResponse:
    """Query audit events with filters.

    Returns a paginated list of audit events filtered by the provided criteria.
    All results are scoped to the authenticated user's organization.

    Args:
        db: Database client
        viewer: Authenticated user with audit access
        entity_type: Optional filter by entity type
        entity_id: Optional filter by entity ID
        action: Optional filter by action type
        actor_id: Optional filter by actor ID
        start_date: Optional filter for events after this date
        end_date: Optional filter for events before this date
        page: Page number for pagination
        page_size: Number of items per page

    Returns:
        AuditEventListResponse with paginated audit events
    """
    org_id = viewer.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User organization ID not found",
        )

    logger.info(f"Querying audit events for org {org_id}")

    service = AuditService(db)
    events, total = await service.query_events(
        org_id=org_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return AuditEventListResponse(
        events=events,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/events/entity/{entity_type}/{entity_id}",
    response_model=DocumentAuditTrailResponse,
    summary="Get Entity Audit Trail",
    description="Get the complete audit trail for a specific entity (document, employee, etc.).",
)
async def get_entity_audit_trail(
    entity_type: str,
    entity_id: str,
    db: DBDep,
    viewer: AuditViewerDep,
) -> DocumentAuditTrailResponse:
    """Get the audit trail for a specific entity.

    Returns all audit events for the specified entity in chronological order.

    Args:
        entity_type: Type of entity (document, employee, legal_hold)
        entity_id: ID of the entity
        db: Database client
        viewer: Authenticated user with audit access

    Returns:
        DocumentAuditTrailResponse with all events for the entity
    """
    org_id = viewer.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User organization ID not found",
        )

    logger.info(f"Getting audit trail for {entity_type}/{entity_id} in org {org_id}")

    service = AuditService(db)

    # Query all events for this entity
    events, total = await service.query_events(
        org_id=org_id,
        entity_type=entity_type,
        entity_id=entity_id,
        page=1,
        page_size=10000,  # Get all events
    )

    # Sort by created_at in chronological order
    events.sort(key=lambda e: e.created_at)

    return DocumentAuditTrailResponse(
        document_id=entity_id,
        events=events,
        total_events=total,
    )


@router.get(
    "/export",
    summary="Export Audit Events",
    description="Export audit events as JSON or CSV file.",
)
async def export_audit_events(
    db: DBDep,
    viewer: AuditViewerDep,
    format: str = Query(default="json", pattern="^(json|csv)$", description="Export format: json or csv"),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type"),
    entity_id: Optional[str] = Query(default=None, description="Filter by entity ID"),
    action: Optional[str] = Query(default=None, description="Filter by action type"),
    actor_id: Optional[str] = Query(default=None, description="Filter by actor ID"),
    start_date: Optional[datetime] = Query(default=None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter events before this date"),
) -> StreamingResponse:
    """Export audit events as a downloadable file.

    Supports JSON and CSV formats. All filters from the query endpoint apply.

    Args:
        db: Database client
        viewer: Authenticated user with audit access
        format: Export format (json or csv)
        entity_type: Optional filter by entity type
        entity_id: Optional filter by entity ID
        action: Optional filter by action type
        actor_id: Optional filter by actor ID
        start_date: Optional filter for events after this date
        end_date: Optional filter for events before this date

    Returns:
        StreamingResponse with the exported file
    """
    org_id = viewer.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User organization ID not found",
        )

    logger.info(f"Exporting audit events for org {org_id} as {format}")

    service = AuditService(db)
    events, _ = await service.query_events(
        org_id=org_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        start_date=start_date,
        end_date=end_date,
        page=1,
        page_size=50000,  # Export limit
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "id", "entity_type", "entity_id", "action",
            "actor_id", "actor_email", "created_at", "metadata"
        ])

        # Data rows
        for event in events:
            writer.writerow([
                event.id,
                event.entity_type,
                event.entity_id,
                event.action,
                event.actor_id,
                event.actor_email or "",
                event.created_at.isoformat(),
                json.dumps(event.metadata) if event.metadata else "",
            ])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_events_{timestamp}.csv"
            },
        )
    else:
        # Generate JSON
        events_data = [
            {
                "id": event.id,
                "org_id": event.org_id,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "action": event.action,
                "actor_id": event.actor_id,
                "actor_email": event.actor_email,
                "metadata": event.metadata,
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ]

        json_output = json.dumps({
            "exported_at": datetime.utcnow().isoformat(),
            "org_id": org_id,
            "total_events": len(events_data),
            "events": events_data,
        }, indent=2)

        return StreamingResponse(
            iter([json_output]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_events_{timestamp}.json"
            },
        )
