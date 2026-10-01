/**
 * Current electricity status card component.
 */

import React from 'react';
import { ElectricityStatus } from '../hooks/useElectricity';

interface ElectricityCardProps {
  countryCode: string;
  data?: ElectricityStatus;
  isLoading?: boolean;
  error?: string;
}

/**
 * Card displaying current electricity status.
 * Shows demand, total generation, renewable percentage, and key sources.
 */
export const ElectricityCard: React.FC<ElectricityCardProps> = ({
  countryCode,
  data,
  isLoading = false,
  error,
}) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading data for {countryCode}...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-600">
          <p className="font-semibold">Error loading data</p>
          <p className="text-sm mt-2">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-gray-500">
          <p>No data available for {countryCode}</p>
        </div>
      </div>
    );
  }

  const renewablePercent = data.renewable_share_percent ?? 0;
  const lastUpdate = new Date(data.last_updated).toLocaleTimeString();

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800">{countryCode}</h2>
        <span className="text-sm text-gray-500">Updated: {lastUpdate}</span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Current Demand */}
        <div className="border-l-4 border-blue-500 pl-4">
          <p className="text-gray-500 text-sm">Current Demand</p>
          <p className="text-2xl font-bold text-gray-800">
            {data.load_mw ? `${(data.load_mw / 1000).toFixed(1)} GW` : '—'}
          </p>
        </div>

        {/* Total Generation */}
        <div className="border-l-4 border-green-500 pl-4">
          <p className="text-gray-500 text-sm">Total Generation</p>
          <p className="text-2xl font-bold text-gray-800">
            {data.total_generation_mw ? `${(data.total_generation_mw / 1000).toFixed(1)} GW` : '—'}
          </p>
        </div>
      </div>

      {/* Renewable Percentage */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <p className="text-gray-600 font-semibold">Renewable Share</p>
          <p className="text-2xl font-bold text-green-600">{renewablePercent.toFixed(1)}%</p>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-green-500 h-3 rounded-full transition-all duration-500"
            style={{ width: `${Math.min(renewablePercent, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Generation Breakdown */}
      <div className="grid grid-cols-3 gap-3 text-sm">
        {[
          { label: 'Solar', value: data.solar_mw },
          { label: 'Wind', value: (data.wind_onshore_mw ?? 0) + (data.wind_offshore_mw ?? 0) },
          { label: 'Nuclear', value: data.nuclear_mw },
          { label: 'Hydro', value: data.hydro_mw },
          { label: 'Gas', value: data.gas_mw },
          { label: 'Coal', value: data.coal_mw },
        ].map((source) => (
          <div key={source.label} className="bg-gray-50 p-3 rounded">
            <p className="text-gray-600 text-xs">{source.label}</p>
            <p className="text-gray-800 font-semibold">
              {source.value ? `${(source.value / 1000).toFixed(2)} GW` : '—'}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
