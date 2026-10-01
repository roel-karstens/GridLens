---
applyTo: "frontend/**/*.{ts,tsx}"
---

# Frontend Development Instructions — GridLens

## Technology Stack

- React 18 with TypeScript
- Vite for builds
- Recharts for data visualization
- Tailwind CSS for styling
- Vitest for tests
- ESLint for code quality

## TypeScript Guidelines

- Strict mode enabled
- No `any` types without documentation
- All function parameters typed
- All return types specified
- Export types for reusable components
- Use discriminated unions for state (`'loading' | 'loaded' | 'error'`)
- Type Recharts props correctly

## Component Conventions

### Structure

```
components/
  ElectricityCard/
    ElectricityCard.tsx       # Component
    ElectricityCard.types.ts  # Props and types
    index.ts                  # Exports
  
  GenerationChart/
    GenerationChart.tsx       # Recharts stacked area chart
    index.ts
  
  CountrySelector/
    CountrySelector.tsx       # Country dropdown
    index.ts
```

### Props and Types

```typescript
// components/ElectricityCard/ElectricityCard.types.ts
export interface ElectricityCardProps {
  country_code: string;
  load_mw: number;
  renewable_percentage: number;
  last_updated: Date;
  isLoading?: boolean;
  error?: string | null;
}

// components/ElectricityCard/ElectricityCard.tsx
export function ElectricityCard({
  country_code,
  load_mw,
  renewable_percentage,
  last_updated,
  isLoading,
  error
}: ElectricityCardProps) {
  // Discriminated union pattern for state
  if (isLoading) return <div className="animate-pulse">Loading...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  
  return (
    <div className="border rounded p-4">
      <h3>{country_code}</h3>
      <p>Load: {load_mw} MW</p>
      <p>Renewable: {renewable_percentage}%</p>
      <small>Updated: {last_updated.toLocaleString()}</small>
    </div>
  );
}
```

### Recharts Components

For charts (Phase 6+):

```typescript
import { AreaChart, Area, CartesianGrid, Tooltip, Legend } from 'recharts';

interface GenerationChartProps {
  data: Array<{
    timestamp: string;
    solar: number;
    wind_onshore: number;
    nuclear: number;
  }>;
  width?: number;
  height?: number;
}

export function GenerationChart({ data, width = 600, height = 300 }: GenerationChartProps) {
  return (
    <AreaChart width={width} height={height} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <Tooltip />
      <Legend />
      <Area type="monotone" dataKey="solar" stackId="1" stroke="#fbbf24" />
      <Area type="monotone" dataKey="wind_onshore" stackId="1" stroke="#0ea5e9" />
      <Area type="monotone" dataKey="nuclear" stackId="1" stroke="#ef4444" />
    </AreaChart>
  );
}
```

### State Management

- Use React hooks (`useState`, `useContext`)
- Keep state close to where it's used
- Avoid unnecessary prop drilling
- Extract to custom hooks for reusable logic (e.g., `useElectricity`)
- Use discriminated unions for async state

```typescript
// Discriminated union for async state
type AsyncState<T> = 
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'loaded'; data: T }
  | { status: 'error'; error: string };

// Usage in hook
function useElectricity(countryCode: string) {
  const [state, setState] = useState<AsyncState<CurrentStatus>>({ status: 'idle' });
  
  useEffect(() => {
    setState({ status: 'loading' });
    api.get(`/api/v1/electricity/current/${countryCode}`)
      .then(data => setState({ status: 'loaded', data }))
      .catch(error => setState({ status: 'error', error: error.message }));
  }, [countryCode]);
  
  return state;
}

// Usage in component
export function Dashboard() {
  const state = useElectricity('NL');
  
  switch (state.status) {
    case 'idle': return null;
    case 'loading': return <div>Loading...</div>;
    case 'loaded': return <ElectricityCard {...state.data} />;
    case 'error': return <div>Error: {state.error}</div>;
  }
}
```

## API Integration

All HTTP calls go through a typed API client in `lib/api.ts`:

```typescript
// lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class APIClient {
  private getHeaders(): Record<string, string> {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    };
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    return response.json();
  }
}

export const api = new APIClient();
```

### GridLens-Specific Hooks

```typescript
// hooks/useElectricity.ts
import { useEffect, useState } from 'react';
import { api } from '../lib/api';

interface CurrentStatus {
  country_code: string;
  load_mw: number;
  renewable_percentage: number;
  last_updated: string;
  generation_breakdown: Record<string, number>;
}

export function useElectricity(countryCode: string) {
  const [data, setData] = useState<CurrentStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.get<CurrentStatus>(
          `/api/v1/electricity/current/${countryCode}`
        );
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [countryCode]);

  return { data, loading, error };
}
```

## Async and Loading States

Every async operation needs state. Use discriminated unions:

```typescript
// BadExample (three separate states)
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
const [data, setData] = useState<Data | null>(null);

// GoodExample (discriminated union)
type State<T> = 
  | { status: 'loading' }
  | { status: 'loaded'; data: T }
  | { status: 'error'; error: string };

const [state, setState] = useState<State<Data>>({ status: 'loading' });

// Render:
switch (state.status) {
  case 'loading':
    return <div className="animate-pulse">Loading...</div>;
  case 'error':
    return <div className="text-red-500">Error: {state.error}</div>;
  case 'loaded':
    return <div>{/* render state.data */}</div>;
}
```

**Never render data without checking loading/error state first.**

## Authentication

- Supabase Auth integration via custom hook
- Store auth state in context or localStorage
- Attach JWT to API requests (see APIClient above)
- Handle 401 responses gracefully (redirect to login)

```typescript
// hooks/useAuth.ts
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in (from localStorage or session)
    const token = localStorage.getItem('auth_token');
    const userId = localStorage.getItem('user_id');
    if (token && userId) {
      setUser({ id: userId, token });
    }
    setLoading(false);
  }, []);

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_id');
    setUser(null);
  };

  return { user, loading, logout };
}
```

## Testing (Vitest)

- Component tests for complex UI (especially Recharts)
- Hook tests for data fetching (`useElectricity`)
- User interaction tests using `@testing-library/react`
- Meaningful coverage, not 100%

```typescript
import { render, screen } from '@testing-library/react';
import { ElectricityCard } from './ElectricityCard';

describe('ElectricityCard', () => {
  it('displays country code', () => {
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
});
```

## Accessibility

- Semantic HTML (use `<button>`, `<form>`, `<select>` not `<div>`)
- ARIA labels for non-semantic elements
- Keyboard navigation (Tab, Enter)
- Color contrast (WCAG AA minimum)
- Form labels and descriptions
- Focus visible on interactive elements

```typescript
// Bad example
<div onClick={() => setSelected(country)}>
  {country}
</div>

// Good example
<select onChange={(e) => setSelected(e.target.value)}>
  <option value="NL">Netherlands</option>
  <option value="DE">Germany</option>
</select>
```

## Build and Validation

All must pass before committing:

```bash
# ESLint
npm run lint

# TypeScript
npm run type-check

# Tests
npm run test

# Build
npm run build
```

**Never claim validation passed unless you actually ran it.**

## Security Rules

- ✅ Use `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (public)
- ✅ Use `VITE_API_URL` for backend endpoint
- ❌ Never import or reference `.env` directly
- ❌ Never hardcode ENTSOE_API_TOKEN (it's backend-only)
- ❌ Never commit `.env.local` (it's in `.gitignore`)
- ❌ Never log or display auth tokens
- ❌ Never make API calls to external services (use backend only)
