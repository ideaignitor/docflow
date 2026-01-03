"""Role model for RBAC in DocFlow HR.

Roles are scoped to organizations and define permissions for users.
Default roles are seeded automatically when an organization is created.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import Field

from app.models.base import ZeroDBBaseModel, TimestampMixin, ZeroDBTableSchema
from app.models.enums import RoleType


class Role(ZeroDBBaseModel, TimestampMixin):
    """Role entity for organization-scoped RBAC.

    Roles define what actions a user can perform within an organization.
    Each organization has its own set of roles, seeded from defaults.

    COMPLIANCE NOTE: Role changes must be audited. Users should only
    have the minimum roles necessary for their job function.
    """

    id: UUID = Field(
        description="Unique role identifier (UUID)",
    )

    org_id: UUID = Field(
        description="Organization this role belongs to (tenant isolation)",
    )

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Role display name (e.g., 'HR Admin')",
    )

    role_type: RoleType = Field(
        description="Role type from predefined list",
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Role description explaining permissions",
    )

    permissions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Role permissions as JSON (resource -> actions)",
    )

    is_default: bool = Field(
        default=False,
        description="Whether this is a default system role (cannot be deleted)",
    )

    is_active: bool = Field(
        default=True,
        description="Whether this role is active",
    )

    @staticmethod
    def table_schema() -> ZeroDBTableSchema:
        """Get ZeroDB table schema for roles.

        Returns:
            Table schema definition for ZeroDB
        """
        return ZeroDBTableSchema(
            columns=[
                ZeroDBTableSchema.column_def(
                    "id", "uuid", primary_key=True, default="gen_random_uuid()"
                ),
                ZeroDBTableSchema.column_def(
                    "org_id", "uuid", nullable=False
                ),
                ZeroDBTableSchema.column_def(
                    "name", "text", nullable=False
                ),
                ZeroDBTableSchema.column_def(
                    "role_type", "text", nullable=False
                ),
                ZeroDBTableSchema.column_def(
                    "description", "text", nullable=True
                ),
                ZeroDBTableSchema.column_def(
                    "permissions", "jsonb", nullable=False, default="'{}'::jsonb"
                ),
                ZeroDBTableSchema.column_def(
                    "is_default", "boolean", nullable=False, default="true"
                ),
                ZeroDBTableSchema.column_def(
                    "is_active", "boolean", nullable=False, default="true"
                ),
                ZeroDBTableSchema.column_def(
                    "created_at", "timestamp", nullable=False, default="now()"
                ),
                ZeroDBTableSchema.column_def(
                    "updated_at", "timestamp", nullable=False, default="now()"
                ),
            ],
            indexes=[
                ZeroDBTableSchema.index_def(
                    "idx_roles_org_id", ["org_id"]
                ),
                ZeroDBTableSchema.index_def(
                    "idx_roles_org_type", ["org_id", "role_type"], unique=True
                ),
            ],
        )


# Role descriptions for default roles
ROLE_DESCRIPTIONS = {
    RoleType.HR_ADMIN: "Full HR operations access. Can manage employees, documents, and HR settings.",
    RoleType.HR_MANAGER: "Standard HR management. Can review documents and manage employee records.",
    RoleType.LEGAL: "Legal compliance access. Can create/manage legal holds and view audit logs.",
    RoleType.IT_ADMIN: "Technical administration. Can manage integrations and system settings.",
    RoleType.AUDITOR: "Read-only audit access. Can view audit logs and generate compliance reports.",
    RoleType.EMPLOYEE: "Self-service access. Can view and submit own documents.",
}

# Role display names
ROLE_DISPLAY_NAMES = {
    RoleType.HR_ADMIN: "HR Admin",
    RoleType.HR_MANAGER: "HR Manager",
    RoleType.LEGAL: "Legal",
    RoleType.IT_ADMIN: "IT Admin",
    RoleType.AUDITOR: "Auditor",
    RoleType.EMPLOYEE: "Employee",
}
