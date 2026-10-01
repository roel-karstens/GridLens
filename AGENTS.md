# AI Development with GitHub Copilot — GridLens

This repository demonstrates efficient AI-assisted development building **GridLens**, a real-time electricity data explorer. These guidelines ensure consistency, security, and maintainability when building with GitHub Copilot.

## About GridLens

**GridLens** is a full-stack web application that explores European electricity data:

- **Frontend**: React + TypeScript + Vite + Recharts
- **Backend**: Python + FastAPI + Pydantic
- **Database**: Supabase PostgreSQL with Row Level Security
- **Data Source**: ENTSO-E Transparency Platform REST API
- **Features**: Dashboard, historical charts, country comparison
- **Scope**: Netherlands, Germany, Belgium, France (MVP)

**Key Innovation**: Demonstrates real-world external API integration, data ingestion, time-series persistence, and public data querying patterns.

## 🎯 Project Goals

1. **Real-world patterns** — Show production-grade patterns for external API integration
2. **Data-driven UI** — Build responsive dashboards with live electricity data
3. **Scalable backend** — Idempotent ingestion, efficient queries, proper auth/authz
4. **AI-friendly** — Clear structure for Copilot-assisted development
5. **Well-documented** — Every decision documented with ADRs and comments

## Architecture

```
ENTSO-E API (XML documents)
         ↓
   Backend Client (HTTP)
         ↓
   Parser (XML → normalized)
         ↓
   Ingestion Service (upsert prevention)
         ↓
PostgreSQL (electricity_observations)
         ↓
   Query Service (aggregation, metrics)
         ↓
FastAPI REST API
         ↓
React Dashboard (Recharts)
```

### Key Design Decisions

**1. Backend-only external API calls**
- Frontend NEVER calls ENTSO-E directly
- Backend client handles auth, retry logic, error handling
- Frontend only calls `/api/v1/electricity/*` endpoints

**2. Public data model**
- Electricity observations are readable by all authenticated users
- No row-level ownership (not user-owned data)
- Queries should include country_code for efficiency

**3. Idempotent ingestion**
- Uniqueness constraint: (country_code, timestamp, metric)
- Can upsert same observation multiple times without errors
- Supports reliable retry logic

**4. Time-series optimization**
- Indexes on (country_code, timestamp) for range queries
- Indexes on (metric, timestamp) for metric-specific queries
- Timestamp in UTC internally, may display in user's timezone

**5. No Celery/Kafka/Redis required**
- Cron jobs or serverless functions trigger ingestion
- Simple sequential processing
- Can scale with databases later if needed

### Responsibilities

**Frontend**
- Dashboard UI with Recharts visualizations
- Country and metric selection
- Date range picker for historical data
- Loading/error/empty state handling
- Authentication (login/logout with Supabase)

**Backend**
- ENTSOEClient: HTTP client for ENTSO-E API
- ENTSOEParser: XML response parsing and normalization
- IngestionService: Idempotent upserts to database
- ElectricityService: Data queries and derived metrics
- API endpoints: RESTful JSON endpoints
- Authentication: JWT validation on protected endpoints
- RLS enforcement: Data access control

**Database**
- electricity_observations table with proper schema
- Uniqueness constraint on (country_code, timestamp, metric)
- Performance indexes for common queries
- RLS policies (readable by authenticated users only)

### Security Boundaries

**Frontend MUST NOT contain:**
- ENTSO-E API token
- Supabase service-role key
- Database credentials
- Any backend secrets

**Backend MUST enforce:**
- Authentication on all `/api/v1/electricity/*` endpoints
- Authorization via Supabase JWT validation
- RLS on database tables

**Data access is public (by design):**
- Any authenticated user can read electricity observations
- Only backend can write (via services)
- No per-user access restrictions

## Development Phases

### ✅ Phase 1: Inspect & Plan (COMPLETE)
- [x] Understand starter architecture
- [x] Define MVP scope
- [x] Create phase breakdown

### ✅ Phase 2: Database & Domain Models (COMPLETE)
- [x] Create electricity_observations table with schema
- [x] Define SQLAlchemy models (ElectricityObservation)
- [x] Create Pydantic schemas (8 schemas)
- [x] Add ENTSO-E configuration (countries, tech mapping)
- [x] Create integration stubs
- [x] Write test suite (56+ tests)
- [x] Register API endpoints

**Validation**: See [docs/validation.md](./docs/validation.md)

