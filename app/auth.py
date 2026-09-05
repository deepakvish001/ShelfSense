import os
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from fastapi import Header, HTTPException, status


class Role(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    role: Role


class APIKeyAuthenticator:
    def __init__(self, principals_by_key: dict[str, Principal]) -> None:
        if not principals_by_key:
            raise ValueError("at least one API key is required")
        if any(not key for key in principals_by_key):
            raise ValueError("API keys cannot be empty")
        self._principals_by_key = principals_by_key.copy()

    @classmethod
    def from_environment(cls) -> "APIKeyAuthenticator":
        raw_keys = os.getenv("API_KEYS", "local-development-key:admin:local-admin")
        principals: dict[str, Principal] = {}
        for item in raw_keys.split(","):
            key, role, subject = (part.strip() for part in item.split(":", maxsplit=2))
            principals[key] = Principal(subject=subject, role=Role(role))
        return cls(principals)

    def authenticate(self, supplied_key: str | None) -> Principal:
        if supplied_key:
            for expected_key, principal in self._principals_by_key.items():
                if secrets.compare_digest(supplied_key, expected_key):
                    return principal
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="valid API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    def require(self, *allowed_roles: Role) -> Callable[..., Principal]:
        allowed = frozenset(allowed_roles)

        def authorize(
            x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
        ) -> Principal:
            principal = self.authenticate(x_api_key)
            if principal.role not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="insufficient role",
                )
            return principal

        return authorize
