# Login and Run Guide

## Start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000/login
```

## Prototype login

```text
Username: admin
Password: admin@123
```

The credentials are intentionally hardcoded for the prototype. Replace this authentication model before any production deployment.

## Workflow

1. **Connection** — enter the pfSense host, SSH port, username and password; run the capability check.
2. **Compliance** — upload one or more CIS benchmark PDFs; review extracted controls; activate the reviewed version.
3. **Assessment** — choose an active benchmark and run the live assessment against the saved pfSense target.
4. **Remediation** — open a failed finding, generate the remediation plan, validate safety, approve the real push, and run post-change verification.
5. **Audit / report** — review recorded events and download the assessment report.
