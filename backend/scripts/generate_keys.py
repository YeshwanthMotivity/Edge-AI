"""
SecureDocAI — POC Key Generation Script
==========================================
Generates a self-signed X.509 certificate and private key for POC use.
Creates both PEM files and a PKCS#12 keystore.

Usage:
    python scripts/generate_keys.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_keys(output_dir: str = None):
    """Generate self-signed certificate and private key for POC."""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.primitives.asymmetric import rsa

    # Output directory
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent / "storage" / "keys"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating signing keys in: {output_dir}")

    # Generate RSA private key (2048-bit for POC, use 4096 for production)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Build self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SecureDocAI"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SecureDocAI Edge Gateway"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,  # Non-repudiation
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Save private key (PEM)
    key_path = output_dir / "private_key.pem"
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    print(f"  [OK] Private key:  {key_path}")

    # Save certificate (PEM)
    cert_path = output_dir / "certificate.pem"
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print(f"  [OK] Certificate:  {cert_path}")

    # Save PKCS#12 keystore
    p12_path = output_dir / "keystore.p12"
    p12_passphrase = b"securedocai_poc"
    p12_data = serialization.pkcs12.serialize_key_and_certificates(
        name=b"securedocai",
        key=private_key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(p12_passphrase),
    )
    with open(p12_path, "wb") as f:
        f.write(p12_data)
    print(f"  [OK] PKCS#12:      {p12_path}")
    print(f"  [KEY] P12 password: securedocai_poc")

    print("\n[OK] All keys generated successfully!")
    print("[WARN] These are for POC only. Use CA-signed certificates in production.")


if __name__ == "__main__":
    generate_keys()
