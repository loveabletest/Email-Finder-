# Email Verifier Backend

A production-ready FastAPI backend conversion of your Google Colab / Gradio bulk email verifier.

## Features

- POST `/verify/` accepts a CSV and runs email verification logic (MX and SMTP checks).
- GET `/health` for a quick health check.
- CSV output returned as base64 and path for download.
- Core verification logic extracted to a service module.

> ⚠️ The SMTP/MX checks rely on dnspython and making direct SMTP connections. When deploying, be mindful of your host's outbound port restrictions (many PaaS providers block SMTP or port 25). Consider using a dedicated email-validation API or a relay service for heavy traffic.

## Quickstart (local)

1. Clone:

```bash
git clone <repo-url>
cd email-verifier-backend
