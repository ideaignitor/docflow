"""Main v1 API router for DocFlow HR."""

from fastapi import APIRouter

from app.config import settings
from app.api.routes.auth import router as auth_router
from app.api.routes.review import router as review_router
from app.api.routes.organizations import router as organizations_router
from app.api.routes.users import router as users_router


# Create v1 router
router = APIRouter(prefix="/v1")


@router.get("/")
async def v1_root():
    """V1 API root endpoint."""
    return {
        "message": "DocFlow HR API v1",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# Include routers
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(review_router, prefix="/review", tags=["Review Workflow"])
router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
router.include_router(users_router, prefix="/users", tags=["Users"])
