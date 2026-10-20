import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _get_encryption_key() -> bytes:
    """
    Returns a 32-byte (256-bit) encryption key derived from TOKEN_ENCRYPTION_KEY or SECRET_KEY.
    """
    raw_key = os.getenv("TOKEN_ENCRYPTION_KEY") or os.getenv("SECRET_KEY", "subtracker-super-secret-jwt-key-2026")
    # Derive exactly 32 bytes via SHA-256
    return hashlib.sha256(raw_key.encode("utf-8")).digest()


def encrypt_token(token: str) -> str:
    """
    Encrypts a token string using AES-256-GCM.
    Returns base64 encoded string containing 12-byte nonce + ciphertext + tag.
    """
    if not token:
        return ""
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # Standard 96-bit nonce for AES-GCM
    ciphertext = aesgcm.encrypt(nonce, token.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_token(encrypted_token_b64: str) -> str:
    """
    Decrypts an AES-256-GCM encrypted token.
    Raises ValueError if decryption fails or data has been tampered with.
    """
    if not encrypted_token_b64:
        return ""
    try:
        raw_data = base64.b64decode(encrypted_token_b64.encode("utf-8"))
        if len(raw_data) < 12:
            raise ValueError("Invalid encrypted data length")
        nonce = raw_data[:12]
        ciphertext = raw_data[12:]
        key = _get_encryption_key()
        aesgcm = AESGCM(key)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")
