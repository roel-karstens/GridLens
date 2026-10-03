"""Pydantic schemas for electricity API endpoints."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_serializer


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
    
    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})

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
    
    @field_serializer('value_mw')
    def serialize_decimal(self, value: Decimal) -> float:
        """Serialize Decimal to float for JSON compatibility."""
        return float(value)


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
    
    model_config = ConfigDict(json_encoders={Decimal: float})

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
    
    @field_serializer('load_mw', 'total_generation_mw', 'renewable_generation_mw', 
                      'renewable_share_percent', 'solar_mw', 'wind_onshore_mw', 
                      'wind_offshore_mw', 'nuclear_mw', 'gas_mw', 'coal_mw', 
                      'hydro_mw', 'biomass_mw', 'other_mw')
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Serialize Decimal to float for JSON compatibility."""
        return float(value) if value is not None else None


class HistoricalDataResponse(BaseModel):
    """Schema for historical electricity data query.
    
    Returns time series data for charting.
    """
    
    model_config = ConfigDict(json_encoders={Decimal: float})

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
    
    model_config = ConfigDict(json_encoders={Decimal: float})

    metric: str = Field(..., description="Electricity metric being compared")
    timestamp: datetime = Field(..., description="Timestamp of observations")
    countries: dict[str, Decimal | None] = Field(..., description="Country code -> value mapping")
    
    @field_serializer('countries')
    def serialize_countries(self, value: dict[str, Decimal | None]) -> dict[str, float | None]:
        """Serialize Decimal values to float for JSON compatibility."""
        return {k: float(v) if v is not None else None for k, v in value.items()}


class GenerationMixResponse(BaseModel):
    """Schema for generation mix breakdown.
    
    Returns current generation by technology type.
    """
    
    model_config = ConfigDict(json_encoders={Decimal: float})

    country_code: str = Field(..., description="ISO 2-letter country code")
    timestamp: datetime = Field(..., description="Timestamp of observations")
    
    generation_by_type: dict[str, Decimal | None] = Field(
        ..., 
        description="Technology -> MW value mapping (solar, wind_onshore, wind_offshore, etc.)"
    )
    total_generation_mw: Decimal = Field(..., description="Sum of all generation types")
    source: str = Field(default="ENTSO-E", description="Data source")
    
    @field_serializer('generation_by_type')
    def serialize_generation_by_type(self, value: dict[str, Decimal | None]) -> dict[str, float | None]:
        """Serialize Decimal values to float for JSON compatibility."""
        return {k: float(v) if v is not None else None for k, v in value.items()}
    
    @field_serializer('total_generation_mw')
    def serialize_total_generation(self, value: Decimal) -> float:
        """Serialize Decimal to float for JSON compatibility."""
        return float(value)
