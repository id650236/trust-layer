-- Trust Service — schéma générique
-- Cœur universel : principals, mandates, receipts, profiles

CREATE TABLE principals (
    principal_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_name      TEXT NOT NULL,
    owner_id            TEXT NOT NULL,
    principal_type      TEXT NOT NULL,
    public_key_jwk      JSONB NOT NULL,
    profile             TEXT NOT NULL DEFAULT 'default',
    status              TEXT NOT NULL DEFAULT 'active',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE mandates (
    mandate_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id        UUID NOT NULL REFERENCES principals(principal_id),
    allowed_actions     TEXT[] NOT NULL,
    constraints         JSONB NOT NULL,
    valid_from          TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_until         TIMESTAMPTZ NOT NULL,
    status              TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE receipts (
    receipt_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id          UUID NOT NULL REFERENCES principals(principal_id),
    action                TEXT NOT NULL,
    resource              TEXT NOT NULL,
    constraints           JSONB,
    passport_hash         TEXT NOT NULL,
    previous_receipt_hash TEXT,
    receipt_cose          BYTEA NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT unique_previous_hash UNIQUE (previous_receipt_hash)
);

CREATE TABLE profiles (
    profile_id          TEXT PRIMARY KEY,
    display_name        TEXT NOT NULL,
    action_catalog      JSONB NOT NULL,
    constraint_schema   JSONB NOT NULL,
    compliance_mappings JSONB
);

CREATE INDEX idx_receipts_principal ON receipts(principal_id);
CREATE INDEX idx_receipts_created   ON receipts(created_at);