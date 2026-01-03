"""Role Service for DocFlow HR.

This module provides role management functionality including
seeding default roles for new organizations.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.db.zerodb_client import ZeroDBClient
from app.models.enums import RoleType, DEFAULT_ORG_ROLES
from app.models.role import ROLE_DESCRIPTIONS, ROLE_DISPLAY_NAMES
from app.schemas.roles import RoleResponse, SeedRolesResponse
from app.services.audit import emit_audit_event
from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)

# Constants
ROLES_TABLE = "roles"


class RoleService:
    """Service for managing roles.

    This service provides methods for creating and managing roles
    with proper organization scoping.

    Attributes:
        db: ZeroDB client instance for database operations.
    """

    def __init__(self, db: ZeroDBClient) -> None:
        """Initialize the role service.

        Args:
            db: ZeroDB client instance.
        """
        self.db = db

    async def seed_default_roles(
        self,
        org_id: str,
        actor_id: str = "system",
        actor_email: Optional[str] = None,
    ) -> SeedRolesResponse:
        """Seed default roles for a new organization.

        Creates the standard set of roles (HR Admin, HR Manager, Legal,
        IT Admin, Auditor, Employee) scoped to the organization.

        Args:
            org_id: The organization ID to seed roles for.
            actor_id: ID of the actor (default: "system" for automated seeding).
            actor_email: Optional email of the actor.

        Returns:
            SeedRolesResponse with created roles.
        """
        logger.info(f"Seeding default roles for organization: {org_id}")

        created_roles: List[RoleResponse] = []
        created_at = datetime.utcnow()

        for role_type in DEFAULT_ORG_ROLES:
            role_id = str(uuid.uuid4())

            role_data = {
                "id": role_id,
                "org_id": org_id,
                "name": ROLE_DISPLAY_NAMES.get(role_type, role_type.value),
                "role_type": role_type.value,
                "description": ROLE_DESCRIPTIONS.get(role_type, ""),
                "permissions": self._get_default_permissions(role_type),
                "is_default": True,
                "is_active": True,
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
            }

            # Insert role into database
            await self.db.table_insert(ROLES_TABLE, [role_data])

            # Emit audit event for role creation
            await emit_audit_event(
                db=self.db,
                entity_type="role",
                entity_id=role_id,
                action="role.created",
                actor_id=actor_id,
                org_id=org_id,
                actor_email=actor_email,
                metadata={
                    "role_type": role_type.value,
                    "name": role_data["name"],
                    "is_default": True,
                },
            )

            created_roles.append(
                RoleResponse(
                    id=role_id,
                    org_id=org_id,
                    name=role_data["name"],
                    role_type=role_type,
                    description=role_data["description"],
                    permissions=role_data["permissions"],
                    is_default=True,
                    is_active=True,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )

        logger.info(f"Created {len(created_roles)} default roles for org {org_id}")

        return SeedRolesResponse(
            org_id=org_id,
            roles_created=len(created_roles),
            roles=created_roles,
        )

    async def get_roles_by_org(self, org_id: str) -> List[RoleResponse]:
        """Get all roles for an organization.

        Args:
            org_id: The organization ID.

        Returns:
            List of RoleResponse objects.
        """
        rows = await self.db.table_query(
            ROLES_TABLE,
            filters={"org_id": org_id},
            limit=100,
        )

        return [self._row_to_response(row) for row in rows]

    async def get_role_by_id(self, org_id: str, role_id: str) -> RoleResponse:
        """Get a specific role by ID.

        Args:
            org_id: The organization ID.
            role_id: The role ID.

        Returns:
            RoleResponse object.

        Raises:
            NotFoundError: If role not found.
        """
        rows = await self.db.table_query(
            ROLES_TABLE,
            filters={"id": role_id, "org_id": org_id},
            limit=1,
        )

        if not rows:
            raise NotFoundError(message=f"Role not found: {role_id}")

        return self._row_to_response(rows[0])

    def _get_default_permissions(self, role_type: RoleType) -> Dict[str, Any]:
        """Get default permissions for a role type.

        Args:
            role_type: The role type.

        Returns:
            Dictionary of permissions.
        """
        # Define permission sets for each role
        permissions = {
            RoleType.HR_ADMIN: {
                "employees": ["create", "read", "update", "delete"],
                "documents": ["create", "read", "update", "delete", "approve", "reject"],
                "roles": ["read", "assign"],
                "settings": ["read", "update"],
                "audit": ["read"],
                "reports": ["read", "export"],
            },
            RoleType.HR_MANAGER: {
                "employees": ["create", "read", "update"],
                "documents": ["create", "read", "update", "approve", "reject"],
                "roles": ["read"],
                "audit": ["read"],
                "reports": ["read"],
            },
            RoleType.LEGAL: {
                "employees": ["read"],
                "documents": ["read"],
                "legal_holds": ["create", "read", "update", "delete"],
                "audit": ["read", "export"],
                "reports": ["read", "export"],
            },
            RoleType.IT_ADMIN: {
                "integrations": ["create", "read", "update", "delete"],
                "settings": ["read", "update"],
                "audit": ["read"],
            },
            RoleType.AUDITOR: {
                "employees": ["read"],
                "documents": ["read"],
                "audit": ["read", "export"],
                "reports": ["read", "export"],
            },
            RoleType.EMPLOYEE: {
                "documents": ["create", "read"],  # Own documents only
                "profile": ["read", "update"],
            },
        }

        return permissions.get(role_type, {})

    def _row_to_response(self, row: Dict[str, Any]) -> RoleResponse:
        """Convert a database row to RoleResponse.

        Args:
            row: Dictionary from database query.

        Returns:
            RoleResponse object.
        """
        created_at = row.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = row.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        return RoleResponse(
            id=row["id"],
            org_id=row["org_id"],
            name=row["name"],
            role_type=RoleType(row["role_type"]),
            description=row.get("description"),
            permissions=row.get("permissions", {}),
            is_default=row.get("is_default", False),
            is_active=row.get("is_active", True),
            created_at=created_at,
            updated_at=updated_at,
        )


async def seed_default_roles(
    db: ZeroDBClient,
    org_id: str,
    actor_id: str = "system",
    actor_email: Optional[str] = None,
) -> SeedRolesResponse:
    """Convenience function to seed default roles for an organization.

    Args:
        db: ZeroDB client instance.
        org_id: The organization ID.
        actor_id: ID of the actor.
        actor_email: Optional email of the actor.

    Returns:
        SeedRolesResponse with created roles.
    """
    service = RoleService(db)
    return await service.seed_default_roles(org_id, actor_id, actor_email)
