---
applyTo: "supabase/**/*.sql"
---

# Database Instructions — GridLens

## Migrations

All schema changes go through numbered migrations in `supabase/migrations/`:

```
0001_initial_schema.sql          # Projects table (starter)
0002_electricity_schema.sql      # ElectricityObservation table (Phase 2)
0003_add_indices.sql             # Performance indexes (Phase 2+)
```

### GridLens Approach: Auto-Migrations via Python (SQLAlchemy)

GridLens uses auto-creating schema from Python models:

**Pattern**: Tables defined in `backend/app/models/` are auto-created on backend startup.

**Advantages**:
- ✅ Development/local testing (zero-friction setup)
- ✅ Rapid prototyping with frequent schema changes
- ✅ Type-safe schema definitions (models are the source of truth)

**For production**:
- Consider Alembic to generate SQL migrations from models
- Or run migrations manually in Supabase

See [ADR-002](../../docs/decisions/ADR-002-auto-migrations-via-python.md) for trade-off analysis.

## Writing Migrations

- Idempotent: Safe to run multiple times
- Include both schema and RLS
- Add comments explaining the purpose
- Test locally before committing
- No destructive changes without approval

Example (electricity_observations table):

```sql
-- 0002_electricity_schema.sql

-- Create electricity_observations table
CREATE TABLE IF NOT EXISTS electricity_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  country_code text NOT NULL,
  timestamp timestamp with time zone NOT NULL,
  metric text NOT NULL,
  value_mw numeric(12,2) NOT NULL,
  unit text NOT NULL DEFAULT 'MW',
  source text NOT NULL DEFAULT 'ENTSO-E',
  source_dataset text NOT NULL,
  source_timestamp timestamp with time zone NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  
  -- Prevent duplicate observations
  UNIQUE(country_code, timestamp, metric),
  
  -- Ensure valid values
  CHECK (value_mw >= 0),
  CHECK (country_code ~ '^[A-Z]{2}$'),  -- 2-letter country code
  CHECK (metric IN ('load', 'solar', 'wind_onshore', 'wind_offshore', 'nuclear', 'gas', 'coal', 'hydro', 'biomass'))
);

-- Enable RLS
ALTER TABLE electricity_observations ENABLE ROW LEVEL SECURITY;

-- RLS: All authenticated users can read electricity data (public data)
CREATE POLICY "authenticated_read" ON electricity_observations
  FOR SELECT USING (auth.role() = 'authenticated');

-- RLS: Deny INSERT/UPDATE/DELETE from API (backend only)
CREATE POLICY "deny_insert" ON electricity_observations
  FOR INSERT WITH CHECK (false);
CREATE POLICY "deny_update" ON electricity_observations
  FOR UPDATE WITH CHECK (false);
CREATE POLICY "deny_delete" ON electricity_observations
  FOR DELETE USING (false);

-- Indexes for common queries
CREATE INDEX idx_country_timestamp ON electricity_observations(country_code, timestamp DESC);
CREATE INDEX idx_metric_timestamp ON electricity_observations(metric, timestamp DESC);
CREATE INDEX idx_country_metric_timestamp ON electricity_observations(country_code, metric, timestamp DESC);
CREATE INDEX idx_timestamp ON electricity_observations(timestamp DESC);
```

## Schema Design

### GridLens: Public Data Model

Unlike typical apps, GridLens electricity observations are **public**:
- All authenticated users can read the same data
- No `owner_id` or user-specific access control needed
- Backend-only writes (no API INSERT/UPDATE/DELETE)

### Primary Keys

Use UUID with `gen_random_uuid()`:

```sql
CREATE TABLE electricity_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  ...
);
```

### Uniqueness Constraints

Prevent duplicate observations:

```sql
CREATE TABLE electricity_observations (
  ...
  country_code text NOT NULL,
  timestamp timestamp with time zone NOT NULL,
  metric text NOT NULL,
  ...
  UNIQUE(country_code, timestamp, metric)
);
```

This ensures same observation can't be inserted twice (critical for idempotent ingestion).

### Timestamps

Track creation and updates:

```sql
CREATE TABLE electricity_observations (
  ...
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
);
```

All timestamps stored in UTC (`timestamp with time zone`).

### Constraints

Enforce data integrity:

```sql
CREATE TABLE electricity_observations (
  ...
  value_mw numeric(12,2) NOT NULL,
  CHECK (value_mw >= 0),  -- Power must be non-negative
  
  country_code text NOT NULL,
  CHECK (country_code ~ '^[A-Z]{2}$'),  -- 2-letter country code
  
  metric text NOT NULL,
  CHECK (metric IN ('load', 'solar', 'wind_onshore', ...)),  -- Valid metrics only
);
```

## Row Level Security (RLS)

### GridLens Data Access Model

- **Public read**: All authenticated users can read electricity data
- **Backend-only write**: Only backend services write (no API INSERT/UPDATE/DELETE)

```sql
ALTER TABLE electricity_observations ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read all observations
CREATE POLICY "authenticated_read" ON electricity_observations
  FOR SELECT USING (auth.role() = 'authenticated');

-- Deny INSERT from API (backend only)
CREATE POLICY "deny_insert" ON electricity_observations
  FOR INSERT WITH CHECK (false);

-- Deny UPDATE from API
CREATE POLICY "deny_update" ON electricity_observations
  FOR UPDATE WITH CHECK (false);

-- Deny DELETE from API
CREATE POLICY "deny_delete" ON electricity_observations
  FOR DELETE USING (false);
```

## Indexes

Add indexes for common queries (Phase 2):

```sql
-- Query by country and timestamp (latest load for NL)
CREATE INDEX idx_country_timestamp ON electricity_observations(country_code, timestamp DESC);

-- Query by metric and timestamp (all solar observations)
CREATE INDEX idx_metric_timestamp ON electricity_observations(metric, timestamp DESC);

-- Query by all three (load for NL in date range)
CREATE INDEX idx_country_metric_timestamp ON electricity_observations(country_code, metric, timestamp DESC);

-- Pure timestamp queries (all observations in timeframe)
CREATE INDEX idx_timestamp ON electricity_observations(timestamp DESC);
```

**Index Strategy**: Start with the most common queries (country + timestamp), add more as needed.

## Testing RLS Locally

In Supabase Studio or psql:

```sql
-- Set a specific user role
SET request.jwt.claims = '{"sub":"user-uuid","role":"authenticated"}';

-- Queries now respect RLS
SELECT * FROM electricity_observations WHERE country_code = 'NL';  -- Works

-- Try to insert (should fail)
INSERT INTO electricity_observations (...) VALUES (...);  -- Denied by RLS
```

## No Destructive Changes

Never drop columns or tables without explicit approval:

```sql
-- ✅ Safe: Add column with default
ALTER TABLE electricity_observations ADD COLUMN new_field text DEFAULT 'value';

-- ❌ Unsafe: Drop column
ALTER TABLE electricity_observations DROP COLUMN deprecated_field;

-- ❌ Unsafe: Drop table
DROP TABLE electricity_observations;
```

If removal is necessary, propose the migration with:
1. Clear reason
2. Backup plan  
3. Rollback strategy
4. Data migration path
