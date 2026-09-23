# Modular Network Compliance & Remediation Prototype

**Prototype scope:** pfSense Firewall + uploaded CIS benchmark PDFs

This project is a modular proof-of-concept for an AI-assisted, vendor-neutral network security compliance and controlled remediation platform.

The current prototype can:

1. Accept multiple benchmark PDF versions.
2. Extract candidate benchmark controls using deterministic parsing and optional AI assistance.
3. Require administrator review before activating extracted controls.
4. Connect to pfSense over SSH.
5. Perform a device capability check before assessment/remediation.
6. Collect live configuration and normalize it.
7. Evaluate reviewed benchmark controls.
8. Use a semantic AI layer for configuration understanding.
9. Use a separate remediation AI layer for remediation planning.
10. Run a safety validator before real changes.
11. Require administrator approval.
12. Create a configuration backup/checkpoint where supported.
13. Push an approved change through the device adapter.
14. Recollect state and verify compliance after the change.
15. Record audit events and generate a PDF report.

## Important safety boundary

Remediation AI output is **not executed directly**. A proposed change must pass safety validation and administrator approval before execution.

## Important prototype boundary

The actual CIS benchmark content is not fabricated in this repository. Upload the benchmark PDF and review the extracted controls before activation.

The live pfSense VM is external to this development environment. The SSH path must be tested against the configured VM before real remediation is used.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python app.py
```

Optional AI dependencies:

```bash
pip install -r requirements-gemini.txt
```

## Project structure

```text
backend/
  api/                 HTTP API
  device/              device adapters and SSH
  parsing/             parsing/normalization
  compliance/          benchmarks and evaluation
  intelligence/        semantic + remediation AI
  remediation/         safety + controlled execution
  verification/        post-change verification
  audit/               audit events
  reporting/           PDF reports
  core/                settings/shared runtime concerns

frontend/              prototype UI
shared/                contracts and common models
data/                  benchmark/demo data
reference/              architecture/reference material
docs/                   project documentation
tests/                  automated tests
```

## Documentation

Start with [`docs/PROTOTYPE_GUIDE.md`](docs/PROTOTYPE_GUIDE.md). It contains both a short explanation for quickly understanding the system and a detailed explanation for developers continuing the project.

See [`docs/README.md`](docs/README.md) for the complete documentation index.
