"""Service for electricity data queries and derived metrics."""

import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.integrations.entsoe.constants import (
    COUNTRIES,
    DEFAULT_METRIC,
    RENEWABLE_METRICS,
    METRIC_TO_TECHNOLOGY_CODES,
)
from app.models.electricity import ElectricityObservation
from app.schemas.electricity import (
    CurrentStatusResponse,
    GenerationMixResponse,
    HistoricalDataResponse,
    ElectricityObservationRead,
    ComparisonDataResponse,
)

logger = logging.getLogger(__name__)


class ElectricityService:
    """Service for electricity data queries and derived metrics."""

    def __init__(self, db: Session):
        self.db = db

    def get_current_status(self, country_code: str) -> CurrentStatusResponse:
        """Get current electricity status for a country."""
        load_obs = self._query_latest_by_metric(country_code, DEFAULT_METRIC)
        load_mw = Decimal(load_obs.value_mw) if load_obs else None
        timestamp = load_obs.timestamp if load_obs else datetime.utcnow()
        
        generation_breakdown = self._get_generation_breakdown(country_code, timestamp)
        total_generation = sum(generation_breakdown.values())
        renewable_mw = Decimal(
            sum(v for k, v in generation_breakdown.items() if k in RENEWABLE_METRICS)
        )
        renewable_pct = (
            (renewable_mw / total_generation * 100) if total_generation > 0 else Decimal(0)
        )
        
        return CurrentStatusResponse(
            country_code=country_code,
            timestamp=timestamp,
            load_mw=load_mw,
            total_generation_mw=Decimal(total_generation),
            renewable_generation_mw=renewable_mw,
            renewable_share_percent=renewable_pct.quantize(Decimal("0.01")),
            solar_mw=Decimal(generation_breakdown.get("solar", 0)),
            wind_onshore_mw=Decimal(generation_breakdown.get("wind_onshore", 0)),
            wind_offshore_mw=Decimal(generation_breakdown.get("wind_offshore", 0)),
            nuclear_mw=Decimal(generation_breakdown.get("nuclear", 0)),
            gas_mw=Decimal(generation_breakdown.get("gas", 0)),
            coal_mw=Decimal(generation_breakdown.get("coal", 0)),
            hydro_mw=Decimal(generation_breakdown.get("hydro", 0)),
            biomass_mw=Decimal(generation_breakdown.get("biomass", 0)),
            other_mw=Decimal(generation_breakdown.get("other", 0)),
            last_updated=timestamp,
        )

    def get_generation_mix(
        self,
        country_code: str,
        timestamp: datetime | None = None,
    ) -> GenerationMixResponse:
        """Get current generation mix (breakdown by technology)."""
        if not timestamp:
            latest = self.db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == country_code,
            ).order_by(ElectricityObservation.timestamp.desc()).first()
            timestamp = latest.timestamp if latest else datetime.utcnow()
        
        generation_breakdown = self._get_generation_breakdown(country_code, timestamp)
        total_generation = sum(generation_breakdown.values())
        
        return GenerationMixResponse(
            country_code=country_code,
            timestamp=timestamp,
            generation_by_type={k: Decimal(v) for k, v in generation_breakdown.items()},
            total_generation_mw=Decimal(total_generation),
        )

    def get_historical_data(
        self,
        country_code: str,
        metric: str,
        start_time: datetime,
        end_time: datetime,
    ) -> HistoricalDataResponse:
        """Get historical observations for a metric over a time range."""
        observations = self.db.query(ElectricityObservation).filter(
            ElectricityObservation.country_code == country_code,
            ElectricityObservation.metric == metric,
            ElectricityObservation.timestamp >= start_time,
            ElectricityObservation.timestamp <= end_time,
        ).order_by(ElectricityObservation.timestamp.asc()).all()
        
        return HistoricalDataResponse(
            country_code=country_code,
            metric=metric,
            start_time=start_time,
            end_time=end_time,
            observations=[ElectricityObservationRead.from_orm(obs) for obs in observations],
            count=len(observations),
        )

    def get_comparison_data(
        self,
        countries: list[str],
        metric: str,
        timestamp: datetime | None = None,
    ) -> dict[str, Decimal | None]:
        """Get metric values for multiple countries at a point in time."""
        comparison = {}
        for country_code in countries:
            obs = (
                self._query_latest_by_metric(country_code, metric)
                if not timestamp
                else self.db.query(ElectricityObservation).filter(
                    ElectricityObservation.country_code == country_code,
                    ElectricityObservation.metric == metric,
                    ElectricityObservation.timestamp == timestamp,
                ).first()
            )
            comparison[country_code] = Decimal(obs.value_mw) if obs else None
        return comparison

    def calculate_renewable_percentage(
        self,
        country_code: str,
        timestamp: datetime | None = None,
    ) -> Decimal | None:
        """Calculate percentage of renewable generation."""
        if not timestamp:
            latest = self.db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == country_code,
            ).order_by(ElectricityObservation.timestamp.desc()).first()
            if not latest:
                return None
            timestamp = latest.timestamp
        
        generation_breakdown = self._get_generation_breakdown(country_code, timestamp)
        total = sum(generation_breakdown.values())
        if total == 0:
            return Decimal(0)
        
        renewable = sum(v for k, v in generation_breakdown.items() if k in RENEWABLE_METRICS)
        pct = (Decimal(renewable) / Decimal(total) * 100).quantize(Decimal("0.01"))
        return pct

    def _get_generation_breakdown(
        self,
        country_code: str,
        timestamp: datetime,
    ) -> dict[str, float]:
        """Internal method to get generation breakdown at a specific timestamp."""
        breakdown = {}
        for metric_name in METRIC_TO_TECHNOLOGY_CODES.keys():
            if metric_name == DEFAULT_METRIC:
                continue
            obs = self.db.query(ElectricityObservation).filter(
                ElectricityObservation.country_code == country_code,
                ElectricityObservation.metric == metric_name,
                ElectricityObservation.timestamp == timestamp,
            ).first()
            breakdown[metric_name] = float(obs.value_mw) if obs else 0.0
        return breakdown

    def _query_latest_by_metric(
        self,
        country_code: str,
        metric: str,
    ) -> ElectricityObservation | None:
        """Query latest observation for a specific metric."""
        return self.db.query(ElectricityObservation).filter(
            ElectricityObservation.country_code == country_code,
            ElectricityObservation.metric == metric,
        ).order_by(ElectricityObservation.timestamp.desc()).first()

    def _query_all_latest_metrics(
        self,
        country_code: str,
    ) -> dict[str, ElectricityObservation]:
        """Query latest observation for all metrics in a country."""
        all_obs = self.db.query(ElectricityObservation).filter(
            ElectricityObservation.country_code == country_code,
        ).order_by(ElectricityObservation.timestamp.desc()).all()
        
        latest_by_metric = {}
        for obs in all_obs:
            if obs.metric not in latest_by_metric:
                latest_by_metric[obs.metric] = obs
        return latest_by_metric
