"""ENTSO-E API response type definitions."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class LoadObservation:
    """Raw load (demand) observation from ENTSO-E."""

    timestamp: datetime  # UTC
    value_mw: float
    source_timestamp: datetime | None = None


@dataclass
class GenerationObservation:
    """Raw generation observation from ENTSO-E."""

    timestamp: datetime  # UTC
    technology: str  # ENTSO-E psrType code (e.g., "B16" for solar)
    value_mw: float
    source_timestamp: datetime | None = None


@dataclass
class ParsedObservation:
    """Normalized observation after parsing and validation."""

    country_code: str
    timestamp: datetime  # UTC
    metric: str  # Normalized metric (e.g., "solar", "wind_onshore", "load")
    value_mw: float
    unit: str = "MW"
    source: str = "ENTSO-E"
    source_dataset: str = ""
    source_timestamp: datetime | None = None
