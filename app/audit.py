from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from app.auth import Principal


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    actor: str
    role: str
    action: str
    resource: str
    details: dict[str, Any]
    occurred_at: datetime

    @property
    def safe_details(self) -> MappingProxyType[str, Any]:
        return MappingProxyType(self.details)


def create_audit_event(
    principal: Principal,
    *,
    action: str,
    resource: str,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    if not action.strip() or not resource.strip():
        raise ValueError("audit action and resource are required")
    return AuditEvent(
        event_id=str(uuid4()),
        actor=principal.subject,
        role=principal.role.value,
        action=action.strip(),
        resource=resource.strip(),
        details=(details or {}).copy(),
        occurred_at=datetime.now(UTC),
    )
