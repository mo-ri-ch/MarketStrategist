from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Competitor Intelligence AI Assistant"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql://postgres:postgrespassword@db:5432/competitor_intelligence"
    REDIS_URL: str = "redis://redis:6379/0"
    QDRANT_URL: str = "http://qdrant:6333"
    ENVIRONMENT: str = "development"
    
    SECRET_KEY: str = "supersecretkeychangeinproduction"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
