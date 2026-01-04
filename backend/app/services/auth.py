"""Authentication service for DocFlow HR.

This module provides authentication functionality including:
- Magic link generation and verification
- JWT token management
- User session handling
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.db.zerodb_client import ZeroDBClient
from app.schemas.auth import (
    AuthResponse,
    CurrentUserResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    TokenResponse,
    TokenVerifyRequest,
    UserAuthInfo,
)

logger = logging.getLogger(__name__)

# Magic link token expiration (15 minutes)
MAGIC_LINK_EXPIRY_MINUTES = 15


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: ZeroDBClient):
        """Initialize auth service with database client."""
        self.db = db

    async def request_magic_link(
        self,
        data: MagicLinkRequest,
    ) -> MagicLinkResponse:
        """Request a magic link for authentication.

        Args:
            data: Magic link request containing email

        Returns:
            MagicLinkResponse with status message
        """
        email = data.email.lower()

        # Find user by email (don't reveal if user exists)
        users = await self.db.query_rows(
            table_id="users",
            filter={"email": email},
            limit=1,
        )

        if users:
            user = users[0]

            # Generate magic link token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(minutes=MAGIC_LINK_EXPIRY_MINUTES)

            # Store magic link token
            await self.db.insert_rows(
                table_id="magic_links",
                rows=[{
                    "user_id": user["id"],
                    "token": token,
                    "expires_at": expires_at.isoformat(),
                    "used": False,
                    "created_at": datetime.utcnow().isoformat(),
                }],
            )

            # Log audit event
            await self._log_audit_event(
                user_id=user["id"],
                org_id=user.get("org_id"),
                action="magic_link.requested",
                details={"email": email},
            )

            # Send magic link email (placeholder - log for now)
            magic_link_url = f"{settings.FRONTEND_URL}/auth/verify?token={token}"
            logger.info(f"Magic link for {email}: {magic_link_url}")

        # Always return same response (security - don't reveal if email exists)
        return MagicLinkResponse(
            message="If an account exists, a magic link has been sent",
            email=email,
            expires_in_minutes=MAGIC_LINK_EXPIRY_MINUTES,
        )

    async def verify_magic_link(
        self,
        data: TokenVerifyRequest,
    ) -> AuthResponse:
        """Verify a magic link token and return JWT tokens.

        Args:
            data: Token verification request

        Returns:
            AuthResponse with user info and JWT tokens

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        # Find magic link token
        magic_links = await self.db.query_rows(
            table_id="magic_links",
            filter={"token": data.token, "used": False},
            limit=1,
        )

        if not magic_links:
            raise AuthenticationError("Invalid or expired token")

        magic_link = magic_links[0]

        # Check expiration
        expires_at = datetime.fromisoformat(magic_link["expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow() > expires_at.replace(tzinfo=None):
            raise AuthenticationError("Token has expired")

        # Get user
        users = await self.db.query_rows(
            table_id="users",
            filter={"id": magic_link["user_id"]},
            limit=1,
        )

        if not users:
            raise AuthenticationError("User not found")

        user = users[0]

        # Mark token as used
        await self.db.update_rows(
            table_id="magic_links",
            filter={"id": magic_link["id"]},
            update={"$set": {"used": True, "used_at": datetime.utcnow().isoformat()}},
        )

        # Update user status to active if pending/invited
        if user.get("status") in ["pending", "invited"]:
            await self.db.update_rows(
                table_id="users",
                filter={"id": user["id"]},
                update={"$set": {
                    "status": "active",
                    "activated_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }},
            )
            user["status"] = "active"

        # Update last login
        await self.db.update_rows(
            table_id="users",
            filter={"id": user["id"]},
            update={"$set": {"last_login_at": datetime.utcnow().isoformat()}},
        )

        # Generate JWT tokens
        token_data = {
            "sub": user["id"],
            "email": user["email"],
            "role": user.get("role", "employee"),
            "org_id": user.get("org_id"),
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Log audit event
        await self._log_audit_event(
            user_id=user["id"],
            org_id=user.get("org_id"),
            action="user.authenticated",
            details={"method": "magic_link"},
        )

        logger.info(f"User authenticated via magic link: {user['email']}")

        return AuthResponse(
            user=UserAuthInfo(
                id=user["id"],
                email=user["email"],
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                role=user.get("role", "employee"),
                status=user["status"],
                org_id=user.get("org_id", ""),
            ),
            tokens=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        """Refresh an access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New TokenResponse with fresh access token

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        try:
            payload = decode_token(refresh_token)

            if not verify_token_type(payload, "refresh"):
                raise AuthenticationError("Invalid token type")

            # Get user to verify still active
            users = await self.db.query_rows(
                table_id="users",
                filter={"id": payload["sub"]},
                limit=1,
            )

            if not users or users[0].get("status") != "active":
                raise AuthenticationError("User not found or inactive")

            user = users[0]

            # Generate new access token
            token_data = {
                "sub": user["id"],
                "email": user["email"],
                "role": user.get("role", "employee"),
                "org_id": user.get("org_id"),
            }

            new_access_token = create_access_token(token_data)

            return TokenResponse(
                access_token=new_access_token,
                refresh_token=refresh_token,  # Return same refresh token
                token_type="bearer",
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise AuthenticationError("Invalid refresh token")

    async def get_current_user(
        self,
        user_id: str,
    ) -> CurrentUserResponse:
        """Get current authenticated user info.

        Args:
            user_id: ID of authenticated user

        Returns:
            CurrentUserResponse with user details

        Raises:
            NotFoundError: If user not found
        """
        users = await self.db.query_rows(
            table_id="users",
            filter={"id": user_id},
            limit=1,
        )

        if not users:
            raise NotFoundError("User not found")

        user = users[0]

        # Get organization name if exists
        org_name = None
        if user.get("org_id"):
            orgs = await self.db.query_rows(
                table_id="organizations",
                filter={"id": user["org_id"]},
                limit=1,
            )
            if orgs:
                org_name = orgs[0].get("name")

        # Get permissions based on role
        permissions = self._get_role_permissions(user.get("role", "employee"))

        return CurrentUserResponse(
            id=user["id"],
            email=user["email"],
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            role=user.get("role", "employee"),
            status=user.get("status", "active"),
            org_id=user.get("org_id", ""),
            org_name=org_name,
            permissions=permissions,
            last_login_at=user.get("last_login_at"),
        )

    def _get_role_permissions(self, role: str) -> list[str]:
        """Get permissions for a role."""
        role_permissions = {
            "super_admin": [
                "users:read", "users:write", "users:delete",
                "orgs:read", "orgs:write", "orgs:delete",
                "documents:read", "documents:write", "documents:delete",
                "settings:read", "settings:write",
                "audit:read",
            ],
            "org_admin": [
                "users:read", "users:write",
                "documents:read", "documents:write", "documents:delete",
                "settings:read", "settings:write",
                "audit:read",
            ],
            "hr_manager": [
                "users:read",
                "documents:read", "documents:write",
                "settings:read",
                "audit:read",
            ],
            "hr_user": [
                "documents:read", "documents:write",
            ],
            "employee": [
                "documents:read:own", "documents:write:own",
            ],
            "viewer": [
                "documents:read",
            ],
        }
        return role_permissions.get(role, [])

    async def _log_audit_event(
        self,
        user_id: str,
        org_id: Optional[str],
        action: str,
        details: dict,
    ) -> None:
        """Log an audit event."""
        try:
            await self.db.insert_rows(
                table_id="audit_events",
                rows=[{
                    "user_id": user_id,
                    "org_id": org_id,
                    "action": action,
                    "details": details,
                    "ip_address": None,  # Would be passed from request context
                    "user_agent": None,
                    "created_at": datetime.utcnow().isoformat(),
                }],
            )
        except Exception as e:
            logger.warning(f"Failed to log audit event: {e}")


# Convenience functions for direct import
async def request_magic_link(
    db: ZeroDBClient,
    data: MagicLinkRequest,
) -> MagicLinkResponse:
    """Request a magic link for authentication."""
    service = AuthService(db)
    return await service.request_magic_link(data)


async def verify_magic_link(
    db: ZeroDBClient,
    data: TokenVerifyRequest,
) -> AuthResponse:
    """Verify a magic link token."""
    service = AuthService(db)
    return await service.verify_magic_link(data)


async def refresh_access_token(
    db: ZeroDBClient,
    refresh_token: str,
) -> TokenResponse:
    """Refresh an access token."""
    service = AuthService(db)
    return await service.refresh_access_token(refresh_token)


async def get_current_user(
    db: ZeroDBClient,
    user_id: str,
) -> CurrentUserResponse:
    """Get current user info."""
    service = AuthService(db)
    return await service.get_current_user(user_id)
