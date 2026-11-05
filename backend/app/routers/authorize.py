import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Principal, Mandate, Receipt
from app.schemas import AuthorizationRequest, AuthorizationDecision, ReceiptRead

router = APIRouter(prefix="/v1", tags=["authorize"])


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def _hash_cose(cose: bytes) -> str:
    return hashlib.sha256(cose).hexdigest()


def _normalize_jsonb(v):
    if isinstance(v, str):
        return json.loads(v)
    return v


def _check_constraints(mandate_c: dict, request_c: dict) -> tuple[bool, str]:
    """MVP: for each 'max_X' in mandate, ensure request's 'X' <= max."""
    for key, max_val in mandate_c.items():
        if key.startswith("max_") and isinstance(max_val, (int, float)):
            req_key = key[4:]
            if req_key in request_c:
                if request_c[req_key] > max_val:
                    return False, f"{req_key}={request_c[req_key]} exceeds limit {max_val}"
    return True, "ok"


@router.post("/authorize", response_model=AuthorizationDecision)
def authorize(payload: AuthorizationRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)

    principal = db.query(Principal).filter(Principal.principal_id == payload.principal_id).first()
    if principal is None:
        return AuthorizationDecision(
            decision="deny", reason="principal not found",
            principal_id=payload.principal_id, action=payload.action, timestamp=now,
        )

    if principal.status != "active":
        return AuthorizationDecision(
            decision="deny", reason=f"principal status is {principal.status}",
            principal_id=payload.principal_id, action=payload.action, timestamp=now,
        )

    mandates = (
        db.query(Mandate)
        .filter(Mandate.principal_id == payload.principal_id)
        .filter(Mandate.status == "active")
        .filter(Mandate.valid_from <= now)
        .filter(Mandate.valid_until > now)
        .all()
    )

    candidate = next((m for m in mandates if payload.action in m.allowed_actions), None)
    if candidate is None:
        return AuthorizationDecision(
            decision="deny", reason=f"no active mandate allows action '{payload.action}'",
            principal_id=payload.principal_id, action=payload.action, timestamp=now,
        )

    ok, msg = _check_constraints(_normalize_jsonb(candidate.constraints) or {}, payload.constraints or {})
    if not ok:
        return AuthorizationDecision(
            decision="deny", reason=msg, mandate_id=candidate.mandate_id,
            principal_id=payload.principal_id, action=payload.action, timestamp=now,
        )

    # ALLOW — create receipt
    passport_hash = hashlib.sha256(_canon(_normalize_jsonb(principal.public_key_jwk))).hexdigest()

    last = (
        db.query(Receipt)
        .filter(Receipt.principal_id == payload.principal_id)
        .order_by(Receipt.created_at.desc())
        .first()
    )
    prev_hash = _hash_cose(last.receipt_cose) if last else None

    body = {
        "principal_id": str(payload.principal_id),
        "action": payload.action,
        "constraints": payload.constraints,
        "mandate_id": str(candidate.mandate_id),
        "timestamp": now.isoformat(),
    }
    cose = _canon(body)

    receipt = Receipt(
        principal_id=payload.principal_id,
        action=payload.action,
        resource="",
        constraints=payload.constraints,
        passport_hash=passport_hash,
        previous_receipt_hash=prev_hash,
        receipt_cose=cose,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    return AuthorizationDecision(
        decision="allow", reason="action authorized by mandate",
        principal_id=payload.principal_id, action=payload.action,
        mandate_id=candidate.mandate_id, receipt_id=receipt.receipt_id, timestamp=now,
    )