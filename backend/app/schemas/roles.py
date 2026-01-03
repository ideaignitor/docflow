"""Pydantic schemas for role management."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import RoleType


class RoleBase(BaseModel):
    """Base schema for role data."""

    name: str = Field(..., min_length=1, max_length=100, description="Role display name")
    role_type: RoleType = Field(..., description="Role type")
    description: Optional[str] = Field(default=None, max_length=500, description="Role description")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="Role permissions")


class RoleCreate(RoleBase):
    """Schema for creating a new role."""

    pass


class RoleResponse(RoleBase):
    """Schema for role response."""

    id: str = Field(..., description="Role unique identifier")
    org_id: str = Field(..., description="Organization ID")
    is_default: bool = Field(..., description="Whether this is a default role")
    is_active: bool = Field(..., description="Whether this role is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class RoleListResponse(BaseModel):
    """Schema for role list response."""

    roles: List[RoleResponse] = Field(..., description="List of roles")
    total: int = Field(..., description="Total number of roles")


class SeedRolesResponse(BaseModel):
    """Schema for seed roles response."""

    org_id: str = Field(..., description="Organization ID")
    roles_created: int = Field(..., description="Number of roles created")
    roles: List[RoleResponse] = Field(..., description="Created roles")