### ✅ Phase 3: ENTSO-E Client & Parser (COMPLETE)
- [x] Implement HTTP client with httpx and exponential backoff
- [x] Parse XML responses (A65 load, A73 generation documents)
- [x] Normalize observations to domain model
- [x] Error handling (timeouts, rate limits, retries)
- [x] Unit tests with mock XML (17 tests)

### ✅ Phase 4: Ingestion Service (COMPLETE)
- [x] Implement idempotent upserts (uniqueness constraint)
- [x] Handle duplicates gracefully
- [x] Add logging (no credentials exposed)
- [x] Error recovery and retry logic
- [x] Integration tests

### ✅ Phase 5: Backend API Implementation (COMPLETE)
- [x] Implement service layer queries (ElectricityService)
- [x] Calculate renewable percentage and metrics
- [x] Wire services into endpoints
- [x] Add real data tests
- [x] Performance optimization with indexes

### ✅ Phase 6: Frontend Dashboard (COMPLETE)
- [x] Build main dashboard page (DashboardPage.tsx)
- [x] Current metrics components (ElectricityCard)
- [x] Recharts generation mix chart (GenerationChart)
- [x] Country selector (CountrySelector)
- [x] Loading/error/empty state handling

### ✅ Phase 7: Historical & Comparison (COMPLETE)
- [x] History page with date range (HistoryPage.tsx)
- [x] Time-series line charts (Recharts LineChart)
- [x] Country comparison page (ComparisonPage.tsx)
- [x] Comparison table and bar charts

### Phase 8-10: Polish, Tests, Deploy (FUTURE)
- [ ] Full test coverage (target: 85%+)
- [ ] Security audit (third-party)
- [ ] Performance optimization
- [ ] Production deployment

## Code Organization

```
backend/app/
├── api/
│   ├── health.py              # Health check
│   ├── projects.py            # Starter CRUD
│   └── electricity.py         # Electricity endpoints (Phase 2+)
│
├── integrations/
│   └── entsoe/
│       ├── __init__.py
│       ├── constants.py       # Country configs, tech mapping (Phase 2)
│       ├── models.py          # Response DTOs (Phase 2)
│       ├── client.py          # HTTP client (Phase 3)
│       └── parser.py          # XML parsing (Phase 3)
│
├── services/
│   ├── project.py             # Starter CRUD service
│   ├── electricity.py         # Query service (Phase 5)
│   └── ingestion.py           # Data ingestion (Phase 4)
│
├── models/
│   ├── project.py             # Starter model (SQLAlchemy)
│   └── electricity.py         # ElectricityObservation (Phase 2)
│
├── schemas/
│   ├── project.py             # Starter schemas (Pydantic)
│   └── electricity.py         # Electricity schemas (Phase 2)
│
├── core/
│   ├── config.py              # Settings (Phase 2 added entsoe_api_token)
│   └── auth.py                # Supabase JWT validation
│
├── dependencies.py            # FastAPI dependencies
└── main.py                     # App factory, router registration

frontend/src/
├── pages/
│   ├── AuthPage.tsx           # Starter (login/signup)
│   ├── ProjectsPage.tsx       # Starter CRUD example
│   ├── DashboardPage.tsx      # Main electricity dashboard (Phase 6)
│   ├── HistoryPage.tsx        # Historical data view (Phase 7)
│   └── ComparisonPage.tsx     # Country comparison (Phase 7)
│
├── components/
│   ├── ElectricityCard.tsx    # Current metrics display (Phase 6)
│   ├── GenerationChart.tsx    # Stacked bar chart - generation mix (Phase 6)
│   ├── CountrySelector.tsx    # Country dropdown selector (Phase 6)
│   ├── ProjectForm.tsx        # Project creation form (starter)
│   └── ProjectList.tsx        # Project list display (starter)
│
├── hooks/
│   └── useElectricity.ts      # Data fetching with async state (Phase 6)
│
└── lib/
    ├── api.ts                 # Typed API client with JWT attachment
    └── supabase.ts            # Supabase client initialization
```

## Coding Standards

### TypeScript (Frontend)

- Strict type mode always enabled
- No `any` types
- Export types from components used by consumers
- Use discriminated unions for state (e.g., `'loading' | 'loaded' | 'error'`)
- Prefer immutable patterns
- Document complex props with JSDoc

### Python (Backend)

- Type hints on ALL functions and methods
- Pydantic for request/response validation
- FastAPI dependency injection for auth + services
- Thin route handlers: 2–5 lines (call service only)
- Services contain business logic
- Consistent HTTP status codes (200, 201, 400, 401, 403, 404, 422, 500)
- Never expose stack traces to clients

