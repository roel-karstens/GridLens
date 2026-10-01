# GitHub Copilot Instructions — GridLens

## Project Overview

**GridLens: European Electricity Data Explorer**
- React + TypeScript frontend (Vite, ESLint, Vitest, Tailwind, Recharts)
- FastAPI + Python backend (Pydantic, Ruff, Pyright, pytest)
- Supabase PostgreSQL + Auth + Row Level Security
- External API: ENTSO-E Transparency Platform (REST + XML)
- Status: MVP (Phases 2-7 complete, production-ready)

## Design & UI Philosophy

**Obsidian Premium-inspired aesthetic** — Sophisticated, professional, minimal:

- **Color Palette**: Slate grays + violet accents (not bright blue)
- **Buttons**: Violet (`violet-600`) instead of blue
- **Backgrounds**: Slate gradients (`slate-50` to `slate-100`)
- **Accents**: Emerald for renewable/positive metrics (`emerald-500`, `emerald-600`)
- **Cards**: White with subtle `shadow-sm` and `border-slate-200`
- **Typography**: `slate-900` for headings, `slate-600` for body (not generic gray)
- **No "AI Slop"**: Avoid bright, generic colors. Aim for refined, professional UI.

**Key Components**:
- Buttons use `violet-600` (primary) and `slate-200` (secondary)
- Spinners use `border-violet-500`
- Progress bars use `bg-emerald-500`
- All focus rings use `focus:ring-violet-500`
- All cards use `border-slate-200` (not `border-gray-300`)

See [docs/design.md](../../docs/design.md) for complete style guide.

## Architecture

```
ENTSO-E Transparency Platform
    ↓ (XML REST API)
ENTSOEClient → ENTSOEParser → IngestionService
    ↓
PostgreSQL (electricity_observations)
    ↓ (RLS: readable by auth users)
ElectricityService → FastAPI REST API
    ↓
React Frontend (Dashboard, Charts)
    ↓
User Dashboard
```

**Critical Rules**:
1. **Frontend NEVER queries external APIs** — All ENTSO-E requests happen backend-only
2. **No private keys in frontend** — ENTSOE_API_TOKEN stays in backend `.env`
3. **Public data model** — Electricity observations are world-readable (all auth users)
4. **UTC timestamps** — Always store in UTC, display in user timezone
5. **Idempotent ingestion** — Same observation can be upserted multiple times safely

## Project Goals

- Demonstrate production-grade external API integration
- Build responsive electricity data dashboard
- Implement time-series data persistence and querying
- Show real-world patterns with Copilot
- Document decisions with ADRs

## Responsibilities

**Frontend**
- Electricity dashboard UI (Recharts charts, metric cards)
- Country and metric selection
- Date range picker for historical views
- Loading/error/empty state handling
- Authentication (Supabase login/logout)
- NO external API calls (backend-only)

**Backend**
- ENTSOEClient: HTTP client for ENTSO-E API
- ENTSOEParser: XML parsing and data normalization
- IngestionService: Idempotent upserts (no duplicates)
- ElectricityService: Query service + derived metrics
- API endpoints: `/api/v1/electricity/*` (thin handlers)
- Authentication: JWT validation on all protected endpoints
- Authorization: RLS enforcement on database

**Database**
- electricity_observations table with schema
- Uniqueness constraint on (country_code, timestamp, metric)
- Performance indexes for common queries
- RLS policies (authenticated SELECT, no API writes)
- Schema migrations only (backend writes data)

## Development Principles

### 1. Inspect Before Modifying

Read existing code first:
- How are services structured?
- What patterns are used for ENTSOE integration?
- How does existing authentication work?
- What is the current schema design?
- How are tests structured?

### 2. Reuse Existing Patterns

- Reuse Recharts components for dashboards
- Follow existing service layer pattern
- Use existing Pydantic schemas
- Match existing error handling
- Reuse FastAPI dependency injection style

### 3. Prefer Minimal Changes

- Smallest change that solves the problem
- No unnecessary refactoring
- No speculative abstractions
- No dead code

### 4. Maintain Strict Typing

**TypeScript (Frontend)**
- No `any` types without justification
- All function parameters typed
- All return types specified
- Discriminated unions for complex state
- Export types for reusable components
- Proper typing for Recharts props

**Python (Backend)**
- Type hints on ALL functions and methods
- Pydantic models for all request/response data
- FastAPI dependency injection with proper types
- Return types specified on all functions
- Domain-specific types (Decimal for MW, datetime for UTC)

### 5. Write Tests

- Add tests for new functionality
- Cover happy paths and error cases
- Fixtures for mock ENTSO-E XML responses
- Integration tests for API endpoints
- Unit tests for parsing and ingestion
- Component tests for complex UI

### 6. Run Validation

Before finishing:
- Frontend: `npm run lint`, `npm run type-check`, `npm run test`
- Backend: `ruff check app/`, `pyright app/`, `pytest tests/`

Do NOT claim validation passed unless you actually ran it.

### 7. Domain Knowledge

