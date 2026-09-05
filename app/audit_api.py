from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth import APIKeyAuthenticator, Role
from app.store import SQLiteStore


class AuditResponse(BaseModel):
    event_id: str
    actor: str
    role: str
    action: str
    resource: str
    details: dict[str, object]
    occurred_at: datetime


def create_audit_router(store: SQLiteStore, authenticator: APIKeyAuthenticator) -> APIRouter:
    router = APIRouter(prefix="/api/v1/audit-events", tags=["audit"])

    @router.get(
        "",
        response_model=list[AuditResponse],
        dependencies=[Depends(authenticator.require(Role.ADMIN))],
    )
    def list_events(limit: int = Query(default=100, ge=1, le=500)) -> list[AuditResponse]:
        return [
            AuditResponse(
                event_id=event.event_id,
                actor=event.actor,
                role=event.role,
                action=event.action,
                resource=event.resource,
                details=event.details,
                occurred_at=event.occurred_at,
            )
            for event in store.list_audit_events(limit=limit)
        ]

    return router
