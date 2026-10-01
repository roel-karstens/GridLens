"""Unit tests for Phase 2: Models and Schemas."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from pydantic import ValidationError

from app.models.electricity import ElectricityObservation
from app.schemas.electricity import (
    ElectricityObservationCreate,
    ElectricityObservationRead,
    CurrentStatusResponse,
    GenerationMixResponse,
    HistoricalDataResponse,
)


# ============================================================================
# Unit Tests: ElectricityObservation Model
# ============================================================================


class TestElectricityObservationModel:
    """Test SQLAlchemy ElectricityObservation model."""

    def test_model_instantiation(self, mock_observation_data):
        """✓ Model can be instantiated with valid data."""
        obs = ElectricityObservation(**mock_observation_data)
        assert obs.country_code == "NL"
        assert obs.metric == "load"
        assert obs.value_mw == Decimal("12456.50")
        assert obs.unit == "MW"
        assert obs.source == "ENTSO-E"

    def test_model_timestamps(self, mock_observation_data):
        """✓ Model correctly stores UTC timestamps."""
        obs = ElectricityObservation(**mock_observation_data)
        assert obs.timestamp is not None
        assert obs.source_timestamp is not None
        assert isinstance(obs.timestamp, datetime)

    def test_model_defaults(self, mock_observation_data):
        """✓ Model has correct default values."""
        # Remove optional fields
        data = {k: v for k, v in mock_observation_data.items() if k != "source_timestamp"}
        obs = ElectricityObservation(**data)
        assert obs.unit == "MW"
        assert obs.source == "ENTSO-E"
        assert obs.source_timestamp is None

    def test_model_repr(self, mock_observation_data):
        """✓ Model has useful string representation."""
        obs = ElectricityObservation(**mock_observation_data)
        repr_str = repr(obs)
        assert "ElectricityObservation" in repr_str
        assert "NL" in repr_str
        assert "load" in repr_str


# ============================================================================
# Unit Tests: Pydantic Schemas
# ============================================================================


class TestElectricityObservationCreateSchema:
    """Test ElectricityObservationCreate schema validation."""

    def test_valid_observation(self, mock_observation_data):
        """✓ Schema accepts valid observation data."""
        obs = ElectricityObservationCreate(**mock_observation_data)
        assert obs.country_code == "NL"
        assert obs.metric == "load"
        assert obs.value_mw == Decimal("12456.50")

    def test_required_fields(self):
        """✓ Schema enforces required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ElectricityObservationCreate(
                country_code="NL",
                # Missing: timestamp, metric, value_mw, source_dataset
            )
        assert "timestamp" in str(exc_info.value)

    def test_country_code_validation(self):
        """✓ Schema validates country_code length."""
        # Valid 2-letter code
        obs = ElectricityObservationCreate(
            country_code="NL",
            timestamp=datetime.utcnow(),
            metric="load",
            value_mw=Decimal("1000"),
            source_dataset="Actual Total Load",
        )
        assert obs.country_code == "NL"

        # Invalid: too long
        with pytest.raises(ValidationError):
            ElectricityObservationCreate(
                country_code="NLD",  # 3 letters
                timestamp=datetime.utcnow(),
                metric="load",
                value_mw=Decimal("1000"),
                source_dataset="Actual Total Load",
            )

    def test_value_mw_non_negative(self):
        """✓ Schema validates value_mw is non-negative."""
        # Valid: positive value
        obs = ElectricityObservationCreate(
            country_code="NL",
            timestamp=datetime.utcnow(),
            metric="load",
            value_mw=Decimal("1000"),
            source_dataset="Actual Total Load",
        )
        assert obs.value_mw == Decimal("1000")

        # Invalid: negative value
        with pytest.raises(ValidationError):
            ElectricityObservationCreate(
                country_code="NL",
                timestamp=datetime.utcnow(),
                metric="load",
                value_mw=Decimal("-100"),  # Negative not allowed
                source_dataset="Actual Total Load",
            )

    def test_default_values(self):
        """✓ Schema applies default values."""
        obs = ElectricityObservationCreate(
            country_code="NL",
            timestamp=datetime.utcnow(),
            metric="load",
            value_mw=Decimal("1000"),
            source_dataset="Actual Total Load",
        )
        assert obs.unit == "MW"
        assert obs.source == "ENTSO-E"
        assert obs.source_timestamp is None


