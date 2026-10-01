"""FastAPI application factory and configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.projects import router as projects_router
from app.api.electricity import router as electricity_router
from app.api.dev import router as dev_router
from app.core.config import settings
from app.dependencies import engine, DATABASE_URL
from app.models.project import Base
# Import all models to register them with Base
from app.models.electricity import ElectricityObservation  # noqa: F401

# Create database tables on startup
print(f"\n🔧 Starting up...")
print(f"📍 DATABASE_URL: {DATABASE_URL[:50]}..." if DATABASE_URL else "No DATABASE_URL")

try:
    print("📝 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
except Exception as e:
    print(f"❌ Error creating tables: {e}")

# Run migrations if using Supabase PostgreSQL
if DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    try:
        print("🔐 Setting up RLS policies...")
        with engine.begin() as conn:
            # Enable RLS
            conn.exec_driver_sql("ALTER TABLE IF EXISTS public.projects ENABLE ROW LEVEL SECURITY;")
            
            # Drop existing policies if they exist (cleaner than trying IF NOT EXISTS)
            for policy_name in [
                "users_select_own_projects",
                "users_insert_own_projects",
                "users_update_own_projects",
                "users_delete_own_projects",
            ]:
                conn.exec_driver_sql(
                    f"DROP POLICY IF EXISTS \"{policy_name}\" ON public.projects;"
                )
            
            # Create policies
            conn.exec_driver_sql("""
                CREATE POLICY "users_select_own_projects" ON public.projects
                  FOR SELECT USING (auth.uid() = owner_id);
            """)
            conn.exec_driver_sql("""
                CREATE POLICY "users_insert_own_projects" ON public.projects
                  FOR INSERT WITH CHECK (auth.uid() = owner_id);
            """)
            conn.exec_driver_sql("""
                CREATE POLICY "users_update_own_projects" ON public.projects
                  FOR UPDATE USING (auth.uid() = owner_id) WITH CHECK (auth.uid() = owner_id);
            """)
            conn.exec_driver_sql("""
                CREATE POLICY "users_delete_own_projects" ON public.projects
                  FOR DELETE USING (auth.uid() = owner_id);
            """)
            
            # Create indexes
            conn.exec_driver_sql("""
                CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON public.projects(owner_id);
            """)
            conn.exec_driver_sql("""
                CREATE INDEX IF NOT EXISTS idx_projects_created_at ON public.projects(created_at DESC);
            """)
            
            print("✅ RLS policies configured")
    except Exception as e:
        print(f"⚠️  Warning setting up RLS: {e}")
else:
    print("ℹ️  Not using PostgreSQL, skipping RLS setup")

print("🚀 Application starting...\n")

app = FastAPI(
    title="AI Full-Stack Starter API",
    description="FastAPI backend for project management",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Dev frontend
        "http://localhost:3000",  # Alt dev frontend
        "https://example.com",  # Production frontend (update as needed)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(projects_router)
app.include_router(electricity_router)

# Dev endpoints only in development mode
if settings.environment == "development":
    app.include_router(dev_router)


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {"message": "AI Full-Stack Starter API"}