**Electricity metrics**
- Load = demand (Actual Total Load, A65)
- Generation breakdown by technology (A73)
- Technologies: solar, wind_onshore, wind_offshore, nuclear, gas, coal, hydro, biomass
- Unit: MW (Megawatts)
- Renewable % = (solar + wind + hydro) / total

**Time-series handling**
- All timestamps stored in UTC internally
- Use `datetime.utcnow()` or `datetime.now(timezone.utc)`
- Never use naive `datetime.now()`
- Display in user's timezone on frontend

**ENTSO-E API**
- Domain identifiers: NL=10YNL----------L, DE=10Y1001A1001A82H, etc.
- psrType codes: B16=solar, B18=wind_onshore, B20=nuclear, etc.
- Queries return XML documents
- Use ElementTree for parsing
- Rate limiting: implement exponential backoff
- Timeout: 30 seconds (configurable in constants)

**Database constraints**
- Uniqueness on (country_code, timestamp, metric) prevents duplicates
- RLS allows SELECT for all authenticated users
- RLS denies INSERT/UPDATE/DELETE (backend-only writes)
- Indexes on (country_code, timestamp), (metric, timestamp) for perf

## Security Requirements

### 1. Never Commit Secrets

- `.env` is in `.gitignore`
- Use `.env.example` to document variables
- Public variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- Secret variables: `ENTSOE_API_TOKEN`, `SUPABASE_SERVICE_ROLE_KEY`
- Never log tokens, credentials, or raw API responses

### 2. Backend-Only External Calls

- Frontend NEVER calls ENTSO-E directly
- Frontend NEVER stores ENTSOE_API_TOKEN
- All external calls happen in backend services
- Frontend calls FastAPI endpoints only (`/api/v1/electricity/*`)

### 3. Authenticate Every Request

- All `/api/v1/electricity/*` endpoints require authentication
- Use `Depends(get_current_user)` on protected routes
- Validate JWT token from Supabase
- Return 401 for missing/invalid token
- Return 403 for insufficient permissions

### 4. Authorize with RLS

- Enable RLS on electricity_observations table
- Policies: SELECT for authenticated users (public data)
- Policies: DENY for INSERT/UPDATE/DELETE (backend-only)
- Test RLS policies before deployment
- No per-user ownership needed (public data)

### 5. Validate Input

- Use Pydantic for all request bodies
- Validate country_code against COUNTRIES dict
- Validate date ranges (start <= end, not too wide)
- Validate metric names
- Return 422 for validation errors

### 6. Secure Error Handling

- Log errors for debugging (no credentials)
- Never expose stack traces to clients
- Never reveal database structure or schema
- Return generic error messages to API users
- Log: "Error fetching data for NL" (not token or API details)

## Code Quality

### Frontend

**Components**
- Single responsibility (one visual concern)
- Reusable with clear props
- Handle loading/error/empty states
- Accessible (labels, ARIA attributes)
- No business logic in components (use hooks)

**Types**
- Discriminated unions for state (loading | loaded | error)
- Export types from components used by consumers
- No `unknown` or `any` types
- Proper typing for Recharts components

**Hooks**
- Encapsulate data fetching (`useElectricity`)
- Clear dependencies array
- Proper cleanup on unmount
- Handle loading and error states

**Testing**
- Component tests for complex UI
- User interaction tests for workflows
- Avoid brittle implementation tests
- Mock API responses appropriately

### Backend

**Routes**
- 2–5 lines of logic per handler
- Validate input with Pydantic
- Call services for all business logic
- Return appropriate status codes
- Thin handlers (example: `handler → service → model → response`)

**Services**
- Encapsulate business logic
- Take dependencies as arguments
- No database queries in handlers (call services)
- Return typed responses
- Handle errors with appropriate exceptions

**Models & Schemas**
- Pydantic for requests/responses
- SQLAlchemy for database models
- Clear separation of concerns
- Reuse schemas across routes where appropriate

**Parsing & Integration**
- ENTSOEParser: XML → domain models
- ENTSOEClient: HTTP + auth + retry logic
- IngestionService: Handle duplicates, logging
- Comprehensive error handling (timeouts, malformed data)

**Testing**
- Unit tests for services, parsers, utils
- Integration tests for API endpoints
- Fixtures for mock data and ENTSO-E responses
- Test auth and authorization on all endpoints
- Test error cases (invalid input, timeouts, malformed XML)
- Aim for 70%+ coverage (not 100%)

### Database

- All changes via migrations
- RLS on all tables with data
- Explicit ownership/access rules
- Indexes on foreign keys and common queries
- Constraints for data integrity
- No destructive changes without approval
- Document RLS implications in migration comments

## Development Workflow

### Phase 2: Database & Domain (COMPLETE)
✅ electricity_observations table  
✅ SQLAlchemy model + Pydantic schemas  
✅ ENTSO-E constants (countries, tech mapping)  
✅ Integration stubs + API endpoints  
✅ 56 comprehensive tests  

See [PHASE2_VALIDATION.md](../../PHASE2_VALIDATION.md) to run tests.

