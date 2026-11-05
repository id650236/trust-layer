import json, time, hashlib, base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

def b64(b):   return base64.urlsafe_b64encode(b).decode().rstrip("=")
def unb64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
def _canon(o): return json.dumps(o, sort_keys=True, separators=(",", ":")).encode()
def h(o):     return hashlib.sha256(_canon(o)).hexdigest()

class ReceiptLog:
    """Journal append-only à chaînage de hachage, signé (style SCITT)."""
    def __init__(self):
        self.sk = Ed25519PrivateKey.generate()
        self.pk = self.sk.public_key()
        self.entries = []

    def pubkey_b64(self):
        return b64(self.pk.public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw))

    def append(self, action, agent_id, passport, payload):
        prev_hash = self.entries[-1]["hash"] if self.entries else "0" * 64
        body = {
            "seq": len(self.entries),
            "ts": time.time_ns(),
            "action": action,
            "agent_id": agent_id,
            "passport_hash": h(passport),
            "payload_hash": h(payload),
            "prev_hash": prev_hash,
        }
        sig = self.sk.sign(_canon(body))
        entry = {**body, "sig": b64(sig), "hash": h(body)}
        self.entries.append(entry)
        return entry

    def verify(self):
        pk = Ed25519PublicKey.from_public_bytes(unb64(self.pubkey_b64()))
        for i, e in enumerate(self.entries):
            body = {k: v for k, v in e.items() if k not in ("sig", "hash")}
            expected_prev = self.entries[i-1]["hash"] if i > 0 else "0" * 64
            if e["prev_hash"] != expected_prev:
                return False, f"chain broken at entry {i}"
            if h(body) != e["hash"]:
                return False, f"hash mismatch at entry {i}"
            try:
                pk.verify(unb64(e["sig"]), _canon(body))
            except InvalidSignature:
                return False, f"bad signature at entry {i}"
        return True, "ok"