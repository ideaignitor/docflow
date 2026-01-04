"""Authentication API routes for DocFlow HR.

This module provides REST API endpoints for authentication:
- POST /magic-link - Request a magic link
- POST /verify - Verify magic link and get JWT tokens
- POST /refresh - Refresh access token
- GET /me - Get current authenticated user
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import ActiveUserDep, DBDep
from app.core.exceptions import AuthenticationError, NotFoundError
from app.schemas.auth import (
    AuthResponse,
    CurrentUserResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    RefreshTokenRequest,
    TokenResponse,
    TokenVerifyRequest,
)
from app.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/magic-link",
    response_model=MagicLinkResponse,
    status_code=status.HTTP_200_OK,
    summary="Request Magic Link",
    description="Request a magic link to be sent to the provided email address.",
)
async def request_magic_link(
    data: MagicLinkRequest,
    db: DBDep,
) -> MagicLinkResponse:
    """Request a magic link for passwordless authentication.

    This endpoint always returns the same response regardless of whether
    the email exists, to prevent email enumeration attacks.

    Args:
        data: Magic link request containing email
        db: Database client dependency

    Returns:
        MagicLinkResponse with status message
    """
    service = AuthService(db)
    return await service.request_magic_link(data)


@router.post(
    "/verify",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Magic Link",
    description="Verify a magic link token and receive JWT access/refresh tokens.",
)
async def verify_magic_link(
    data: TokenVerifyRequest,
    db: DBDep,
) -> AuthResponse:
    """Verify a magic link token and authenticate the user.

    On successful verification:
    - Token is marked as used (single-use)
    - User status is updated to 'active' if pending/invited
    - JWT access and refresh tokens are returned
    - Audit event is logged

    Args:
        data: Token verification request
        db: Database client dependency

    Returns:
        AuthResponse with user info and JWT tokens

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        service = AuthService(db)
        return await service.verify_magic_link(data)
    except AuthenticationError as e:
        logger.warning(f"Magic link verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh Access Token",
    description="Get a new access token using a valid refresh token.",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: DBDep,
) -> TokenResponse:
    """Refresh an access token using a refresh token.

    Args:
        data: Refresh token request
        db: Database client dependency

    Returns:
        TokenResponse with new access token

    Raises:
        HTTPException: 401 if refresh token is invalid
    """
    try:
        service = AuthService(db)
        return await service.refresh_access_token(data.refresh_token)
    except AuthenticationError as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get the currently authenticated user's information.",
)
async def get_current_user(
    db: DBDep,
    current_user: ActiveUserDep,
) -> CurrentUserResponse:
    """Get current authenticated user's information.

    Requires a valid JWT access token in the Authorization header.

    Args:
        db: Database client dependency
        current_user: Authenticated user from JWT token

    Returns:
        CurrentUserResponse with user details and permissions

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 404 if user not found
    """
    try:
        service = AuthService(db)
        return await service.get_current_user(current_user["id"])
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout",
    description="Logout the current user (client should discard tokens).",
)
async def logout(
    current_user: ActiveUserDep,
) -> dict:
    """Logout the current user.

    Note: Since JWTs are stateless, this endpoint mainly serves as
    a signal for the client to discard tokens. In a production system,
    you might want to implement token blacklisting.

    Args:
        current_user: Authenticated user from JWT token

    Returns:
        Success message
    """
    logger.info(f"User logged out: {current_user.get('email')}")
    return {"message": "Successfully logged out"}
