from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Secure Employee API"

    database_url: SecretStr

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    cors_origins: str = (
        "http://localhost:3000,http://localhost:5173"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


'''

Explanation
----------------
BaseSettings loads configuration from environment variables and the .env file.

SecretStr helps prevent accidental exposure when a secret value is displayed or represented.

@lru_cache avoids recreating the settings object on every call.

The following configuration:

jwt_secret_key: SecretStr

means the JWT secret must be provided.

The application should fail to start if the required secret is missing.

Important: SecretStr is not a secret manager or encryption mechanism. It does not prevent application code from deliberately accessing or leaking the underlying value.

'''