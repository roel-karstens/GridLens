"""ENTSO-E XML response parser and data normalizer."""

import logging
from datetime import datetime, timedelta
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
        
        # Extract namespace from root tag if present
        ns = ""
        if "}" in root.tag:
            ns_part = root.tag.split("}")[0][1:]  # Extract namespace URL
            ns = f"{{{ns_part}}}"
        
        # ENTSO-E XML structure: GL_MarketDocument/TimeSeries/Period/Point
        # Find all TimeSeries elements (with or without namespace)
        for timeseries in root.findall(f".//{ns}TimeSeries"):
            period = timeseries.find(f"{ns}Period")
            if period is None:
                continue
            
            # Get time interval
            time_interval = period.find(f"{ns}timeInterval")
            if time_interval is None:
                continue
            
            start_elem = time_interval.find(f"{ns}start")
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
            
            # Get resolution for calculating point timestamps
            resolution_elem = period.find(f"{ns}resolution")
            resolution_minutes = 15  # Default to 15 minutes
            
            if resolution_elem is not None and resolution_elem.text:
                # Parse ISO 8601 duration: PT15M, PT60M, etc.
                res_text = resolution_elem.text
                try:
                    if "PT" in res_text:
                        # Extract minutes from PT15M format
                        if "M" in res_text:
                            minutes_str = res_text.replace("PT", "").replace("M", "")
                            resolution_minutes = int(minutes_str)
                except (ValueError, IndexError):
                    logger.debug(f"Could not parse resolution: {res_text}, using default 15 minutes")
            
            # Parse each point in the period
            for point in period.findall(f"{ns}Point"):
                position_elem = point.find(f"{ns}position")
                quantity_elem = point.find(f"{ns}quantity")
                
                if position_elem is None or quantity_elem is None:
                    continue
                
                try:
                    position = int(position_elem.text or 0)
                    quantity = float(quantity_elem.text or 0)
                    
                    # Calculate timestamp for this point
                    # Position is 1-based, so position 1 is the first interval
                    point_time = start_time + timedelta(
                        minutes=resolution_minutes * (position - 1)
                    )
                    
                    observations.append(
                        LoadObservation(
                            timestamp=point_time,
                            value_mw=quantity,
                            source_timestamp=datetime.utcnow(),
                        )
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Invalid data in load XML for {country_code}: "
                        f"position={position_elem.text}, quantity={quantity_elem.text}: {e}"
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
        
        # Extract namespace from root tag if present
        ns = ""
        if "}" in root.tag:
            ns_part = root.tag.split("}")[0][1:]  # Extract namespace URL
            ns = f"{{{ns_part}}}"
        
        # ENTSO-E XML structure: GL_MarketDocument/TimeSeries/Period/Point
        # Each TimeSeries represents one technology type
        for timeseries in root.findall(f".//{ns}TimeSeries"):
            # Extract technology type (psrType)
            psrtype_elem = timeseries.find(f"{ns}MktPSRType/{ns}psrType")
            psrtype = None
            
            if psrtype_elem is not None and psrtype_elem.text:
                psrtype = psrtype_elem.text
            
            # Alternative: try to find psrType in attributes or other locations
            if not psrtype:
                for attr_name, attr_val in timeseries.attrib.items():
                    if "psrType" in attr_name.lower():
                        psrtype = attr_val
                        break
            
            period = timeseries.find(f"{ns}Period")
            if period is None:
                continue
            
            # Get time interval
            time_interval = period.find(f"{ns}timeInterval")
            if time_interval is None:
                continue
            
            start_elem = time_interval.find(f"{ns}start")
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
            
            # Get resolution for calculating point timestamps
            resolution_elem = period.find(f"{ns}resolution")
            resolution_minutes = 60  # Default to 60 minutes for generation data
            
            if resolution_elem is not None and resolution_elem.text:
                # Parse ISO 8601 duration: PT15M, PT60M, etc.
                res_text = resolution_elem.text
                try:
                    if "PT" in res_text:
                        if "M" in res_text:
                            minutes_str = res_text.replace("PT", "").replace("M", "")
                            resolution_minutes = int(minutes_str)
                except (ValueError, IndexError):
                    logger.debug(f"Could not parse resolution: {res_text}, using default 60 minutes")
            
            # Parse each point (each technology measurement)
            for point in period.findall(f"{ns}Point"):
                position_elem = point.find(f"{ns}position")
                quantity_elem = point.find(f"{ns}quantity")
                
                if position_elem is None or quantity_elem is None:
                    continue
                
                try:
                    position = int(position_elem.text or 0)
                    quantity = float(quantity_elem.text or 0)
                    
                    # Calculate timestamp for this point
                    point_time = start_time + timedelta(
                        minutes=resolution_minutes * (position - 1)
                    )
                    
                    # Use psrtype if found, otherwise use a generic identifier
                    technology = psrtype or "unknown"
                    
                    observations.append(
                        GenerationObservation(
                            timestamp=point_time,
                            technology=technology,
                            value_mw=quantity,
                            source_timestamp=datetime.utcnow(),
                        )
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Invalid data in generation XML for {country_code}: "
                        f"position={position_elem.text}, quantity={quantity_elem.text}: {e}"
                    )
                    continue
        
        if not observations:
            logger.debug(f"No generation observations found in XML for {country_code}")
        
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
