from app.audit import create_audit_event
from app.auth import Principal, Role


def test_audit_event_captures_actor_and_safe_details() -> None:
    event = create_audit_event(
        Principal("operator-1", Role.OPERATOR),
        action="inventory.received",
        resource="SOAP",
        details={"quantity": 10},
    )
    assert event.actor == "operator-1"
    assert event.role == "operator"
    assert event.safe_details["quantity"] == 10
