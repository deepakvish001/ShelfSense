import os
from dataclasses import dataclass
from enum import StrEnum


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True, slots=True)
class Settings:
    environment: Environment
    database_path: str
    allowed_origins: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "Settings":
        environment = Environment(os.getenv("APP_ENV", Environment.DEVELOPMENT))
        database_path = os.getenv("DATABASE_PATH", "shelfsense.db").strip()
        if not database_path:
            raise RuntimeError("DATABASE_PATH cannot be empty")
        allowed_origins = tuple(
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
            if origin.strip()
        )
        if environment is Environment.PRODUCTION and "*" in allowed_origins:
            raise RuntimeError("wildcard CORS origin is not allowed in production")
        return cls(
            environment=environment,
            database_path=database_path,
            allowed_origins=allowed_origins,
        )
