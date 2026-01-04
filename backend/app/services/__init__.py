"""Business logic services for DocFlow HR."""

from app.services.audit import (
    AuditService,
    emit_audit_event,
    emit_document_received,
    emit_document_version_created,
    emit_document_review_approved,
    emit_document_review_rejected,
    emit_employee_created,
    emit_employee_updated,
    emit_legal_hold_created,
    emit_legal_hold_released,
)
from app.services.auth import (
    AuthService,
    request_magic_link,
    verify_magic_link,
    refresh_access_token,
    get_current_user,
)
from app.services.document import (
    DocumentService,
    create_document,
    get_document,
    get_expiring_documents,
)
from app.services.organization import (
    OrganizationService,
    create_organization,
)
from app.services.retention import RetentionService
from app.services.role import (
    RoleService,
    seed_default_roles,
)
from app.services.user import (
    UserService,
    invite_user,
)

__all__ = [
    # Audit Service
    "AuditService",
    "emit_audit_event",
    "emit_document_received",
    "emit_document_version_created",
    "emit_document_review_approved",
    "emit_document_review_rejected",
    "emit_employee_created",
    "emit_employee_updated",
    "emit_legal_hold_created",
    "emit_legal_hold_released",
    # Auth Service
    "AuthService",
    "request_magic_link",
    "verify_magic_link",
    "refresh_access_token",
    "get_current_user",
    # Document Service
    "DocumentService",
    "create_document",
    "get_document",
    "get_expiring_documents",
    # Organization Service
    "OrganizationService",
    "create_organization",
    # Retention Service
    "RetentionService",
    # Role Service
    "RoleService",
    "seed_default_roles",
    # User Service
    "UserService",
    "invite_user",
]
