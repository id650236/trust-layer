import base64
import json
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.schemas import PrincipalCreate, PrincipalCreated, PrincipalRead
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from app.db import get_db
from app.models import Principal
from app.schemas import PrincipalCreate, PrincipalCreated

router = APIRouter(prefix="/v1", tags=["principals"])


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


@router.post("/principals", response_model=PrincipalCreated, status_code=201)
def create_principal(payload: PrincipalCreate, db: Session = Depends(get_db)):
    """
    Register a new principal and issue its Ed25519 key pair.
    The private key is returned exactly once — store it securely.
    """
    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key()

    priv_bytes = sk.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = pk.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    jwk = {"kty": "OKP", "crv": "Ed25519", "x": _b64url(pub_bytes)}

    principal = Principal(
        principal_name=payload.principal_name,
        owner_id=payload.owner_id,
        principal_type=payload.principal_type,
        public_key_jwk=jwk,
        profile=payload.profile,
    )
    db.add(principal)
    db.commit()
    db.refresh(principal)

    # Normalize: psycopg3 may return JSONB as str instead of dict
    jwk_out = principal.public_key_jwk
    if isinstance(jwk_out, str):
        jwk_out = json.loads(jwk_out)

    return PrincipalCreated(
        principal_id=principal.principal_id,
        principal_name=principal.principal_name,
        owner_id=principal.owner_id,
        principal_type=principal.principal_type,
        public_key_jwk=jwk_out,
        profile=principal.profile,
        status=principal.status,
        created_at=principal.created_at,
        private_key_b64=_b64url(priv_bytes),
    )

@router.get("/principals/{principal_id}", response_model=PrincipalRead)
def get_principal(principal_id: UUID, db: Session = Depends(get_db)):
    """
    Retrieve a principal by its ID.
    The private key is never returned by this endpoint.
    """
    principal = db.query(Principal).filter(Principal.principal_id == principal_id).first()
    if principal is None:
        raise HTTPException(status_code=404, detail="Principal not found")

    jwk = principal.public_key_jwk
    if isinstance(jwk, str):
        jwk = json.loads(jwk)

    return PrincipalRead(
        principal_id=principal.principal_id,
        principal_name=principal.principal_name,
        owner_id=principal.owner_id,
        principal_type=principal.principal_type,
        public_key_jwk=jwk,
        profile=principal.profile,
        status=principal.status,
        created_at=principal.created_at,
    )