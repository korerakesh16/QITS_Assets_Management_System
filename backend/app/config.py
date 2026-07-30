import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str 
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 
    CORS_ORIGINS: str = 

    @property
    def cors_origins_list(self) -> List[str]:
        return [i.strip() for i in self.CORS_ORIGINS.split(",") if i.strip()]

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
