"""
SecureDocAI — Digital Signer
================================
Signs sanitized PDF documents using X.509 certificates.
Guarantees document authenticity and tamper protection.
"""

from pathlib import Path
from typing import Optional

import structlog

from app.services.signing.key_manager import KeyManager
from app.core.exceptions import SigningError

logger = structlog.get_logger(__name__)


class DigitalSigner:
    """
    Digitally sign sanitized PDF documents.

    Uses PyHanko for PAdES-compliant PDF signing:
        - Embeds X.509 signature into the PDF
        - Includes certificate chain
        - Optional timestamping (TSA)
        - Signature verification support
    """

    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager

    def sign_pdf(
        self,
        input_path: Path,
        output_path: Path,
        reason: str = "Document sanitized and verified",
        location: str = "Edge Security Gateway",
    ) -> dict:
        """
        Sign a sanitized PDF document.

        Args:
            input_path: Path to the sanitized (redacted) PDF.
            output_path: Path for the signed output.
            reason: Reason for signing (embedded in signature).
            location: Location of signing (embedded in signature).

        Returns:
            Dict with signature metadata (serial, algorithm, etc.)

        Raises:
            SigningError: If signing fails.
        """
        try:
            from pyhanko.sign import signers, fields
            from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Get certificate info for audit
            cert_info = self.key_manager.get_cert_info()

            # Create signer using KeyManager paths
            if self.key_manager.p12_path and self.key_manager.p12_path.exists():
                signer = signers.SimpleSigner.load_pkcs12(
                    pfx_file=str(self.key_manager.p12_path),
                    passphrase=self.key_manager.p12_passphrase.encode() if self.key_manager.p12_passphrase else None,
                )
            elif self.key_manager.cert_path and self.key_manager.key_path:
                signer = signers.SimpleSigner.load(
                    key_file=str(self.key_manager.key_path),
                    cert_file=str(self.key_manager.cert_path),
                )
            else:
                raise SigningError(
                    message="Missing key paths for PyHanko SimpleSigner",
                    document_id="",
                )

            # Open the PDF for signing
            with open(str(input_path), "rb") as inf:
                w = IncrementalPdfFileWriter(inf)

                # Apply signature
                out = signers.sign_pdf(
                    w,
                    signers.PdfSignatureMetadata(
                        field_name="SecureDocAI_Signature",
                        reason=reason,
                        location=location,
                    ),
                    signer=signer,
                )

                # Write signed PDF
                with open(str(output_path), "wb") as outf:
                    outf.write(out.getbuffer())

            logger.info(
                "pdf_signed",
                input=str(input_path),
                output=str(output_path),
                cert_subject=cert_info["subject"],
            )

            return {
                "signed_path": str(output_path),
                "signature_serial": cert_info["serial_number"],
                "certificate_subject": cert_info["subject"],
                "certificate_issuer": cert_info["issuer"],
                "signing_algorithm": "SHA256withRSA",
                "reason": reason,
                "location": location,
            }

        except ImportError as e:
            logger.error("pyhanko_import_error", error=str(e))
            raise SigningError(
                message=f"PyHanko is not installed or import failed: {str(e)}",
                document_id="",
            )
        except Exception as e:
            raise SigningError(
                message=f"PDF signing failed: {str(e)}",
                document_id="",
            )

    def verify_signature(self, signed_path: Path) -> dict:
        """
        Verify the digital signature of a signed PDF.

        Returns:
            Dict with verification status and details.
        """
        try:
            from pyhanko.sign.validation import validate_pdf_signature
            from pyhanko.pdf_utils.reader import PdfFileReader

            with open(str(signed_path), "rb") as f:
                reader = PdfFileReader(f)
                sigs = reader.embedded_signatures

                if not sigs:
                    return {"valid": False, "reason": "No signatures found"}

                # Verify the first (primary) signature
                sig = sigs[0]
                status = validate_pdf_signature(sig)

                return {
                    "valid": status.valid,
                    "intact": status.intact,
                    "signer": str(status.signing_cert.subject) if status.signing_cert else "unknown",
                    "timestamp": status.timestamp_validity if hasattr(status, "timestamp_validity") else None,
                }

        except Exception as e:
            logger.error("signature_verification_error", error=str(e))
            return {"valid": False, "reason": str(e)}
