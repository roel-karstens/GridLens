# Documentation Index

Complete documentation for GridLens. Start here to understand the project.

## 📚 Core Documentation

### [implementation.md](implementation.md)
**What was built** — Complete overview of all 6 phases (2-7):
- Phase 2: Database & domain models
- Phase 3: ENTSO-E client & parser
- Phase 4: Ingestion service
- Phase 5: Backend API implementation
- Phase 6: Frontend dashboard UI
- Phase 7: Historical & comparison views
- Code statistics, features, and limitations

**Use this to**: Understand the full implementation and architecture

---

### [validation.md](validation.md)
**How to test everything** — Comprehensive testing and validation guide:
- Prerequisites and environment setup
- Backend validation (Python syntax, linting, type checking, tests)
- Frontend validation (ESLint, TypeScript, build, tests)
- Integration testing (manual flows, API testing with cURL)
- Security validation (authentication, RLS, input validation)
- Troubleshooting guide

**Use this to**: Verify the implementation works correctly

---

### [compliance.md](compliance.md)
**Instruction file adherence** — Verification that all code follows guidelines:
- Backend instructions compliance (type hints, services, auth)
- Frontend instructions compliance (types, hooks, components)
- Testing instructions (test structure, coverage)
- Database instructions (migrations, RLS, constraints)
- Code quality standards
- Security verification
- Pre-commit checklist

**Use this to**: Confirm all architecture decisions are sound

---

## 📐 Architecture & Design

### [architecture.md](architecture.md)
System design and component interactions:
- Data flow (ENTSO-E → Parser → Ingestion → Query → API → Frontend)
- Layer responsibilities
- Key design decisions
- Technology choices

**Use this to**: Understand how components fit together

---

### [database.md](database.md)
Database schema and design:
- Table structure (electricity_observations)
- Columns and types
- Constraints and indexes
- Row Level Security (RLS) policies
- Migration strategy

**Use this to**: Learn about data persistence layer

---

### [security.md](security.md)
Security architecture and best practices:
- Authentication (Supabase JWT)
- Authorization (RLS policies)
- API security
- Frontend security
- Data validation
- Error handling

**Use this to**: Understand security model

---

### [development.md](development.md)
Development workflow and guidelines:
- Getting started
- Development environment setup
- Coding standards
- Running tests
- Building for production

**Use this to**: Set up local development

---

## 🎯 Decision Records

### [decisions/](decisions/)
Architecture Decision Records (ADRs) documenting major choices:
- ADR-001: Auto-migrations via Python (SQLAlchemy)
- Why each approach was chosen
- Trade-offs considered

**Use this to**: Understand why certain decisions were made

---

## Quick Links

- **First time here?** → Start with [implementation.md](implementation.md)
- **Want to test it?** → Read [validation.md](validation.md)
- **Curious about architecture?** → Check [architecture.md](architecture.md)
- **Setting up locally?** → See [development.md](development.md)
- **Security concerns?** → Review [security.md](security.md)
- **Database questions?** → Look at [database.md](database.md)

---

## Audit & Quality

### [AUDIT.md](AUDIT.md)
Comprehensive code quality and consistency review:
- Type safety verification (TypeScript, Python)
- SOLID principles audit
- DRY principle verification
- Security review
- Documentation completeness
- Test coverage analysis
- Best practices checklist
- Issues found and resolved

**Use this to**: Understand the code quality standards met by this project

---

## Root Documentation

The root folder also contains:
- **[README.md](../README.md)** — Project overview and getting started
- **[AGENTS.md](../AGENTS.md)** — AI development workflow with Copilot

---

**Last updated**: October 1, 2026  
**Status**: All phases implemented and validated ✓
