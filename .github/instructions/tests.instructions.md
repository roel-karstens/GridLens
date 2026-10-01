---
applyTo: "**/*.{test,spec}.{ts,tsx},**/tests/**/*.py"
---

# Testing Instructions — GridLens

## Philosophy

- Write tests for behavior, not implementation
- Meaningful coverage is better than 100% coverage
- Never remove tests to make validation pass
- Bug fixes should include regression tests
- Avoid brittle tests that break with refactoring
- **Electricity domain**: Mock ENTSO-E responses, test parsing, test ingestion idempotency

## Backend Tests (pytest)

### Test Structure

```
tests/
  __init__.py
  conftest.py                           # Fixtures and configuration
  fixtures_electricity.py               # Reusable electricity test data
  test_electricity_models_schemas.py   # Model and schema validation
  test_electricity_database.py         # Database persistence
  test_electricity_api.py              # API endpoint tests
  test_electricity_parser.py           # ENTSO-E XML parsing (Phase 3)
  test_electricity_ingestion.py        # Idempotent upserts (Phase 4)
```

### Service Tests (Phase 5)

Test electricity business logic:

```python
# tests/test_electricity_service.py
import pytest
from decimal import Decimal
from datetime import datetime
from app.services.electricity import ElectricityService
from app.models.electricity import ElectricityObservation

@pytest.fixture
def service(db):
    return ElectricityService(db)

def test_calculate_renewable_percentage():
    """Should calculate renewable % from generation breakdown."""
    service = ElectricityService(db=None)
    generation = {
        "solar": Decimal(100),
        "wind_onshore": Decimal(50),
        "nuclear": Decimal(150)
    }
    result = service._calculate_renewable_percentage(generation)
    assert result == 37.5  # (100 + 50) / 300 * 100

def test_get_current_status_returns_latest_data(service, db):
    """Should return latest load and generation for country."""
    # Insert sample observations
    obs = ElectricityObservation(
        country_code="NL",
        timestamp=datetime.utcnow(),
        metric="load",
        value_mw=Decimal("12345.50"),
        unit="MW",
        source="ENTSO-E",
        source_dataset="Actual Total Load"
    )
    db.add(obs)
    db.commit()
    
    result = service.get_current_status("NL")
    
    assert result.country_code == "NL"
    assert result.load_mw == Decimal("12345.50")
    assert result.last_updated is not None
```

### API Tests

Test endpoints with authentication and public data:

```python
# tests/test_electricity_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Return valid auth headers."""
    return {"Authorization": "Bearer test-token"}

def test_get_countries_public():
    """GET /api/v1/electricity/countries should not require auth."""
    response = client.get("/api/v1/electricity/countries")
    assert response.status_code == 200
    data = response.json()
    assert any(c["code"] == "NL" for c in data)

def test_current_status_requires_auth(client):
    """GET /api/v1/electricity/current/{country} requires authentication."""
    response = client.get("/api/v1/electricity/current/NL")
    assert response.status_code == 401

def test_current_status_with_auth(client, auth_headers):
    """Authenticated user can fetch current status."""
    response = client.get(
        "/api/v1/electricity/current/NL",
        headers=auth_headers
    )
    # May be 200 (if data exists) or 404 (if no data yet)
    assert response.status_code in [200, 404]

def test_unsupported_country_returns_404(client, auth_headers):
    """Invalid country code returns 404."""
    response = client.get(
        "/api/v1/electricity/current/XX",
        headers=auth_headers
    )
    assert response.status_code == 404

def test_invalid_date_range_returns_422(client, auth_headers):
    """Invalid date range returns validation error."""
    response = client.get(
        "/api/v1/electricity/history/NL?metric=load&start=2024-01-01&end=2023-01-01",
        headers=auth_headers
    )
    assert response.status_code == 422
```

### Parser Tests (Phase 3)

Test ENTSO-E XML parsing:

```python
# tests/test_electricity_parser.py
import pytest
from app.integrations.entsoe.parser import ENTSOEParser

@pytest.fixture
def parser():
    return ENTSOEParser()

@pytest.fixture
def sample_load_xml():
    """Mock ENTSO-E A65 response (Actual Total Load)."""
    return """<?xml version="1.0"?>
<Publication>
  <TimeSeries>
    <mRID>NL-load</mRID>
    <Period>
      <timeInterval>
        <start>2024-01-01T00:00Z</start>
        <end>2024-01-01T01:00Z</end>
      </timeInterval>
      <Point>
        <position>1</position>
        <quantity>12000</quantity>  <!-- MW -->
      </Point>
    </Period>
  </TimeSeries>
</Publication>"""

def test_parse_load_xml_valid(parser, sample_load_xml):
    """Parse valid ENTSO-E A65 load response."""
    result = parser.parse_load_xml(sample_load_xml)
    
    assert len(result) > 0
    assert result[0].country_code == "NL"
    assert result[0].metric == "load"
    assert result[0].value_mw == Decimal("12000")

def test_parse_load_xml_malformed(parser):
    """Parse invalid XML raises ValueError."""
    with pytest.raises(ValueError, match="Invalid XML"):
        parser.parse_load_xml("<invalid")
```

### Ingestion Tests (Phase 4)

Test idempotent ingestion:

