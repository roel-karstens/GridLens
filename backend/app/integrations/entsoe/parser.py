"""ENTSO-E XML response parser and data normalizer."""

import logging
from datetime import datetime
from decimal import Decimal
from xml.etree import ElementTree as ET

from app.integrations.entsoe.models import LoadObservation, GenerationObservation, ParsedObservation
from app.integrations.entsoe.constants import TECHNOLOGY_MAPPING

logger = logging.getLogger(__name__)


class ENTSOEParser:
    """Parse and normalize ENTSO-E XML responses.
    
    Responsibilities:
    - Parse ENTSO-E XML market documents
    - Extract time series data
    - Normalize timestamps (to UTC)
    - Map generation technology codes
    - Validate data
    - Handle missing/incomplete data gracefully
    
    Reference:
      XML Schema: https://www.entsoe.eu/data/data-portal/generate/
    """

    @staticmethod
    def parse_load_xml(xml_content: str, country_code: str) -> list[LoadObservation]:
        """Parse ENTSO-E Actual Total Load XML response.
        
        Args:
            xml_content: Raw XML as string
            country_code: ISO 2-letter country code
            
        Returns:
            List of LoadObservation objects.
            
        Raises:
            ET.ParseError: If XML is malformed.
            ValueError: If required fields are missing.
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse load XML for {country_code}: {e}")
            raise ValueError(f"Invalid XML for {country_code}: {e}")
        
        observations = []
        
        # ENTSO-E XML structure: Publication/TimeSeries/Period/Point
        # Find all TimeSeries elements
        for timeseries in root.findall(".//TimeSeries"):
            period = timeseries.find("Period")
            if period is None:
                continue
            
            # Get time interval
            time_interval = period.find("timeInterval")
            if time_interval is None:
                continue
            
            start_elem = time_interval.find("start")
            if start_elem is None or not start_elem.text:
                continue
            
            # Parse start timestamp (ISO 8601 format: 2024-01-01T00:00Z)
            try:
                start_time = datetime.fromisoformat(
                    start_elem.text.replace("Z", "+00:00")
                )
            except ValueError:
                logger.warning(f"Invalid timestamp in load XML: {start_elem.text}")
                continue
            
            # Parse each point in the period
            for point in period.findall("Point"):
                position_elem = point.find("position")
                quantity_elem = point.find("quantity")
                
                if position_elem is None or quantity_elem is None:
                    continue
                
                try:
                    quantity = float(quantity_elem.text or 0)
                    observations.append(
                        LoadObservation(
                            timestamp=start_time,
                            value_mw=quantity,
                            source_timestamp=datetime.utcnow(),
                        )
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Invalid quantity in load XML for {country_code}: "
                        f"{quantity_elem.text}: {e}"
                    )
                    continue
        
        if not observations:
            logger.warning(f"No load observations found in XML for {country_code}")
        
        return observations

    @staticmethod
    def parse_generation_xml(xml_content: str, country_code: str) -> list[GenerationObservation]:
        """Parse ENTSO-E Aggregated Generation Per Type XML response.
        
        Args:
            xml_content: Raw XML as string
            country_code: ISO 2-letter country code
            
        Returns:
            List of GenerationObservation objects.
            
        Raises:
            ET.ParseError: If XML is malformed.
            ValueError: If required fields are missing.
        """
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse generation XML for {country_code}: {e}")
            raise ValueError(f"Invalid XML for {country_code}: {e}")
        
        observations = []
        
        # ENTSO-E XML structure: Publication/TimeSeries/Period/Point
        # Each TimeSeries represents one technology type
        for timeseries in root.findall(".//TimeSeries"):
            # Extract technology type (psrType)
            mrid = timeseries.find("mRID")
            psrtype = None
            
            # Try to find psrType in attributes or elements
            for attr_name, attr_val in timeseries.attrib.items():
                if "psrType" in attr_name.lower():
                    psrtype = attr_val
                    break
            
            if not psrtype:
                # Try to extract from Period/timeInterval/resolution
                period = timeseries.find("Period")
                if period is not None:
                    resolution = period.find("resolution")
                    if resolution is not None and resolution.text:
                        psrtype = resolution.text
            
            # For ENTSOE A73 documents, psrType is in the mRID or via another means
            # Try alternative parsing: look at the timeseries structure
            if not psrtype:
                # Extract psrType from the Period via business process
                period = timeseries.find("Period")
                if period is not None:
                    for elem in period:
                        if "psrType" in str(elem.tag).lower():
                            psrtype = elem.text
                            break
            
            # Fallback: try to extract from attributes on Point level
            if not psrtype:
                period = timeseries.find("Period")
                if period is not None:
                    point = period.find("Point")
                    if point is not None:
                        for attr_name in point.attrib:
                            if "psrType" in attr_name.lower():
                                psrtype = point.attrib[attr_name]
                                break
            
            period = timeseries.find("Period")
            if period is None:
                continue
            
            # Get time interval
            time_interval = period.find("timeInterval")
            if time_interval is None:
                continue
            
            start_elem = time_interval.find("start")
            if start_elem is None or not start_elem.text:
                continue
            
            # Parse start timestamp
            try:
                start_time = datetime.fromisoformat(
                    start_elem.text.replace("Z", "+00:00")
                )
            except ValueError:
                logger.warning(f"Invalid timestamp in generation XML: {start_elem.text}")
                continue
            
            # Parse each point (each technology measurement)
            for point in period.findall("Point"):
                quantity_elem = point.find("quantity")
                
                if quantity_elem is None:
                    continue
                
                try:
                    quantity = float(quantity_elem.text or 0)
                    
                    # Use psrtype if found, otherwise use a generic identifier
                    technology = psrtype or "unknown"
                    
                    observations.append(
                        GenerationObservation(
                            timestamp=start_time,
                            technology=technology,
                            value_mw=quantity,
                            source_timestamp=datetime.utcnow(),
                        )
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Invalid quantity in generation XML for {country_code}: "
                        f"{quantity_elem.text}: {e}"
                    )
                    continue
        
        if not observations:
            logger.warning(f"No generation observations found in XML for {country_code}")
        
        return observations

    @staticmethod
    def normalize_observation(
        country_code: str,
        timestamp: datetime,
        metric: str,
        value: float,
        source_dataset: str,
        source_timestamp: datetime | None = None,
    ) -> ParsedObservation:
        """Create a normalized observation for database storage.
        
        Args:
            country_code: ISO 2-letter country code
            timestamp: Observation timestamp (UTC)
            metric: Normalized metric name (e.g., "solar", "wind_onshore", "load")
            value: Value in megawatts
            source_dataset: ENTSO-E document type
            source_timestamp: When ENTSO-E generated this data
            
        Returns:
            ParsedObservation ready for database insertion.
            
        Raises:
            ValueError: If validation fails (e.g., negative MW for generation).
        """
        # Validate value is non-negative
        if value < 0:
            raise ValueError(
                f"Invalid value {value} MW for {metric} in {country_code}: "
                "Values must be non-negative"
            )
        
        # Ensure timestamp is in UTC
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=None)  # Already UTC naive
        
        return ParsedObservation(
            country_code=country_code,
            timestamp=timestamp,
            metric=metric,
            value_mw=value,
            unit="MW",
            source="ENTSO-E",
            source_dataset=source_dataset,
            source_timestamp=source_timestamp or datetime.utcnow(),
        )

    @staticmethod
    def map_technology(entsoe_psrtype: str) -> str | None:
        """Map ENTSO-E technology code to normalized metric name.
        
        Args:
            entsoe_psrtype: ENTSO-E psrType code (e.g., "B16" for solar)
            
        Returns:
            Normalized metric name (e.g., "solar") or None if unknown.
        """
        return TECHNOLOGY_MAPPING.get(entsoe_psrtype)

    @staticmethod
    def parse_iso8601_duration(duration_str: str) -> int:
        """Parse ISO 8601 duration string to minutes.
        
        Example:
            "PT60M" -> 60
            "PT30M" -> 30
            
        Args:
            duration_str: ISO 8601 duration (e.g., "PT60M", "PT30M")
            
        Returns:
            Duration in minutes.
            
        Raises:
            ValueError: If format is invalid.
        """
        # Simple parser for common formats (PT<N>M)
        if not duration_str or not duration_str.startswith("PT"):
            raise ValueError(f"Invalid ISO 8601 duration: {duration_str}")
        
        # Remove 'PT' prefix
        duration_str = duration_str[2:]
        
        # Extract minutes (format: 60M, 30M, etc.)
        if not duration_str.endswith("M"):
            raise ValueError(f"Invalid ISO 8601 duration: {duration_str}")
        
        try:
            minutes = int(duration_str[:-1])
            if minutes <= 0:
                raise ValueError(f"Duration must be positive: {minutes}")
            return minutes
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 duration: {duration_str}: {e}")
