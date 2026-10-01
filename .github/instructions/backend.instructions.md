---
applyTo: "backend/**/*.py"
---

# Backend Development Instructions — GridLens

## Technology Stack

- Python 3.12+
- FastAPI web framework
- Pydantic for validation & schemas
- SQLAlchemy for ORM (via Supabase)
- httpx for HTTP client
- pytest + pytest-asyncio for tests
- Pyright for type checking
- Ruff for linting & formatting

## Python Guidelines

- Type hints on ALL functions and methods
- Docstrings for public functions and classes
- Return types always specified (never omit)
- Prefer `from __future__ import annotations` for forward references
- Use `|` syntax for union types (Python 3.10+)
- Use `Decimal` for monetary values and power measurements (MW)

## Project Structure

```
app/
  api/
    __init__.py
    health.py              # Health check
    projects.py            # Starter project endpoints
    electricity.py         # Electricity data endpoints (Phase 2+)
  
  core/
    __init__.py
    auth.py                # Supabase JWT authentication
    config.py              # Environment configuration
  
  integrations/
    __init__.py
    entsoe/
      __init__.py
      constants.py         # Country codes, tech mapping (Phase 2)
      models.py            # Response DTOs (Phase 2)
      client.py            # ENTSO-E HTTP client (Phase 3)
      parser.py            # XML parsing (Phase 3)
  
  models/
    __init__.py
    project.py             # Starter project model
    electricity.py         # ElectricityObservation model (Phase 2)
  
  schemas/
    __init__.py
    project.py             # Project request/response schemas
    electricity.py         # Electricity schemas (Phase 2)
  
  services/
    __init__.py
    project.py             # Starter project service
    electricity.py         # Query service (Phase 5)
    ingestion.py           # Data ingestion (Phase 4)
  
  dependencies.py          # FastAPI dependencies
  main.py                  # Application entry point
```

### GridLens-Specific Modules

- **`integrations/entsoe/`** — ENTSO-E Transparency Platform integration
  - Phase 3: HTTP client + XML parsing
  - Phase 4: Ingestion service with idempotent upserts
  - Phase 5: Query service with aggregations

- **`api/electricity.py`** — REST API endpoints (Phase 2+)
  - GET /api/v1/electricity/countries
  - GET /api/v1/electricity/current/{country_code}
  - GET /api/v1/electricity/generation/{country_code}
  - GET /api/v1/electricity/history/{country_code}?metric=&start=&end=
  - GET /api/v1/electricity/compare?countries=NL,DE&metric=load

## Route Handlers (Thin)

Keep handlers simple (2–5 lines):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.electricity import CurrentStatusResponse
from app.services.electricity import ElectricityService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/electricity", tags=["electricity"])

@router.get("/countries")
async def get_countries() -> list[dict[str, str]]:
    """Get list of supported countries."""
    return [{"code": "NL", "name": "Netherlands"}, ...]

@router.get("/current/{country_code}", response_model=CurrentStatusResponse)
async def get_current_status(
    country_code: str,
    user_id: str = Depends(get_current_user),
    service: ElectricityService = Depends(),
) -> CurrentStatusResponse:
    """Get current electricity status for country."""
    return await service.get_current_status(country_code)
```

**Key Rules**:
- All data endpoints require `Depends(get_current_user)`
- Validate country_code against COUNTRIES dict in constants
- Return appropriate status codes (200, 401, 403, 404, 422)
- Never expose stack traces or sensitive data in errors

## Services (Business Logic)

Encapsulate logic in services. Services take database session and dependencies via `__init__`:

```python
from decimal import Decimal
from datetime import datetime
from app.models.electricity import ElectricityObservation
from app.schemas.electricity import CurrentStatusResponse

