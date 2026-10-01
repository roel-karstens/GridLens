-- GridLens: Electricity observations schema
-- Stores normalized electricity data from ENTSO-E Transparency Platform
-- Source: ENTSO-E REST API (XML responses)
-- Supports: demand (load), generation by type (solar, wind, gas, nuclear, hydro, biomass, coal, other)

-- Create electricity_observations table
-- Stores normalized electricity metrics for each country and timestamp
CREATE TABLE IF NOT EXISTS public.electricity_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Geography
  country_code text NOT NULL,  -- ISO 2-letter code: NL, DE, BE, FR
  
  -- Time (all UTC)
  timestamp timestamp with time zone NOT NULL,  -- UTC time of the observation
  source_timestamp timestamp with time zone,     -- When ENTSO-E generated this data
  
  -- Metric
  metric text NOT NULL,  -- e.g., "load", "solar", "wind_onshore", "wind_offshore", "nuclear", "gas", "coal", "hydro", "biomass", "other"
  
  -- Value
  value_mw numeric NOT NULL,  -- Megawatts
  unit text NOT NULL DEFAULT 'MW',
  
  -- Source attribution
  source text NOT NULL DEFAULT 'ENTSO-E',  -- Data source
  source_dataset text NOT NULL,  -- e.g., "Actual Total Load", "Aggregated Generation Per Type"
  
  -- Audit timestamps
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  
  -- Unique constraint: prevent duplicate observations for the same logical data point
  -- (country + timestamp + metric must be unique)
  UNIQUE(country_code, timestamp, metric)
);

-- Enable Row Level Security
ALTER TABLE public.electricity_observations ENABLE ROW LEVEL SECURITY;

-- RLS Policy: All authenticated users can read electricity observations (data is public)
CREATE POLICY "authenticated_read_electricity_observations" ON public.electricity_observations
  FOR SELECT
  USING (auth.role() = 'authenticated');

-- RLS Policy: Prevent INSERT/UPDATE/DELETE via API (only backend ingestion writes data)
CREATE POLICY "electricity_observations_no_public_write" ON public.electricity_observations
  FOR INSERT
  WITH CHECK (false);

CREATE POLICY "electricity_observations_no_public_update" ON public.electricity_observations
  FOR UPDATE
  USING (false);

CREATE POLICY "electricity_observations_no_public_delete" ON public.electricity_observations
  FOR DELETE
  USING (false);

-- Create indexes for query performance
-- Index 1: Query by country (for current demand/generation by country)
CREATE INDEX idx_electricity_country_timestamp ON public.electricity_observations(country_code, timestamp DESC);

-- Index 2: Query by metric (for specific metric queries across countries)
CREATE INDEX idx_electricity_metric_timestamp ON public.electricity_observations(metric, timestamp DESC);

-- Index 3: Query by country and metric (common combined query)
CREATE INDEX idx_electricity_country_metric_timestamp ON public.electricity_observations(country_code, metric, timestamp DESC);

-- Index 4: Timestamp range queries (for history views)
CREATE INDEX idx_electricity_timestamp ON public.electricity_observations(timestamp DESC);

-- Add comment for documentation
COMMENT ON TABLE public.electricity_observations IS 'Normalized electricity observations from ENTSO-E. Data is public and read-only via API.';
COMMENT ON COLUMN public.electricity_observations.country_code IS 'ISO 2-letter country code (NL, DE, BE, FR)';
COMMENT ON COLUMN public.electricity_observations.timestamp IS 'UTC timestamp of the observation (aligned to quarter-hour or hour)';
COMMENT ON COLUMN public.electricity_observations.metric IS 'Electricity metric: load (demand) or generation type (solar, wind_onshore, etc.)';
COMMENT ON COLUMN public.electricity_observations.value_mw IS 'Value in megawatts (MW)';
COMMENT ON COLUMN public.electricity_observations.source_dataset IS 'ENTSO-E document type: "Actual Total Load" or "Aggregated Generation Per Type"';
