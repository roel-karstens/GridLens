"""Pydantic schemas for electricity API endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ElectricityObservationCreate(BaseModel):
    """Schema for creating electricity observations (ingestion only).
    
    Used internally during data ingestion from ENTSO-E.
    """

    country_code: str = Field(..., min_length=2, max_length=2, description="ISO 2-letter country code")
    timestamp: datetime = Field(..., description="UTC timestamp of observation")
    metric: str = Field(..., description="Electricity metric (load, solar, wind_onshore, etc.)")
    value_mw: Decimal = Field(..., ge=0, description="Value in megawatts")
    unit: str = Field(default="MW", description="Unit of measurement")
    source: str = Field(default="ENTSO-E", description="Data source")
    source_dataset: str = Field(..., description="ENTSO-E dataset type")
    source_timestamp: datetime | None = Field(None, description="When ENTSO-E generated this data")


class ElectricityObservationRead(BaseModel):
    """Schema for reading electricity observations (API response)."""

    id: str = Field(..., description="Unique observation ID")
    country_code: str = Field(..., description="ISO 2-letter country code")
    timestamp: datetime = Field(..., description="UTC timestamp of observation")
    metric: str = Field(..., description="Electricity metric")
    value_mw: Decimal = Field(..., description="Value in megawatts")
    unit: str = Field(..., description="Unit of measurement")
    source: str = Field(..., description="Data source")
    source_dataset: str = Field(..., description="Dataset type")
    source_timestamp: datetime | None = Field(None, description="When ENTSO-E generated this data")
    created_at: datetime = Field(..., description="When we ingested this observation")

    class Config:
        """Pydantic config for SQLAlchemy compatibility."""
        from_attributes = True


class CurrentMetricResponse(BaseModel):
    """Schema for current electricity metric (latest observation).
    
    Used in dashboard widgets showing current demand/generation.
    """

    country_code: str = Field(..., description="ISO 2-letter country code")
    metric: str = Field(..., description="Electricity metric")
    value_mw: Decimal = Field(..., description="Current value in megawatts")
    timestamp: datetime = Field(..., description="Timestamp of this observation")
    unit: str = Field(default="MW", description="Unit of measurement")


class CurrentStatusResponse(BaseModel):
    """Schema for current electricity status of a country.
    
    Aggregates multiple metrics for dashboard display.
    """

    country_code: str = Field(..., description="ISO 2-letter country code")
    timestamp: datetime = Field(..., description="Timestamp of observations")
    
    # Current metrics
    load_mw: Decimal | None = Field(None, description="Current demand in MW")
    total_generation_mw: Decimal | None = Field(None, description="Total generation in MW")
    renewable_generation_mw: Decimal | None = Field(None, description="Renewable generation in MW")
    renewable_share_percent: Decimal | None = Field(None, description="Renewable share as percentage")
    
    # Generation breakdown
    solar_mw: Decimal | None = None
    wind_onshore_mw: Decimal | None = None
    wind_offshore_mw: Decimal | None = None
    nuclear_mw: Decimal | None = None
    gas_mw: Decimal | None = None
    coal_mw: Decimal | None = None
    hydro_mw: Decimal | None = None
    biomass_mw: Decimal | None = None
    other_mw: Decimal | None = None
    
    # Metadata
    source: str = Field(default="ENTSO-E", description="Data source")
    last_updated: datetime = Field(..., description="When this data was last updated")


class HistoricalDataResponse(BaseModel):
    """Schema for historical electricity data query.
    
    Returns time series data for charting.
    """

    country_code: str = Field(..., description="ISO 2-letter country code")
    metric: str = Field(..., description="Electricity metric")
    start_time: datetime = Field(..., description="Start of requested time range")
    end_time: datetime = Field(..., description="End of requested time range")
    observations: list[ElectricityObservationRead] = Field(..., description="Time series observations")
    count: int = Field(..., description="Number of observations returned")


class ComparisonDataResponse(BaseModel):
    """Schema for multi-country comparison data.
    
    Returns data for comparison table/chart.
    """

    metric: str = Field(..., description="Electricity metric being compared")
    timestamp: datetime = Field(..., description="Timestamp of observations")
    countries: dict[str, Decimal | None] = Field(..., description="Country code -> value mapping")


class GenerationMixResponse(BaseModel):
    """Schema for generation mix breakdown.
    
    Returns current generation by technology type.
    """

    country_code: str = Field(..., description="ISO 2-letter country code")
    timestamp: datetime = Field(..., description="Timestamp of observations")
    
    generation_by_type: dict[str, Decimal | None] = Field(
        ..., 
        description="Technology -> MW value mapping (solar, wind_onshore, wind_offshore, etc.)"
    )
    total_generation_mw: Decimal = Field(..., description="Sum of all generation types")
    source: str = Field(default="ENTSO-E", description="Data source")
