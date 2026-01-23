import os
from pydantic import BaseModel


class Settings(BaseModel):
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_password: str = os.getenv("REDIS_PASSWORD", "MatKhau2026")

    # PostgreSQL Configuration
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", 5432))
    postgres_db: str = os.getenv("POSTGRES_DB", "cvjd_matcher")
    postgres_user: str = os.getenv("POSTGRES_USER", "anhld")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "MatKhau2026")

    @property
    def redis_url(self):
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}"


# Global settings instance (singleton-ish)
settings = Settings()


def update_settings(new_host: str, new_port: int, new_password: str = ""):
    """Update Redis settings at runtime."""
    global settings
    settings = Settings(
        redis_host=new_host,
        redis_port=new_port,
        redis_password=new_password
    )
