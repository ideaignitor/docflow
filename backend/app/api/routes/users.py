"""User API routes for DocFlow HR.

This module provides REST API endpoints for user management,
including inviting users to organizations.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import ActiveUserDep, DBDep
from app.schemas.users import (
    UserInviteRequest,
    UserInviteResponse,
    UserResponse,
)
from app.services.user import UserService
from app.core.exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/invite",
    response_model=UserInviteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite User",
    description="Invite a new user to the organization by email.",
)
async def invite_user(
    data: UserInviteRequest,
    db: DBDep,
    current_user: ActiveUserDep,
) -> UserInviteResponse:
    """Invite a new user to the organization.

    Creates a user with status='invited' and sends an invitation email
    with a magic link for activation.

    Args:
        data: User invitation data.
        db: ZeroDB client (injected).
        current_user: Current authenticated user (injected).

    Returns:
        The invitation details.

    Raises:
        HTTPException: 409 if user already exists.
        HTTPException: 404 if role not found.
    """
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
        )

    try:
        service = UserService(db)
        invitation = await service.invite_user(
            org_id=org_id,
            data=data,
            actor_id=current_user.get("sub", "system"),
            actor_email=current_user.get("email"),
        )
        logger.info(f"User invited: {data.email} by {current_user.get('sub')}")
        return invitation

    except ConflictError as e:
        logger.warning(f"User invitation conflict: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except NotFoundError as e:
        logger.warning(f"User invitation failed - not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List Users",
    description="List all users in the organization.",
)
async def list_users(
    db: DBDep,
    current_user: ActiveUserDep,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> List[UserResponse]:
    """List users in the organization.

    Args:
        db: ZeroDB client (injected).
        current_user: Current authenticated user (injected).
        status_filter: Optional status filter.
        limit: Maximum number of results.
        offset: Number of results to skip.

    Returns:
        List of users.
    """
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
        )

    service = UserService(db)
    return await service.list_users(
        org_id=org_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User",
    description="Get user details by ID.",
)
async def get_user(
    user_id: str,
    db: DBDep,
    current_user: ActiveUserDep,
) -> UserResponse:
    """Get a user by ID.

    Args:
        user_id: The user ID.
        db: ZeroDB client (injected).
        current_user: Current authenticated user (injected).

    Returns:
        The user details.

    Raises:
        HTTPException: 404 if user not found.
    """
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context required",
        )

    try:
        service = UserService(db)
        return await service.get_user_by_id(org_id, user_id)

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
