"""User Service for DocFlow HR.

This module provides user management functionality including
inviting users, activating accounts, and managing user status.
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.db.zerodb_client import ZeroDBClient
from app.models.enums import UserStatus, RoleType
from app.schemas.users import (
    UserInviteRequest,
    UserInviteResponse,
    UserResponse,
    UserRole,
)
from app.services.audit import emit_audit_event
from app.core.exceptions import ConflictError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)

# Constants
USERS_TABLE = "users"
ROLES_TABLE = "roles"
INVITATIONS_TABLE = "invitations"
INVITATION_EXPIRY_HOURS = 72  # 3 days


class UserService:
    """Service for managing users.

    This service provides methods for inviting, activating, and
    managing user accounts with proper organization scoping.

    Attributes:
        db: ZeroDB client instance for database operations.
    """

    def __init__(self, db: ZeroDBClient) -> None:
        """Initialize the user service.

        Args:
            db: ZeroDB client instance.
        """
        self.db = db

    async def invite_user(
        self,
        org_id: str,
        data: UserInviteRequest,
        actor_id: str,
        actor_email: Optional[str] = None,
    ) -> UserInviteResponse:
        """Invite a new user to the organization.

        Creates a user with status='invited' and generates a magic link
        token for activation.

        Args:
            org_id: The organization ID.
            data: User invitation data.
            actor_id: ID of the admin inviting the user.
            actor_email: Optional email of the admin.

        Returns:
            UserInviteResponse with invitation details.

        Raises:
            ConflictError: If user with email already exists in org.
            NotFoundError: If specified role doesn't exist.
        """
        logger.info(f"Inviting user {data.email} to org {org_id}")

        # Check if user already exists in this org
        existing = await self.db.table_query(
            USERS_TABLE,
            filters={"org_id": org_id, "email": data.email},
            limit=1,
        )
        if existing:
            raise ConflictError(
                message=f"User with email {data.email} already exists in this organization"
            )

        # Get the role for the user
        role_id = await self._get_role_id_for_user_role(org_id, data.role)

        # Generate IDs and tokens
        user_id = str(uuid.uuid4())
        invitation_id = str(uuid.uuid4())
        magic_token = secrets.token_urlsafe(32)
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(hours=INVITATION_EXPIRY_HOURS)

        # Create user with status='invited'
        # Password hash is placeholder until user activates
        placeholder_hash = "$2b$12$placeholder.hash.for.invited.user.only"

        user_data = {
            "id": user_id,
            "org_id": org_id,
            "email": data.email,
            "password_hash": placeholder_hash,
            "first_name": data.first_name or "",
            "last_name": data.last_name or "",
            "status": "invited",
            "role_id": role_id,
            "employee_id": data.employee_id,
            "email_verified": False,
            "email_verification_token": magic_token,
            "failed_login_attempts": 0,
            "preferences": {},
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
        }

        # Create invitation record
        invitation_data = {
            "id": invitation_id,
            "org_id": org_id,
            "user_id": user_id,
            "email": data.email,
            "token": magic_token,
            "status": "pending",
            "expires_at": expires_at.isoformat(),
            "custom_message": data.custom_message,
            "invited_by": actor_id,
            "created_at": created_at.isoformat(),
        }

        # Insert user and invitation
        await self.db.table_insert(USERS_TABLE, [user_data])
        await self.db.table_insert(INVITATIONS_TABLE, [invitation_data])

        # Emit audit event
        await emit_audit_event(
            db=self.db,
            entity_type="user",
            entity_id=user_id,
            action="user.invited",
            actor_id=actor_id,
            org_id=org_id,
            actor_email=actor_email,
            metadata={
                "invited_email": data.email,
                "role": data.role.value,
                "expires_at": expires_at.isoformat(),
            },
        )

        # Send invitation email (logged for now, real email in production)
        await self._send_invitation_email(
            email=data.email,
            magic_token=magic_token,
            org_id=org_id,
            custom_message=data.custom_message,
        )

        logger.info(f"User {data.email} invited successfully with ID {user_id}")

        return UserInviteResponse(
            id=invitation_id,
            user_id=user_id,
            email=data.email,
            role=data.role,
            status="pending",
            expires_at=expires_at,
            magic_link_sent=True,
        )

    async def get_user_by_id(self, org_id: str, user_id: str) -> UserResponse:
        """Get a user by ID.

        Args:
            org_id: The organization ID.
            user_id: The user ID.

        Returns:
            UserResponse object.

        Raises:
            NotFoundError: If user not found.
        """
        rows = await self.db.table_query(
            USERS_TABLE,
            filters={"id": user_id, "org_id": org_id},
            limit=1,
        )

        if not rows:
            raise NotFoundError(message=f"User not found: {user_id}")

        return self._row_to_response(rows[0])

    async def get_user_by_email(self, org_id: str, email: str) -> UserResponse:
        """Get a user by email.

        Args:
            org_id: The organization ID.
            email: The user email.

        Returns:
            UserResponse object.

        Raises:
            NotFoundError: If user not found.
        """
        rows = await self.db.table_query(
            USERS_TABLE,
            filters={"email": email, "org_id": org_id},
            limit=1,
        )

        if not rows:
            raise NotFoundError(message=f"User not found: {email}")

        return self._row_to_response(rows[0])

    async def list_users(
        self,
        org_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[UserResponse]:
        """List users in an organization.

        Args:
            org_id: The organization ID.
            status: Optional status filter.
            limit: Maximum number of users to return.
            offset: Number of users to skip.

        Returns:
            List of UserResponse objects.
        """
        filters: Dict[str, Any] = {"org_id": org_id}
        if status:
            filters["status"] = status

        rows = await self.db.table_query(
            USERS_TABLE,
            filters=filters,
            limit=limit,
            offset=offset,
        )

        return [self._row_to_response(row) for row in rows]

    async def _get_role_id_for_user_role(self, org_id: str, user_role: UserRole) -> str:
        """Map UserRole enum to actual role ID in the organization.

        Args:
            org_id: The organization ID.
            user_role: The UserRole enum value.

        Returns:
            The role ID.

        Raises:
            NotFoundError: If role not found.
        """
        # Map UserRole to RoleType
        role_type_map = {
            UserRole.SUPER_ADMIN: RoleType.HR_ADMIN,  # Map to HR_ADMIN for org context
            UserRole.ORG_ADMIN: RoleType.HR_ADMIN,
            UserRole.HR_MANAGER: RoleType.HR_MANAGER,
            UserRole.HR_USER: RoleType.HR_MANAGER,
            UserRole.EMPLOYEE: RoleType.EMPLOYEE,
            UserRole.VIEWER: RoleType.AUDITOR,
        }

        role_type = role_type_map.get(user_role, RoleType.EMPLOYEE)

        rows = await self.db.table_query(
            ROLES_TABLE,
            filters={"org_id": org_id, "role_type": role_type.value},
            limit=1,
        )

        if not rows:
            # Fall back to employee role
            rows = await self.db.table_query(
                ROLES_TABLE,
                filters={"org_id": org_id, "role_type": RoleType.EMPLOYEE.value},
                limit=1,
            )

        if not rows:
            raise NotFoundError(message=f"No roles found for organization: {org_id}")

        return rows[0]["id"]

    async def _send_invitation_email(
        self,
        email: str,
        magic_token: str,
        org_id: str,
        custom_message: Optional[str] = None,
    ) -> None:
        """Send invitation email with magic link.

        In production, this would integrate with an email service.
        For now, it logs the email details.

        Args:
            email: Recipient email address.
            magic_token: The magic link token.
            org_id: The organization ID.
            custom_message: Optional custom message to include.
        """
        # Build magic link URL (would be configured per environment)
        magic_link = f"https://app.docflow.hr/activate?token={magic_token}"

        logger.info(
            f"[EMAIL] Invitation sent to {email}\n"
            f"  Magic Link: {magic_link}\n"
            f"  Org ID: {org_id}\n"
            f"  Custom Message: {custom_message or 'None'}"
        )

        # TODO: Integrate with actual email service (SendGrid, SES, etc.)

    def _row_to_response(self, row: Dict[str, Any]) -> UserResponse:
        """Convert a database row to UserResponse.

        Args:
            row: Dictionary from database query.

        Returns:
            UserResponse object.
        """
        created_at = row.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = row.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        last_login_at = row.get("last_login_at")
        if isinstance(last_login_at, str):
            last_login_at = datetime.fromisoformat(last_login_at.replace("Z", "+00:00"))

        # Map status string to enum
        status_str = row.get("status", "pending")
        status_map = {
            "active": "active",
            "inactive": "inactive",
            "pending": "pending",
            "invited": "pending",  # Map invited to pending for response
            "suspended": "suspended",
        }
        status = status_map.get(status_str, "pending")

        return UserResponse(
            id=row["id"],
            email=row["email"],
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            role=UserRole.HR_USER,  # Simplified for now
            status=status,
            org_id=row["org_id"],
            employee_id=row.get("employee_id"),
            last_login_at=last_login_at,
            created_at=created_at,
            updated_at=updated_at,
        )


async def invite_user(
    db: ZeroDBClient,
    org_id: str,
    data: UserInviteRequest,
    actor_id: str,
    actor_email: Optional[str] = None,
) -> UserInviteResponse:
    """Convenience function to invite a user.

    Args:
        db: ZeroDB client instance.
        org_id: The organization ID.
        data: User invitation data.
        actor_id: ID of the admin inviting the user.
        actor_email: Optional email of the admin.

    Returns:
        UserInviteResponse with invitation details.
    """
    service = UserService(db)
    return await service.invite_user(org_id, data, actor_id, actor_email)