class ElectricityService:
    def __init__(self, db):
        self.db = db

    async def get_current_status(self, country_code: str) -> CurrentStatusResponse:
        """Get latest load and generation for country."""
        # Query latest observations
        load = await self.db.query(ElectricityObservation).filter(
            ElectricityObservation.country_code == country_code,
            ElectricityObservation.metric == "load"
        ).order_by(ElectricityObservation.timestamp.desc()).first()
        
        if not load:
            raise ValueError(f"No data for {country_code}")
        
        # Aggregate generation by technology
        generation = await self._get_generation_breakdown(country_code)
        renewable = self._calculate_renewable_percentage(generation)
        
        return CurrentStatusResponse(
            country_code=country_code,
            load_mw=load.value_mw,
            generation=generation,
            renewable_percentage=renewable,
            last_updated=load.timestamp
        )
    
    async def _get_generation_breakdown(self, country_code: str) -> dict[str, Decimal]:
        """Get latest generation by technology."""
        # Implementation in Phase 5
        pass
    
    def _calculate_renewable_percentage(self, generation: dict) -> float:
        """Calculate % of generation from renewable sources."""
        renewable = generation.get("solar", 0) + generation.get("wind_onshore", 0)
        total = sum(generation.values())
        return round(renewable / total * 100, 1) if total > 0 else 0
```

**Service Guidelines**:
- Take database session in `__init__`
- All database queries in service (never in handlers)
- Use `Decimal` for MW values (no floats for measurements)
- Use `datetime` in UTC (never naive datetime)
- Return typed responses (Pydantic schemas)
- Raise appropriate exceptions (ValueError, HTTPException)

## Authentication & Authorization

### GridLens Data Model

- **Public data**: Electricity observations readable by ALL authenticated users
- **No ownership**: Observations are not user-owned (global public data)
- **Backend-only writes**: Only backend services can write (via ingestion)
- **RLS policy**: Database SELECT allowed for all authenticated users, INSERT/UPDATE/DELETE denied

### Get Current User

Use FastAPI dependency injection:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
import jwt

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> str:
    """Extract user ID from Supabase JWT token."""
    try:
        token = credentials.credentials
        # Verify JWT with Supabase
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
```

### Required on All Data Endpoints

```python
@router.get("/current/{country_code}", response_model=CurrentStatusResponse)
async def get_current_status(
    country_code: str,
    user_id: str = Depends(get_current_user),  # ALWAYS require auth
    service: ElectricityService = Depends(),
) -> CurrentStatusResponse:
    """Electricity data requires authentication."""
    return await service.get_current_status(country_code)
```

### Validate Country Code

Always validate against supported countries:

```python
from app.integrations.entsoe.constants import COUNTRIES

if country_code not in COUNTRIES:
    raise HTTPException(status_code=404, detail=f"Country {country_code} not supported")
```

## Pydantic Schemas

Use for request/response validation. Define in `app/schemas/electricity.py`:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

class ElectricityObservationCreate(BaseModel):
    """Schema for ingesting new observations (Phase 4)."""
    country_code: str = Field(..., min_length=2, max_length=2)
    timestamp: datetime
    metric: str = Field(..., pattern="^(load|solar|wind_onshore|wind_offshore|nuclear|gas|coal|hydro|biomass)$")
    value_mw: Decimal = Field(..., ge=0)
    source_dataset: str

class CurrentStatusResponse(BaseModel):
    """Response for current electricity status."""
    country_code: str
    load_mw: Decimal
    renewable_percentage: float
    last_updated: datetime
    generation_breakdown: dict[str, Decimal]

    class Config:
        from_attributes = True
```

**Schema Rules**:
- Use `Decimal` for MW values (precision, not float)
- Use `datetime` for timestamps (always UTC)
- Validate enums with `pattern` or Pydantic Enum
- Set `ge=0` for non-negative values
- Add `Config.from_attributes = True` to work with SQLAlchemy models

## Error Handling

Return appropriate HTTP status codes. Never expose sensitive data or stack traces:

```python
# 400: Bad request (invalid input format)
raise HTTPException(status_code=400, detail="Invalid country code format")

# 401: Unauthorized (missing/invalid auth token)
raise HTTPException(status_code=401, detail="Unauthorized")

# 403: Forbidden (authenticated but data unavailable)
raise HTTPException(status_code=403, detail="Forbidden")