```python
# tests/test_electricity_ingestion.py
import pytest
from decimal import Decimal
from datetime import datetime
from app.services.ingestion import IngestionService
from app.models.electricity import ElectricityObservation

def test_idempotent_upsert_same_observation_twice(db):
    """Ingesting same observation twice should not create duplicates."""
    service = IngestionService(db)
    
    obs_data = {
        "country_code": "NL",
        "timestamp": datetime.utcnow(),
        "metric": "load",
        "value_mw": Decimal("12345"),
        "source_dataset": "Actual Total Load"
    }
    
    # Ingest same observation twice
    service.upsert_observation(**obs_data)
    service.upsert_observation(**obs_data)
    
    # Should have only one record
    count = db.query(ElectricityObservation).filter(
        ElectricityObservation.country_code == "NL",
        ElectricityObservation.metric == "load"
    ).count()
    assert count == 1
```

### Fixtures

Define reusable test data:

```python
# tests/fixtures_electricity.py
import pytest
from decimal import Decimal
from datetime import datetime
from app.models.electricity import ElectricityObservation

@pytest.fixture
def sample_load_observation(db):
    """Create a sample load observation."""
    obs = ElectricityObservation(
        country_code="NL",
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        metric="load",
        value_mw=Decimal("12000"),
        unit="MW",
        source="ENTSO-E",
        source_dataset="Actual Total Load"
    )
    db.add(obs)
    db.commit()
    return obs

@pytest.fixture
def auth_headers():
    """Return valid auth headers."""
    return {"Authorization": "Bearer test-token"}
```

## Frontend Tests (Vitest)

### Component Tests

Test electricity UI components:

```typescript
// components/ElectricityCard/ElectricityCard.test.tsx
import { render, screen } from '@testing-library/react';
import { ElectricityCard } from './ElectricityCard';

describe('ElectricityCard', () => {
  it('renders country code', () => {
    render(
      <ElectricityCard
        country_code="NL"
        load_mw={10000}
        renewable_percentage={45.5}
        last_updated={new Date()}
      />
    );
    expect(screen.getByText('NL')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(
      <ElectricityCard
        country_code="NL"
        load_mw={0}
        renewable_percentage={0}
        last_updated={new Date()}
        isLoading={true}
      />
    );
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(
      <ElectricityCard
        country_code="NL"
        load_mw={0}
        renewable_percentage={0}
        last_updated={new Date()}
        error="Failed to load data"
      />
    );
    expect(screen.getByText('Failed to load data')).toBeInTheDocument();
  });
});
```

### Hook Tests

Test electricity data fetching:

```typescript
// hooks/useElectricity.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useElectricity } from './useElectricity';
import * as api from '../lib/api';

vi.mock('../lib/api');

describe('useElectricity', () => {
  it('fetches current status on mount', async () => {
    vi.mocked(api.get).mockResolvedValue({
      country_code: 'NL',
      load_mw: 10000,
      renewable_percentage: 45.5,
      last_updated: new Date().toISOString()
    });

    const { result } = renderHook(() => useElectricity('NL'));

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data?.country_code).toBe('NL');
  });

  it('handles API errors', async () => {
    vi.mocked(api.get).mockRejectedValue(
      new Error('Network error')
    );

    const { result } = renderHook(() => useElectricity('NL'));

    await waitFor(() => {
      expect(result.current.error).toBe('Network error');
    });
  });
});
```

### Integration Tests

Test electricity dashboard flows:

```typescript
// pages/Dashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { Dashboard } from './Dashboard';
import * as api from '../lib/api';

vi.mock('../lib/api');

describe('Dashboard page', () => {
  it('displays current electricity status', async () => {
    vi.mocked(api.get).mockResolvedValue({
      country_code: 'NL',
      load_mw: 10000,
      renewable_percentage: 45.5,
      last_updated: new Date().toISOString(),
      generation_breakdown: {
        solar: 500,
        wind_onshore: 200
      }
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('NL')).toBeInTheDocument();
      expect(screen.getByText(/10000/)).toBeInTheDocument();
    });
  });
});
```

## Coverage Goals

Aim for meaningful coverage:

- **Services** (electricity, ingestion): 80%+ coverage
- **Parsers** (ENTSO-E XML): 85%+ coverage (critical data path)
- **API endpoints**: 70%+ coverage (auth, validation)
- **Components** (charts, cards): 60%+ coverage
- **Utilities**: 90%+ coverage

**Never target 100% coverage** if it means writing brittle tests.

## Never Claim Tests Passed Unless Executed

Always run tests before claiming they pass:

```bash
# Frontend
npm run test

# Backend
pytest tests/ -v
```

If tests fail, fix the code. Do not modify tests to make them pass.

## Regression Tests

When fixing a bug, add a test that reproduces it:

```python
# Example: Bug where same observation ingested twice created duplicates
def test_idempotent_upsert_handles_duplicates():
    """Regression: Ensure duplicate observations are prevented."""
    service = IngestionService(db)
    obs = {"country_code": "NL", "timestamp": ..., "metric": "load", ...}
    
    service.upsert_observation(**obs)
    service.upsert_observation(**obs)  # Same observation again
    
    count = db.query(ElectricityObservation).filter(...).count()
    assert count == 1  # Should be 1, not 2
```

```python
def test_project_update_requires_ownership(client, auth_headers):
    """
    Regression test for bug #42: Users could update projects they didn't own.
    """
    # Create project as user-123
    other_user_project_id = "other-user-project-id"
    
    # Try to update as different user
    response = client.patch(
        f"/api/v1/projects/{other_user_project_id}",
        json={"name": "Hacked"},
        headers=auth_headers
    )
    
    # Should be forbidden
    assert response.status_code == 403
```

## Test Organization

- One test file per module/component
- Related tests in same `describe` block
- Clear test names that describe behavior
- Use `# Arrange, Act, Assert` comments for clarity
