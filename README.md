# GridLens — European Electricity Data Explorer

A full-stack web application for exploring European electricity demand and generation data in real-time. Built on React + FastAPI + Supabase.

**Explore electricity data from the ENTSO-E Transparency Platform** with an intuitive, responsive dashboard. View current demand, generation by technology type, and historical trends for Netherlands, Germany, Belgium, and France.

## 🎯 Purpose

GridLens demonstrates:
- **External API integration** — REST API client for ENTSO-E Transparency Platform
- **Data ingestion** — Fetch, parse, normalize electricity data
- **Database design** — PostgreSQL schema for time-series data
- **Production backend** — FastAPI with authentication, authorization, RLS
- **Interactive frontend** — React dashboard with Recharts visualizations
- **Testing & documentation** — Comprehensive tests and API docs

**Status**: Phases 2-7 complete ✓ (Ready for evaluation)

## 🌍 Supported Countries

- 🇳🇱 **Netherlands** (NL)
- 🇩🇪 **Germany** (DE)
- 🇧🇪 **Belgium** (BE)
- 🇫🇷 **France** (FR)

## ✨ Features

### Dashboard
- **Current Metrics**: Real-time demand, generation mix, renewable percentage
- **Generation Breakdown**: Solar, wind, nuclear, gas, hydro, coal, biomass
- **Historical Charts**: 24h, 7d, 30d trends
- **Country Comparison**: Side-by-side metrics across countries
- **Last Updated**: Timestamp of latest data from ENTSO-E

