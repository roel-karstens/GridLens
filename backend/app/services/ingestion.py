"""Ingestion service for electricity data from ENTSO-E."""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.integrations.entsoe.client import ENTSOEClient
from app.integrations.entsoe.parser import ENTSOEParser
from app.integrations.entsoe.constants import COUNTRIES, DEFAULT_METRIC
from app.integrations.entsoe.models import ParsedObservation
from app.models.electricity import ElectricityObservation
from app.schemas.electricity import ElectricityObservationCreate

logger = logging.getLogger(__name__)


class IngestionService:
    """Orchestrate data ingestion from ENTSO-E.
    
    Responsibilities:
    - Request data from ENTSO-E API
    - Parse responses
    - Normalize data
    - Validate data
    - Upsert into database (idempotent)
    - Handle errors and retries
    - Manage logging (no credentials)
    """

    def __init__(self, db: Session, client: ENTSOEClient | None = None):
        """Initialize ingestion service.
        
        Args:
            db: SQLAlchemy database session
            client: ENTSOEClient instance (default: create new)
        """
        self.db = db
        self.client = client or ENTSOEClient()

    async def ingest_country_data(
        self,
        country_code: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, int]:
        """Ingest load and generation data for a country.
        
        Fetches both load (demand) and generation data for the specified
        time range, normalizes it, and upserts into database.
        
        Args:
            country_code: ISO 2-letter country code (e.g., "NL")
            start_time: Start of ingestion period (UTC)
            end_time: End of ingestion period (UTC)
            
        Returns:
            Dictionary with ingestion stats:
            {
                "created": int,
                "duplicate": int,
                "failed": int,
            }
            
        Raises:
            ValueError: If country_code is not supported.
            Exception: If ingestion fails (will be logged, not raised in production).
        """
        # Validate country
        if country_code not in COUNTRIES:
            raise ValueError(f"Unsupported country: {country_code}")
        
        stats = {
            "created": 0,
            "duplicate": 0,
            "failed": 0,
        }
        
        try:
            # Ingest load data
            load_count = await self.ingest_load_data(country_code, start_time, end_time)
            stats["created"] += load_count
        except Exception as e:
            logger.error(f"Failed to ingest load data for {country_code}: {e}")
            stats["failed"] += 1
        
        try:
            # Ingest generation data
            gen_stats = await self.ingest_generation_data(country_code, start_time, end_time)
            stats["created"] += gen_stats.get("created", 0)
            stats["duplicate"] += gen_stats.get("duplicate", 0)
            stats["failed"] += gen_stats.get("failed", 0)
        except Exception as e:
            logger.error(f"Failed to ingest generation data for {country_code}: {e}")
            stats["failed"] += 1
        
        logger.info(
            f"Ingestion complete for {country_code} "
            f"({start_time} to {end_time}): "
            f"created={stats['created']}, duplicate={stats['duplicate']}, failed={stats['failed']}"
        )
        
        return stats

    async def ingest_load_data(
        self,
        country_code: str,
        start_time: datetime,
        end_time: datetime,
    ) -> int:
        """Ingest load (demand) data for a country.
        
        Args:
            country_code: ISO 2-letter country code
            start_time: Start of ingestion period (UTC)
            end_time: End of ingestion period (UTC)
            
        Returns:
            Number of observations ingested.
        """
        country = COUNTRIES[country_code]
        
        # Fetch load data from ENTSO-E
        try:
            xml_response = await self.client.get_load(
                area_code=country.entsoe_domain,
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as e:
            logger.error(f"Failed to fetch load data for {country_code}: {e}")
            raise
        
        # Parse XML response
        try:
            raw_observations = ENTSOEParser.parse_load_xml(xml_response, country_code)
        except Exception as e:
            logger.error(f"Failed to parse load XML for {country_code}: {e}")
            raise
        
        # Normalize and upsert
        ingested_count = 0
        for raw_obs in raw_observations:
            try:
                parsed_obs = ENTSOEParser.normalize_observation(
                    country_code=country_code,
                    timestamp=raw_obs.timestamp,
                    metric=DEFAULT_METRIC,  # "load"
                    value=raw_obs.value_mw,
                    source_dataset="Actual Total Load",
                    source_timestamp=raw_obs.source_timestamp,
                )
                
                success, message = self._upsert_parsed_observation(parsed_obs)
                if success:
                    ingested_count += 1
            except Exception as e:
                logger.warning(f"Failed to ingest load observation for {country_code}: {e}")
                continue
        
        logger.info(f"Ingested {ingested_count} load observations for {country_code}")
        return ingested_count

    async def ingest_generation_data(
        self,
        country_code: str,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, int]:
        """Ingest generation per type data for a country.
        
        Args:
            country_code: ISO 2-letter country code
            start_time: Start of ingestion period (UTC)
            end_time: End of ingestion period (UTC)
            
        Returns:
            Dictionary with stats: created, duplicate, failed
        """
        country = COUNTRIES[country_code]
        
        # Fetch generation data from ENTSO-E
        try:
            xml_response = await self.client.get_generation(
                area_code=country.entsoe_domain,
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as e:
            logger.error(f"Failed to fetch generation data for {country_code}: {e}")
            raise
        
        # Parse XML response
        try:
            raw_observations = ENTSOEParser.parse_generation_xml(xml_response, country_code)
        except Exception as e:
            logger.error(f"Failed to parse generation XML for {country_code}: {e}")
            raise
        
        # Normalize and upsert
        stats = {"created": 0, "duplicate": 0, "failed": 0}
        for raw_obs in raw_observations:
            try:
                # Map technology code to normalized metric name
                metric = ENTSOEParser.map_technology(raw_obs.technology)
                if not metric:
                    logger.debug(f"Unknown technology code: {raw_obs.technology}")
                    continue
                
                parsed_obs = ENTSOEParser.normalize_observation(
                    country_code=country_code,
                    timestamp=raw_obs.timestamp,
                    metric=metric,
                    value=raw_obs.value_mw,
                    source_dataset="Aggregated Generation Per Type",
                    source_timestamp=raw_obs.source_timestamp,
                )
                
                success, message = self._upsert_parsed_observation(parsed_obs)
                if success:
                    if message == "Created":
                        stats["created"] += 1
                    elif message == "Duplicate":
                        stats["duplicate"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.warning(f"Failed to ingest generation observation for {country_code}: {e}")
                stats["failed"] += 1
                continue
        
        logger.info(
            f"Ingested generation data for {country_code}: "
            f"created={stats['created']}, duplicate={stats['duplicate']}, failed={stats['failed']}"
        )
        return stats

    def _upsert_parsed_observation(self, parsed_obs: ParsedObservation) -> tuple[bool, str]:
        """Internal method to upsert a parsed observation.
        
        Returns:
            Tuple of (success, message) where message is "Created", "Duplicate", or error description
        """
        try:
            # Check if already exists
            existing = self.db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == parsed_obs.country_code,
                ElectricityObservation.timestamp == parsed_obs.timestamp,
                ElectricityObservation.metric == parsed_obs.metric,
            ).first()
            
            if existing:
                return (True, "Duplicate")
            
            # Create new observation
            obs = ElectricityObservation(
                country_code=parsed_obs.country_code,
                timestamp=parsed_obs.timestamp,
                metric=parsed_obs.metric,
                value_mw=Decimal(str(parsed_obs.value_mw)),
                unit=parsed_obs.unit,
                source=parsed_obs.source,
                source_dataset=parsed_obs.source_dataset,
                source_timestamp=parsed_obs.source_timestamp,
            )
            
            self.db.add(obs)
            self.db.commit()
            
            return (True, "Created")
            
        except IntegrityError:
            self.db.rollback()
            return (True, "Duplicate")
        except Exception as e:
            self.db.rollback()
            return (False, str(e))

    def upsert_observation(
        self,
        observation_create: ElectricityObservationCreate,
    ) -> ElectricityObservation | None:
        """Upsert a single observation into database.
        
        Idempotent: if an observation with same (country, timestamp, metric)
        already exists, it is updated rather than duplicated.
        
        Args:
            observation_create: Normalized observation to insert/update
            
        Returns:
            The persisted observation, or None if upsert failed.
        """
        try:
            # Check if exists
            existing = self.db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == observation_create.country_code,
                ElectricityObservation.timestamp == observation_create.timestamp,
                ElectricityObservation.metric == observation_create.metric,
            ).first()
            
            if existing:
                # Update if exists
                for key, value in observation_create.dict().items():
                    setattr(existing, key, value)
                self.db.commit()
                return existing
            else:
                # Insert if new
                obs = ElectricityObservation(**observation_create.dict())
                self.db.add(obs)
                self.db.commit()
                self.db.refresh(obs)
                return obs
                
        except IntegrityError:
            self.db.rollback()
            # Return existing record
            return self.db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == observation_create.country_code,
                ElectricityObservation.timestamp == observation_create.timestamp,
                ElectricityObservation.metric == observation_create.metric,
            ).first()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to upsert observation: {e}")
            return None

    def get_latest_observation(
        self,
        country_code: str,
        metric: str,
    ) -> ElectricityObservation | None:
        """Get the latest observation for a country and metric.
        
        Args:
            country_code: ISO 2-letter country code
            metric: Electricity metric
            
        Returns:
            Latest observation or None if not found.
        """
        return self.db.query(ElectricityObservation).filter(
            ElectricityObservation.country_code == country_code,
            ElectricityObservation.metric == metric,
        ).order_by(ElectricityObservation.timestamp.desc()).first()

    def get_observations_for_range(
        self,
        country_code: str,
        metric: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[ElectricityObservation]:
        """Get observations for a time range and metric.
        
        Args:
            country_code: ISO 2-letter country code
            metric: Electricity metric
            start_time: Start of time range (UTC)
            end_time: End of time range (UTC)
            
        Returns:
            List of observations ordered by timestamp (ascending).
        """
        return self.db.query(ElectricityObservation).filter(
            ElectricityObservation.country_code == country_code,
            ElectricityObservation.metric == metric,
            ElectricityObservation.timestamp >= start_time,
            ElectricityObservation.timestamp <= end_time,
        ).order_by(ElectricityObservation.timestamp.asc()).all()
