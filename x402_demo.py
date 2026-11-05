from passport import Issuer, verify_passport, check_mandate
from receipt import ReceiptLog

def demo():
    issuer = Issuer()
    log = ReceiptLog()

    # 1. La banque émet un passeport pour l'agent A1
    passport = issuer.issue_passport(
        agent_id="agent:A1",
        mandate=["pay.invoice"],
        limits={"max_amount_eur": 100, "per_day": 1000},
    )
    print(f"[1] Passeport émis pour {passport['agent_id']} | mandat: {passport['mandate']}")
    ok, msg = verify_passport(passport)
    print(f"    Vérification: {ok} ({msg})")

    # 2. Le serveur répond 402 Payment Required (style x402)
    resource = {"url": "https://api.supplier.example/invoice/42", "price_eur": 42}
    print(f"[2] Serveur -> 402 Payment Required: {resource}")

    # 3. L'agent renvoie une autorisation de paiement
    payment = {"agent_id": "agent:A1", "resource": resource["url"], "amount_eur": 42}

    # 4. Le serveur vérifie passeport + mandat + plafond
    ok, msg = verify_passport(passport); assert ok, msg
    ok, msg = check_mandate(passport, "pay.invoice", payment["amount_eur"]); assert ok, msg
    print(f"[3] Contrôle mandat/plafond: OK (42 EUR <= 100 EUR)")

    # 5. Le serveur émet un reçu SCITT et l'ajoute au journal
    receipt = log.append("pay.invoice", "agent:A1", passport, payment)
    print(f"[4] Reçu SCITT émis: hash={receipt['hash'][:16]}...")

    # 6. Un auditeur externe vérifie l'intégrité du journal
    ok, msg = log.verify()
    print(f"[5] Intégrité du journal: {ok} ({msg})")

    # 7. Reconstitution d'audit
    print(f"[6] Audit: l'agent A1 a payé {payment['amount_eur']} EUR pour {payment['resource']}")
    print(f"    passport_hash={receipt['passport_hash'][:16]}...")
    print(f"    payload_hash ={receipt['payload_hash'][:16]}...")

    # 8. Test de falsification : on modifie un reçu et on vérifie que le journal le détecte
    log.entries[0]["action"] = "pay.invoice_FAKE"
    ok, msg = log.verify()
    print(f"[7] Test de falsification -> détecté: {not ok} ({msg})")
    # Bonus : ajouter une 2e entrée, puis falsifier la 1re -> détection par chaîne
    log2 = ReceiptLog()
    e0 = log2.append("pay.invoice", "agent:A1", passport, payment)
    e1 = log2.append("pay.invoice", "agent:A1", passport, payment)
    print(f"\n[BONUS] Journal à 2 entrées, intégrité: {log2.verify()}")

    # On falsifie l'entrée 0 (hash + action)
    log2.entries[0]["action"] = "FAKE"
    ok, msg = log2.verify()
    print(f"[BONUS] Après falsification entrée 0 -> détecté: {not ok} ({msg})")

    # On tente de recalculer le hash de l'entrée 0 pour masquer la fraude
    from receipt import h, _canon
    body0 = {k: v for k, v in log2.entries[0].items() if k not in ("sig", "hash")}
    log2.entries[0]["hash"] = h(body0)
    ok, msg = log2.verify()
    print(f"[BONUS] Après recalcul du hash entrée 0 -> détecté: {not ok} ({msg})")

if __name__ == "__main__":
    demo()