# 404: Not found (country not supported or data missing)
raise HTTPException(status_code=404, detail="Data not found")

# 409: Conflict (duplicate observation during ingestion)
raise HTTPException(status_code=409, detail="Observation already exists")

# 422: Unprocessable entity (Pydantic validation error)
# FastAPI handles this automatically

# 500: Internal server error (log full error, return generic message)
import logging
logger = logging.getLogger(__name__)
logger.error("Failed to fetch ENTSO-E data for NL", exc_info=True)
raise HTTPException(status_code=500, detail="Internal server error")
```

**Logging Rules**:
- ✅ Log: "Error ingesting data for country NL"
- ✅ Log: "Duplicate observation (NL, 2024-01-01 12:00, load)"
- ❌ Never log: API tokens, raw API responses, user credentials
- ❌ Never expose: Stack traces, internal error details, database schema

## Testing (pytest)

All new code requires tests. Three types:

```python
# Unit tests for services and utilities
def test_calculate_renewable_percentage():
    """Test renewable % calculation."""
    service = ElectricityService(db=None)
    generation = {"solar": Decimal(100), "wind_onshore": Decimal(50), "nuclear": Decimal(150)}
    result = service._calculate_renewable_percentage(generation)
    assert result == 37.5  # (100 + 50) / 300 * 100

# Integration tests for API endpoints
@pytest.mark.asyncio
async def test_get_current_status_requires_auth(client):
    """Current status endpoint requires authentication."""
    response = client.get("/api/v1/electricity/current/NL")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_current_status_with_valid_token(client, auth_token):
    """Authenticated user can fetch current status."""
    response = client.get("/api/v1/electricity/current/NL", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    data = response.json()
    assert "load_mw" in data
    assert "renewable_percentage" in data

# Error case tests
@pytest.mark.asyncio
async def test_unsupported_country_returns_404(client, auth_token):
    """Invalid country code returns 404."""
    response = client.get("/api/v1/electricity/current/XX", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 404
```

**Testing Checklist**:
- Unit tests for services and parsing logic
- Integration tests for all endpoints
- Test authentication (401 without token)
- Test validation (422 for invalid input)
- Test error cases (malformed XML, timeouts, API unavailable)
- Aim for 70%+ coverage (not 100%)
- Use fixtures for mock data and mock ENTSO-E responses

## Logging

Log errors and key events for debugging. Never log sensitive data:

```python
import logging

logger = logging.getLogger(__name__)

# ✅ DO: Log meaningful events and errors
logger.info("Ingesting electricity data", extra={"country": "NL", "metric": "load"})
logger.warning("Rate limit approaching for ENTSO-E API")
logger.error("Failed to parse XML response", exc_info=True)

# ❌ DON'T: Log sensitive data
logger.info(f"Using API token: {token}")  # NEVER!
logger.debug(f"API response: {raw_xml}")  # NEVER!
logger.error(f"User {user_email} not found")  # NEVER!
```

**Logging Levels**:
- `INFO`: Key operations ("Data ingested for NL")
- `WARNING`: Recoverable issues ("Timeout, retrying...")
- `ERROR`: Unrecoverable issues ("Cannot parse XML")
- `DEBUG`: Low-level details (not used in production)

## Build and Validation

All must pass before committing:

```bash
# Type checking
pyright app/

# Linting and formatting
ruff check app/
ruff format app/

# Tests
pytest tests/ -v

# Build check
python -m py_compile app/main.py
```

**Never claim validation passed unless you actually ran it.**

## Environment Variables

Document required variables in `.env.example`. Load with pydantic-settings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # ENTSO-E API (only for Phase 3+)
    entsoe_api_token: str | None = None
    
    # Database (optional, defaults to SQLite)
    database_url: str | None = None
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Security**:
- Never commit `.env` (it's in `.gitignore`)
- Never expose `entsoe_api_token` or `service_role_key` in logs
- `anon_key` and `url` are public (safe for frontend)
- Service role key is secret (backend only)
