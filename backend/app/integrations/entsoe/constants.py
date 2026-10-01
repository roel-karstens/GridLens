"""ENTSO-E constants: country mappings, technology codes, and API configuration.

Reference:
  https://transparency.entsoe.eu/
  https://www.entsoe.eu/data/data-portal/consumption/Pages/default.aspx
"""

from dataclasses import dataclass


@dataclass
class CountryConfig:
    """Configuration for a supported country."""

    code: str  # ISO 2-letter code (NL, DE, BE, FR)
    name: str  # Full name
    entsoe_domain: str  # ENTSO-E bidding zone domain identifier
    entsoe_control_area: str | None = None  # Alternative control area ID if needed


# Country configurations with ENTSO-E domain identifiers
# Reference: https://transparency.entsoe.eu/content/static_content/download?path=/Static%20content/XML%20File%20Reference%20v2.1_rev3_20210929.zip
COUNTRIES: dict[str, CountryConfig] = {
    "NL": CountryConfig(
        code="NL",
        name="Netherlands",
        entsoe_domain="10YNL----------L",  # Netherlands bidding zone
    ),
    "DE": CountryConfig(
        code="DE",
        name="Germany",
        entsoe_domain="10Y1001A1001A82H",  # Germany/Luxembourg bidding zone
    ),
    "BE": CountryConfig(
        code="BE",
        name="Belgium",
        entsoe_domain="10YBE----------2",  # Belgium bidding zone
    ),
    "FR": CountryConfig(
        code="FR",
        name="France",
        entsoe_domain="10YFR-RTE------C",  # France bidding zone
    ),
}

# Default metric (load/demand) - available for all countries
DEFAULT_METRIC = "load"

# Supported generation technology types
# Maps ENTSO-E psrType codes to our normalized metric names
# Reference: https://www.entsoe.eu/data/data-portal/generation/Pages/default.aspx
TECHNOLOGY_MAPPING: dict[str, str] = {
    # Solar
    "B16": "solar",
    # Wind
    "B18": "wind_onshore",
    "B19": "wind_offshore",
    # Nuclear
    "B20": "nuclear",
    # Fossil/Thermal
    "B21": "coal",
    "B22": "coal",  # Hard coal (Brown coal uses B22)
    "B23": "gas",  # Natural gas
    "B25": "gas",  # Oil
    # Renewable
    "B26": "hydro",  # Hydro run-of-river
    "B27": "hydro",  # Hydro water reservoir
    "B28": "hydro",  # Hydro pumped storage
    "B29": "biomass",
    "B30": "biomass",  # Biomass waste
    "B31": "other",  # Geothermal
    "B32": "other",  # Other renewable
    "B33": "other",  # Waste
    # Other
    "B34": "other",  # Other
    "B35": "other",  # Marine
    "B36": "other",  # Non-renewable waste
}

# Reverse mapping: normalized metric -> list of ENTSO-E codes
METRIC_TO_TECHNOLOGY_CODES: dict[str, list[str]] = {}
for entsoe_code, metric in TECHNOLOGY_MAPPING.items():
    if metric not in METRIC_TO_TECHNOLOGY_CODES:
        METRIC_TO_TECHNOLOGY_CODES[metric] = []
    METRIC_TO_TECHNOLOGY_CODES[metric].append(entsoe_code)

# Renewable metrics (for calculating renewable percentage)
RENEWABLE_METRICS = {"solar", "wind_onshore", "wind_offshore", "hydro", "biomass"}

# ENTSO-E API Configuration
ENTSOE_API_BASE_URL = "https://web-api.tp.entsoe.eu/api"

# Document types for different data queries
DOCUMENT_TYPE_LOAD = "A65"  # Actual Total Load
DOCUMENT_TYPE_GENERATION = "A73"  # Aggregated Generation Per Type
DOCUMENT_TYPE_FORECAST_LOAD = "A61"  # Day Ahead Total Load Forecast

# Process type
PROCESS_TYPE_REALTIME = "A18"  # Realtime
PROCESS_TYPE_INTRADAY = "A16"  # Intraday
PROCESS_TYPE_DAY_AHEAD = "A01"  # Day Ahead

# Default process type for historical data retrieval
DEFAULT_PROCESS_TYPE = PROCESS_TYPE_REALTIME

# Time resolution
DEFAULT_TIME_PERIOD_HOURS = 24  # Default to last 24 hours
MAX_TIME_PERIOD_DAYS = 365  # Max query window (avoid too large requests)

# Rate limiting / timeout configuration
REQUEST_TIMEOUT_SECONDS = 30  # HTTP timeout
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Data point limit per query
MAX_DATA_POINTS_PER_REQUEST = 10000  # ENTSO-E API limit

# Logging configuration
LOG_SENSITIVE_DATA = False  # Never log API tokens, credentials