### Data
- **Public Data**: Electricity observations readable by all authenticated users
- **Normalized**: Unified schema across all countries and metrics
- **Audited**: Source attribution and timestamp tracking
- **Cached**: Database-first approach (don't query ENTSO-E on every request)

## 🏗️ Architecture

```
ENTSO-E Transparency Platform
    ↓ (REST API)
ENTSOEClient
    ↓ (fetch & validate)
ENTSOEParser
    ↓ (XML → normalized)
IngestionService
    ↓ (upsert with duplicate prevention)
PostgreSQL (electricity_observations table)
    ↓ (RLS: readable by authenticated users)
ElectricityService
    ↓ (queries + derived metrics)
FastAPI REST API
    ↓ (HTTP + JWT auth)
React Frontend
    ↓ (Recharts, Tailwind CSS)
User Dashboard
```

### Key Design Decisions

1. **Frontend never queries external APIs** — All ENTSO-E requests happen on backend (security)
2. **Idempotent ingestion** — Can run multiple times without creating duplicates
3. **Timezone aware** — All timestamps stored in UTC internally
4. **Public data model** — Electricity observations are readable by all authenticated users (not user-owned)
5. **Minimal dependencies** — No Celery/Kafka/Redis; scheduled jobs can run as cron or serverless

## 📁 Repository Structure

```
/
├── README.md                          # This file
├── AGENTS.md                          # AI development workflow
├── PHASE2_VALIDATION.md               # Phase 2 test guide
│
├── .github/
│   ├── copilot-instructions.md       # GridLens Copilot guidance
│   ├── instructions/                 # Domain-specific rules
│   │   ├── frontend.instructions.md
│   │   ├── backend.instructions.md
│   │   ├── database.instructions.md
│   │   └── tests.instructions.md
│
├── frontend/                         # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx    # Main dashboard (Phase 6)
│   │   │   ├── HistoryPage.tsx      # Historical view (Phase 7)
│   │   │   └── ComparisonPage.tsx   # Multi-country comparison (Phase 7)
│   │   ├── components/
│   │   │   ├── ElectricityCard.tsx        # Current metrics widget
│   │   │   ├── GenerationChart.tsx        # Stacked bar chart (generation mix)
│   │   │   ├── ProjectForm.tsx            # Project creation form
│   │   │   ├── ProjectList.tsx            # Project list display
│   │   │   └── CountrySelector.tsx        # Country picker
│   │   ├── hooks/
│   │   │   └── useElectricity.ts          # Data fetching hook
│   │   └── lib/
│   │       ├── api.ts                     # API client
│   │       └── supabase.ts                # Supabase client
│   ├── tests/
│   └── package.json
│
├── backend/                         # FastAPI + Python
│   ├── app/
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   ├── projects.py
│   │   │   └── electricity.py       # Electricity endpoints
│   │   ├── core/
│   │   │   ├── auth.py
│   │   │   └── config.py
│   │   ├── models/
│   │   │   ├── project.py
│   │   │   └── electricity.py       # ElectricityObservation model
│   │   ├── schemas/
│   │   │   ├── project.py
│   │   │   └── electricity.py       # Pydantic schemas
│   │   ├── services/
│   │   │   ├── project.py
│   │   │   ├── electricity.py       # Query & derived metrics (Phase 5)
│   │   │   └── ingestion.py         # Data ingestion (Phase 4)
│   │   ├── integrations/
│   │   │   └── entsoe/
│   │   │       ├── client.py        # HTTP client (Phase 3)
│   │   │       ├── parser.py        # XML parsing (Phase 3)
│   │   │       ├── models.py        # Response types
│   │   │       └── constants.py     # Country & tech mappings
│   │   ├── dependencies.py
│   │   └── main.py
│   ├── tests/
│   │   ├── fixtures_electricity.py
│   │   ├── test_electricity_models_schemas.py
│   │   ├── test_electricity_database.py
│   │   └── test_electricity_api.py
│   ├── pyproject.toml
│   └── .env.example
│
├── supabase/                        # Database
│   └── migrations/
│       ├── 0001_initial_schema.sql    # Projects table (starter)
│       └── 0002_electricity_schema.sql # Electricity observations (Phase 2)
│
└── docs/
    ├── README.md                          # Documentation index
    ├── implementation.md                  # What was built (Phases 2-7)
    ├── validation.md                      # How to test everything
    ├── compliance.md                      # Instruction adherence verification
    ├── architecture.md                    # System design
    ├── database.md                        # Schema and RLS
    ├── development.md                     # Setup and workflow
    ├── security.md                        # Auth and security
    └── decisions/
        └── ADR-002-auto-migrations-via-python.md
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+
- Supabase account (free tier available)
- ENTSO-E API token (request via email — see setup guide)

### 1. Clone Repository

```bash
git clone https://github.com/roel-karstens/GridLens.git
cd GridLens
```

### 2. Supabase Setup

Create a new Supabase project at [supabase.com](https://supabase.com):
1. Click "New Project"
2. Choose your region
3. Wait for creation
4. Go to **Project Settings** → **API**
5. Copy:
   - Project URL
   - `anon` public key
   - `service_role` secret key (keep secure!)

### 3. Frontend Setup

```bash
cd frontend
npm install

# Copy environment template
cp .env.example .env.local

# Edit .env.local with your Supabase credentials
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=xxx
VITE_API_URL=http://localhost:8000
```

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Edit .env with Supabase credentials
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
```

### 5. ENTSO-E API Token (Optional for Phase 2 Testing)

To use real ENTSO-E data:
1. Register at [transparency.entsoe.eu](https://transparency.entsoe.eu/)
2. Email: `request-api@entsoe.eu` with username and organization
3. Wait for token email (1-2 days)
4. Add to `backend/.env`:
   ```
   ENTSOE_API_TOKEN=<your-token>
   ```

(Not required for Phase 2 testing — Phase 3+ needs it)

### 6. Run Development Servers

**Backend** (creates database tables on startup):
```bash
cd backend
python -m uvicorn app.main:app --reload
# Runs at http://localhost:8000
# Auto-creates electricity_observations table with RLS
```

**Frontend**:
```bash
cd frontend
npm run dev
# Runs at http://localhost:5173
```

## 📊 Development Phases

### ✅ Phase 1: Inspect & Plan (COMPLETE)
- [x] Understand existing starter architecture
- [x] Define GridLens MVP scope
- [x] Create implementation plan

### ✅ Phase 2: Database & Domain Models (COMPLETE)
- [x] Create `electricity_observations` table with schema
- [x] Define SQLAlchemy models
- [x] Create Pydantic schemas
- [x] Add ENTSO-E configuration (countries, tech mapping)
- [x] Create integration layer stubs
- [x] Write comprehensive test suite (56 tests)
- [x] Register API endpoints

**Validate Phase 2**: See [docs/validation.md](./docs/validation.md)

### ✅ Phase 3: ENTSO-E Client & Parser (COMPLETE)
- [x] Implement HTTP client with auth & retry logic
- [x] Implement XML response parsing (A65, A73 documents)
- [x] Implement data normalization and validation
- [x] Write parsing tests with mock responses (17 tests)
- [x] Exponential backoff retry logic for rate limiting

### ✅ Phase 4: Ingestion Service (COMPLETE)
- [x] Implement idempotent upsert logic
- [x] Handle errors (timeouts, rate limiting, malformed data)
- [x] Add logging (no credentials)
- [x] Test duplicate prevention with uniqueness constraint

### ✅ Phase 5: Backend Electricity API (COMPLETE)
- [x] Implement service layer queries
- [x] Calculate derived metrics (renewable %, generation mix)
- [x] Implement all endpoints with real data
- [x] Add integration tests

### ✅ Phase 6: Frontend Dashboard (COMPLETE)
- [x] Build main dashboard page
- [x] Create metric display components (ElectricityCard)
- [x] Integrate Recharts for visualizations (GenerationChart)
- [x] Add country selector
- [x] Implement loading/error/empty states

### ✅ Phase 7: Historical & Comparison Views (COMPLETE)
- [x] Implement history page with date range picker
- [x] Add time-series line charts
- [x] Implement country comparison with bar charts
- [x] Add comparison table with metrics
- [x] Full async state management with hooks

## 🛠️ Commands

### Backend

```bash
cd backend

# Run development server (auto-reload)
python -m uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=app

# Lint and type check
ruff check app/
pyright app/

# Format code
ruff format app/
```

### Frontend

```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Run type checking
npm run type-check

# Lint
npm run lint
```

## 📚 Documentation

**Start here**: [docs/README.md](./docs/README.md) — Full documentation index

Detailed guides:
- [Implementation](./docs/implementation.md) — What was built (all phases)
- [Validation](./docs/validation.md) — How to test everything
- [Compliance](./docs/compliance.md) — Instruction adherence verification
- [Architecture](./docs/architecture.md) — System design
- [Database](./docs/database.md) — Schema and RLS
- [Development](./docs/development.md) — Setup and workflow
- [Security](./docs/security.md) — Auth, RLS, secrets
- [Decisions](./docs/decisions/) — ADRs and design rationale

## 🔐 Security

### Key Rules

1. **Never commit secrets** — Use `.env.example` as template
2. **ENTSO-E token backend-only** — Never expose to frontend
3. **Authenticate all endpoints** — JWT from Supabase
4. **RLS on all tables** — Database-level access control
5. **Validate input** — Pydantic schemas + parameter validation
6. **No arbitrary API calls** — Backend makes all external requests

See [Security Documentation](./docs/security.md) for details.

## 🤝 Contributing

This project uses GitHub Copilot for efficient development. See [AGENTS.md](./AGENTS.md) for:
- Development workflow
- Code quality standards
- Testing requirements
- Copilot prompt templates

## 📄 License

MIT

## 🙏 Attribution

**Data Source**: ENTSO-E Transparency Platform  
Electricity data © ENTSO-E  
Used under [ENTSO-E Open Data Licence](https://transparency.entsoe.eu/)

---

**Built with**: React, TypeScript, FastAPI, Python, Supabase, Recharts, Tailwind CSS

## 📚 Environment Variables

### Frontend (.env.local)

```
VITE_SUPABASE_URL=https://project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...
VITE_API_URL=http://localhost:8000
```

These are **public** (prefixed with `VITE_`) and safe to commit as `.env.example`.

### Backend (.env)

```
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
ENVIRONMENT=development
# Optional: PostgreSQL connection (auto-migration, production Supabase)
# If set, backend uses PostgreSQL. Otherwise falls back to SQLite.
DATABASE_URL=postgresql://user:password@host:5432/postgres
```

The `.env` file is in `.gitignore` — **never commit it**.

### Development Features

**Dev Auth Mode** (Frontend only, requires `ENVIRONMENT=development` in backend):
- Green "🚀 Development Mode" button on login page
- Generates mock JWT tokens without Supabase rate limiting
- Useful for testing authentication flows during development

**Auto-Migration** (Backend on startup):
- Creates database tables from SQLAlchemy models
- Enables Row Level Security (RLS) on PostgreSQL
- Configures policies for owner-based access control
- Creates performance indexes
- Works on first startup, idempotent on subsequent runs

## 🔐 Security

### Key Principles

1. **Frontend never accesses private keys**
   - Never commit `.env` with secrets
   - Never import service-role keys in frontend code

2. **Server-side authentication**
   - All protected endpoints validate JWT
   - User ID extracted from token claims
   - 401 for missing/invalid auth, 403 for insufficient permissions

3. **Database-level security**
   - Row Level Security (RLS) enabled on all tables
   - Explicit policies for SELECT, INSERT, UPDATE, DELETE
   - Users only access their own data

4. **Input validation**
   - Pydantic validation on all requests
   - Whitelisted fields
   - Type and constraint validation

5. **Error handling**
   - Log errors for debugging
   - Never expose stack traces to clients
   - Generic error messages to users

See [docs/security.md](docs/security.md) for detailed security guidelines.

## 💻 Development

### Frontend

**Run dev server:**
```bash
cd frontend
npm run dev
```

**Lint and format:**
```bash
npm run lint          # ESLint
npm run format        # Prettier
npm run type-check    # TypeScript
```

**Run tests:**
```bash
npm run test          # Vitest
npm run test:ui       # Test UI
```

**Build for production:**
```bash
npm run build
```

### Backend

**Run dev server:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Lint and format:**
```bash
ruff check .          # Check
ruff format .         # Format
ruff check --fix .    # Fix issues
```

**Type checking:**
```bash
pyright
```

**Run tests:**
```bash
pytest                # All tests
pytest -v             # Verbose
pytest -k test_name   # Specific test
pytest --cov          # With coverage
```

**Code quality:**
```bash
python -m pytest --cov=app tests/
```

### Database

**Schema is managed automatically via SQLAlchemy models** — no manual SQL migrations for tables!

To add new tables:
1. Create a new model in `backend/app/models/`
2. Import it in `backend/app/models/__init__.py`
3. Restart the backend — it auto-creates the table on startup

**For custom SQL operations** (indexes, triggers, etc.):
1. Add SQL to `backend/app/main.py` in the RLS setup section
2. Restart the backend

**View schema:**
```bash
# Supabase dashboard → Table Editor
# or
psql postgresql://user:password@host:5432/postgres  # Using pooler connection
```

## 🧪 Testing

### Backend (pytest)

```bash
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest -k test_projects   # Run specific tests
pytest --cov              # With coverage report
```

### Frontend (Vitest)

```bash
cd frontend
npm run test              # Run tests
npm run test:ui           # Interactive test UI
npm run test:watch        # Watch mode
```

## ✅ Validation

Run the complete validation suite before committing:

```bash
# Backend
cd backend
ruff check .
ruff format --check .
pyright
pytest

# Frontend
cd frontend
npm run lint
npm run type-check
npm run test
npm run build
```

Or use the convenience script:
```bash
./scripts/validate.sh
```

## 🔗 API

### Health Check

```
GET /health
→ { "status": "ok" }
```

### Projects (Example)

All endpoints require authentication (Bearer token).

```
GET    /api/v1/projects              # List your projects
POST   /api/v1/projects              # Create project
GET    /api/v1/projects/{id}         # Get project
PATCH  /api/v1/projects/{id}         # Update project
DELETE /api/v1/projects/{id}         # Delete project
```

See [docs/architecture.md](docs/architecture.md) for full API docs.

## 🚢 Deployment

### Frontend (Vercel)

1. Push code to GitHub
2. Connect repository to Vercel
3. Set environment variables in Vercel dashboard:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_URL`
4. Deploy

### Backend

Options:
- **Vercel**: Deploy as serverless function
- **Heroku**: `git push heroku main`
- **Railway**: Connect Git repository
- **Render**: Connect Git repository

Set environment variables on your hosting platform (never commit `.env`).

## 🤖 GitHub Copilot Workflow

This repository is optimized for AI-assisted development.

### Using Copilot Chat

Use the prompts in `.github/prompts/`:

1. **Implement a feature**
   - Use `implement-feature.prompt.md`
   - Copilot will follow the UNDERSTAND → INSPECT → PLAN → IMPLEMENT workflow

2. **Review code**
   - Use `review.prompt.md`
   - Get feedback on correctness, architecture, security

3. **Security audit**
   - Use `security-review.prompt.md`
   - Check for vulnerabilities and compliance

4. **Database changes**
   - Use `database-change.prompt.md`
   - Create migrations with RLS policies

5. **Test and validate**
   - Use `test-and-review.prompt.md`
   - Run full validation suite

### Inline Completions

Copilot will follow:
- `.github/copilot-instructions.md` (global)
- `.github/instructions/*.instructions.md` (path-specific)

Just start typing and Copilot will suggest completions following the patterns.

### Best Practices

1. **Be specific**: Describe what you want, not just "add a feature"
2. **Reference code**: Point to existing patterns to follow
3. **Ask for validation**: Always request validation before claiming done
4. **Review diffs**: Check Copilot's changes against security guidelines
5. **Test first**: Ask for tests before implementation

See [AGENTS.md](AGENTS.md) for complete AI development guide.

## 📖 Documentation

- [AGENTS.md](AGENTS.md) — Complete AI development guide
- [docs/architecture.md](docs/architecture.md) — System architecture
- [docs/security.md](docs/security.md) — Security guidelines
- [docs/database.md](docs/database.md) — Database schema and migrations
- [docs/development.md](docs/development.md) — Development setup and workflow

## 📋 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Frontend** | React | 18+ |
| | TypeScript | 5+ |
| | Vite | 4+ |
| | ESLint | Latest |
| | Vitest | Latest |
| **Backend** | Python | 3.12+ |
| | FastAPI | 0.100+ |
| | Pydantic | 2+ |
| | Pyright | Latest |
| | Ruff | Latest |
| | pytest | 7+ |
| **Database** | Supabase | Latest |
| | PostgreSQL | 15+ |
| **Deployment** | Vercel | - |

## 📝 License

[Choose a license]

## 🤝 Contributing

This is a starter repository. For a specific project:

1. Fork or clone this repository
2. Update `package.json`, `pyproject.toml`, README as needed
3. Replace example app with your actual application
4. Follow the development workflow in AGENTS.md

## ❓ Questions?

Refer to:
- [AGENTS.md](AGENTS.md) for AI development workflow
- [docs/development.md](docs/development.md) for setup help
- [docs/security.md](docs/security.md) for security questions