### Domain-Specific (Electricity)

**Time-series data handling**
- All timestamps stored in UTC (PostgreSQL `timestamptz`)
- Use `datetime.utcnow()` not `datetime.now()`
- Display times in user's timezone on frontend (optional)

**ENTSO-E API**
- A65 = Actual Total Load (demand)
- A73 = Aggregated Generation Per Type
- psrType codes map to technologies (B16=solar, B18=wind, etc.)
- Queries return XML; use ElementTree for parsing
- Implement exponential backoff for rate limiting

**Metrics**
- `value_mw` = power in Megawatts (Decimal for precision)
- `metric` enum: 'load', 'solar', 'wind_onshore', 'wind_offshore', 'nuclear', etc.
- Renewable percentage = (solar + wind + hydro) / total * 100

**Database queries**
- Always filter by country_code (index for performance)
- Use timestamp range queries with indexes
- Aggregate/downsample for historical data (e.g., hourly → daily)

## Security Requirements

### 1. Never Commit Secrets
```
VITE_SUPABASE_URL     → public (frontend)
VITE_SUPABASE_ANON_KEY → public (frontend)
SUPABASE_SERVICE_ROLE_KEY → SECRET (backend)
ENTSOE_API_TOKEN      → SECRET (backend)
```

- Use `.env.example` as template
- `.env` is in `.gitignore`
- Never commit `.env`

### 2. Authenticate Every Request
- All `/api/v1/electricity/*` require `Authorization: Bearer <jwt>`
- Use `Depends(get_current_user)` on protected endpoints
- Return 401 if missing/invalid token
- Return 403 if insufficient permissions

### 3. Authorize with RLS
- Enable RLS on electricity_observations table
- Define explicit RLS policies:
  - SELECT: Allow all authenticated users (public data)
  - INSERT/UPDATE/DELETE: Deny all (backend-only writes)
- Test policies before deployment

### 4. Validate All Input
- Pydantic models for request bodies
- Validate country_code against COUNTRIES dict
- Validate date ranges (start ≤ end, not too wide)
- Return 422 for validation errors

### 5. Avoid Sensitive Logging
- ✅ Log: "Ingesting data for country NL, metric load"
- ❌ Don't log: API tokens, credentials, raw responses
- Don't log PII (user emails, etc.)

### 6. Use HTTPS in Production
- Ensure Supabase uses HTTPS (it does by default)
- Ensure backend uses HTTPS (Vercel, Heroku, etc.)
- Set secure cookie flags if using cookies

## Testing Requirements

### Backend (pytest)

All new code requires tests:

- **Unit tests** for services, parsers, utils (17 parser tests, 5 test files total)
- **Integration tests** for API endpoints
- **Fixtures** for mock data, mock ENTSO-E responses
- **Error cases** — invalid input, timeouts, parse errors
- Test coverage target: 70%+ (currently ~70%, appropriate)

**Never weaken or remove tests to make validation pass.**

### Frontend (Vitest)

- **Component tests** for complex UI (charts, selectors)
- **Hook tests** for data fetching (`useElectricity`)
- **Integration tests** for full page flows
- Avoid brittle snapshot tests
- Test user interactions, not implementation details

### Example Test Structure

```python
# backend/tests/test_electricity_parser.py
def test_parse_load_xml_valid():
    """Parse valid ENTSO-E A65 load response"""
    parser = ENTSOEParser()
    xml_response = load_fixture("entsoe_a65_nl.xml")
    result = parser.parse_load_xml(xml_response)
    
    assert len(result) > 0
    assert result[0].country_code == "NL"
    assert result[0].metric == "load"
    assert result[0].value_mw > 0

def test_parse_load_xml_malformed():
    """Parse invalid XML raises ValueError"""
    parser = ENTSOEParser()
    with pytest.raises(ValueError, match="Invalid XML"):
        parser.parse_load_xml("<invalid")
```

## Database Migration Rules

1. **One file per logical change**
   - `0001_initial_schema.sql` (projects table)
   - `0002_electricity_schema.sql` (electricity_observations)
   - `0003_add_indices.sql` (performance)

2. **Idempotent migrations**
   - Use `CREATE TABLE IF NOT EXISTS`
   - Use `DROP TABLE IF EXISTS` for rollbacks
   - Safe to run multiple times