class TestElectricityObservationReadSchema:
    """Test ElectricityObservationRead schema (API response)."""

    def test_valid_read_response(self):
        """✓ Schema accepts valid API response data."""
        now = datetime.utcnow()
        obs = ElectricityObservationRead(
            id=str(uuid4()),
            country_code="NL",
            timestamp=now,
            metric="load",
            value_mw=Decimal("12456.50"),
            unit="MW",
            source="ENTSO-E",
            source_dataset="Actual Total Load",
            source_timestamp=now,
            created_at=now,
        )
        assert obs.id is not None
        assert obs.created_at == now

    def test_read_schema_from_orm(self, mock_observation_data):
        """✓ Schema can be created from ORM model (from_attributes=True)."""
        # Create a model instance
        model = ElectricityObservation(**mock_observation_data)
        model.id = str(uuid4())
        model.created_at = datetime.utcnow()

        # Convert to schema (simulating from_orm)
        read_data = {
            "id": model.id,
            "country_code": model.country_code,
            "timestamp": model.timestamp,
            "metric": model.metric,
            "value_mw": model.value_mw,
            "unit": model.unit,
            "source": model.source,
            "source_dataset": model.source_dataset,
            "source_timestamp": model.source_timestamp,
            "created_at": model.created_at,
        }
        obs = ElectricityObservationRead(**read_data)
        assert obs.country_code == "NL"


class TestCurrentStatusResponseSchema:
    """Test CurrentStatusResponse schema."""

    def test_valid_current_status(self, current_status_response):
        """✓ CurrentStatusResponse accepts valid data."""
        assert current_status_response.country_code == "NL"
        assert current_status_response.load_mw == Decimal("12456.50")
        assert current_status_response.renewable_share_percent == Decimal("52.5")

    def test_nullable_metrics(self):
        """✓ Individual metrics can be None."""
        now = datetime.utcnow()
        resp = CurrentStatusResponse(
            country_code="NL",
            timestamp=now,
            load_mw=Decimal("12000"),
            total_generation_mw=None,  # Can be None if data missing
            renewable_generation_mw=None,
            renewable_share_percent=None,
            last_updated=now,
        )
        assert resp.total_generation_mw is None
        assert resp.renewable_generation_mw is None


class TestGenerationMixResponseSchema:
    """Test GenerationMixResponse schema."""

    def test_valid_generation_mix(self, generation_mix_response):
        """✓ GenerationMixResponse accepts valid data."""
        assert generation_mix_response.country_code == "NL"
        assert generation_mix_response.total_generation_mw == Decimal("18234.75")
        assert "solar" in generation_mix_response.generation_by_type
        assert generation_mix_response.generation_by_type["solar"] == Decimal("1234.25")

    def test_missing_technologies(self):
        """✓ Technologies can be missing (None) if not available."""
        now = datetime.utcnow()
        resp = GenerationMixResponse(
            country_code="NL",
            timestamp=now,
            generation_by_type={
                "solar": Decimal("1000"),
                "wind_onshore": None,  # Missing in this country
                "nuclear": Decimal("3000"),
            },
            total_generation_mw=Decimal("4000"),
            source="ENTSO-E",
        )
        assert resp.generation_by_type["wind_onshore"] is None


class TestHistoricalDataResponseSchema:
    """Test HistoricalDataResponse schema."""

    def test_valid_historical_data(self, multiple_observations):
        """✓ HistoricalDataResponse accepts valid time series data."""
        observations = [
            ElectricityObservationRead(
                id=str(uuid4()),
                created_at=datetime.utcnow(),
                **obs,
            )
            for obs in multiple_observations
        ]

        resp = HistoricalDataResponse(
            country_code="NL",
            metric="load",
            start_time=multiple_observations[0]["timestamp"],
            end_time=multiple_observations[-1]["timestamp"],
            observations=observations,
            count=len(observations),
        )
        assert resp.count == 24
        assert len(resp.observations) == 24

    def test_count_matches_observations(self):
        """✓ Count field matches number of observations."""
        now = datetime.utcnow()
        observations = [
            ElectricityObservationRead(
                id=str(uuid4()),
                country_code="NL",
                timestamp=now,
                metric="load",
                value_mw=Decimal("1000"),
                unit="MW",
                source="ENTSO-E",
                source_dataset="Test",
                created_at=now,
            )
        ]
        resp = HistoricalDataResponse(
            country_code="NL",
            metric="load",
            start_time=now,
            end_time=now,
            observations=observations,
            count=1,
        )
        assert resp.count == len(resp.observations)


# ============================================================================
# Integration: Schema ↔ Model
# ============================================================================


class TestSchemaModelIntegration:
    """Test that schemas and models work together."""

    def test_create_to_model(self, mock_observation_data):
        """✓ Can create model from CreateSchema."""
        create_schema = ElectricityObservationCreate(**mock_observation_data)
        model = ElectricityObservation(**create_schema.model_dump())
        assert model.country_code == create_schema.country_code
        assert model.metric == create_schema.metric

    def test_model_to_read_schema(self, mock_observation_data):
        """✓ Can convert model to ReadSchema."""
        model = ElectricityObservation(**mock_observation_data)
        model.id = str(uuid4())
        model.created_at = datetime.utcnow()

        read_data = {
            "id": model.id,
            "country_code": model.country_code,
            "timestamp": model.timestamp,
            "metric": model.metric,
            "value_mw": model.value_mw,
            "unit": model.unit,
            "source": model.source,
            "source_dataset": model.source_dataset,
            "source_timestamp": model.source_timestamp,
            "created_at": model.created_at,
        }
        read_schema = ElectricityObservationRead(**read_data)
        assert read_schema.country_code == model.country_code
