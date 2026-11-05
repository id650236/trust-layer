import json
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Principal, Mandate
from app.schemas import MandateCreate, MandateRead

router = APIRouter(prefix="/v1", tags=["mandates"])


@router.post(
    "/principals/{principal_id}/mandates",
    response_model=MandateRead,
    status_code=201,
)
def create_mandate(
    principal_id: UUID,
    payload: MandateCreate,
    db: Session = Depends(get_db),
):
    """
    Attach a mandate to a principal.
    A mandate defines which actions the principal is allowed to perform,
    under which constraints, and for how long.
    """
    principal = db.query(Principal).filter(Principal.principal_id == principal_id).first()
    if principal is None:
        raise HTTPException(status_code=404, detail="Principal not found")

    valid_until = datetime.now(timezone.utc) + timedelta(hours=payload.valid_for_hours)

    mandate = Mandate(
        principal_id=principal_id,
        allowed_actions=payload.allowed_actions,
        constraints=payload.constraints,
        valid_until=valid_until,
    )
    db.add(mandate)
    db.commit()
    db.refresh(mandate)

    constraints = mandate.constraints
    if isinstance(constraints, str):
        constraints = json.loads(constraints)

    return MandateRead(
        mandate_id=mandate.mandate_id,
        principal_id=mandate.principal_id,
        allowed_actions=list(mandate.allowed_actions),
        constraints=constraints,
        valid_from=mandate.valid_from,
        valid_until=mandate.valid_until,
        status=mandate.status,
    )


@router.get(
    "/principals/{principal_id}/mandates",
    response_model=list[MandateRead],
)
def list_mandates(principal_id: UUID, db: Session = Depends(get_db)):
    """List all mandates attached to a principal."""
    principal = db.query(Principal).filter(Principal.principal_id == principal_id).first()
    if principal is None:
        raise HTTPException(status_code=404, detail="Principal not found")

    mandates = db.query(Mandate).filter(Mandate.principal_id == principal_id).all()

    result = []
    for m in mandates:
        c = m.constraints
        if isinstance(c, str):
            c = json.loads(c)
        result.append(MandateRead(
            mandate_id=m.mandate_id,
            principal_id=m.principal_id,
            allowed_actions=list(m.allowed_actions),
            constraints=c,
            valid_from=m.valid_from,
            valid_until=m.valid_until,
            status=m.status,
        ))
    return result