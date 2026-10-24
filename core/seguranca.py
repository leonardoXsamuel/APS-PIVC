"""Hash e verificação de PIN (segundo fator do nível 3)."""
import hashlib
import hmac

import config


def hash_pin(pin: str) -> str:
    return hashlib.sha256((config.PIN_PEPPER + pin).encode()).hexdigest()


def pin_valido(pin: str, pin_hash: str | None) -> bool:
    if not pin or not pin_hash:
        return False
    return hmac.compare_digest(hash_pin(pin), pin_hash)


def formato_pin_ok(pin: str) -> bool:
    return len(pin) == 6 and pin.isdigit()
