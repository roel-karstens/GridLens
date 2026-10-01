from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    environment: str = "development"
    database_url: str | None = None
    
    # ENTSO-E integration
    entsoe_api_token: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
