import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://assignment6:assignment6@127.0.0.1:5432/assignment6",
    )
    token_ttl_hours: int = int(os.environ.get("TOKEN_TTL_HOURS", "168"))


settings = Settings()
