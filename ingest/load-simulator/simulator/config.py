from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "app_db"
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "app_password"
    QUERY_RATE: int = 10
    SLOW_QUERY_PROBABILITY: float = 0.1
    WRITE_PROBABILITY: float = 0.3
    
    class Config:
        env_file = ".env"
