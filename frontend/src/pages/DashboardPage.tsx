/**
 * Main electricity dashboard page.
 */

import React, { useState } from 'react';
import { ElectricityCard } from '../components/ElectricityCard';
import { GenerationChart } from '../components/GenerationChart';
import { CountrySelector } from '../components/CountrySelector';
import { useElectricity, useGenerationMix } from '../hooks/useElectricity';

/**
 * Main dashboard page showing current electricity status and generation mix.
 * Allows user to select a country and view its real-time electricity data.
 */
export function DashboardPage() {
  const [selectedCountry, setSelectedCountry] = useState<string>('NL');

  // Fetch data
  const statusData = useElectricity(selectedCountry);
  const mixData = useGenerationMix(selectedCountry);

  // Extract state
  const statusLoading = statusData.state === 'loading';
  const statusError = statusData.state === 'error' ? statusData.error : undefined;
  const status = statusData.state === 'loaded' ? statusData.data : undefined;

  const mixLoading = mixData.state === 'loading';
  const mixError = mixData.state === 'error' ? mixData.error : undefined;
  const mix = mixData.state === 'loaded' ? mixData.data : undefined;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            European Electricity Explorer
          </h1>
          <p className="text-slate-600">
            Real-time electricity data from ENTSO-E Transparency Platform
          </p>
        </div>

        {/* Country Selector */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-8">
          <CountrySelector
            selectedCountry={selectedCountry}
            onSelectCountry={setSelectedCountry}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Status Card - spans 2 columns */}
          <div className="lg:col-span-2">
            <ElectricityCard
              countryCode={selectedCountry}
              data={status}
              isLoading={statusLoading}
              error={statusError}
            />
          </div>

          {/* Info Panel */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-800 mb-4">About This Dashboard</h3>
            <div className="space-y-3 text-sm text-gray-600">
              <p>
                <strong className="text-gray-800">Current Demand:</strong> The electricity load
                consumed by the country (real-time data).
              </p>
              <p>
                <strong className="text-gray-800">Generation:</strong> Total electricity
                production by all sources (data availability limited).
              </p>
              <p>
                <strong className="text-gray-800">Renewable Share:</strong> Percentage of
                generation from renewable sources.
              </p>
              <p className="text-xs text-gray-500 pt-3 border-t">
                ⚡ Demand data: Available from ENTSO-E Actual Total Load (A65)
              </p>
              <p className="text-xs text-gray-500">
                📊 Generation data: Limited availability from intraday generation dataset
              </p>
            </div>
          </div>
        </div>

        {/* Generation Chart */}
        {mix && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <GenerationChart
              data={mix.generation_by_type}
              title={`Generation Mix - ${selectedCountry}`}
            />
          </div>
        )}

        {/* Data not available message */}
        {mixLoading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center text-blue-800">
            <p>Loading generation data...</p>
          </div>
        )}

        {mixError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center text-red-800">
            <p>Could not load generation data: {mixError}</p>
          </div>
        )}
      </div>
    </div>
  );
}
