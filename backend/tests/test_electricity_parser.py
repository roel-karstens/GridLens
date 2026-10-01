"""Unit tests for ENTSO-E XML parser."""

import pytest
from datetime import datetime
from decimal import Decimal

from app.integrations.entsoe.parser import ENTSOEParser
from app.integrations.entsoe.models import LoadObservation, GenerationObservation


class TestENTSOEParserLoadXML:
    """Tests for parse_load_xml method."""

    @pytest.fixture
    def parser(self):
        return ENTSOEParser()

    @pytest.fixture
    def sample_load_xml(self):
        """Mock ENTSO-E A65 (Actual Total Load) response."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<Publication_MarketDocument xmlns="http://iec.ch/TC57/2011/schema/msgtype">
  <mRID>20240101T0000Z</mRID>
  <createdDateTime>2024-01-01T00:30:00Z</createdDateTime>
  <TimeSeries>
    <mRID>NL-load-001</mRID>
    <Period>
      <timeInterval>
        <start>2024-01-01T00:00Z</start>
        <end>2024-01-01T01:00Z</end>
      </timeInterval>
      <Point>
        <position>1</position>
        <quantity>12500.00</quantity>
      </Point>
    </Period>
    <Period>
      <timeInterval>
        <start>2024-01-01T01:00Z</start>
        <end>2024-01-01T02:00Z</end>
      </timeInterval>
      <Point>
        <position>1</position>
        <quantity>12300.50</quantity>
      </Point>
    </Period>
  </TimeSeries>
</Publication_MarketDocument>"""

    def test_parse_load_xml_valid(self, parser, sample_load_xml):
        """Should parse valid ENTSO-E A65 load response."""
        result = parser.parse_load_xml(sample_load_xml, "NL")

        assert len(result) == 2
        assert result[0].value_mw == 12500.00
        assert result[1].value_mw == 12300.50
        assert result[0].timestamp == datetime(2024, 1, 1, 0, 0, 0)
        assert result[1].timestamp == datetime(2024, 1, 1, 1, 0, 0)

    def test_parse_load_xml_malformed(self, parser):
        """Should raise ValueError for malformed XML."""
        with pytest.raises(ValueError, match="Invalid XML"):
            parser.parse_load_xml("<invalid", "NL")

    def test_parse_load_xml_empty_response(self, parser):
        """Should handle empty XML response gracefully."""
        xml = """<?xml version="1.0"?>
<Publication_MarketDocument xmlns="http://iec.ch/TC57/2011/schema/msgtype">
</Publication_MarketDocument>"""
        result = parser.parse_load_xml(xml, "NL")
        assert result == []

    def test_parse_load_xml_missing_timestamp(self, parser):
        """Should skip points with missing timestamps."""
        xml = """<?xml version="1.0"?>
<Publication_MarketDocument xmlns="http://iec.ch/TC57/2011/schema/msgtype">
  <TimeSeries>
    <Period>
      <timeInterval>
        <start></start>
        <end>2024-01-01T01:00Z</end>
      </timeInterval>
      <Point>
        <position>1</position>
        <quantity>12500</quantity>
      </Point>
    </Period>
  </TimeSeries>
</Publication_MarketDocument>"""
        result = parser.parse_load_xml(xml, "NL")
        assert result == []

    def test_parse_load_xml_invalid_quantity(self, parser):
        """Should skip points with invalid quantities."""
        xml = """<?xml version="1.0"?>
<Publication_MarketDocument xmlns="http://iec.ch/TC57/2011/schema/msgtype">
  <TimeSeries>
    <Period>
      <timeInterval>
        <start>2024-01-01T00:00Z</start>
        <end>2024-01-01T01:00Z</end>
      </timeInterval>
      <Point>
        <position>1</position>
        <quantity>invalid</quantity>
      </Point>
    </Period>
  </TimeSeries>
</Publication_MarketDocument>"""
        result = parser.parse_load_xml(xml, "NL")
        assert result == []


