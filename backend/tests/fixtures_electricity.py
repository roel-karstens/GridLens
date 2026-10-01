"""Test fixtures for electricity domain (Phase 2 validation)."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.electricity import ElectricityObservation
from app.schemas.electricity import (
    ElectricityObservationCreate,
    ElectricityObservationRead,
    CurrentStatusResponse,
    GenerationMixResponse,
)


# ============================================================================
# Mock Data Fixtures
# ============================================================================


@pytest.fixture
def mock_observation_data():
    """Sample electricity observation data."""
    return {
        "country_code": "NL",
        "timestamp": datetime.utcnow().replace(microsecond=0),
        "metric": "load",
        "value_mw": Decimal("12456.50"),
        "unit": "MW",
        "source": "ENTSO-E",
        "source_dataset": "Actual Total Load",
        "source_timestamp": datetime.utcnow().replace(microsecond=0) - timedelta(minutes=15),
    }


@pytest.fixture
def mock_solar_data():
    """Sample solar generation data."""
    return {
        "country_code": "NL",
        "timestamp": datetime.utcnow().replace(microsecond=0),
        "metric": "solar",
        "value_mw": Decimal("1234.25"),
        "unit": "MW",
        "source": "ENTSO-E",
        "source_dataset": "Aggregated Generation Per Type",
        "source_timestamp": datetime.utcnow().replace(microsecond=0) - timedelta(minutes=15),
    }


@pytest.fixture
def mock_wind_data():
    """Sample wind onshore data."""
    return {
        "country_code": "DE",
        "timestamp": datetime.utcnow().replace(microsecond=0),
        "metric": "wind_onshore",
        "value_mw": Decimal("5678.75"),
        "unit": "MW",
        "source": "ENTSO-E",
        "source_dataset": "Aggregated Generation Per Type",
        "source_timestamp": datetime.utcnow().replace(microsecond=0) - timedelta(minutes=15),
    }


@pytest.fixture
def multiple_observations():
    """Multiple time-series observations for history tests."""
    base_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return [
        {
            "country_code": "NL",
            "timestamp": base_time - timedelta(hours=i),
            "metric": "load",
            "value_mw": Decimal(str(10000 + i * 100)),
            "unit": "MW",
            "source": "ENTSO-E",
            "source_dataset": "Actual Total Load",
        }
        for i in range(24)
    ]


# ============================================================================
# Schema Fixtures
# ============================================================================


@pytest.fixture
def observation_create_schema(mock_observation_data):
    """Create schema instance."""
    return ElectricityObservationCreate(**mock_observation_data)


@pytest.fixture
def observation_read_schema(mock_observation_data):
    """Read schema instance."""
    data = {
        "id": str(uuid4()),
        "created_at": datetime.utcnow(),
        **mock_observation_data,
    }
    return ElectricityObservationRead(**data)


# ============================================================================
# Model Fixtures
# ============================================================================


@pytest.fixture
def electricity_observation_model(mock_observation_data):
    """Create a model instance (without DB)."""
    return ElectricityObservation(**mock_observation_data)


# ============================================================================
# Response Fixtures
# ============================================================================


@pytest.fixture
def current_status_response():
    """Sample current status response."""
    now = datetime.utcnow()
    return CurrentStatusResponse(
        country_code="NL",
        timestamp=now,
        load_mw=Decimal("12456.50"),
        total_generation_mw=Decimal("18234.75"),
        renewable_generation_mw=Decimal("9567.25"),
        renewable_share_percent=Decimal("52.5"),
        solar_mw=Decimal("1234.25"),
        wind_onshore_mw=Decimal("5678.50"),
        wind_offshore_mw=Decimal("1234.75"),
        nuclear_mw=Decimal("3200.00"),
        gas_mw=Decimal("4850.25"),
        coal_mw=Decimal("1200.00"),
        hydro_mw=Decimal("1100.00"),
        biomass_mw=Decimal("70.00"),
        other_mw=Decimal("335.00"),
        source="ENTSO-E",
        last_updated=now,
    )


@pytest.fixture
def generation_mix_response():
    """Sample generation mix response."""
    now = datetime.utcnow()
    return GenerationMixResponse(
        country_code="NL",
        timestamp=now,
        generation_by_type={
            "solar": Decimal("1234.25"),
            "wind_onshore": Decimal("5678.50"),
            "wind_offshore": Decimal("1234.75"),
            "nuclear": Decimal("3200.00"),
            "gas": Decimal("4850.25"),
            "coal": Decimal("1200.00"),
            "hydro": Decimal("1100.00"),
            "biomass": Decimal("70.00"),
            "other": Decimal("335.00"),
        },
        total_generation_mw=Decimal("18234.75"),
        source="ENTSO-E",
    )
