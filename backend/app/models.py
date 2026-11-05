from sqlalchemy import Column, String, DateTime, LargeBinary, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
import uuid
from app.db import Base


class Principal(Base):
    __tablename__ = "principals"

    principal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    principal_name = Column(String, nullable=False)
    owner_id = Column(String, nullable=False)
    principal_type = Column(String, nullable=False)
    public_key_jwk = Column(JSONB, nullable=False)
    profile = Column(String, nullable=False, default="default")
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Mandate(Base):
    __tablename__ = "mandates"

    mandate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    principal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("principals.principal_id"),
        nullable=False,
    )
    allowed_actions = Column(ARRAY(String), nullable=False)
    constraints = Column(JSONB, nullable=False, default=dict)
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False, default="active")


class Receipt(Base):
    __tablename__ = "receipts"

    receipt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    principal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("principals.principal_id"),
        nullable=False,
    )
    action = Column(String, nullable=False)
    resource = Column(String, nullable=False, default="")
    constraints = Column(JSONB, nullable=True)
    passport_hash = Column(String, nullable=False)
    previous_receipt_hash = Column(String, nullable=True)
    receipt_cose = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())