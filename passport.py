import json, time, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

def b64(b):   return base64.urlsafe_b64encode(b).decode().rstrip("=")
def unb64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def canonical(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()

class Issuer:
    """L'entreprise qui émet les passeports d'agents (ex: la banque)."""
    def __init__(self):
        self.sk = Ed25519PrivateKey.generate()
        self.pk = self.sk.public_key()

    def pubkey_b64(self):
        return b64(self.pk.public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw))

    def issue_passport(self, agent_id, mandate, limits, ttl=3600):
        now = int(time.time())
        body = {
            "v": 1,
            "agent_id": agent_id,
            "issuer": self.pubkey_b64(),
            "mandate": mandate,
            "limits": limits,
            "iat": now,
            "exp": now + ttl,
        }
        sig = self.sk.sign(canonical(body))
        return {**body, "sig": b64(sig)}

def verify_passport(passport, expected_issuer=None):
    body = {k: v for k, v in passport.items() if k != "sig"}
    if expected_issuer and passport["issuer"] != expected_issuer:
        return False, "wrong issuer"
    if passport["exp"] < int(time.time()):
        return False, "expired"
    pk = Ed25519PublicKey.from_public_bytes(unb64(passport["issuer"]))
    try:
        pk.verify(unb64(passport["sig"]), canonical(body))
        return True, "ok"
    except InvalidSignature:
        return False, "bad signature"

def check_mandate(passport, action, amount_eur=0):
    if action not in passport["mandate"]:
        return False, f"action '{action}' not in mandate"
    if amount_eur > passport["limits"].get("max_amount_eur", 0):
        return False, f"amount {amount_eur} exceeds limit"
    return True, "ok"