from datetime import datetime
from typing import Literal, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PrincipalCreate(BaseModel):
    """Input for creating a new principal (agent, service, bot, robot)."""
    principal_name: str = Field(..., min_length=1, max_length=200)
    owner_id: str = Field(..., min_length=1, max_length=200)
    principal_type: Literal["agent", "service", "robot", "bot"] = "agent"
    profile: str = Field(default="default", max_length=50)


class PrincipalCreated(BaseModel):
    """Response after creating a principal. The private key is shown ONCE."""
    principal_id: UUID
    principal_name: str
    owner_id: str
    principal_type: str
    public_key_jwk: dict
    profile: str
    status: str
    created_at: datetime
    private_key_b64: str = Field(
        ...,
        description="Ed25519 private key, base64url-encoded. Store securely. Shown only once.",
    )

class PrincipalRead(BaseModel):
    """Public view of a principal. Never exposes the private key."""
    principal_id: UUID
    principal_name: str
    owner_id: str
    principal_type: str
    public_key_jwk: dict
    profile: str
    status: str
    created_at: datetime    

class MandateCreate(BaseModel):
    """Input for attaching a mandate to a principal."""
    allowed_actions: list[str] = Field(..., min_length=1, examples=[["payment.initiate", "invoice.approve"]])
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        examples=[{"max_amount_eur": 100, "per_day": 10}],
    )
    valid_for_hours: int = Field(default=24, ge=1, le=8760)


class MandateRead(BaseModel):
    """Response after creating a mandate."""
    mandate_id: UUID
    principal_id: UUID
    allowed_actions: list[str]
    constraints: dict[str, Any]
    valid_from: datetime
    valid_until: datetime
    status: str



class AuthorizationRequest(BaseModel):
    """Input for requesting authorization of an action."""
    principal_id: UUID
    action: str = Field(..., examples=["payment.initiate"])
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        examples=[{"amount_eur": 42}],
    )


class AuthorizationDecision(BaseModel):
    """Result of an authorization check. A receipt is created on 'allow'."""
    decision: Literal["allow", "deny"]
    reason: str
    principal_id: UUID
    action: str
    mandate_id: Optional[UUID] = None
    receipt_id: Optional[UUID] = None
    timestamp: datetime


class ReceiptRead(BaseModel):
    """Public view of a receipt (audit trail)."""
    receipt_id: UUID
    principal_id: UUID
    action: str
    resource: str
    constraints: Optional[dict[str, Any]]
    passport_hash: str
    previous_receipt_hash: Optional[str]
    created_at: datetime    