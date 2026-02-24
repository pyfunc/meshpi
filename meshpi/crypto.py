"""
meshpi.crypto
=============
Asymmetric + symmetric encryption for secure config exchange.

Flow:
  1. Host generates RSA key pair on first run → stores in ~/.meshpi/host_key
  2. Client sends its RSA public key to host
  3. Host encrypts config with AES session key, wraps session key with client's RSA public key
  4. Client decrypts session key, then decrypts config
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

MESHPI_DIR = Path.home() / ".meshpi"


def ensure_meshpi_dir() -> Path:
    MESHPI_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    return MESHPI_DIR


def generate_rsa_keypair() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def save_private_key(private_key: rsa.RSAPrivateKey, path: Path) -> None:
    path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    path.chmod(0o600)


def load_private_key(path: Path) -> rsa.RSAPrivateKey:
    return serialization.load_pem_private_key(path.read_bytes(), password=None)


def save_public_key(public_key: rsa.RSAPublicKey, path: Path) -> None:
    path.write_bytes(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )


def load_public_key(path: Path) -> rsa.RSAPublicKey:
    return serialization.load_pem_public_key(path.read_bytes())


def public_key_to_pem(public_key: rsa.RSAPublicKey) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def public_key_from_pem(pem: bytes) -> rsa.RSAPublicKey:
    return serialization.load_pem_public_key(pem)


# ---------------------------------------------------------------------------
# Host key setup
# ---------------------------------------------------------------------------

def get_or_create_host_keys() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Return host RSA key pair, generating on first run."""
    d = ensure_meshpi_dir()
    priv_path = d / "host_key.pem"
    pub_path = d / "host_key_pub.pem"

    if not priv_path.exists():
        priv, pub = generate_rsa_keypair()
        save_private_key(priv, priv_path)
        save_public_key(pub, pub_path)
        return priv, pub

    priv = load_private_key(priv_path)
    return priv, priv.public_key()


def get_or_create_client_keys() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Return client RSA key pair, generating on first run."""
    d = ensure_meshpi_dir()
    priv_path = d / "client_key.pem"
    pub_path = d / "client_key_pub.pem"

    if not priv_path.exists():
        priv, pub = generate_rsa_keypair()
        save_private_key(priv, priv_path)
        save_public_key(pub, pub_path)
        return priv, pub

    priv = load_private_key(priv_path)
    return priv, priv.public_key()


# ---------------------------------------------------------------------------
# Encrypt / Decrypt config payload
# ---------------------------------------------------------------------------

def encrypt_config(config: dict, client_public_key: rsa.RSAPublicKey) -> bytes:
    """
    Encrypt config dict for delivery to client.

    Returns JSON bytes:
    {
        "session_key_enc": <hex>,   # AES key encrypted with client RSA pub key
        "nonce": <hex>,
        "ciphertext": <hex>
    }
    """
    # Generate random 256-bit AES session key
    session_key = os.urandom(32)
    nonce = os.urandom(12)

    # Encrypt config with AES-GCM
    aes = AESGCM(session_key)
    plaintext = json.dumps(config).encode()
    ciphertext = aes.encrypt(nonce, plaintext, None)

    # Wrap session key with client RSA public key
    session_key_enc = client_public_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    payload = {
        "session_key_enc": session_key_enc.hex(),
        "nonce": nonce.hex(),
        "ciphertext": ciphertext.hex(),
    }
    return json.dumps(payload).encode()


def decrypt_config(payload_bytes: bytes, client_private_key: rsa.RSAPrivateKey) -> dict:
    """Decrypt config payload received from host."""
    payload = json.loads(payload_bytes)

    session_key = client_private_key.decrypt(
        bytes.fromhex(payload["session_key_enc"]),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    nonce = bytes.fromhex(payload["nonce"])
    ciphertext = bytes.fromhex(payload["ciphertext"])

    aes = AESGCM(session_key)
    plaintext = aes.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext)