### Phase 3: ENTSO-E Client (IN PROGRESS)
- [ ] Implement ENTSOEClient (HTTP + auth + retry)
- [ ] Implement ENTSOEParser (XML parsing)
- [ ] Implement data normalization
- [ ] Error handling (timeouts, rate limits)
- [ ] Unit tests with mock responses

### Phase 4: Ingestion Service
- [ ] Implement idempotent upsert logic
- [ ] Handle duplicates gracefully
- [ ] Error recovery and retry
- [ ] Logging (no credentials)
- [ ] Integration tests

### Phase 5: Backend API
- [ ] Implement service queries
- [ ] Calculate derived metrics
- [ ] Wire services into endpoints
- [ ] Add real data tests
- [ ] Performance testing

### Phase 6-10: Frontend & Deployment
- Dashboard, charts, comparison views
- Full test coverage
- Security audit
- Production deployment

## Model Independence

These instructions work with ANY GitHub Copilot model:
- Claude
- OpenAI (GPT)
- Other supported Copilot models

Do not assume model-specific capabilities.

## When to Ask for Help

- Ambiguous requirements
- Architectural decisions
- Security concerns
- External API integration strategy
- Large refactorings
- Performance optimization
- Dependency decisions

## Development Principles

### 1. Inspect Before Modifying

Read existing code first:
- How are components structured?
- What patterns are used?
- Where is similar logic already implemented?
- What authentication/authorization patterns exist?

### 2. Reuse Existing Patterns

- Reuse components, hooks, and services
- Follow naming conventions
- Match code style
- Use existing error handling

### 3. Prefer Minimal Changes

- Smallest change that solves the problem
- No unnecessary refactoring
- No speculative abstractions
- No dead code

### 4. Maintain Strict Typing

**TypeScript (Frontend)**
- No `any` types
- All function parameters typed
- All return types specified
- Discriminated unions for complex state
- Export types for reusable components

**Python (Backend)**
- Type hints on all functions
- Pydantic models for validation
- FastAPI dependency injection
- Return types on all functions

### 5. Write Tests

- Add tests for new functionality
- Cover happy paths and error cases
- Component tests for UI changes
- Integration tests for API changes
- Unit tests for services

### 6. Run Validation

Before finishing:
- Frontend: ESLint, TypeScript, Vitest, Vite build
- Backend: Ruff, Pyright, pytest, build

Do NOT claim tests passed unless you actually ran them.

## Security Requirements

### 1. Never Commit Secrets

- `.env` is in `.gitignore`
- Use `.env.example` to document variables
- Distinguish public (VITE_*) and secret variables
- Never log sensitive data

### 2. Authenticate Server-Side

- Validate JWT on every protected endpoint
- Extract `user_id` from token
- Use FastAPI dependency injection
- Return 401 for missing/invalid tokens
- Return 403 for insufficient permissions

### 3. Enforce Authorization

**Backend**
- Check user ownership of resources
- Verify permissions before returning data
- Use consistent error responses

**Database**
- Enable RLS on all tables
- Define explicit policies for SELECT, INSERT, UPDATE, DELETE
- Test policies before deployment

### 4. Validate Input

- Use Pydantic for all requests
- Whitelist allowed fields
- Validate types, lengths, formats
- Return 422 for validation errors

### 5. Protect API Endpoints

- All data endpoints require authentication
- POST/PATCH/DELETE require ownership
- Return appropriate HTTP status codes
- Avoid revealing internal details in errors

### 6. Secure Error Handling

- Log errors for debugging
- Never expose stack traces to clients
- Never reveal database structure
- Return generic error messages

## Code Quality

### Frontend

**Components**
- Single responsibility
- Reusable with clear props
- Handle loading/error/empty states
- Accessible (labels, ARIA)
- No business logic (belongs in hooks/services)

**Types**
- Discriminated unions for state
- Exported from components that need them
- No `unknown` or `any`

**Hooks**
- Encapsulate stateful logic
- Clear dependencies
- Proper cleanup

**Testing**
- Component tests for complexity
- User interaction tests for flows
- Avoid brittle implementation tests

### Backend

**Routes**
- 2–5 lines of logic per handler
- Validate input with Pydantic
- Call services for business logic
- Return appropriate status codes

**Services**
- Encapsulate business logic
- Take dependencies as arguments
- No database queries in handlers
- Return typed responses

**Models & Schemas**
- Pydantic for requests/responses
- SQLAlchemy for database models
- Clear separation of concerns

**Testing**
- Unit tests for services
- Integration tests for endpoints
- Test auth and authorization
- Test error cases

### Database

- All changes via migrations
- RLS on tables with user data
- Explicit ownership rules
- Indexes on foreign keys
- Constraints for data integrity
- No destructive changes without approval

## Model Independence

These instructions work with ANY GitHub Copilot model:
- Claude
- OpenAI (GPT)
- Other supported models

Do not assume capabilities of a specific model.

## When to Ask for Help

- Ambiguous requirements
- Architectural decisions
- Security concerns
- Large refactorings
- External integrations
- Performance issues