3. **RLS policies documented**
   ```sql
   -- Allow authenticated users to read electricity observations (public data)
   CREATE POLICY "public_read" ON electricity_observations
   FOR SELECT USING (auth.role() = 'authenticated');
   ```

4. **Test migrations locally**
   - In Supabase UI or with psql
   - Verify schema is created correctly
   - Verify RLS policies work

5. **No destructive changes without approval**
   - Dropping columns requires data migration plan
   - Renaming tables requires backward compatibility

## Definition of Done

A feature is done when:

1. ✅ **Code written** using established patterns
2. ✅ **Tests pass** (unit, integration, component)
3. ✅ **Validation passes** (ESLint, Ruff, TypeScript, Pyright)
4. ✅ **No secrets** in code or diffs
5. ✅ **Auth/authz** enforced (protected endpoints, RLS)
6. ✅ **Documentation** updated (README, ADR, comments)
7. ✅ **Git diff** reviewed for correctness
8. ✅ **No breaking changes** to APIs

**Example for Phase 3 (Parser):**
- ✅ ENTSOEParser.parse_load_xml() returns normalized observations
- ✅ ENTSOEParser.parse_generation_xml() returns normalized observations
- ✅ Error handling for malformed XML
- ✅ Unit tests with 5+ ENTSO-E XML examples
- ✅ Type hints on all methods
- ✅ No API token in response objects

## AI Development Workflow

### 1. UNDERSTAND
- Read the phase/feature description
- Identify acceptance criteria
- Ask for clarification if needed

### 2. INSPECT
- Read existing code in that domain
- Study the patterns already in use
- Check similar implementations
- Review the test structure

### 3. PLAN
- List the files to create/modify
- Identify dependencies between changes
- Sketch the data flow
- Note any risks or unknowns

### 4. IMPLEMENT
- Use established patterns
- Reuse existing components/functions
- Add full type hints
- Include error handling
- Add docstrings for complex logic

### 5. TEST
- Write unit tests
- Write integration tests
- Test error cases
- Verify with manual testing

### 6. VALIDATE
- Run `pytest` (backend)
- Run `npm run test` (frontend)
- Run `ruff check app/` (backend linting)
- Run `npm run lint` (frontend linting)
- Run type checking (Pyright, TypeScript)
- Check for unused imports
- Verify no secrets in diff

### 7. REVIEW
- Review git diff carefully
- Check against architecture guidelines
- Verify security requirements
- Look for unnecessary complexity

### 8. SUMMARIZE
- Explain what was built
- Link to tests
- Note any limitations
- Describe validation steps

## Copilot Prompts

Use these prompts in Copilot Chat:

- **`implement-feature.prompt.md`** — "Build Phase 3: ENTSO-E Client"
- **`review.prompt.md`** — "Review my parser implementation"
- **`security-review.prompt.md`** — "Audit Phase 2 for security"
- **`database-change.prompt.md`** — "Create migration for indices"
- **`test-and-review.prompt.md`** — "Write and validate tests"

## What NOT to Do

- ❌ **Hardcode configuration** — Use `config.py` settings
- ❌ **Ignore time zones** — Always use UTC internally
- ❌ **Query ENTSO-E from frontend** — Backend-only API calls
- ❌ **Store secrets in code** — Use `.env` files
- ❌ **Weak error handling** — Handle timeouts, parse errors, rate limits
- ❌ **Weak validation** — Validate all inputs with Pydantic
- ❌ **Skip tests** — Every feature needs tests
- ❌ **Brittle queries** — Index performance-critical queries
- ❌ **Ignore RLS** — Always enforce with database policies

## Model Independence

These instructions work with:
- Claude
- OpenAI (GPT-4, GPT-4o)
- Other supported Copilot models

Don't assume model-specific capabilities.

---

**Status**: Phases 2-7 complete, production-ready  
**Last updated**: October 2026  
**Contact**: Build with Copilot!

## Repository Structure

