/**
 * Country selector dropdown component.
 */

import React, { useState, useEffect } from 'react';
import { APIClient } from '../lib/api';

interface CountrySelectorProps {
  onSelectCountry: (countryCode: string) => void;
  selectedCountry?: string;
  disabled?: boolean;
}

interface Country {
  code: string;
  name: string;
}

/**
 * Dropdown to select an electricity country.
 */
export const CountrySelector: React.FC<CountrySelectorProps> = ({
  onSelectCountry,
  selectedCountry = 'NL',
  disabled = false,
}) => {
  const [countries, setCountries] = useState<Country[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const client = new APIClient();
        const data = await client.get<Country[]>('/api/v1/electricity/countries');
        setCountries(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load countries';
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCountries();
  }, []);

  if (error) {
    return (
      <div className="p-2 bg-red-50 border border-red-200 rounded text-red-600 text-sm">
        {error}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="country-select" className="font-semibold text-gray-700">
        Select Country
      </label>
      <select
        id="country-select"
        value={selectedCountry}
        onChange={(e) => onSelectCountry(e.target.value)}
        disabled={disabled || isLoading}
        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        {countries.map((country) => (
          <option key={country.code} value={country.code}>
            {country.name} ({country.code})
          </option>
        ))}
      </select>
    </div>
  );
};
