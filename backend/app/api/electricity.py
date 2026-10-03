"""Electricity API endpoints."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.dependencies import get_db
from app.integrations.entsoe.constants import COUNTRIES
from app.schemas.electricity import (
    CurrentStatusResponse,
    GenerationMixResponse,
    HistoricalDataResponse,
    ComparisonDataResponse,
)
from app.services.electricity import ElectricityService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/electricity", tags=["electricity"])


@router.get("/countries", response_model=list[dict])
async def list_countries() -> list[dict]:
    """Get list of supported countries.
    
    Returns:
        List of countries with code and name.
    """
    return [
        {"code": config.code, "name": config.name}
        for config in COUNTRIES.values()
    ]


@router.get("/current/{country_code}", response_model=CurrentStatusResponse)
async def get_current_status(
    country_code: str,
    db: Session = Depends(get_db),
) -> CurrentStatusResponse:
    """Get current electricity status for a country.
    
    Returns latest demand, generation by type, renewable %, etc.
    
    Args:
        country_code: ISO 2-letter country code (e.g., "NL")
        db: Database session
        
    Returns:
        CurrentStatusResponse with current metrics.
        
    Raises:
        404: If country is not supported.
    """
    if country_code not in COUNTRIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country '{country_code}' not supported",
        )
    
    service = ElectricityService(db)
    return service.get_current_status(country_code)


@router.get("/generation/{country_code}", response_model=GenerationMixResponse)
async def get_generation_mix(
    country_code: str,
    db: Session = Depends(get_db),
) -> GenerationMixResponse:
    """Get current generation mix (breakdown by technology type).
    
    Args:
        country_code: ISO 2-letter country code
        db: Database session
        
    Returns:
        GenerationMixResponse with generation by type.
        
    Raises:
        404: If country is not supported.
    """
    if country_code not in COUNTRIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country '{country_code}' not supported",
        )
    
    service = ElectricityService(db)
    return service.get_generation_mix(country_code)


@router.get("/history/{country_code}", response_model=HistoricalDataResponse)
async def get_history(
    country_code: str,
    metric: str = Query(..., description="Electricity metric (load, solar, wind_onshore, etc.)"),
    start: str | None = Query(None, description="Start time (ISO 8601, default: 24h ago)"),
    end: str | None = Query(None, description="End time (ISO 8601, default: now)"),
    db: Session = Depends(get_db),
) -> HistoricalDataResponse:
    """Get historical observations for a metric.
    
    Args:
        country_code: ISO 2-letter country code
        metric: Electricity metric
        start: Start time (ISO 8601 format, default: 24h ago)
        end: End time (ISO 8601 format, default: now)
        db: Database session
        
    Returns:
        HistoricalDataResponse with time series data.
        
    Raises:
        404: If country is not supported.
        422: If date range is invalid.
    """
    if country_code not in COUNTRIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country '{country_code}' not supported",
        )
    
    # Parse dates
    try:
        end_time = datetime.fromisoformat(end) if end else datetime.utcnow()
        start_time = datetime.fromisoformat(start) if start else (end_time - timedelta(hours=24))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid date format: {str(e)}",
        )
    
    # Validate range
    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time must be before end_time",
        )
    
    max_range = timedelta(days=365)
    if (end_time - start_time) > max_range:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Date range too large (max {max_range.days} days)",
        )
    
    service = ElectricityService(db)
    return service.get_historical_data(country_code, metric, start_time, end_time)


@router.get("/compare", response_model=ComparisonDataResponse)
async def compare_countries(
    countries: str = Query(..., description="Comma-separated country codes (e.g., 'NL,DE,BE')"),
    metric: str = Query(..., description="Electricity metric"),
    db: Session = Depends(get_db),
) -> ComparisonDataResponse:
    """Compare a metric across multiple countries.
    
    Args:
        countries: Comma-separated country codes
        metric: Electricity metric
        db: Database session
        
    Returns:
        ComparisonDataResponse with values for each country.
        
    Raises:
        422: If any country is not supported or format is invalid.
    """
    # Parse countries
    country_list = [c.strip().upper() for c in countries.split(",")]
    
    # Validate
    invalid_countries = [c for c in country_list if c not in COUNTRIES]
    if invalid_countries:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported countries: {', '.join(invalid_countries)}",
        )
    
    service = ElectricityService(db)
    data = service.get_comparison_data(country_list, metric)
    
    return ComparisonDataResponse(
        metric=metric,
        timestamp=datetime.utcnow(),
        countries=data,
    )


@router.get("/status")
async def get_ingestion_status(
    user_id: str = Depends(get_current_user),
) -> dict:
    """Get ingestion status (last update, data freshness).
    
    Returns:
        Dictionary with ingestion metadata.
    """
    # Implementation stub - will check when data was last ingested
    raise NotImplementedError("Ingestion status endpoint not yet implemented")
