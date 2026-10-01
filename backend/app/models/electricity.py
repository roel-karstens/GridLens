"""SQLAlchemy model for electricity observations."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, String, Numeric, DateTime, UniqueConstraint, Index

from app.models.project import Base


class ElectricityObservation(Base):
    """Electricity observation from ENTSO-E.
    
    Represents a single electricity metric (load, solar, wind, etc.) 
    for a specific country and timestamp.
    
    Attributes:
        id: Unique identifier (UUID)
        country_code: ISO 2-letter country code (NL, DE, BE, FR)
        timestamp: UTC timestamp of observation (quarter-hour or hourly)
        metric: Electricity metric (load, solar, wind_onshore, wind_offshore, etc.)
        value_mw: Value in megawatts
        unit: Unit of measurement (always 'MW')
        source: Data source (always 'ENTSO-E')
        source_dataset: ENTSO-E document type (e.g., 'Actual Total Load')
        source_timestamp: When ENTSO-E generated this data
        created_at: When we ingested this observation
        updated_at: When we last updated this observation
    """

    __tablename__ = "electricity_observations"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(UUID(int=0)))

    # Geography
    country_code = Column(String(2), nullable=False, index=True)

    # Time (all UTC)
    timestamp = Column(DateTime, nullable=False, index=True)
    source_timestamp = Column(DateTime, nullable=True)

    # Metric
    metric = Column(String, nullable=False, index=True)

    # Value
    value_mw = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(10), nullable=False, default="MW")

    # Source attribution
    source = Column(String, nullable=False, default="ENTSO-E")
    source_dataset = Column(String, nullable=False)

    # Audit timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: (country_code, timestamp, metric)
    __table_args__ = (
        UniqueConstraint("country_code", "timestamp", "metric", name="uq_country_timestamp_metric"),
        Index("idx_country_timestamp", "country_code", "timestamp"),
        Index("idx_metric_timestamp", "metric", "timestamp"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"ElectricityObservation("
            f"id={self.id}, "
            f"country={self.country_code}, "
            f"timestamp={self.timestamp}, "
            f"metric={self.metric}, "
            f"value={self.value_mw} MW)"
        )
