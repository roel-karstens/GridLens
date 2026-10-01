/**
 * Generation mix visualization with Recharts.
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface GenerationChartProps {
  data: Record<string, number>;
  title?: string;
}

const COLORS: Record<string, string> = {
  solar: '#FDD835',
  wind_onshore: '#42A5F5',
  wind_offshore: '#1976D2',
  nuclear: '#FFB74D',
  gas: '#66BB6A',
  coal: '#757575',
  hydro: '#29B6F6',
  biomass: '#8BC34A',
  other: '#BDBDBD',
};

/**
 * Stacked bar chart showing generation breakdown by technology.
 */
export const GenerationChart: React.FC<GenerationChartProps> = ({
  data,
  title = 'Generation Mix',
}) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500 text-center">No generation data available</p>
      </div>
    );
  }

  // Format data for Recharts (single point)
  const chartData = [
    {
      name: 'Generation',
      ...Object.entries(data).reduce((acc, [key, value]) => ({
        ...acc,
        [key]: value / 1000, // Convert to GW
      }), {}),
    },
  ];

  const technologies = Object.keys(data).sort();

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis label={{ value: 'Generation (GW)', angle: -90, position: 'insideLeft' }} />
          <Tooltip
            formatter={(value: number) => `${value.toFixed(2)} GW`}
            labelFormatter={() => 'Generation Mix'}
          />
          <Legend />
          {technologies.map((tech) => (
            <Bar
              key={tech}
              dataKey={tech}
              stackId="generation"
              fill={COLORS[tech] || '#999'}
              name={tech.replace('_', ' ').charAt(0).toUpperCase() + tech.replace('_', ' ').slice(1)}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* Technology legend with colors */}
      <div className="grid grid-cols-3 gap-2 mt-4 text-sm">
        {technologies.map((tech) => (
          <div key={tech} className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded"
              style={{ backgroundColor: COLORS[tech] || '#999' }}
            ></div>
            <span className="text-gray-700">
              {tech.replace('_', ' ').charAt(0).toUpperCase() + tech.replace('_', ' ').slice(1)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
