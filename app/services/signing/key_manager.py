"""
SecureDocAI — Key Manager
============================
Manages X.509 certificates and private keys for digital signing.
Handles key loading, validation, and rotation.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

import structlog

from app.core.exceptions import KeyManagementError

logger = structlog.get_logger(__name__)


class KeyManager:
    """
    Manage signing keys and certificates for the digital signature module.

    Supports:
        - PEM certificate + private key (separate files)
        - PKCS#12 keystore (.p12)
        - Key rotation (manual for POC)
    """

    def __init__(
        self,
        cert_path: Optional[Path] = None,
        key_path: Optional[Path] = None,
        p12_path: Optional[Path] = None,
        p12_passphrase: Optional[str] = None,
    ):
        self.cert_path = cert_path
        self.key_path = key_path
        self.p12_path = p12_path
        self.p12_passphrase = p12_passphrase
        self._certificate = None
        self._private_key = None

    def load_keys(self) -> None:
        """
        Load certificate and private key.

        Tries PKCS#12 first, then falls back to separate PEM files.
        """
        try:
            from cryptography import x509
            from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

            if self.p12_path and self.p12_path.exists():
                # Load from PKCS#12 keystore
                with open(self.p12_path, "rb") as f:
                    p12_data = f.read()

                private_key, certificate, _ = pkcs12.load_key_and_certificates(
                    p12_data,
                    self.p12_passphrase.encode() if self.p12_passphrase else None,
                )
                self._private_key = private_key
                self._certificate = certificate
                logger.info("keys_loaded", source="pkcs12", cert_subject=str(certificate.subject))

            elif self.cert_path and self.key_path:
                # Load from separate PEM files
                from cryptography.hazmat.primitives.serialization import load_pem_private_key

                with open(self.cert_path, "rb") as f:
                    self._certificate = x509.load_pem_x509_certificate(f.read())

                with open(self.key_path, "rb") as f:
                    self._private_key = load_pem_private_key(f.read(), password=None)

                logger.info("keys_loaded", source="pem", cert_subject=str(self._certificate.subject))
            else:
                raise KeyManagementError(message="No signing keys configured")

        except KeyManagementError:
            raise
        except Exception as e:
            raise KeyManagementError(message=f"Failed to load signing keys: {str(e)}")

    @property
    def certificate(self):
        """Get the loaded X.509 certificate."""
        if not self._certificate:
            raise KeyManagementError(message="Certificate not loaded. Call load_keys() first.")
        return self._certificate

    @property
    def private_key(self):
        """Get the loaded private key."""
        if not self._private_key:
            raise KeyManagementError(message="Private key not loaded. Call load_keys() first.")
        return self._private_key

    def get_cert_info(self) -> dict:
        """Get certificate metadata for audit logging."""
        cert = self.certificate
        return {
            "subject": str(cert.subject),
            "issuer": str(cert.issuer),
            "serial_number": str(cert.serial_number),
            "valid_from": cert.not_valid_before_utc.isoformat(),
            "valid_to": cert.not_valid_after_utc.isoformat(),
        }

    def is_cert_valid(self) -> bool:
        """Check if the certificate is currently valid (not expired)."""
        cert = self.certificate
        now = datetime.utcnow()
        return cert.not_valid_before_utc <= now <= cert.not_valid_after_utc
