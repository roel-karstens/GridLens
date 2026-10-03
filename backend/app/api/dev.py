"""Development-only endpoints for testing without Supabase Auth."""

import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies import get_db
from app.models.project import Project
from app.core.auth import get_current_user
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/api/v1/dev", tags=["dev"])

# Only enable in development
DEV_MODE = settings.environment == "development"


class TokenRequest(BaseModel):
    """Request to generate a dev token."""

    user_id: str


class TokenResponse(BaseModel):
    """Response with generated token."""

    token: str


class ProjectDebugInfo(BaseModel):
    """Debug info for a project."""
    
    id: str
    name: str
    owner_id: str
    created_at: str


class UserInfo(BaseModel):
    """Current user info."""
    
    user_id: str


class IngestionRequest(BaseModel):
    """Request to ingest electricity data."""
    
    country_code: str
    days: int = 1  # ENTSO-E A16 (intraday generation) limited to 1-day windows


class IngestionResponse(BaseModel):
    """Response from ingestion."""
    
    country_code: str
    created: int
    duplicate: int
    failed: int
    message: str


@router.post("/token", response_model=TokenResponse)
async def generate_dev_token(request: TokenRequest) -> TokenResponse:
    """
    Generate a test JWT token for development.

    Only available in development mode.
    """
    if not DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev endpoints only available in development mode",
        )

    try:
        # Create JWT payload
        now = datetime.now(timezone.utc)
        payload = {
            "sub": request.user_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=24)).timestamp()),
            "dev_mode": True,
        }

        # Create token with a test key
        token = jwt.encode(
            payload,
            key="test-secret-key",
            algorithm="HS256",
        )

        return TokenResponse(token=token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate token: {str(e)}",
        )


@router.get("/debug/projects", response_model=list[ProjectDebugInfo])
async def debug_all_projects(db: Session = Depends(get_db)) -> list[ProjectDebugInfo]:
    """
    DEBUG ENDPOINT: Show all projects with owner_ids (no filtering).
    
    Only available in development mode.
    """
    if not DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev endpoints only available in development mode",
        )
    
    projects = db.query(Project).all()
    return [
        ProjectDebugInfo(
            id=str(project.id),
            name=project.name,
            owner_id=str(project.owner_id),
            created_at=project.created_at.isoformat() if project.created_at else "N/A",
        )
        for project in projects
    ]


@router.get("/debug/me", response_model=UserInfo)
async def debug_current_user(user_id: str = Depends(get_current_user)) -> UserInfo:
    """
    DEBUG ENDPOINT: Get current authenticated user's ID.
    
    Only available in development mode.
    """
    if not DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev endpoints only available in development mode",
        )
    
    return UserInfo(user_id=user_id)


@router.post("/ingest", response_model=IngestionResponse)
async def dev_ingest_data(
    request: IngestionRequest,
    db: Session = Depends(get_db),
) -> IngestionResponse:
    """
    DEV ENDPOINT: Ingest electricity data from ENTSO-E.
    
    Only available in development mode.
    
    Args:
        request: IngestionRequest with country_code and days
        db: Database session
        
    Returns:
        IngestionResponse with count of ingested records
    """
    if not DEV_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev endpoints only available in development mode",
        )
    
    try:
        service = IngestionService(db)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=request.days)
        
        result = await service.ingest_country_data(
            request.country_code,
            start_time,
            end_time,
        )
        
        return IngestionResponse(
            country_code=request.country_code,
            created=result.get("created", 0),
            duplicate=result.get("duplicate", 0),
            failed=result.get("failed", 0),
            message=f"Successfully ingested data for {request.country_code}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {str(e)}",
        )

