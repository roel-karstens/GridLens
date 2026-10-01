"""Integration tests for Phase 2: Database schema and RLS."""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import text, inspect

from app.models.electricity import ElectricityObservation
from app.dependencies import SessionLocal


# ============================================================================
# Database Schema Tests
# ============================================================================


class TestElectricityObservationTable:
    """Test electricity_observations table structure."""

    def test_table_exists(self):
        """✓ electricity_observations table is created."""
        db = SessionLocal()
        try:
            inspector = inspect(db.get_bind())
            tables = inspector.get_table_names()
            assert "electricity_observations" in tables
        finally:
            db.close()

    def test_table_columns(self):
        """✓ Table has all required columns."""
        db = SessionLocal()
        try:
            inspector = inspect(db.get_bind())
            columns = {col["name"]: col for col in inspector.get_columns("electricity_observations")}

            # Required columns
            assert "id" in columns
            assert "country_code" in columns
            assert "timestamp" in columns
            assert "metric" in columns
            assert "value_mw" in columns
            assert "unit" in columns
            assert "source" in columns
            assert "source_dataset" in columns
            assert "source_timestamp" in columns
            assert "created_at" in columns
            assert "updated_at" in columns
        finally:
            db.close()

    def test_column_types(self):
        """✓ Columns have correct data types."""
        db = SessionLocal()
        try:
            inspector = inspect(db.get_bind())
            columns = {col["name"]: col for col in inspector.get_columns("electricity_observations")}

            # Check key columns
            assert columns["id"]["type"].__class__.__name__ in ("String", "UUID")
            assert columns["country_code"]["type"].__class__.__name__ == "String"
            assert columns["timestamp"]["type"].__class__.__name__ == "DateTime"
            assert columns["value_mw"]["type"].__class__.__name__ == "Numeric"
        finally:
            db.close()

    def test_column_nullability(self):
        """✓ Columns have correct nullable settings."""
        db = SessionLocal()
        try:
            inspector = inspect(db.get_bind())
            columns = {col["name"]: col for col in inspector.get_columns("electricity_observations")}

            # Required (not nullable)
            assert not columns["country_code"]["nullable"]
            assert not columns["timestamp"]["nullable"]
            assert not columns["metric"]["nullable"]
            assert not columns["value_mw"]["nullable"]

            # Optional (nullable)
            assert columns["source_timestamp"]["nullable"]
        finally:
            db.close()


# ============================================================================
# Constraints Tests
# ============================================================================


class TestElectricityObservationConstraints:
    """Test uniqueness constraint and indexes."""

    def test_uniqueness_constraint_exists(self):
        """✓ UNIQUE constraint on (country_code, timestamp, metric)."""
        db = SessionLocal()
        try:
            inspector = inspect(db.get_bind())
            constraints = inspector.get_unique_constraints("electricity_observations")
            # At least one unique constraint should exist
            assert len(constraints) > 0
            # Check if it contains our expected columns
            found = False
            for constraint in constraints:
                if set(constraint["column_names"]) >= {"country_code", "timestamp", "metric"}:
                    found = True
                    break
            assert found, "Unique constraint on (country_code, timestamp, metric) not found"
        finally:
            db.close()

    def test_primary_key_exists(self):
        """✓ Primary key on id column."""
        db = SessionLocal()
        try:
            inspector = inspect(db.get_bind())
            pk = inspector.get_pk_constraint("electricity_observations")
            assert "id" in pk["constrained_columns"]
        finally:
            db.close()

    def test_indexes_exist(self):
        """✓ Performance indexes are created."""
        db = SessionLocal()
        try:
            inspector = inspect(db.get_bind())
            indexes = inspector.get_indexes("electricity_observations")
            index_names = [idx["name"] for idx in indexes]

            # Should have indexes for common queries
            assert any("country" in name and "timestamp" in name for name in index_names), \
                "Missing index for country + timestamp"
            assert any("metric" in name and "timestamp" in name for name in index_names), \
                "Missing index for metric + timestamp"
        finally:
            db.close()


# ============================================================================
# Model Persistence Tests
# ============================================================================


