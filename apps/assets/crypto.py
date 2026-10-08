"""Symmetric encryption for sensitive fields (credentials).

Uses Fernet (AES-128-CBC + HMAC). The key comes from the FIELD_ENCRYPTION_KEY
environment variable in production; for dev it is derived deterministically
from SECRET_KEY so the app runs out of the box. Set FIELD_ENCRYPTION_KEY
(urlsafe base64, 32 bytes) in any real deployment.
"""
import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _key():
    env = os.environ.get("FIELD_ENCRYPTION_KEY")
    if env:
        return env.encode()
    # Dev fallback: derive a valid 32-byte Fernet key from SECRET_KEY.
    digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet():
    return Fernet(_key())


def encrypt(text):
    if text is None or text == "":
        return ""
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token):
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except (InvalidToken, ValueError):
        # Key rotated or corrupt data; fail closed rather than leak/raise.
        return ""
