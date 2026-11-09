"""Read-only runtime guard. uCore owns backend/.venv; uv.lock owns dependencies.

No state or services are created. Rebuild with uv sync --project backend --locked
--extra dev. Remove only backend/.venv to discard this product's environment.
"""

import sys
from pathlib import Path


def check() -> None:
    owner = Path(__file__).resolve().parents[1] / "backend" / ".venv"
    if owner.is_symlink() or Path(sys.prefix).resolve() != owner:
        raise RuntimeError("Use uCore/backend/.venv, not a shared or system Python")
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("uCore requires Python 3.12")
    import importlib

    for name in ("aiohttp", "pydantic", "yaml"):
        importlib.import_module(name)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key = AESGCM.generate_key(bit_length=256)
    cipher = AESGCM(key)
    nonce = b"ucore-check!"
    assert (
        cipher.decrypt(nonce, cipher.encrypt(nonce, b"check", None), None) == b"check"
    )
    print("uCore backend environment: owned, Python 3.12, core imports and AES-GCM OK")


if __name__ == "__main__":
    try:
        check()
    except (RuntimeError, ImportError, AssertionError) as exc:
        print(f"Backend environment check failed: {exc}", file=sys.stderr)
        sys.exit(1)