class TestElectricityObservationPersistence:
    """Test creating and querying observations."""

    def test_create_observation(self, mock_observation_data):
        """✓ Can insert observation into database."""
        db = SessionLocal()
        try:
            obs = ElectricityObservation(**mock_observation_data)
            db.add(obs)
            db.commit()
            db.refresh(obs)

            assert obs.id is not None
            assert obs.country_code == "NL"
            assert obs.metric == "load"

            # Clean up
            db.delete(obs)
            db.commit()
        finally:
            db.close()

    def test_query_observation(self, mock_observation_data):
        """✓ Can query observation from database."""
        db = SessionLocal()
        try:
            # Insert
            obs = ElectricityObservation(**mock_observation_data)
            db.add(obs)
            db.commit()
            db.refresh(obs)
            obs_id = obs.id

            # Query
            queried = db.query(ElectricityObservation).filter(
                ElectricityObservation.id == obs_id
            ).first()

            assert queried is not None
            assert queried.country_code == "NL"

            # Clean up
            db.delete(queried)
            db.commit()
        finally:
            db.close()

    def test_uniqueness_constraint_enforced(self, mock_observation_data):
        """✓ Duplicate (country, timestamp, metric) raises error."""
        db = SessionLocal()
        try:
            # Insert first observation
            obs1 = ElectricityObservation(**mock_observation_data)
            db.add(obs1)
            db.commit()

            # Try to insert duplicate (same country, timestamp, metric)
            obs2 = ElectricityObservation(**mock_observation_data)
            db.add(obs2)

            # Should raise IntegrityError
            with pytest.raises(Exception):  # IntegrityError or similar
                db.commit()

            # Clean up
            db.rollback()
            db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == "NL"
            ).delete()
            db.commit()
        finally:
            db.close()

    def test_update_observation(self, mock_observation_data):
        """✓ Can update observation (for upserts)."""
        db = SessionLocal()
        try:
            # Insert
            obs = ElectricityObservation(**mock_observation_data)
            db.add(obs)
            db.commit()
            db.refresh(obs)

            # Update value
            obs.value_mw = Decimal("99999.99")
            db.commit()
            db.refresh(obs)

            # Verify update
            assert obs.value_mw == Decimal("99999.99")

            # Clean up
            db.delete(obs)
            db.commit()
        finally:
            db.close()

    def test_timestamps_are_set(self, mock_observation_data):
        """✓ created_at and updated_at are auto-set."""
        db = SessionLocal()
        try:
            obs = ElectricityObservation(**mock_observation_data)
            db.add(obs)
            db.commit()
            db.refresh(obs)

            assert obs.created_at is not None
            assert obs.updated_at is not None

            # Clean up
            db.delete(obs)
            db.commit()
        finally:
            db.close()


# ============================================================================
# Query Performance Tests
# ============================================================================


class TestElectricityObservationQueries:
    """Test query patterns for common use cases."""

    def test_query_latest_for_country_metric(self, mock_observation_data):
        """✓ Can efficiently query latest observation for country+metric."""
        db = SessionLocal()
        try:
            # Insert multiple observations
            for i in range(5):
                obs_data = mock_observation_data.copy()
                obs_data["timestamp"] = datetime.utcnow().replace(hour=i)
                obs = ElectricityObservation(**obs_data)
                db.add(obs)
            db.commit()

            # Query latest
            latest = db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == "NL",
                ElectricityObservation.metric == "load",
            ).order_by(
                ElectricityObservation.timestamp.desc()
            ).first()

            assert latest is not None
            assert latest.country_code == "NL"

            # Clean up
            db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == "NL"
            ).delete()
            db.commit()
        finally:
            db.close()

    def test_query_time_range(self, multiple_observations):
        """✓ Can query observations within time range."""
        db = SessionLocal()
        try:
            # Insert multiple observations
            for obs_data in multiple_observations:
                obs = ElectricityObservation(**obs_data)
                db.add(obs)
            db.commit()

            # Query time range
            start = multiple_observations[0]["timestamp"]
            end = multiple_observations[5]["timestamp"]

            results = db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == "NL",
                ElectricityObservation.timestamp >= start,
                ElectricityObservation.timestamp <= end,
            ).all()

            assert len(results) > 0
            for obs in results:
                assert start <= obs.timestamp <= end

            # Clean up
            db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == "NL"
            ).delete()
            db.commit()
        finally:
            db.close()

    def test_query_all_metrics_for_country(self, mock_observation_data, mock_solar_data):
        """✓ Can query all metrics for a country."""
        db = SessionLocal()
        try:
            # Insert multiple metrics
            obs1 = ElectricityObservation(**mock_observation_data)
            obs2 = ElectricityObservation(**mock_solar_data)
            db.add_all([obs1, obs2])
            db.commit()

            # Query all for country
            results = db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == "NL"
            ).all()

            assert len(results) >= 2
            metrics = {obs.metric for obs in results}
            assert "load" in metrics
            assert "solar" in metrics

            # Clean up
            db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == "NL"
            ).delete()
            db.commit()
        finally:
            db.close()
