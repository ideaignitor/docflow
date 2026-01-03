"""Organization API routes for DocFlow HR.

This module provides REST API endpoints for organization management,
including creation with proper validation and audit logging.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_user
from app.db.zerodb_client import ZeroDBClient, get_zerodb_client
from app.schemas.organizations import (
    OrganizationCreate,
    OrganizationResponse,
)
from app.services.organization import OrganizationService
from app.core.exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new organization with unique slug and tenant isolation.",
)
async def create_organization(
    data: OrganizationCreate,
    db: Annotated[ZeroDBClient, Depends(get_zerodb_client)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> OrganizationResponse:
    """Create a new organization.

    Creates an organization with:
    - Unique slug (auto-generated from name if not provided)
    - Tenant isolation (org_id scoping)
    - Audit event emission

    Args:
        data: Organization creation data.
        db: ZeroDB client (injected).
        current_user: Current authenticated user (injected).

    Returns:
        The created organization.

    Raises:
        HTTPException: 409 if slug already exists.
    """
    try:
        service = OrganizationService(db)
        org = await service.create_organization(
            data=data,
            actor_id=current_user.get("sub", "system"),
            actor_email=current_user.get("email"),
        )
        logger.info(f"Organization created: {org.id} by user {current_user.get('sub')}")
        return org

    except ConflictError as e:
        logger.warning(f"Organization creation conflict: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get Organization",
    description="Get organization details by ID.",
)
async def get_organization(
    org_id: str,
    db: Annotated[ZeroDBClient, Depends(get_zerodb_client)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> OrganizationResponse:
    """Get an organization by ID.

    Args:
        org_id: The organization ID.
        db: ZeroDB client (injected).
        current_user: Current authenticated user (injected).

    Returns:
        The organization details.

    Raises:
        HTTPException: 404 if organization not found.
    """
    try:
        service = OrganizationService(db)
        return await service.get_organization_by_id(org_id)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.get(
    "/slug/{slug}",
    response_model=OrganizationResponse,
    summary="Get Organization by Slug",
    description="Get organization details by slug.",
)
async def get_organization_by_slug(
    slug: str,
    db: Annotated[ZeroDBClient, Depends(get_zerodb_client)],
    current_user: Annotated[dict, Depends(get_current_user)],
) -> OrganizationResponse:
    """Get an organization by slug.

    Args:
        slug: The organization slug.
        db: ZeroDB client (injected).
        current_user: Current authenticated user (injected).

    Returns:
        The organization details.

    Raises:
        HTTPException: 404 if organization not found.
    """
    try:
        service = OrganizationService(db)
        return await service.get_organization_by_slug(slug)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
