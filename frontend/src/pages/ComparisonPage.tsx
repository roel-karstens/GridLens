/**
 * Country comparison page for Phase 7.
 */

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { APIClient } from '../lib/api';

/**
 * Page for comparing electricity metrics across multiple countries.
 */
export function ComparisonPage() {
  const [selectedCountries, setSelectedCountries] = useState<string[]>(['NL', 'DE', 'BE', 'FR']);
  const [metric, setMetric] = useState<string>('load');
  const [data, setData] = useState<Array<{ country: string; load: number; renewable: number; generation: number }> | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch comparison data
  useEffect(() => {
    const fetchComparison = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const client = new APIClient();
        
        // Fetch current status for each country
        const results: Array<{ country: string; load: number; renewable: number; generation: number }> = [];
        for (const country of selectedCountries) {
          try {
            const status = await client.get<{ load_mw: number | null; renewable_share_percent: number | null; total_generation_mw: number | null }>(`/api/v1/electricity/current/${country}`);
            results.push({
              country: country,
              load: typeof status.load_mw === 'number' ? status.load_mw / 1000 : 0,
              renewable: typeof status.renewable_share_percent === 'number' ? status.renewable_share_percent : 0,
              generation: typeof status.total_generation_mw === 'number' ? status.total_generation_mw / 1000 : 0,
            });
          } catch (error) {
            // Continue with other countries if one fails
            console.warn(`Failed to fetch data for ${country}: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
        }
        
        setData(results);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load comparison data';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    if (selectedCountries.length > 0) {
      fetchComparison();
    }
  }, [selectedCountries]);

  const toggleCountry = (countryCode: string) => {
    setSelectedCountries((prev) =>
      prev.includes(countryCode)
        ? prev.filter((c) => c !== countryCode)
        : [...prev, countryCode]
    );
  };



  const metricLabel = {
    load: 'Demand (GW)',
    renewable: 'Renewable Share (%)',
    generation: 'Total Generation (GW)',
  }[metric] || metric;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            Country Comparison
          </h1>
          <p className="text-slate-600">
            Compare electricity metrics across European countries
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="mb-4">
            <label className="block font-semibold text-gray-700 mb-2">
              Select Metric
            </label>
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="load">Current Demand</option>
              <option value="renewable">Renewable Share %</option>
              <option value="generation">Total Generation</option>
            </select>
          </div>

          <div>
            <label className="block font-semibold text-gray-700 mb-2">
              Select Countries
            </label>
            <div className="flex flex-wrap gap-2">
              {['NL', 'DE', 'BE', 'FR'].map((country) => (
                <button
                  key={country}
                  onClick={() => toggleCountry(country)}
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    selectedCountries.includes(country)
                      ? 'bg-violet-600 text-white hover:bg-violet-700'
                      : 'bg-slate-200 text-slate-800 hover:bg-slate-300'
                  }`}
                >
                  {country}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Chart */}
        {isLoading && (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            <p className="mt-4">Loading comparison data...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-800">
            <p><strong>Error:</strong> {error}</p>
          </div>
        )}

        {data && data.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">{metricLabel}</h2>

            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="country" />
                <YAxis
                  label={{ value: metricLabel, angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: number) => value.toFixed(2)}
                  labelFormatter={(label) => `Country: ${label}`}
                />
                <Legend />
                <Bar
                  dataKey={metric === 'load' ? 'load' : metric === 'renewable' ? 'renewable' : 'generation'}
                  fill="#2196F3"
                  name={metricLabel}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {data && data.length === 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-yellow-800">
            <p>No data available for the selected countries.</p>
          </div>
        )}

        {/* Comparison Table */}
        {data && data.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Detailed Comparison</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-gray-300">
                    <th className="px-4 py-2 text-left font-semibold text-gray-700">Country</th>
                    <th className="px-4 py-2 text-right font-semibold text-gray-700">Demand (GW)</th>
                    <th className="px-4 py-2 text-right font-semibold text-gray-700">Renewable %</th>
                    <th className="px-4 py-2 text-right font-semibold text-gray-700">Generation (GW)</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((row) => (
                    <tr key={row.country} className="border-b border-gray-200 hover:bg-gray-50">
                      <td className="px-4 py-3 font-semibold text-gray-800">{row.country}</td>
                      <td className="px-4 py-3 text-right text-gray-600">
                        {row.load.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">
                        {row.renewable.toFixed(1)}%
                      </td>
                      <td className="px-4 py-3 text-right text-gray-600">
                        {row.generation.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
