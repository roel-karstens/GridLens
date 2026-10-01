/**
 * Custom hook for fetching electricity data.
 */

import { useEffect, useState } from 'react';
import { APIClient } from '../lib/api';

export interface ElectricityStatus {
  country_code: string;
  timestamp: string;
  load_mw: number | null;
  total_generation_mw: number | null;
  renewable_generation_mw: number | null;
  renewable_share_percent: number | null;
  solar_mw: number | null;
  wind_onshore_mw: number | null;
  wind_offshore_mw: number | null;
  nuclear_mw: number | null;
  gas_mw: number | null;
  coal_mw: number | null;
  hydro_mw: number | null;
  biomass_mw: number | null;
  other_mw: number | null;
  last_updated: string;
}

export interface GenerationMix {
  country_code: string;
  timestamp: string;
  generation_by_type: Record<string, number>;
  total_generation_mw: number;
  source: string;
}

export type AsyncState<T> = 
  | { state: 'loading' }
  | { state: 'loaded'; data: T }
  | { state: 'error'; error: string };

/**
 * Hook to fetch current electricity status for a country.
 */
export function useElectricity(countryCode: string): AsyncState<ElectricityStatus> {
  const [status, setStatus] = useState<AsyncState<ElectricityStatus>>({ state: 'loading' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const client = new APIClient();
        const data = await client.get<ElectricityStatus>(
          `/api/v1/electricity/current/${countryCode}`
        );
        setStatus({ state: 'loaded', data });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch data';
        setStatus({ state: 'error', error: message });
      }
    };

    fetchData();
  }, [countryCode]);

  return status;
}

/**
 * Hook to fetch generation mix for a country.
 */
export function useGenerationMix(countryCode: string): AsyncState<GenerationMix> {
  const [status, setStatus] = useState<AsyncState<GenerationMix>>({ state: 'loading' });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const client = new APIClient();
        const data = await client.get<GenerationMix>(
          `/api/v1/electricity/generation/${countryCode}`
        );
        setStatus({ state: 'loaded', data });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to fetch data';
        setStatus({ state: 'error', error: message });
      }
    };

    fetchData();
  }, [countryCode]);

  return status;
}