class TestENTSOEParserGenerationXML:
    """Tests for parse_generation_xml method."""

    @pytest.fixture
    def parser(self):
        return ENTSOEParser()

    @pytest.fixture
    def sample_generation_xml(self):
        """Mock ENTSO-E A73 (Aggregated Generation Per Type) response."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<Publication_MarketDocument xmlns="http://iec.ch/TC57/2011/schema/msgtype">
  <mRID>20240101T0000Z</mRID>
  <createdDateTime>2024-01-01T00:30:00Z</createdDateTime>
  <TimeSeries>
    <mRID>NL-solar-001</mRID>
    <Period>
      <timeInterval>
        <start>2024-01-01T00:00Z</start>
        <end>2024-01-01T01:00Z</end>
      </timeInterval>
      <Point>
        <position>1</position>
        <quantity>500.00</quantity>
      </Point>
    </Period>
  </TimeSeries>
  <TimeSeries>
    <mRID>NL-wind-001</mRID>
    <Period>
      <timeInterval>
        <start>2024-01-01T00:00Z</start>
        <end>2024-01-01T01:00Z</end>
      </timeInterval>
      <Point>
        <position>1</position>
        <quantity>1200.50</quantity>
      </Point>
    </Period>
  </TimeSeries>
</Publication_MarketDocument>"""

    def test_parse_generation_xml_valid(self, parser, sample_generation_xml):
        """Should parse valid ENTSO-E A73 generation response."""
        result = parser.parse_generation_xml(sample_generation_xml, "NL")

        assert len(result) == 2
        assert result[0].value_mw == 500.00
        assert result[1].value_mw == 1200.50

    def test_parse_generation_xml_malformed(self, parser):
        """Should raise ValueError for malformed XML."""
        with pytest.raises(ValueError, match="Invalid XML"):
            parser.parse_generation_xml("<invalid", "NL")

    def test_parse_generation_xml_empty_response(self, parser):
        """Should handle empty XML response gracefully."""
        xml = """<?xml version="1.0"?>
<Publication_MarketDocument xmlns="http://iec.ch/TC57/2011/schema/msgtype">
</Publication_MarketDocument>"""
        result = parser.parse_generation_xml(xml, "NL")
        assert result == []


class TestENTSOEParserNormalization:
    """Tests for normalize_observation method."""

    @pytest.fixture
    def parser(self):
        return ENTSOEParser()

    def test_normalize_observation_valid(self, parser):
        """Should create normalized observation."""
        obs = parser.normalize_observation(
            country_code="NL",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            metric="load",
            value=12500.50,
            source_dataset="Actual Total Load",
        )

        assert obs.country_code == "NL"
        assert obs.metric == "load"
        assert obs.value_mw == 12500.50
        assert obs.source == "ENTSO-E"
        assert obs.unit == "MW"

    def test_normalize_observation_negative_value_raises_error(self, parser):
        """Should raise error for negative MW values."""
        with pytest.raises(ValueError, match="Values must be non-negative"):
            parser.normalize_observation(
                country_code="NL",
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                metric="solar",
                value=-100.0,
                source_dataset="Aggregated Generation Per Type",
            )

    def test_normalize_observation_zero_value(self, parser):
        """Should accept zero value (valid for generation)."""
        obs = parser.normalize_observation(
            country_code="NL",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            metric="solar",
            value=0.0,
            source_dataset="Aggregated Generation Per Type",
        )

        assert obs.value_mw == 0.0


class TestENTSOEParserHelpers:
    """Tests for helper methods."""

    @pytest.fixture
    def parser(self):
        return ENTSOEParser()

    def test_map_technology_solar(self, parser):
        """Should map B16 to solar."""
        assert parser.map_technology("B16") == "solar"

    def test_map_technology_wind_onshore(self, parser):
        """Should map B18 to wind_onshore."""
        assert parser.map_technology("B18") == "wind_onshore"

    def test_map_technology_wind_offshore(self, parser):
        """Should map B19 to wind_offshore."""
        assert parser.map_technology("B19") == "wind_offshore"

    def test_map_technology_unknown(self, parser):
        """Should return None for unknown technology."""
        assert parser.map_technology("B99") is None

    def test_parse_iso8601_duration_60m(self, parser):
        """Should parse PT60M to 60 minutes."""
        assert parser.parse_iso8601_duration("PT60M") == 60

    def test_parse_iso8601_duration_30m(self, parser):
        """Should parse PT30M to 30 minutes."""
        assert parser.parse_iso8601_duration("PT30M") == 30

    def test_parse_iso8601_duration_invalid_format(self, parser):
        """Should raise ValueError for invalid format."""
        with pytest.raises(ValueError, match="Invalid ISO 8601 duration"):
            parser.parse_iso8601_duration("60M")

    def test_parse_iso8601_duration_invalid_value(self, parser):
        """Should raise ValueError for invalid value."""
        with pytest.raises(ValueError, match="Invalid ISO 8601 duration"):
            parser.parse_iso8601_duration("PT-60M")
