# 📁 SecureDocAI — Storage Directory

This directory contains all document artifacts managed by the system.

## Structure

| Directory | Purpose | Retention |
|-----------|---------|-----------|
| `uploads/` | Temporarily stored uploaded documents | Deleted after processing |
| `processed/` | Sanitized (redacted) PDFs | Retained for audit |
| `signed/` | Digitally signed sanitized PDFs | Final deliverable |
| `keys/` | Signing certificates and private keys | Secured access only |

## Security Notes

- **`keys/`** — Contains cryptographic material. Restrict filesystem permissions.
- **`uploads/`** — Original documents are deleted after processing. Never shared externally.
- **`processed/`** and **`signed/`** — Contain sanitized documents safe for external use.

## File Naming Convention

```
{document_id}_sanitized.pdf     → in processed/
{document_id}_signed.pdf        → in signed/
```