```
/
├── AGENTS.md                          # This file
├── README.md                          # Getting started
├── .gitignore
├── .editorconfig
│
├── .github/
│   ├── copilot-instructions.md       # Primary Copilot guidance
│   ├── instructions/                 # Path-specific instructions
│   │   ├── frontend.instructions.md
│   │   ├── backend.instructions.md
│   │   ├── database.instructions.md
│   │   └── tests.instructions.md
│   └── prompts/                      # Reusable Copilot prompts
│       ├── implement-feature.prompt.md
│       ├── review.prompt.md
│       ├── security-review.prompt.md
│       ├── database-change.prompt.md
│       └── test-and-review.prompt.md
│
├── frontend/                         # React + TypeScript
│   ├── src/
│   │   ├── components/              # Reusable React components
│   │   ├── pages/                   # Page components
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── lib/                     # Utilities and helpers
│   │   ├── types/                   # TypeScript types
│   │   ├── App.tsx                  # Main app component
│   │   └── main.tsx                 # Entry point
│   ├── tests/                       # Component tests
│   ├── public/                      # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── eslint.config.js
│   └── .env.example
│
├── backend/                         # FastAPI + Python
│   ├── app/
│   │   ├── api/                    # API routes
│   │   ├── core/                   # Core utilities (config, auth)
│   │   ├── models/                 # Database models (SQLAlchemy)
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/               # Business logic
│   │   ├── dependencies.py         # FastAPI dependencies
│   │   └── main.py                 # Application entry point
│   ├── tests/                      # API and service tests
│   ├── pyproject.toml
│   └── .env.example
│
├── supabase/                        # Database
│   ├── migrations/
│   │   └── 0001_initial_schema.sql # Initial schema
│   └── seed.sql                     # Optional: seed data
│
├── docs/                            # Documentation
│   ├── architecture.md
│   ├── security.md
│   ├── database.md
│   ├── development.md
│   └── decisions/
│       └── README.md
│
└── scripts/                         # Utility scripts
    ├── test.sh
    └── validate.sh
```

## Example Application

The repository includes a minimal but fully functional project management app:

**Database Schema**: `projects` table
- `id` (UUID primary key)
- `owner_id` (references auth.users)
- `name` (project name)
- `description` (project description)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**API Endpoints**
- `GET /health` — Health check
- `GET /api/v1/projects` — List authenticated user's projects
- `POST /api/v1/projects` — Create new project
- `GET /api/v1/projects/{id}` — Get project details
- `PATCH /api/v1/projects/{id}` — Update project
- `DELETE /api/v1/projects/{id}` — Delete project

**Frontend Features**
- Signup and login with Supabase Auth
- Protected dashboard (requires authentication)
- List, create, edit, and delete projects
- Loading states, error handling, empty states

## Coding Standards

### TypeScript (Frontend)

- Strict type mode always enabled
- No `any` types without justification
- Export types from components that need them
- Use discriminated unions for complex state
- Prefer immutable patterns
- Write meaningful prop types for reusable components

### Python (Backend)

- Type hints on all functions and methods
- Pydantic models for request/response validation
- FastAPI dependency injection for services and auth
- Thin route handlers (2–5 lines of logic)
- Business logic in service layer
- Consistent HTTP status codes
- Descriptive error messages (without exposing internal details)

### SQL (Database)

- All schema changes via migrations
- RLS enabled on all tables with user data
- Explicit ownership rules (owner_id, created_by, etc.)
- Appropriate indexes on foreign keys and search fields
- Constraints to enforce data integrity
- No destructive changes without explicit approval

## Security Requirements

1. **Never commit secrets**
   - Use `.env.example` to document required variables
   - `.env` is in `.gitignore`

2. **Authenticate server-side**
   - Validate JWT tokens on every protected endpoint
   - Use FastAPI's dependency injection
   - Extract `user_id` from token claims

3. **Authorize with RLS**
   - Enable RLS on all tables
   - Define explicit SELECT, INSERT, UPDATE, DELETE policies
   - Test policies before deployment

4. **Validate input**
   - Use Pydantic for request validation
   - Whitelist allowed fields
   - Validate data types and constraints

5. **Avoid sensitive logging**
   - Do not log passwords, tokens, or sensitive user data
   - Log sufficient detail for debugging without exposing secrets

6. **Use HTTPS in production**
   - Set secure cookie flags
   - Use environment-aware settings

## Testing Requirements

### Backend (pytest)

- Unit tests for services and utilities
- API integration tests for key endpoints
- Authentication and authorization tests
- Test happy paths and error cases
- Aim for meaningful coverage, not 100%

### Frontend (Vitest)

- Component tests for complex UI
- Hook tests for custom logic
- User interaction tests for critical flows
- Integration tests for page-level features
- Avoid brittle implementation-detail tests

**Never remove tests to make validation pass.**

## Database Migration Rules

1. Create a new migration file for each change
2. Migrations are numbered sequentially: `0001_`, `0002_`, etc.
3. Write migrations to be idempotent (safe to run multiple times if needed)
4. Include both up and down logic for reversibility
5. Test migrations locally before committing
6. Add comments explaining the purpose and RLS implications
7. No destructive changes (drop table, drop column) without explicit approval

