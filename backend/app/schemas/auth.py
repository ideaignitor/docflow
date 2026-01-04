"""Pydantic schemas for authentication."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr

from app.schemas.users import UserRole, UserStatus


class MagicLinkRequest(BaseModel):
    """Schema for requesting a magic link."""

    email: EmailStr = Field(
        ...,
        description="Email address to send magic link to"
    )


class MagicLinkResponse(BaseModel):
    """Schema for magic link request response."""

    message: str = Field(
        default="If an account exists, a magic link has been sent",
        description="Response message"
    )
    email: str = Field(..., description="Email address")
    expires_in_minutes: int = Field(
        default=15,
        description="Token expiration in minutes"
    )


class TokenVerifyRequest(BaseModel):
    """Schema for verifying a magic link token."""

    token: str = Field(
        ...,
        min_length=32,
        description="Magic link token to verify"
    )


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class AuthResponse(BaseModel):
    """Schema for authentication response with user info."""

    user: "UserAuthInfo" = Field(..., description="Authenticated user info")
    tokens: TokenResponse = Field(..., description="JWT tokens")


class UserAuthInfo(BaseModel):
    """Schema for authenticated user info."""

    id: str = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="User status")
    org_id: str = Field(..., description="Organization identifier")

    model_config = {"from_attributes": True}


class CurrentUserResponse(BaseModel):
    """Schema for current user response."""

    id: str = Field(..., description="User unique identifier")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = Field(default=None, description="First name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    role: UserRole = Field(..., description="User role")
    status: UserStatus = Field(..., description="User status")
    org_id: str = Field(..., description="Organization identifier")
    org_name: Optional[str] = Field(default=None, description="Organization name")
    permissions: list[str] = Field(default=[], description="User permissions")
    last_login_at: Optional[datetime] = Field(default=None, description="Last login")

    model_config = {"from_attributes": True}


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing access token."""

    refresh_token: str = Field(..., description="Refresh token")


# Update forward reference
AuthResponse.model_rebuild()
