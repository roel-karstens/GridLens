/**
 * Historical electricity data page.
 */

import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { APIClient } from '../lib/api';

interface HistoricalData {
  country_code: string;
  metric: string;
  start_time: string;
  end_time: string;
  observations: Array<{ timestamp: string; value_mw: number }>;
  count: number;
}

/**
 * Page for viewing historical electricity data.
 * Allows user to select a country, metric, and date range for analysis.
 */
export function HistoryPage() {
  const [selectedCountry, setSelectedCountry] = useState<string>('NL');
  const [metric, setMetric] = useState<string>('load');
  const [startDate, setStartDate] = useState<string>(
    new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );

  const [data, setData] = useState<HistoricalData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch historical data
  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const client = new APIClient();
        const params = new URLSearchParams({
          metric,
          start: `${startDate}T00:00:00Z`,
          end: `${endDate}T23:59:59Z`,
        });
        const response = await client.get<HistoricalData>(
          `/api/v1/electricity/history/${selectedCountry}?${params}`
        );
        setData(response);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load data';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, [selectedCountry, metric, startDate, endDate]);

  // Format data for chart
  const chartData = data?.observations.map((obs) => ({
    time: new Date(obs.timestamp).toLocaleTimeString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    value: obs.value_mw / 1000, // Convert to GW
  })) || [];

  const metricLabel = metric.replace('_', ' ').toUpperCase();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Historical Data Analysis
          </h1>
          <p className="text-gray-600">
            View electricity trends over time
          </p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Country Selector */}
            <div>
              <label className="block font-semibold text-gray-700 mb-2">Country</label>
              <select
                value={selectedCountry}
                onChange={(e) => setSelectedCountry(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="NL">Netherlands (NL)</option>
                <option value="DE">Germany (DE)</option>
                <option value="BE">Belgium (BE)</option>
                <option value="FR">France (FR)</option>
              </select>
            </div>

            {/* Metric Selector */}
            <div>
              <label className="block font-semibold text-gray-700 mb-2">Metric</label>
              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="load">Demand (Load)</option>
                <option value="solar">Solar</option>
                <option value="wind_onshore">Wind Onshore</option>
                <option value="wind_offshore">Wind Offshore</option>
                <option value="nuclear">Nuclear</option>
                <option value="gas">Natural Gas</option>
                <option value="coal">Coal</option>
                <option value="hydro">Hydro</option>
                <option value="biomass">Biomass</option>
              </select>
            </div>

            {/* Start Date */}
            <div>
              <label className="block font-semibold text-gray-700 mb-2">Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* End Date */}
            <div>
              <label className="block font-semibold text-gray-700 mb-2">End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Chart */}
        {isLoading && (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            <p className="mt-4">Loading historical data...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-red-800">
            <p><strong>Error:</strong> {error}</p>
          </div>
        )}

        {data && chartData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              {selectedCountry} - {metricLabel}
            </h2>
            <p className="text-gray-600 mb-4">
              {data.count} observations from {startDate} to {endDate}
            </p>

            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="time"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  label={{ value: `${metricLabel} (GW)`, angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  formatter={(value: number) => `${value.toFixed(2)} GW`}
                  labelFormatter={(label) => `Time: ${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#2196F3"
                  dot={false}
                  name={metricLabel}
                  isAnimationActive={true}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {data && chartData.length === 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-yellow-800">
            <p>No data available for the selected period and metric.</p>
          </div>
        )}
      </div>
    </div>
  );
}