## Definition of Done

**Phases 2-7 are COMPLETE.** A feature is complete when:

1. ✅ Code follows established patterns (SOLID principles)
2. ✅ Tests pass (unit, integration, component)
3. ✅ Linting passes (ESLint, Ruff)
4. ✅ Type checking passes (Pyright, TypeScript) — 0 `any` types
5. ✅ Builds succeed (Vite, backend)
6. ✅ Security review passes (no secrets, proper auth/authz, RLS)
7. ✅ No unnecessary dependencies introduced
8. ✅ No breaking changes to public APIs
9. ✅ Documentation updated (README, docs/, comments)
10. ✅ Git diff is reviewed for correctness

**Audit Status**: Comprehensive audit completed. See [docs/AUDIT.md](./docs/AUDIT.md) for details. Score: 98/100

## AI Development Workflow

Follow this workflow for every feature, bug fix, or change:

### 1. UNDERSTAND

- Read the feature request or issue carefully
- Identify acceptance criteria
- Clarify scope and constraints
- Ask questions if anything is ambiguous

### 2. INSPECT

- Examine existing code related to the change
- Review relevant schemas, types, and services
- Check authentication and authorization patterns
- Look for similar implementations to reuse
- Study the test structure

### 3. PLAN

- Identify affected layers (frontend, backend, database)
- List the smallest, most appropriate changes
- Consider existing patterns and conventions
- Plan database migrations if needed
- Sketch the API contract if building endpoints

### 4. IMPLEMENT

- Write code using established patterns
- Reuse existing components, hooks, and services
- Prefer composition and small functions
- Maintain strict typing
- Add error handling and edge cases
- Include loading states where appropriate

### 5. TEST

- Add unit tests for new functions/services
- Add integration tests for API changes
- Add component tests for UI changes
- Test happy paths and error scenarios
- Verify authentication/authorization

### 6. VALIDATE

- Run linting (ESLint for frontend, Ruff for backend)
- Run type checking (TypeScript, Pyright)
- Run tests (Vitest for frontend, pytest for backend)
- Run builds (Vite, FastAPI)
- Check for unused imports
- Verify no secrets in the diff

### 7. REVIEW

- Review your own git diff carefully
- Check for correctness, security, and maintainability
- Look for unnecessary complexity or dead code
- Verify tests actually test the feature
- Confirm RLS and authorization are correct
- Check for performance issues

### 8. SUMMARIZE

- Write a clear summary of what changed
- Explain why changes were made
- Note any limitations or known issues
- List validation steps executed
- Describe remaining risks or follow-up work

## What AI Should NOT Do

- **Over-engineer**: Use simple solutions
- **Introduce unnecessary abstractions**: Add only when proven necessary
- **Add unnecessary dependencies**: Prefer built-in or minimal libraries
- **Rewrite working code**: Change only what's needed for the feature
- **Duplicate functionality**: Reuse existing code
- **Weaken tests**: Never remove tests or reduce coverage
- **Bypass security**: Always enforce auth/authz
- **Expose secrets**: Never include credentials in code or logs
- **Make unrelated changes**: Stay focused on the feature

## Using This Repository with GitHub Copilot

### Copilot Chat

Use the [GitHub Copilot Chat](https://docs.github.com/en/copilot/using-github-copilot/prompt-templates) prompts in `.github/prompts/`:

- `implement-feature.prompt.md` — For building new features
- `review.prompt.md` — For code review
- `security-review.prompt.md` — For security audits
- `database-change.prompt.md` — For schema migrations
- `test-and-review.prompt.md` — For testing and validation

### Inline Copilot Completions

Copilot will follow the guidelines in `.github/copilot-instructions.md` and path-specific instruction files automatically.

### Best Practices

1. **Be specific**: Describe what you're building, not just "add a feature"
2. **Reference code**: Point Copilot to existing patterns to follow
3. **Request validation**: Always ask to "run validation" before claiming done
4. **Review diffs**: Check Copilot's changes against security and architecture guidelines
5. **Test first**: Ask for tests before implementation when appropriate

## Model Independence

These instructions are **model-agnostic** and work equally well with:
- Claude
- OpenAI (GPT)
- Other supported GitHub Copilot models

Do not assume capabilities or behavior of a specific model. The repository setup and instructions are designed to be compatible with any AI model Copilot uses.

---

**Last updated**: October 2026  
**Status**: Phases 2-7 complete, production-ready
