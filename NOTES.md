# Known gaps — Trust Layer reference implementation

This document lists the deliberate simplifications in the current implementation
and what would be required to reach production parity with the SCITT spec and
real-world KYA/x402 ecosystems.

## 1. Single-issuer receipts (vs. SCITT's separation of roles)

In SCITT, the issuer signs a *statement* (what happened), and a separate
transparency service signs a *receipt* (attestation that the statement was
logged). Witnesses then replicate receipts to prevent retroactive rewrite.

**Current state:** one service signs everything. No separation of trust domains.
**Next step:** split `ReceiptLog` into `StatementIssuer` and `TransparencyService`.

## 2. No witness distribution

Receipts are stored in a single PostgreSQL table. A malicious operator could
truncate the table without detection.

**Current state:** append-only at the application level, not at the infrastructure level.
**Next step:** publish a Merkle root periodically to an external anchor (a public
transparency log, or a notary service), and replicate the log to at least two
independent witnesses.

## 3. Simulated x402 payments

The `POST /v1/authorize` endpoint checks constraints (`max_amount_eur`) but does
not initiate any real payment.

**Next step:** integrate a real x402 facilitator, issue a signed payment
authorization, and settle on-chain (USDC on Base or equivalent).

## 4. No KYC/KYB binding

`owner_id` is a free-form string. Nothing prevents an attacker from claiming to
be a different organization.

**Next step:** add a verification layer that binds `owner_id` to a legal entity
through a KYC/KYB provider, and store the verification result alongside the
principal.

## 5. No revocation endpoint

A principal remains `active` until it is deleted (which is blocked by foreign
keys) or its mandates expire.

**Next step:** add `POST /v1/principals/{id}/revoke` and `POST /v1/mandates/{id}/revoke`.
Both must emit a receipt in the audit log — revocation is itself an auditable event.

## 6. Receipt format not yet COSE-signed

The `receipt_cose` column currently stores the canonical JSON payload, not a
CBOR-encoded COSE Sign1 object as SCITT requires.

**Next step:** replace the JSON body with a real COSE Sign1 structure signed by
the transparency service key.

---

These gaps are intentional. The goal of this repository is to demonstrate the
mechanism end-to-end in a small, readable codebase — not to ship a production
system. Each gap is a small, well-scoped next step.