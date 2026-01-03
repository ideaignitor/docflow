"""Organization Service for DocFlow HR.

This module provides the core organization management functionality,
including creating, updating, and querying organizations with proper
multi-tenant isolation and audit logging.
"""

import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.db.zerodb_client import ZeroDBClient
from app.schemas.organizations import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationStatus,
)
from app.services.audit import emit_audit_event
from app.core.exceptions import ConflictError, NotFoundError

logger = logging.getLogger(__name__)

# Constants
ORGANIZATIONS_TABLE = "organizations"


class OrganizationService:
    """Service for managing organizations.

    This service provides methods for creating and managing organizations
    with proper multi-tenant isolation and audit logging.

    Attributes:
        db: ZeroDB client instance for database operations.
    """

    def __init__(self, db: ZeroDBClient) -> None:
        """Initialize the organization service.

        Args:
            db: ZeroDB client instance.
        """
        self.db = db

    def _generate_slug(self, name: str) -> str:
        """Generate a URL-safe slug from organization name.

        Args:
            name: The organization name.

        Returns:
            A lowercase, URL-safe slug.
        """
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        # Remove leading/trailing hyphens and consecutive hyphens
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug

    async def _is_slug_unique(self, slug: str) -> bool:
        """Check if a slug is unique.

        Args:
            slug: The slug to check.

        Returns:
            True if slug is unique, False otherwise.
        """
        existing = await self.db.table_query(
            ORGANIZATIONS_TABLE,
            filters={"slug": slug},
            limit=1,
        )
        return len(existing) == 0

    async def _generate_unique_slug(self, name: str) -> str:
        """Generate a unique slug, appending numbers if necessary.

        Args:
            name: The organization name.

        Returns:
            A unique, URL-safe slug.
        """
        base_slug = self._generate_slug(name)
        slug = base_slug
        counter = 1

        while not await self._is_slug_unique(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
            if counter > 100:  # Safety limit
                slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
                break

        return slug

    async def create_organization(
        self,
        data: OrganizationCreate,
        actor_id: str,
        actor_email: Optional[str] = None,
    ) -> OrganizationResponse:
        """Create a new organization.

        Creates an organization with a unique slug, proper tenant isolation,
        and emits an audit event.

        Args:
            data: Organization creation data.
            actor_id: ID of the user creating the organization.
            actor_email: Optional email of the actor.

        Returns:
            The created OrganizationResponse.

        Raises:
            ConflictError: If slug already exists and was explicitly provided.
        """
        org_id = str(uuid.uuid4())
        created_at = datetime.utcnow()

        # Generate or validate slug
        if data.slug:
            # User provided a slug, check uniqueness
            if not await self._is_slug_unique(data.slug):
                raise ConflictError(
                    message=f"Organization slug '{data.slug}' already exists"
                )
            slug = data.slug
        else:
            # Auto-generate unique slug from name
            slug = await self._generate_unique_slug(data.name)

        # Prepare organization data
        org_data = {
            "id": org_id,
            "name": data.name,
            "slug": slug,
            "domain": data.domain,
            "admin_email": data.admin_email,
            "status": OrganizationStatus.ACTIVE.value,
            "settings": data.settings or {},
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
        }

        logger.info(f"Creating organization: {data.name} with slug: {slug}")

        # Insert into database
        await self.db.table_insert(ORGANIZATIONS_TABLE, [org_data])

        # Emit audit event
        await emit_audit_event(
            db=self.db,
            entity_type="organization",
            entity_id=org_id,
            action="organization.created",
            actor_id=actor_id,
            org_id=org_id,  # Org is its own scope
            actor_email=actor_email,
            metadata={
                "name": data.name,
                "slug": slug,
                "admin_email": data.admin_email,
            },
        )

        logger.info(f"Organization created successfully: {org_id}")

        return OrganizationResponse(
            id=org_id,
            name=data.name,
            slug=slug,
            domain=data.domain,
            admin_email=data.admin_email,
            status=OrganizationStatus.ACTIVE,
            settings=data.settings or {},
            created_at=created_at,
            updated_at=created_at,
        )

    async def get_organization_by_id(self, org_id: str) -> OrganizationResponse:
        """Get an organization by ID.

        Args:
            org_id: The organization ID.

        Returns:
            The OrganizationResponse.

        Raises:
            NotFoundError: If organization not found.
        """
        rows = await self.db.table_query(
            ORGANIZATIONS_TABLE,
            filters={"id": org_id},
            limit=1,
        )

        if not rows:
            raise NotFoundError(message=f"Organization not found: {org_id}")

        return self._row_to_response(rows[0])

    async def get_organization_by_slug(self, slug: str) -> OrganizationResponse:
        """Get an organization by slug.

        Args:
            slug: The organization slug.

        Returns:
            The OrganizationResponse.

        Raises:
            NotFoundError: If organization not found.
        """
        rows = await self.db.table_query(
            ORGANIZATIONS_TABLE,
            filters={"slug": slug},
            limit=1,
        )

        if not rows:
            raise NotFoundError(message=f"Organization not found: {slug}")

        return self._row_to_response(rows[0])

    def _row_to_response(self, row: Dict[str, Any]) -> OrganizationResponse:
        """Convert a database row to OrganizationResponse.

        Args:
            row: Dictionary from database query.

        Returns:
            OrganizationResponse object.
        """
        created_at = row.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = row.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        return OrganizationResponse(
            id=row["id"],
            name=row["name"],
            slug=row["slug"],
            domain=row.get("domain"),
            admin_email=row["admin_email"],
            status=OrganizationStatus(row.get("status", "active")),
            settings=row.get("settings", {}),
            created_at=created_at,
            updated_at=updated_at,
        )


async def create_organization(
    db: ZeroDBClient,
    data: OrganizationCreate,
    actor_id: str,
    actor_email: Optional[str] = None,
) -> OrganizationResponse:
    """Convenience function to create an organization.

    Args:
        db: ZeroDB client instance.
        data: Organization creation data.
        actor_id: ID of the user creating the organization.
        actor_email: Optional email of the actor.

    Returns:
        The created OrganizationResponse.
    """
    service = OrganizationService(db)
    return await service.create_organization(data, actor_id, actor_email)
