"""Rotacao de chaves Fernet: re-cifra todos os registros com a primaria atual.

Uso (com FERNET_KEYS="nova,atual" ja ativo):
    python -m app.security.rotate

Aborta com erro na primeira linha ilegivel (nada meio-migrado em silencio).
Registra uma linha de auditoria de sistema (ator NULL) com o total.
"""

from sqlalchemy import select

from app.audit.logger import log_action
from app.core.exceptions import DecryptionError
from app.db.session import SessionLocal
from app.models.audit_log import AuditAction, AuditResult
from app.models.record import Record
from app.security.crypto import KeyRing, keyring

BATCH_SIZE = 500


def rotate_records(db, ring: KeyRing, batch_size: int = BATCH_SIZE) -> dict[str, int]:
    """Decifra (qualquer chave do anel) e re-cifra (primaria), em lotes."""
    total = 0
    offset = 0
    while True:
        rows = db.scalars(
            select(Record).order_by(Record.id).offset(offset).limit(batch_size)
        ).all()
        if not rows:
            break
        for record in rows:
            try:
                plain = ring.decrypt(record.notes_ciphertext)
            except DecryptionError:
                raise DecryptionError(
                    f"registro {record.id} ilegivel com as chaves atuais; "
                    "rotacao abortada, nada foi commitado neste lote"
                ) from None
            record.notes_ciphertext = ring.encrypt(plain)
            total += 1
        offset += len(rows)
        db.commit()
    log_action(
        db,
        actor_id=None,
        action=AuditAction.RECORD_REENCRYPT,
        resource_type="record",
        result=AuditResult.SUCCESS,
    )
    db.commit()
    return {"total": total}


def main() -> None:
    db = SessionLocal()
    try:
        counts = rotate_records(db, keyring)
    finally:
        db.close()
    print(f"ROTATE-OK total={counts['total']}")


if __name__ == "__main__":
    main()
